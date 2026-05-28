import platform
import os
import sys
import ctypes


def get_os() -> str:
    """Returns 'windows' or 'linux'"""
    s = platform.system().lower()
    if 'windows' in s:
        return 'windows'
    elif 'linux' in s:
        return 'linux'
    return 'unknown'


def is_admin() -> bool:
    """Check if the process has admin/root privileges"""
    try:
        if get_os() == 'windows':
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False


def get_default_install_path(os_type: str = None) -> str:
    if os_type is None:
        os_type = get_os()
    if os_type == 'windows':
        drive = os.environ.get('SYSTEMDRIVE', 'C:')
        return os.path.join(drive + '\\', 'TheIsleServer')
    else:
        return os.path.expanduser('~/TheIsleServer')


def get_steamcmd_url(os_type: str = None) -> str:
    if os_type is None:
        os_type = get_os()
    if os_type == 'windows':
        return 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip'
    else:
        return 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz'


def get_steamcmd_executable(base_path: str, os_type: str = None) -> str:
    if os_type is None:
        os_type = get_os()
    if os_type == 'windows':
        return os.path.join(base_path, 'steamcmd', 'steamcmd.exe')
    else:
        return os.path.join(base_path, 'steamcmd', 'steamcmd.sh')


def get_server_executable(install_path: str, os_type: str = None) -> str:
    if os_type is None:
        os_type = get_os()
    if os_type == 'windows':
        return os.path.join(install_path, 'server', 'TheIsleServer.exe')
    else:
        return os.path.join(install_path, 'server', 'TheIsleServer.sh')


def get_config_path(install_path: str, os_type: str = None) -> str:
    if os_type is None:
        os_type = get_os()
    folder = 'WindowsServer' if os_type == 'windows' else 'LinuxServer'
    return os.path.join(install_path, 'server', 'TheIsle', 'Saved', 'Config', folder)


def run_as_admin_request():
    """On Windows, re-launch with admin rights. On Linux, print sudo hint."""
    if get_os() == 'windows':
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
    else:
        print("[INFO] Run with: sudo python3 main.py")
