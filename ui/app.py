import customtkinter as ctk
import tkinter as tk
import traceback
import os
from core.os_utils import get_os, get_default_install_path
from core.config_manager import load_manager_config, save_manager_config

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('dark-blue')

COLORS = {
    'sidebar':  '#0D1117',
    'bg':       '#1A1A2E',
    'card':     '#16213E',
    'accent':   '#00C853',
    'text':     '#E0E0E0',
    'muted':    '#555577',
    'hover':    '#1A3A2A',
    'selected': '#0D2E1A',
}

NAV_ITEMS = [
    ('dashboard', '⚡', 'Dashboard'),
    ('install',   '⚙️', 'Installation'),
    ('config',    '🔧', 'Konfiguration'),
    ('logs',      '📋', 'Loggar'),
    ('backup',    '💾', 'Backup'),
]

APP_VERSION = '1.0.0'


class TheIsleServerManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f'The Isle Server Manager  v{APP_VERSION}')
        self.geometry('1200x780')
        self.minsize(900, 600)
        self.configure(fg_color=COLORS['bg'])

        self._os_type   = tk.StringVar(value=get_os())
        self._base_path = tk.StringVar(value=get_default_install_path())
        self._config    = load_manager_config(self._base_path.get())
        self._active_tab  = None
        self._nav_buttons = {}
        self._tab_frames  = {}


        # Set window icon
        try:
            import os, sys
            if getattr(sys, 'frozen', False):
                base = sys._MEIPASS
            else:
                base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base, 'assets', 'icon.ico')
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass

        self._build_layout()
        self._switch_tab('dashboard')

    # ── Layout ────────────────────────────────────────────────────────

    def _build_layout(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=220, fg_color=COLORS['sidebar'],
                               corner_radius=0)
        sidebar.grid(row=0, column=0, sticky='ns')
        sidebar.grid_propagate(False)
        sidebar.columnconfigure(0, weight=1)
        self._build_sidebar(sidebar)

        self._content = ctk.CTkFrame(self, fg_color=COLORS['bg'], corner_radius=0)
        self._content.grid(row=0, column=1, sticky='nsew')
        self._content.columnconfigure(0, weight=1)
        self._content.rowconfigure(0, weight=1)

    def _build_sidebar(self, sidebar):
        logo_frame = ctk.CTkFrame(sidebar, fg_color='#060A10', corner_radius=0)
        logo_frame.grid(row=0, column=0, sticky='ew', pady=(0, 8))
        logo_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(logo_frame, text='🦖',
                     font=ctk.CTkFont(size=40)).grid(row=0, column=0, pady=(20, 4))
        ctk.CTkLabel(logo_frame, text='The Isle',
                     font=ctk.CTkFont(size=18, weight='bold'),
                     text_color=COLORS['accent']).grid(row=1, column=0, pady=2)
        ctk.CTkLabel(logo_frame, text='Server Manager',
                     font=ctk.CTkFont(size=12),
                     text_color=COLORS['muted']).grid(row=2, column=0, pady=(0, 16))

        for i, (key, icon, label) in enumerate(NAV_ITEMS):
            btn = ctk.CTkButton(
                sidebar,
                text=f'  {icon}  {label}',
                anchor='w',
                height=44,
                fg_color='transparent',
                text_color=COLORS['text'],
                hover_color=COLORS['hover'],
                font=ctk.CTkFont(size=14),
                corner_radius=8,
                command=lambda k=key: self._switch_tab(k))
            btn.grid(row=i + 1, column=0, padx=12, pady=3, sticky='ew')
            self._nav_buttons[key] = btn

        ctk.CTkFrame(sidebar, height=1, fg_color='#333333').grid(
            row=20, column=0, padx=12, pady=8, sticky='ew')
        ctk.CTkLabel(sidebar, textvariable=self._os_type,
                     text_color=COLORS['muted'],
                     font=ctk.CTkFont(size=11)).grid(
            row=21, column=0, padx=16, pady=(0, 4), sticky='w')
        ctk.CTkLabel(sidebar, text=f'v{APP_VERSION}',
                     text_color=COLORS['muted'],
                     font=ctk.CTkFont(size=11)).grid(
            row=22, column=0, padx=16, pady=(0, 16), sticky='w')

    # ── Tab switching ─────────────────────────────────────────────────

    def _switch_tab(self, key: str):
        if self._active_tab == key:
            return

        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(fg_color=COLORS['selected'],
                              text_color=COLORS['accent'])
            else:
                btn.configure(fg_color='transparent',
                              text_color=COLORS['text'])

        for frame in self._tab_frames.values():
            frame.grid_forget()

        if key not in self._tab_frames:
            self._tab_frames[key] = self._create_tab(key)

        self._tab_frames[key].grid(row=0, column=0, sticky='nsew')
        self._active_tab = key

    def _create_tab(self, key: str) -> ctk.CTkFrame:
        """Lazy-build each tab. Shows a readable error if creation fails."""

        # Logs tab must exist first (used for logging by other tabs)
        if 'logs' not in self._tab_frames:
            try:
                from ui.tabs.logs_tab import LogsTab
                self._tab_frames['logs'] = LogsTab(self._content)
            except Exception as e:
                return self._error_frame('logs', traceback.format_exc())

        def _log(msg: str):
            if 'logs' in self._tab_frames:
                self._tab_frames['logs'].after(
                    0, lambda m=msg: self._tab_frames['logs'].append(m))

        args = (self._content, self._base_path, self._os_type,
                self._config, _log)

        try:
            if key == 'dashboard':
                from ui.tabs.dashboard_tab import DashboardTab
                return DashboardTab(*args)
            elif key == 'install':
                from ui.tabs.install_tab import InstallTab
                return InstallTab(*args)
            elif key == 'config':
                from ui.tabs.config_tab import ConfigTab
                return ConfigTab(*args)
            elif key == 'logs':
                return self._tab_frames['logs']
            elif key == 'backup':
                from ui.tabs.backup_tab import BackupTab
                return BackupTab(self._content, self._base_path, _log)
            else:
                f = ctk.CTkFrame(self._content, fg_color='transparent')
                ctk.CTkLabel(f, text=f'Tab: {key}').pack(padx=40, pady=40)
                return f

        except Exception:
            return self._error_frame(key, traceback.format_exc())

    def _error_frame(self, tab_key: str, tb: str) -> ctk.CTkFrame:
        """Render a visible error card so the user can report the problem."""
        f = ctk.CTkFrame(self._content, fg_color='transparent')
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(f, fg_color='#2A0A0A', corner_radius=12)
        card.grid(row=0, column=0, padx=60, pady=60, sticky='nsew')
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)

        ctk.CTkLabel(card,
                     text=f'⚠  Fel vid laddning av fliken "{tab_key}"',
                     font=ctk.CTkFont(size=15, weight='bold'),
                     text_color='#FF5252').grid(
            row=0, column=0, padx=24, pady=(20, 8), sticky='w')

        box = ctk.CTkTextbox(card,
                             fg_color='#1A0505',
                             font=ctk.CTkFont(family='Courier', size=11),
                             text_color='#FF8A80',
                             wrap='word')
        box.grid(row=1, column=0, padx=24, pady=(0, 20), sticky='nsew')
        box.insert('0.0', tb)
        box.configure(state='disabled')
        return f

    def on_closing(self):
        from core import server_manager as sm
        if sm.is_running():
            sm.stop_server()
        save_manager_config(self._base_path.get(), self._config)
        self.destroy()
