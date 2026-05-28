import os
import subprocess
import zipfile
import tarfile
import stat
import requests
from core.os_utils import get_os, get_steamcmd_url, get_steamcmd_executable

THE_ISLE_SERVER_APP_ID = "412680"
THE_ISLE_BETA_BRANCH   = "evrima"


def download_file(url: str, dest_path: str, progress_callback=None) -> bool:
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        total = int(response.headers.get('content-length', 0))
        downloaded = 0
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total > 0:
                        progress_callback(int(downloaded / total * 100))
        return True
    except Exception as e:
        print(f"[SteamCMD] Download error: {e}")
        return False


def install_steamcmd(base_path: str, os_type: str = None,
                     log_callback=None, progress_callback=None) -> bool:
    """
    Download, extract and self-initialise SteamCMD.
    Must run steamcmd +quit once so it updates itself – otherwise
    app_update fails with 'Missing configuration'.
    """
    if os_type is None:
        os_type = get_os()

    steamcmd_dir = os.path.join(base_path, 'steamcmd')
    os.makedirs(steamcmd_dir, exist_ok=True)

    url = get_steamcmd_url(os_type)
    archive_name = 'steamcmd.zip' if os_type == 'windows' else 'steamcmd.tar.gz'
    archive_path = os.path.join(steamcmd_dir, archive_name)

    if log_callback:
        log_callback(f"Downloading SteamCMD from {url}...")

    ok = download_file(url, archive_path, progress_callback)
    if not ok:
        if log_callback:
            log_callback("[ERROR] Failed to download SteamCMD.")
        return False

    if log_callback:
        log_callback("Extracting SteamCMD...")

    try:
        if os_type == 'windows':
            with zipfile.ZipFile(archive_path, 'r') as z:
                z.extractall(steamcmd_dir)
        else:
            with tarfile.open(archive_path, 'r:gz') as t:
                t.extractall(steamcmd_dir)

        if os_type == 'linux':
            exe_path = os.path.join(steamcmd_dir, 'steamcmd.sh')
            if os.path.exists(exe_path):
                s = os.stat(exe_path)
                os.chmod(exe_path, s.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        os.remove(archive_path)
        if log_callback:
            log_callback("SteamCMD extracted successfully.")
    except Exception as e:
        if log_callback:
            log_callback(f"[ERROR] Extraction failed: {e}")
        return False

    # Run once so SteamCMD downloads its own updates (prevents 'Missing configuration')
    exe = get_steamcmd_executable(base_path, os_type)
    if log_callback:
        log_callback("Initialiserar SteamCMD (laddar ner egna uppdateringar)...")
        log_callback("  Detta kan ta 1-2 minuter...")
    try:
        subprocess.run([exe, '+quit'], cwd=steamcmd_dir, timeout=180,
                       capture_output=True)
        if log_callback:
            log_callback("SteamCMD är redo.")
    except Exception as e:
        if log_callback:
            log_callback(f"[WARN] SteamCMD init: {e}")
    return True


def is_steamcmd_installed(base_path: str, os_type: str = None) -> bool:
    return os.path.exists(get_steamcmd_executable(base_path, os_type))


def install_server(base_path: str, os_type: str = None,
                   log_callback=None, steam_username: str = 'anonymous',
                   steam_password: str = '') -> subprocess.Popen:
    """
    Run SteamCMD to install/update The Isle Evrima server.
    Returns the live Popen process so the caller can stream stdout.
    """
    if os_type is None:
        os_type = get_os()

    server_dir  = os.path.join(base_path, 'server')
    # ── FIX: define steamcmd_dir here so cwd is correct ─────────────
    steamcmd_dir = os.path.join(base_path, 'steamcmd')
    os.makedirs(server_dir, exist_ok=True)

    steamcmd_exe = get_steamcmd_executable(base_path, os_type)
    if not os.path.exists(steamcmd_exe):
        if log_callback:
            log_callback("[ERROR] SteamCMD saknas – installera det först.")
        return None

    login = ('anonymous' if steam_username == 'anonymous'
             else f'{steam_username} {steam_password}')

    cmd = [
        steamcmd_exe,
        '+@ShutdownOnFailedCommand', '1',
        '+@NoPromptForPassword',     '1',
        '+force_install_dir', server_dir,
        '+login', login,
        '+app_update', THE_ISLE_SERVER_APP_ID,
        '-beta', THE_ISLE_BETA_BRANCH,
        'validate',
        '+quit',
    ]

    if log_callback:
        log_callback(f"Starting server installation "
                     f"(AppID {THE_ISLE_SERVER_APP_ID} -beta {THE_ISLE_BETA_BRANCH})...")
        log_callback(f"Install directory: {server_dir}")

    # Windows: CREATE_NO_WINDOW so SteamCMD doesn't pop a console window
    kwargs = {}
    if os_type == 'windows':
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        bufsize=1,
        cwd=steamcmd_dir,   # ← was NameError before; now correctly defined
        **kwargs
    )
    return proc


def update_server(base_path: str, os_type: str = None,
                  log_callback=None) -> subprocess.Popen:
    return install_server(base_path, os_type, log_callback)
