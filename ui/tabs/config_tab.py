import customtkinter as ctk
import tkinter as tk
from core.config_manager import save_manager_config, write_all_configs

COLORS = {
    'accent': '#00C853',
    'warn':   '#FF6D00',
    'bg':     '#1A1A2E',
    'card':   '#16213E',
    'text':   '#E0E0E0',
}

MAPS = [
    'Gateway',        # Evrima – nuvarande huvudkarta
    'Isla_Spiro',     # Evrima – äldre karta (branch: spiro0.11.59.04)
    'TestLevel',      # Dev/testkarta
    'Isle_V3',        # Legacy-karta
    'Thenyaw_Island', # Legacy-karta
]


class ConfigTab(ctk.CTkFrame):
    def __init__(self, parent, base_path_var: tk.StringVar,
                 os_type_var: tk.StringVar, config_ref: dict, log_fn):
        super().__init__(parent, fg_color='transparent')
        self.base_path_var = base_path_var
        self.os_type_var = os_type_var
        self.config_ref = config_ref
        self.log = log_fn
        self._vars = {}
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)

        # Scroll frame
        scroll = ctk.CTkScrollableFrame(self, fg_color='transparent')
        scroll.grid(row=0, column=0, sticky='nsew', padx=0, pady=0)
        scroll.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # ── Server Identity ───────────────────────────────────────────
        self._section(scroll, 0, '🏷️  Server Identitet')
        row = self._text_field(scroll, 1, 'Servernamn', 'server_name')
        row = self._text_field(scroll, row, 'Serverlösenord', 'server_password', show='*')
        row = self._text_field(scroll, row, 'Admin-lösenord', 'admin_password', show='*')
        row = self._text_field(scroll, row, 'Webbsida URL', 'website_url')
        row = self._text_field(scroll, row, 'Discord URL', 'discord_url')

        # ── Map & Gamemode ────────────────────────────────────────────
        self._section(scroll, row, '🗺️  Karta & Spelläge')
        row += 1
        row = self._dropdown(scroll, row, 'Karta', 'map', MAPS)
        row = self._int_field(scroll, row, 'Max spelare', 'max_players', 1, 500)

        # ── Ports ─────────────────────────────────────────────────────
        self._section(scroll, row, '🔌  Portar')
        row += 1
        row = self._int_field(scroll, row, 'Game Port', 'game_port', 1024, 65535)
        row = self._int_field(scroll, row, 'Query Port', 'query_port', 1024, 65535)
        row = self._int_field(scroll, row, 'RCON Port', 'rcon_port', 1024, 65535)
        row = self._text_field(scroll, row, 'RCON-lösenord', 'rcon_password', show='*')

        # ── Time ──────────────────────────────────────────────────────
        self._section(scroll, row, '⏰  Tid')
        row += 1
        row = self._int_field(scroll, row, 'Daglängd (min)', 'day_length', 5, 1440)
        row = self._int_field(scroll, row, 'Nattlängd (min)', 'night_length', 5, 1440)

        # ── Multipliers ───────────────────────────────────────────────
        self._section(scroll, row, '⚖️  Multiplikatorer')
        row += 1
        for key, label in [
            ('growth_multiplier', 'Tillväxt'),
            ('food_multiplier', 'Mat'),
            ('water_multiplier', 'Vatten'),
            ('stamina_multiplier', 'Uthållighet'),
            ('bleed_multiplier', 'Blödning'),
        ]:
            row = self._float_field(scroll, row, label, key, 0.1, 10.0)

        # ── Switches ──────────────────────────────────────────────────
        self._section(scroll, row, '🔧  Alternativ')
        row += 1
        row = self._switch(scroll, row, 'Tillåt dinosaurval', 'allow_dinosaur_selection')

        # ── Save Button ───────────────────────────────────────────────
        save_frame = ctk.CTkFrame(scroll, fg_color='transparent')
        save_frame.grid(row=row + 1, column=0, padx=20, pady=20, sticky='ew')
        save_frame.columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            save_frame, text='💾  Spara konfiguration',
            fg_color=COLORS['accent'], text_color='#000000',
            font=ctk.CTkFont(size=14, weight='bold'), height=44,
            hover_color='#00E676',
            command=self._save).grid(row=0, column=0, padx=(0, 8), sticky='ew')

        ctk.CTkButton(
            save_frame, text='📝  Spara & Skriv .ini-filer',
            fg_color='#1565C0', hover_color='#1976D2',
            font=ctk.CTkFont(size=14, weight='bold'), height=44,
            command=self._save_and_write_ini).grid(row=0, column=1, padx=(8, 0), sticky='ew')

    # ── Widget helpers ────────────────────────────────────────────────

    def _section(self, parent, row: int, title: str):
        ctk.CTkLabel(parent, text=title,
                     font=ctk.CTkFont(size=15, weight='bold'),
                     text_color=COLORS['accent']).grid(
            row=row, column=0, padx=20, pady=(18, 4), sticky='w')

    def _row_frame(self, parent, row: int, label: str):
        f = ctk.CTkFrame(parent, fg_color=COLORS['card'], corner_radius=8)
        f.grid(row=row, column=0, padx=20, pady=3, sticky='ew')
        f.columnconfigure(1, weight=1)
        ctk.CTkLabel(f, text=label, text_color='#888888', width=180,
                     anchor='w').grid(row=0, column=0, padx=(16, 8), pady=10)
        return f

    def _text_field(self, parent, row: int, label: str, key: str,
                    show: str = '') -> int:
        f = self._row_frame(parent, row, label)
        var = tk.StringVar(value=str(self.config_ref.get(key, '')))
        self._vars[key] = var
        e = ctk.CTkEntry(f, textvariable=var, show=show, height=32)
        e.grid(row=0, column=1, padx=(0, 16), pady=8, sticky='ew')
        return row + 1

    def _int_field(self, parent, row: int, label: str, key: str,
                   min_val: int, max_val: int) -> int:
        f = self._row_frame(parent, row, label)
        var = tk.IntVar(value=int(self.config_ref.get(key, 0)))
        self._vars[key] = var
        spin = ctk.CTkEntry(f, textvariable=var, height=32, width=100)
        spin.grid(row=0, column=1, padx=(0, 16), pady=8, sticky='w')
        ctk.CTkLabel(f, text=f'{min_val}–{max_val}',
                     text_color='#555555', font=ctk.CTkFont(size=11)).grid(
            row=0, column=2, padx=(0, 16))
        return row + 1

    def _float_field(self, parent, row: int, label: str, key: str,
                     min_val: float, max_val: float) -> int:
        f = self._row_frame(parent, row, label)
        var = tk.DoubleVar(value=float(self.config_ref.get(key, 1.0)))
        self._vars[key] = var
        slider = ctk.CTkSlider(f, from_=min_val, to=max_val, variable=var,
                               button_color=COLORS['accent'],
                               button_hover_color='#00E676',
                               progress_color=COLORS['accent'])
        slider.grid(row=0, column=1, padx=(0, 8), pady=8, sticky='ew')
        lbl = ctk.CTkLabel(f, text=f'{var.get():.1f}', width=40)
        lbl.grid(row=0, column=2, padx=(0, 16))
        var.trace_add('write', lambda *_: lbl.configure(text=f'{var.get():.1f}'))
        return row + 1

    def _dropdown(self, parent, row: int, label: str, key: str,
                  options: list) -> int:
        f = self._row_frame(parent, row, label)
        var = tk.StringVar(value=str(self.config_ref.get(key, options[0])))
        self._vars[key] = var
        ctk.CTkOptionMenu(f, variable=var, values=options,
                          fg_color=COLORS['bg'],
                          button_color=COLORS['accent'],
                          button_hover_color='#00E676').grid(
            row=0, column=1, padx=(0, 16), pady=8, sticky='w')
        return row + 1

    def _switch(self, parent, row: int, label: str, key: str) -> int:
        f = self._row_frame(parent, row, label)
        var = tk.BooleanVar(value=bool(self.config_ref.get(key, True)))
        self._vars[key] = var
        ctk.CTkSwitch(f, text='', variable=var,
                      progress_color=COLORS['accent']).grid(
            row=0, column=1, padx=(0, 16), pady=8, sticky='w')
        return row + 1

    # ── Save ──────────────────────────────────────────────────────────

    def _collect(self):
        for key, var in self._vars.items():
            try:
                self.config_ref[key] = var.get()
            except Exception:
                pass

    def _save(self):
        self._collect()
        base = self.base_path_var.get()
        save_manager_config(base, self.config_ref)
        self.log('[Config] Konfiguration sparad.')

    def _save_and_write_ini(self):
        self._collect()
        base = self.base_path_var.get()
        install_path = base
        os_type = self.os_type_var.get()
        save_manager_config(base, self.config_ref)
        ok = write_all_configs(install_path, self.config_ref, os_type)
        if ok:
            self.log('[Config] .ini-filer skrivna till servermappen.')
        else:
            self.log('[Config] FEL: Kunde inte skriva .ini-filer.')
