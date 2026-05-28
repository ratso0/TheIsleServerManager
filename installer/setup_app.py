"""
The Isle Server Manager – Setup
================================
Detta är installationsprogrammet.
PyInstaller paketerar detta + huvudprogrammet till en Setup.exe.
"""
import sys
import os
import shutil
import threading
import subprocess
import ctypes
import struct
import winreg

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog

# ── Konstanter ────────────────────────────────────────────────────────
APP_NAME        = "The Isle Server Manager"
APP_VERSION     = "1.0.0"
EXE_NAME        = "TheIsleServerManager.exe"
UNINSTALLER_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TheIsleServerManager"

DEFAULT_INSTALL = os.path.join(
    os.environ.get("PROGRAMFILES", "C:\\Program Files"), APP_NAME
)

COLORS = {
    "bg":     "#0D1117",
    "card":   "#161B22",
    "accent": "#00C853",
    "text":   "#E6EDF3",
    "muted":  "#8B949E",
    "btn":    "#21262D",
    "hover":  "#30363D",
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def relaunch_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit(0)


def get_bundled_exe() -> str:
    """
    Hitta huvud-.exe:en som är buntad med installern av PyInstaller.
    PyInstaller extraherar filer till sys._MEIPASS vid körning.
    """
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
        path = os.path.join(base, EXE_NAME)
        if os.path.exists(path):
            return path
    # Dev-läge: leta i dist/
    dev_path = os.path.join(os.path.dirname(__file__), "..", "dist", EXE_NAME)
    if os.path.exists(dev_path):
        return os.path.abspath(dev_path)
    return None


def create_shortcut(target: str, shortcut_path: str, description: str = ""):
    """Skapa en .lnk-genväg via PowerShell (kräver inga extra paket)."""
    ps_script = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
$Shortcut.TargetPath = '{target}'
$Shortcut.Description = '{description}'
$Shortcut.Save()
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
        capture_output=True
    )


def register_uninstaller(install_dir: str):
    """Lägg till i Windows 'Appar och funktioner'."""
    uninstaller = os.path.join(install_dir, "Uninstall.exe")
    try:
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, UNINSTALLER_KEY)
        winreg.SetValueEx(key, "DisplayName",     0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "DisplayVersion",  0, winreg.REG_SZ, APP_VERSION)
        winreg.SetValueEx(key, "Publisher",       0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_dir)
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ,
                          f'"{uninstaller}" /uninstall')
        winreg.SetValueEx(key, "DisplayIcon",     0, winreg.REG_SZ,
                          os.path.join(install_dir, EXE_NAME))
        winreg.SetValueEx(key, "NoModify",        0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair",        0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
    except Exception as e:
        print(f"[Installer] Registernyckel fel: {e}")


def create_uninstaller(install_dir: str):
    """Skapa ett enkelt uninstall.bat som raderar mappen och registernyckeln."""
    bat = os.path.join(install_dir, "Uninstall.bat")
    content = f"""@echo off
echo Avinstallerar {APP_NAME}...
reg delete "HKLM\\{UNINSTALLER_KEY}" /f >nul 2>&1
rmdir /s /q "%~dp0"
echo Klart.
"""
    with open(bat, "w") as f:
        f.write(content)


# ══════════════════════════════════════════════════════════════════════
class InstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} – Installation")
        self.geometry("560x520")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg"])

        self._install_dir = tk.StringVar(value=DEFAULT_INSTALL)
        self._desktop_shortcut = tk.BooleanVar(value=True)
        self._startmenu_shortcut = tk.BooleanVar(value=True)
        self._launch_after = tk.BooleanVar(value=True)

        self._pages = {}
        self._build_pages()
        self._show("welcome")

    # ── Sidor ──────────────────────────────────────────────────────────

    def _build_pages(self):
        for key in ("welcome", "options", "progress", "done"):
            f = ctk.CTkFrame(self, fg_color="transparent")
            f.place(relwidth=1, relheight=1)
            self._pages[key] = f

        self._build_welcome()
        self._build_options()
        self._build_progress()
        self._build_done()

    def _show(self, key: str):
        for k, f in self._pages.items():
            f.lower() if k != key else f.lift()

    # ── Sida 1: Välkommen ─────────────────────────────────────────────

    def _build_welcome(self):
        p = self._pages["welcome"]

        # Header
        header = ctk.CTkFrame(p, fg_color=COLORS["card"], corner_radius=0, height=160)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="🦖",
                     font=ctk.CTkFont(size=56)).pack(pady=(20, 4))
        ctk.CTkLabel(header, text=APP_NAME,
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=COLORS["accent"]).pack()

        # Body
        body = ctk.CTkFrame(p, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=40, pady=30)

        ctk.CTkLabel(body,
                     text=f"Välkommen till installationsguiden för\n{APP_NAME} v{APP_VERSION}",
                     font=ctk.CTkFont(size=14),
                     text_color=COLORS["text"],
                     justify="center").pack(pady=(0, 16))

        ctk.CTkLabel(body,
                     text="Programmet låter dig installera och hantera\n"
                          "The Isle Evrima-server direkt via ett grafiskt gränssnitt.\n\n"
                          "• Automatisk installation av SteamCMD och server\n"
                          "• Öppnar portar i brandväggen automatiskt\n"
                          "• Serverhantering, loggning och backup",
                     font=ctk.CTkFont(size=12),
                     text_color=COLORS["muted"],
                     justify="left").pack(anchor="w")

        # Footer
        footer = ctk.CTkFrame(p, fg_color=COLORS["card"], corner_radius=0, height=60)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        ctk.CTkButton(footer, text="Nästa  →",
                      fg_color=COLORS["accent"], text_color="#000000",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      hover_color="#00E676", width=120, height=36,
                      command=lambda: self._show("options")).pack(
            side="right", padx=20, pady=12)

    # ── Sida 2: Alternativ ────────────────────────────────────────────

    def _build_options(self):
        p = self._pages["options"]

        header = ctk.CTkFrame(p, fg_color=COLORS["card"], corner_radius=0, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="⚙️  Installationsalternativ",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COLORS["accent"]).pack(padx=24, pady=20, side="left")

        body = ctk.CTkFrame(p, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=30, pady=20)
        body.columnconfigure(0, weight=1)

        # Installationsmapp
        ctk.CTkLabel(body, text="Installationsmapp:",
                     text_color=COLORS["muted"],
                     font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, sticky="w", pady=(0, 4))

        path_row = ctk.CTkFrame(body, fg_color="transparent")
        path_row.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        path_row.columnconfigure(0, weight=1)

        ctk.CTkEntry(path_row, textvariable=self._install_dir,
                     height=36, font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(path_row, text="Bläddra", width=90, height=36,
                      fg_color=COLORS["btn"], hover_color=COLORS["hover"],
                      command=self._browse).grid(row=0, column=1)

        # Genvägar
        ctk.CTkLabel(body, text="Genvägar:",
                     text_color=COLORS["muted"],
                     font=ctk.CTkFont(size=12)).grid(
            row=2, column=0, sticky="w", pady=(0, 8))

        ctk.CTkCheckBox(body, text="Skapa genväg på skrivbordet",
                        variable=self._desktop_shortcut,
                        checkmark_color="#000000",
                        fg_color=COLORS["accent"],
                        hover_color="#00E676").grid(
            row=3, column=0, sticky="w", pady=4)

        ctk.CTkCheckBox(body, text="Skapa genväg i startmenyn",
                        variable=self._startmenu_shortcut,
                        checkmark_color="#000000",
                        fg_color=COLORS["accent"],
                        hover_color="#00E676").grid(
            row=4, column=0, sticky="w", pady=4)

        ctk.CTkCheckBox(body, text="Starta programmet efter installation",
                        variable=self._launch_after,
                        checkmark_color="#000000",
                        fg_color=COLORS["accent"],
                        hover_color="#00E676").grid(
            row=5, column=0, sticky="w", pady=4)

        # Footer
        footer = ctk.CTkFrame(p, fg_color=COLORS["card"], corner_radius=0, height=60)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        ctk.CTkButton(footer, text="← Tillbaka",
                      fg_color=COLORS["btn"], hover_color=COLORS["hover"],
                      width=110, height=36,
                      command=lambda: self._show("welcome")).pack(
            side="left", padx=20, pady=12)

        ctk.CTkButton(footer, text="Installera  →",
                      fg_color=COLORS["accent"], text_color="#000000",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      hover_color="#00E676", width=140, height=36,
                      command=self._start_install).pack(
            side="right", padx=20, pady=12)

    def _browse(self):
        path = filedialog.askdirectory(title="Välj installationsmapp")
        if path:
            self._install_dir.set(path.replace("/", "\\"))

    # ── Sida 3: Installerar ───────────────────────────────────────────

    def _build_progress(self):
        p = self._pages["progress"]

        header = ctk.CTkFrame(p, fg_color=COLORS["card"], corner_radius=0, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="⚙️  Installerar...",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COLORS["accent"]).pack(padx=24, pady=20, side="left")

        body = ctk.CTkFrame(p, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=30, pady=20)
        body.columnconfigure(0, weight=1)

        self._prog_bar = ctk.CTkProgressBar(body, progress_color=COLORS["accent"])
        self._prog_bar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self._prog_bar.set(0)

        self._prog_label = ctk.CTkLabel(body, text="Förbereder...",
                                        text_color=COLORS["muted"],
                                        font=ctk.CTkFont(size=12))
        self._prog_label.grid(row=1, column=0, sticky="w", pady=(0, 12))

        self._log_box = ctk.CTkTextbox(body, height=220,
                                       fg_color=COLORS["card"],
                                       font=ctk.CTkFont(family="Courier", size=11),
                                       text_color=COLORS["muted"])
        self._log_box.grid(row=2, column=0, sticky="nsew")
        body.rowconfigure(2, weight=1)
        self._log_box.configure(state="disabled")

    def _log(self, msg: str):
        self._log_box.configure(state="normal")
        self._log_box.insert("end", msg + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")
        self._prog_label.configure(text=msg)
        self.update_idletasks()

    def _set_progress(self, val: float):
        self._prog_bar.set(val)
        self.update_idletasks()

    # ── Sida 4: Klar ─────────────────────────────────────────────────

    def _build_done(self):
        p = self._pages["done"]

        body = ctk.CTkFrame(p, fg_color="transparent")
        body.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(body, text="✅",
                     font=ctk.CTkFont(size=64)).pack(pady=(0, 12))
        ctk.CTkLabel(body, text="Installation klar!",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=COLORS["accent"]).pack()
        ctk.CTkLabel(body,
                     text=f"{APP_NAME} är installerat\noch redo att användas.",
                     font=ctk.CTkFont(size=13),
                     text_color=COLORS["muted"],
                     justify="center").pack(pady=12)

        self._done_launch_btn = ctk.CTkButton(
            body, text="🚀  Starta The Isle Server Manager",
            fg_color=COLORS["accent"], text_color="#000000",
            font=ctk.CTkFont(size=14, weight="bold"),
            hover_color="#00E676", height=44, width=300,
            command=self._launch_and_exit)
        self._done_launch_btn.pack(pady=8)

        ctk.CTkButton(body, text="Stäng",
                      fg_color=COLORS["btn"], hover_color=COLORS["hover"],
                      height=36, width=120,
                      command=self.destroy).pack(pady=4)

    # ── Installationslogik ────────────────────────────────────────────

    def _start_install(self):
        self._show("progress")
        threading.Thread(target=self._do_install, daemon=True).start()

    def _do_install(self):
        install_dir = self._install_dir.get()

        try:
            # 1. Hitta .exe att installera
            self._set_progress(0.1)
            self._log("Letar efter programmets filer...")
            exe_src = get_bundled_exe()
            if not exe_src:
                self._log("FEL: Kunde inte hitta TheIsleServerManager.exe")
                return

            # 2. Skapa installationsmapp
            self._set_progress(0.2)
            self._log(f"Skapar mapp: {install_dir}")
            os.makedirs(install_dir, exist_ok=True)

            # 3. Kopiera .exe
            self._set_progress(0.4)
            self._log("Kopierar programfiler...")
            dest_exe = os.path.join(install_dir, EXE_NAME)
            shutil.copy2(exe_src, dest_exe)
            self._log(f"  → {dest_exe}")

            # 4. Skapa uninstaller
            self._set_progress(0.55)
            self._log("Skapar avinstallerare...")
            create_uninstaller(install_dir)

            # 5. Registrera i Windows Appar & Funktioner
            self._set_progress(0.65)
            self._log("Registrerar i Windows...")
            register_uninstaller(install_dir)

            # 6. Skrivbordsgenväg
            if self._desktop_shortcut.get():
                self._set_progress(0.75)
                self._log("Skapar genväg på skrivbordet...")
                desktop = os.path.join(
                    os.environ.get("USERPROFILE", ""), "Desktop"
                )
                create_shortcut(
                    dest_exe,
                    os.path.join(desktop, f"{APP_NAME}.lnk"),
                    APP_NAME
                )

            # 7. Startmeny
            if self._startmenu_shortcut.get():
                self._set_progress(0.85)
                self._log("Skapar genväg i startmenyn...")
                start_menu = os.path.join(
                    os.environ.get("APPDATA", ""),
                    "Microsoft", "Windows", "Start Menu", "Programs", APP_NAME
                )
                os.makedirs(start_menu, exist_ok=True)
                create_shortcut(
                    dest_exe,
                    os.path.join(start_menu, f"{APP_NAME}.lnk"),
                    APP_NAME
                )

            self._set_progress(1.0)
            self._log("Installation klar!")
            self._installed_exe = dest_exe
            self.after(800, lambda: self._show("done"))

        except Exception as e:
            self._log(f"FEL: {e}")
            import traceback
            self._log(traceback.format_exc())

    def _launch_and_exit(self):
        exe = getattr(self, "_installed_exe", None)
        if exe and os.path.exists(exe):
            subprocess.Popen([exe])
        self.destroy()


# ── Entry point ────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not is_admin():
        relaunch_as_admin()

    app = InstallerApp()
    app.mainloop()
