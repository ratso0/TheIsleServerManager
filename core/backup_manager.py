import os
import shutil
import zipfile
import datetime
import threading


def get_save_path(install_path: str) -> str:
    return os.path.join(install_path, 'server', 'TheIsle', 'Saved', 'SaveGames')


def get_backup_dir(base_path: str) -> str:
    path = os.path.join(base_path, 'backups')
    os.makedirs(path, exist_ok=True)
    return path


def create_backup(install_path: str, base_path: str,
                  label: str = '', log_callback=None) -> str:
    """
    Create a zip backup of the SaveGames folder.
    Returns the path to the created zip, or None on failure.
    """
    save_path = get_save_path(install_path)
    if not os.path.exists(save_path):
        if log_callback:
            log_callback(f"[Backup] Save directory not found: {save_path}")
        return None

    backup_dir = get_backup_dir(base_path)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    suffix = f'_{label}' if label else ''
    zip_name = f'backup_{timestamp}{suffix}.zip'
    zip_path = os.path.join(backup_dir, zip_name)

    if log_callback:
        log_callback(f"[Backup] Creating backup: {zip_name}")

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(save_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, save_path)
                    zf.write(full_path, arcname)
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        if log_callback:
            log_callback(f"[Backup] Done: {zip_name} ({size_mb:.1f} MB)")
        return zip_path
    except Exception as e:
        if log_callback:
            log_callback(f"[Backup] Error: {e}")
        return None


def restore_backup(zip_path: str, install_path: str,
                   log_callback=None) -> bool:
    """Restore a backup by extracting to SaveGames folder"""
    save_path = get_save_path(install_path)

    if log_callback:
        log_callback(f"[Backup] Restoring from: {os.path.basename(zip_path)}")

    # Backup current saves before restoring
    if os.path.exists(save_path):
        old_backup = save_path + '_before_restore'
        shutil.copytree(save_path, old_backup, dirs_exist_ok=True)
        if log_callback:
            log_callback(f"[Backup] Current saves backed up to: {old_backup}")

    try:
        os.makedirs(save_path, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(save_path)
        if log_callback:
            log_callback("[Backup] Restore complete.")
        return True
    except Exception as e:
        if log_callback:
            log_callback(f"[Backup] Restore failed: {e}")
        return False


def list_backups(base_path: str) -> list:
    """List all available backups sorted newest first"""
    backup_dir = get_backup_dir(base_path)
    backups = []
    for f in os.listdir(backup_dir):
        if f.endswith('.zip') and f.startswith('backup_'):
            full_path = os.path.join(backup_dir, f)
            stat = os.stat(full_path)
            backups.append({
                'name': f,
                'path': full_path,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            })
    backups.sort(key=lambda x: x['created'], reverse=True)
    return backups


def delete_backup(zip_path: str) -> bool:
    try:
        os.remove(zip_path)
        return True
    except Exception:
        return False


def schedule_backup(install_path: str, base_path: str,
                    interval_hours: float, log_callback=None) -> threading.Event:
    """
    Start a background thread that creates backups every interval_hours.
    Returns a stop_event – set it to stop the scheduler.
    """
    stop_event = threading.Event()

    def _loop():
        while not stop_event.wait(timeout=interval_hours * 3600):
            create_backup(install_path, base_path,
                          label='auto', log_callback=log_callback)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return stop_event
