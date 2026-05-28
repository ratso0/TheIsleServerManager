import subprocess
import os
import time
import threading
import psutil
from core.os_utils import get_os, get_server_executable

_server_process: subprocess.Popen = None
_log_thread: threading.Thread = None
_running = False


def get_launch_command(install_path: str, config: dict, os_type: str = None) -> list:
    """Build the server launch command from config"""
    if os_type is None:
        os_type = get_os()

    exe = get_server_executable(install_path, os_type)

    map_name    = config.get('map', 'Gateway')
    game_port   = config.get('game_port', 7777)
    query_port  = config.get('query_port', 27015)
    max_players = config.get('max_players', 100)
    server_name = config.get('server_name', 'The Isle Server')
    password    = config.get('server_password', '')
    rcon_port   = config.get('rcon_port', 27020)
    rcon_pass   = config.get('rcon_password', '')

    # EOS credentials – required, server crashes without these
    EOS_ID     = 'xyza7891gk5PRo3J7G9puCJGFJjmEguW'
    EOS_SECRET = 'pKWl6t5i9NJK8gTpVlAxzENZ65P8hYzodV8Dqe5Rlc8'

    args = [
        exe,
        map_name,
        f'-Port={game_port}',
        f'-QueryPort={query_port}',
        f'-MaxPlayers={max_players}',
        f'-ServerName={server_name}',
        '-log',
        f'-ini:Engine:[EpicOnlineServices]:DedicatedServerClientId={EOS_ID}',
        f'-ini:Engine:[EpicOnlineServices]:DedicatedServerClientSecret={EOS_SECRET}',
    ]

    if password:
        args.append(f'-Password={password}')

    if rcon_pass:
        args += [f'-RCONPort={rcon_port}', f'-RCONPassword={rcon_pass}']

    return args


def start_server(install_path: str, config: dict, os_type: str = None,
                 log_callback=None) -> bool:
    global _server_process, _log_thread, _running

    if is_running():
        if log_callback:
            log_callback("[WARN] Server is already running.")
        return False

    cmd = get_launch_command(install_path, config, os_type)
    exe = cmd[0]

    if not os.path.exists(exe):
        if log_callback:
            log_callback(f"[ERROR] Server executable not found: {exe}")
        return False

    if log_callback:
        log_callback(f"[INFO] Starting server: {' '.join(cmd[:3])}...")

    try:
        _server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=os.path.dirname(exe)
        )
        _running = True

        if log_callback:
            _log_thread = threading.Thread(
                target=_stream_logs,
                args=(log_callback,),
                daemon=True
            )
            _log_thread.start()

        if log_callback:
            log_callback(f"[INFO] Server started (PID: {_server_process.pid})")
        return True
    except Exception as e:
        if log_callback:
            log_callback(f"[ERROR] Failed to start server: {e}")
        return False


def _stream_logs(log_callback):
    global _server_process, _running
    try:
        for line in _server_process.stdout:
            if line:
                log_callback(line.rstrip())
    except Exception:
        pass
    _running = False
    log_callback("[INFO] Server process ended.")


def stop_server(log_callback=None) -> bool:
    global _server_process, _running
    if _server_process is None or not is_running():
        if log_callback:
            log_callback("[WARN] Server is not running.")
        return False
    try:
        proc = psutil.Process(_server_process.pid)
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except psutil.TimeoutExpired:
            proc.kill()
        _running = False
        _server_process = None
        if log_callback:
            log_callback("[INFO] Server stopped.")
        return True
    except Exception as e:
        if log_callback:
            log_callback(f"[ERROR] Failed to stop server: {e}")
        return False


def restart_server(install_path: str, config: dict, os_type: str = None,
                   log_callback=None) -> bool:
    if log_callback:
        log_callback("[INFO] Restarting server...")
    stop_server(log_callback)
    time.sleep(3)
    return start_server(install_path, config, os_type, log_callback)


def is_running() -> bool:
    global _server_process
    if _server_process is None:
        return False
    return _server_process.poll() is None


def get_stats() -> dict:
    """Return CPU/RAM usage of the server process"""
    global _server_process
    if _server_process is None or not is_running():
        return {'cpu': 0.0, 'ram_mb': 0.0, 'pid': None}
    try:
        proc = psutil.Process(_server_process.pid)
        return {
            'cpu': proc.cpu_percent(interval=0.1),
            'ram_mb': proc.memory_info().rss / (1024 * 1024),
            'pid': _server_process.pid
        }
    except Exception:
        return {'cpu': 0.0, 'ram_mb': 0.0, 'pid': None}
