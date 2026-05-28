import sys
import os

def _ensure_packages():
    if getattr(sys, 'frozen', False):
        return
    import importlib, subprocess
    packages = {'customtkinter': 'customtkinter', 'requests': 'requests',
                'psutil': 'psutil', 'Pillow': 'PIL'}
    missing = [p for p, i in packages.items()
               if not __import_ok(i)]
    if missing:
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', *missing, '-q'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def __import_ok(name):
    try:
        __import__(name); return True
    except ImportError:
        return False

if __name__ == '__main__':
    _ensure_packages()

    # Bättre DPI på Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    try:
        from ui.app import TheIsleServerManager
        app = TheIsleServerManager()
        app.protocol('WM_DELETE_WINDOW', app.on_closing)
        app.mainloop()
    except Exception:
        import traceback, tkinter as tk
        tb = traceback.format_exc()
        print(tb)
        # Visa popup om GUI kraschar vid start
        root = tk.Tk()
        root.title('Startfel')
        root.geometry('700x400')
        txt = tk.Text(root, font=('Courier', 10), bg='#1a0000', fg='#ff8080')
        txt.pack(fill='both', expand=True, padx=10, pady=10)
        txt.insert('1.0', tb)
        txt.configure(state='disabled')
        root.mainloop()
