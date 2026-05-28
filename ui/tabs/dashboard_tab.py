import customtkinter as ctk
import tkinter as tk
import threading
import time
from core import server_manager as sm

COLORS = {
    'accent':  '#00C853',
    'warn':    '#FF6D00',
    'error':   '#D50000',
    'bg':      '#1A1A2E',
    'card':    '#16213E',
    'text':    '#E0E0E0',
    'online':  '#00E676',
    'offline': '#FF1744',
}


class DashboardTab(ctk.CTkFrame):
    def __init__(self, parent, base_path_var: tk.StringVar,
                 os_type_var: tk.StringVar, config_ref: dict, log_fn):
        super().__init__(parent, fg_color='transparent')
        self.base_path_var = base_path_var
        self.os_type_var = os_type_var
        self.config_ref = config_ref
        self.log = log_fn
        self._uptime_start = None
        self._poll_running = False
        self._build()
        self._start_polling()

    def _build(self):
        self.columnconfigure((0, 1), weight=1)

        # ── Status Card ───────────────────────────────────────────────
        status_card = ctk.CTkFrame(self, fg_color=COLORS['card'], corner_radius=12)
        status_card.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky='ew')
        status_card.columnconfigure(1, weight=1)

        ctk.CTkLabel(status_card, text='⚡  Server Status',
                     font=ctk.CTkFont(size=18, weight='bold'),
                     text_color=COLORS['accent']).grid(
            row=0, column=0, columnspan=3, padx=20, pady=(15, 10), sticky='w')

        self.status_dot = ctk.CTkLabel(status_card, text='●',
                                       font=ctk.CTkFont(size=24),
                                       text_color=COLORS['offline'])
        self.status_dot.grid(row=1, column=0, padx=(20, 8), pady=(0, 15))

        self.status_label = ctk.CTkLabel(status_card, text='OFFLINE',
                                         font=ctk.CTkFont(size=22, weight='bold'),
                                         text_color=COLORS['offline'])
        self.status_label.grid(row=1, column=1, pady=(0, 15), sticky='w')

        self.uptime_label = ctk.CTkLabel(status_card, text='',
                                         text_color='#888888',
                                         font=ctk.CTkFont(size=13))
        self.uptime_label.grid(row=1, column=2, padx=20, pady=(0, 15), sticky='e')

        # ── Control Buttons ───────────────────────────────────────────
        btn_card = ctk.CTkFrame(self, fg_color=COLORS['card'], corner_radius=12)
        btn_card.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky='ew')
        btn_card.columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(btn_card, text='🎮  Serverkontroll',
                     font=ctk.CTkFont(size=16, weight='bold'),
                     text_color=COLORS['accent']).grid(
            row=0, column=0, columnspan=3, padx=20, pady=(15, 12), sticky='w')

        self.start_btn = ctk.CTkButton(
            btn_card, text='▶  Starta',
            fg_color='#1B5E20', hover_color='#2E7D32',
            font=ctk.CTkFont(size=15, weight='bold'), height=50,
            command=self._start_server)
        self.start_btn.grid(row=1, column=0, padx=12, pady=(0, 15), sticky='ew')

        self.stop_btn = ctk.CTkButton(
            btn_card, text='⏹  Stoppa',
            fg_color='#B71C1C', hover_color='#C62828',
            font=ctk.CTkFont(size=15, weight='bold'), height=50,
            command=self._stop_server, state='disabled')
        self.stop_btn.grid(row=1, column=1, padx=12, pady=(0, 15), sticky='ew')

        self.restart_btn = ctk.CTkButton(
            btn_card, text='🔄  Starta om',
            fg_color='#E65100', hover_color='#F57C00',
            font=ctk.CTkFont(size=15, weight='bold'), height=50,
            command=self._restart_server, state='disabled')
        self.restart_btn.grid(row=1, column=2, padx=12, pady=(0, 15), sticky='ew')

        # ── Stats Cards ───────────────────────────────────────────────
        self.cpu_card = self._stat_card('💻  CPU', '0%', 0)
        self.ram_card = self._stat_card('🧠  RAM', '0 MB', 1)
        self.pid_card = self._stat_card('🔧  PID', '–', 2)

        # ── Server Info ───────────────────────────────────────────────
        info_card = ctk.CTkFrame(self, fg_color=COLORS['card'], corner_radius=12)
        info_card.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky='ew')
        info_card.columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(info_card, text='ℹ️  Serverinfo',
                     font=ctk.CTkFont(size=16, weight='bold'),
                     text_color=COLORS['accent']).grid(
            row=0, column=0, columnspan=2, padx=20, pady=(15, 8), sticky='w')

        self.info_labels = {}
        fields = [
            ('Servernamn', 'server_name'),
            ('Karta', 'map'),
            ('Max spelare', 'max_players'),
            ('Game Port', 'game_port'),
        ]
        for i, (label, key) in enumerate(fields):
            col = i % 2
            row = (i // 2) + 1
            ctk.CTkLabel(info_card, text=f'{label}:',
                         text_color='#888888').grid(
                row=row, column=col, padx=20, pady=4, sticky='w')
            lbl = ctk.CTkLabel(info_card, text='–', text_color=COLORS['text'])
            lbl.grid(row=row, column=col, padx=(110, 20), pady=4, sticky='w')
            self.info_labels[key] = lbl

        ctk.CTkFrame(info_card, height=1, fg_color='#333333').grid(
            row=10, column=0, columnspan=2, padx=20, pady=(8, 15), sticky='ew')

    def _stat_card(self, title: str, value: str, col: int):
        card = ctk.CTkFrame(self, fg_color=COLORS['card'], corner_radius=12)
        card.grid(row=2, column=col % 2, padx=20, pady=10, sticky='ew')
        if col < 2:
            pass

        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=13),
                     text_color='#888888').pack(padx=15, pady=(12, 2))
        lbl = ctk.CTkLabel(card, text=value,
                           font=ctk.CTkFont(size=26, weight='bold'),
                           text_color=COLORS['accent'])
        lbl.pack(padx=15, pady=(0, 12))
        return lbl

    # ── Actions ───────────────────────────────────────────────────────

    def _start_server(self):
        base = self.base_path_var.get()
        os_type = self.os_type_var.get()
        self.start_btn.configure(state='disabled', text='Startar...')

        def _run():
            ok = sm.start_server(base, self.config_ref, os_type, self.log)
            if ok:
                self._uptime_start = time.time()
            self.after(0, self._update_ui_state)

        threading.Thread(target=_run, daemon=True).start()

    def _stop_server(self):
        self.stop_btn.configure(state='disabled', text='Stoppar...')

        def _run():
            sm.stop_server(self.log)
            self._uptime_start = None
            self.after(0, self._update_ui_state)

        threading.Thread(target=_run, daemon=True).start()

    def _restart_server(self):
        base = self.base_path_var.get()
        os_type = self.os_type_var.get()
        self.restart_btn.configure(state='disabled', text='Startar om...')

        def _run():
            sm.restart_server(base, self.config_ref, os_type, self.log)
            self._uptime_start = time.time()
            self.after(0, self._update_ui_state)

        threading.Thread(target=_run, daemon=True).start()

    def _update_ui_state(self):
        running = sm.is_running()
        color = COLORS['online'] if running else COLORS['offline']
        text = 'ONLINE' if running else 'OFFLINE'

        self.status_dot.configure(text_color=color)
        self.status_label.configure(text=text, text_color=color)

        self.start_btn.configure(
            state='disabled' if running else 'normal',
            text='▶  Starta')
        self.stop_btn.configure(state='normal' if running else 'disabled', text='⏹  Stoppa')
        self.restart_btn.configure(state='normal' if running else 'disabled', text='🔄  Starta om')

        # Update info labels
        for key, lbl in self.info_labels.items():
            lbl.configure(text=str(self.config_ref.get(key, '–')))

    def _start_polling(self):
        self._poll_running = True
        self._poll()

    def _poll(self):
        if not self._poll_running:
            return
        self._update_ui_state()
        stats = sm.get_stats()
        self.cpu_card.configure(text=f"{stats['cpu']:.1f}%")
        self.ram_card.configure(text=f"{stats['ram_mb']:.0f} MB")
        self.pid_card.configure(text=str(stats['pid']) if stats['pid'] else '–')

        if self._uptime_start and sm.is_running():
            elapsed = int(time.time() - self._uptime_start)
            h, rem = divmod(elapsed, 3600)
            m, s = divmod(rem, 60)
            self.uptime_label.configure(text=f'Uptime: {h:02d}:{m:02d}:{s:02d}')
        else:
            self.uptime_label.configure(text='')

        self.after(2000, self._poll)

    def destroy(self):
        self._poll_running = False
        super().destroy()
