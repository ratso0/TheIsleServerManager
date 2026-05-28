import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import os
from core.os_utils import get_os, get_default_install_path, is_admin
from core.steamcmd import install_steamcmd, install_server, is_steamcmd_installed
from core.firewall import open_all_ports, DEFAULT_PORTS
from core.config_manager import load_manager_config, save_manager_config

COLORS = {
    'accent': '#00C853',
    'warn':   '#FF6D00',
    'error':  '#D50000',
    'bg':     '#1A1A2E',
    'card':   '#16213E',
    'text':   '#E0E0E0',
}


class InstallTab(ctk.CTkFrame):
    def __init__(self, parent, base_path_var: tk.StringVar, os_type_var: tk.StringVar,
                 config_ref: dict, log_fn):
        super().__init__(parent, fg_color='transparent')
        self.base_path_var = base_path_var
        self.os_type_var = os_type_var
        self.config_ref = config_ref
        self.log = log_fn
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)

        # ── OS Selection ─────────────────────────────────────────────
        os_card = ctk.CTkFrame(self, fg_color=COLORS['card'], corner_radius=12)
        os_card.grid(row=0, column=0, padx=20, pady=(20, 10), sticky='ew')
        os_card.columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(os_card, text='🖥️  Operativsystem',
                     font=ctk.CTkFont(size=16, weight='bold'),
                     text_color=COLORS['accent']).grid(
            row=0, column=0, columnspan=2, padx=20, pady=(15, 8), sticky='w')

        ctk.CTkLabel(os_card, text='Välj det OS där servern ska köras:',
                     text_color=COLORS['text']).grid(
            row=1, column=0, columnspan=2, padx=20, pady=(0, 8), sticky='w')

        detected = get_os()
        if self.os_type_var.get() == '':
            self.os_type_var.set(detected)

        win_btn = ctk.CTkRadioButton(
            os_card, text='🪟  Windows',
            variable=self.os_type_var, value='windows',
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent'])
        win_btn.grid(row=2, column=0, padx=40, pady=(0, 15), sticky='w')

        lin_btn = ctk.CTkRadioButton(
            os_card, text='🐧  Linux',
            variable=self.os_type_var, value='linux',
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent'])
        lin_btn.grid(row=2, column=1, padx=40, pady=(0, 15), sticky='w')

        ctk.CTkLabel(os_card,
                     text=f'Upptäckt OS: {detected.capitalize()}',
                     text_color='#888888', font=ctk.CTkFont(size=12)).grid(
            row=3, column=0, columnspan=2, padx=20, pady=(0, 12), sticky='w')

        # ── Install Path ─────────────────────────────────────────────
        path_card = ctk.CTkFrame(self, fg_color=COLORS['card'], corner_radius=12)
        path_card.grid(row=1, column=0, padx=20, pady=10, sticky='ew')
        path_card.columnconfigure(0, weight=1)

        ctk.CTkLabel(path_card, text='📁  Installationsmapp',
                     font=ctk.CTkFont(size=16, weight='bold'),
                     text_color=COLORS['accent']).grid(
            row=0, column=0, columnspan=2, padx=20, pady=(15, 8), sticky='w')

        path_row = ctk.CTkFrame(path_card, fg_color='transparent')
        path_row.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 15), sticky='ew')
        path_row.columnconfigure(0, weight=1)

        if not self.base_path_var.get():
            self.base_path_var.set(get_default_install_path())

        self.path_entry = ctk.CTkEntry(
            path_row, textvariable=self.base_path_var,
            font=ctk.CTkFont(size=13), height=36)
        self.path_entry.grid(row=0, column=0, sticky='ew', padx=(0, 8))

        ctk.CTkButton(
            path_row, text='Bläddra', width=100, height=36,
            fg_color=COLORS['card'], border_color=COLORS['accent'],
            border_width=1, hover_color='#0D3322',
            command=self._browse_path).grid(row=0, column=1)

        # ── Firewall / Ports ──────────────────────────────────────────
        fw_card = ctk.CTkFrame(self, fg_color=COLORS['card'], corner_radius=12)
        fw_card.grid(row=2, column=0, padx=20, pady=10, sticky='ew')
        fw_card.columnconfigure(0, weight=1)

        ctk.CTkLabel(fw_card, text='🔒  Brandvägg & Portar',
                     font=ctk.CTkFont(size=16, weight='bold'),
                     text_color=COLORS['accent']).grid(
            row=0, column=0, padx=20, pady=(15, 8), sticky='w')

        for i, p in enumerate(DEFAULT_PORTS):
            ctk.CTkLabel(fw_card,
                         text=f"  •  Port {p['port']}/{p['protocol']}  –  {p['description']}",
                         text_color=COLORS['text']).grid(
                row=i + 1, column=0, padx=30, pady=2, sticky='w')

        ctk.CTkLabel(fw_card,
                     text='⚠  Kräver administratörs-/root-behörighet',
                     text_color=COLORS['warn'],
                     font=ctk.CTkFont(size=12)).grid(
            row=len(DEFAULT_PORTS) + 1, column=0, padx=20, pady=(8, 4), sticky='w')

        self.fw_btn = ctk.CTkButton(
            fw_card, text='🔓  Öppna portar nu',
            fg_color=COLORS['accent'], text_color='#000000',
            font=ctk.CTkFont(size=14, weight='bold'),
            hover_color='#00E676', height=38,
            command=self._open_ports)
        self.fw_btn.grid(row=len(DEFAULT_PORTS) + 2, column=0,
                         padx=20, pady=(8, 15), sticky='w')

        # ── Installation Buttons ──────────────────────────────────────
        btn_card = ctk.CTkFrame(self, fg_color=COLORS['card'], corner_radius=12)
        btn_card.grid(row=3, column=0, padx=20, pady=10, sticky='ew')
        btn_card.columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(btn_card, text='⚙️  Installation',
                     font=ctk.CTkFont(size=16, weight='bold'),
                     text_color=COLORS['accent']).grid(
            row=0, column=0, columnspan=3, padx=20, pady=(15, 12), sticky='w')

        self.steamcmd_btn = ctk.CTkButton(
            btn_card, text='1️⃣  Installera SteamCMD',
            fg_color='#1565C0', hover_color='#1976D2',
            font=ctk.CTkFont(size=13, weight='bold'), height=42,
            command=self._install_steamcmd)
        self.steamcmd_btn.grid(row=1, column=0, padx=12, pady=(0, 15), sticky='ew')

        self.server_btn = ctk.CTkButton(
            btn_card, text='2️⃣  Installera Serverfilerna',
            fg_color='#6A1B9A', hover_color='#7B1FA2',
            font=ctk.CTkFont(size=13, weight='bold'), height=42,
            command=self._install_server)
        self.server_btn.grid(row=1, column=1, padx=12, pady=(0, 15), sticky='ew')

        self.update_btn = ctk.CTkButton(
            btn_card, text='🔄  Uppdatera Server',
            fg_color='#00695C', hover_color='#00796B',
            font=ctk.CTkFont(size=13, weight='bold'), height=42,
            command=self._install_server)
        self.update_btn.grid(row=1, column=2, padx=12, pady=(0, 15), sticky='ew')

        # ── Progress ──────────────────────────────────────────────────
        self.progress = ctk.CTkProgressBar(self, progress_color=COLORS['accent'])
        self.progress.grid(row=4, column=0, padx=20, pady=(0, 5), sticky='ew')
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(
            self, text='', text_color='#888888', font=ctk.CTkFont(size=12))
        self.status_label.grid(row=5, column=0, padx=20, pady=(0, 10), sticky='w')

    # ── Actions ───────────────────────────────────────────────────────

    def _browse_path(self):
        path = filedialog.askdirectory(title='Välj installationsmapp')
        if path:
            self.base_path_var.set(path)
            save_manager_config(path, self.config_ref)

    def _set_status(self, text: str):
        self.status_label.configure(text=text)

    def _open_ports(self):
        os_type = self.os_type_var.get()
        self.fw_btn.configure(state='disabled', text='Öppnar portar...')
        self.log(f"[Firewall] Öppnar portar för {os_type}...")

        def _run():
            results = open_all_ports(os_type=os_type, log_callback=self.log)
            ok = all(r['success'] for r in results)
            self.after(0, lambda: self.fw_btn.configure(
                state='normal',
                text='✅  Portar öppnade!' if ok else '⚠  Delvis öppnat – se loggen',
                fg_color=COLORS['accent'] if ok else COLORS['warn']
            ))

        threading.Thread(target=_run, daemon=True).start()

    def _install_steamcmd(self):
        base = self.base_path_var.get()
        os_type = self.os_type_var.get()
        self.steamcmd_btn.configure(state='disabled', text='Installerar...')
        self.progress.set(0)
        self._set_status('Laddar ner SteamCMD...')

        def _run():
            def prog(pct):
                self.after(0, lambda: self.progress.set(pct / 100))

            ok = install_steamcmd(base, os_type,
                                  log_callback=self.log,
                                  progress_callback=prog)
            self.after(0, lambda: self.steamcmd_btn.configure(
                state='normal',
                text='✅  SteamCMD klar!' if ok else '❌  SteamCMD misslyckades'
            ))
            self.after(0, lambda: self.progress.set(1 if ok else 0))
            self.after(0, lambda: self._set_status(
                'SteamCMD installerad!' if ok else 'Fel – se loggen'))

        threading.Thread(target=_run, daemon=True).start()

    def _install_server(self):
        base = self.base_path_var.get()
        os_type = self.os_type_var.get()
        self.server_btn.configure(state='disabled', text='Installerar server...')
        self.update_btn.configure(state='disabled')
        self._set_status('Installerar serverfilerna via SteamCMD...')
        self.progress.set(0)

        def _run():
            try:
                from core.steamcmd import install_server as do_install
                proc = do_install(base, os_type, log_callback=self.log)
                if proc is None:
                    self.after(0, lambda: self.server_btn.configure(
                        state='normal', text='❌  SteamCMD saknas'))
                    self.after(0, lambda: self.update_btn.configure(state='normal'))
                    return
                for line in iter(proc.stdout.readline, ''):
                    stripped = line.rstrip()
                    if stripped:
                        self.log(stripped)
                    if '%]' in stripped or '% ]' in stripped:
                        try:
                            pct = int(stripped.split('%')[0].split('[')[-1].strip()) / 100.0
                            self.after(0, lambda p=pct: self.progress.set(p))
                        except Exception:
                            pass
                proc.wait()
                ok = proc.returncode == 0
            except Exception as e:
                import traceback
                self.log(f'[ERROR] {e}')
                self.log(traceback.format_exc())
                ok = False
            self.after(0, lambda: self.server_btn.configure(
                state='normal',
                text='✅  Server installerad!' if ok else '❌  Fel vid installation'
            ))
            self.after(0, lambda: self.update_btn.configure(state='normal'))
            self.after(0, lambda: self.progress.set(1 if ok else 0))
            self.after(0, lambda: self._set_status(
                'Serverfilerna nedladdade!' if ok else 'Fel – se loggen'))

        threading.Thread(target=_run, daemon=True).start()
