import customtkinter as ctk
import tkinter as tk
import threading
from core.backup_manager import (create_backup, restore_backup,
                                  list_backups, delete_backup,
                                  schedule_backup)

COLORS = {
    'accent': '#00C853',
    'warn':   '#FF6D00',
    'error':  '#D50000',
    'card':   '#16213E',
    'text':   '#E0E0E0',
}


class BackupTab(ctk.CTkFrame):
    def __init__(self, parent, base_path_var: tk.StringVar, log_fn):
        super().__init__(parent, fg_color='transparent')
        self.base_path_var = base_path_var
        self.log = log_fn
        self._schedule_stop = None
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)

        # ── Manual Backup ─────────────────────────────────────────────
        ctrl_card = ctk.CTkFrame(self, fg_color=COLORS['card'], corner_radius=12)
        ctrl_card.grid(row=0, column=0, padx=20, pady=(20, 10), sticky='ew')
        ctrl_card.columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(ctrl_card, text='💾  Säkerhetskopiering',
                     font=ctk.CTkFont(size=16, weight='bold'),
                     text_color=COLORS['accent']).grid(
            row=0, column=0, columnspan=3, padx=20, pady=(15, 8), sticky='w')

        self.label_entry = ctk.CTkEntry(
            ctrl_card, placeholder_text='Backup-namn (valfritt)', height=36)
        self.label_entry.grid(row=1, column=0, padx=12, pady=(0, 15), sticky='ew')

        ctk.CTkButton(
            ctrl_card, text='📦  Skapa backup nu',
            fg_color=COLORS['accent'], text_color='#000000',
            font=ctk.CTkFont(size=13, weight='bold'), height=38,
            hover_color='#00E676',
            command=self._create_backup).grid(
            row=1, column=1, padx=12, pady=(0, 15), sticky='ew')

        ctk.CTkButton(
            ctrl_card, text='♻️  Återställ vald',
            fg_color='#1565C0', hover_color='#1976D2',
            font=ctk.CTkFont(size=13, weight='bold'), height=38,
            command=self._restore_selected).grid(
            row=1, column=2, padx=12, pady=(0, 15), sticky='ew')

        # ── Auto Backup ───────────────────────────────────────────────
        auto_card = ctk.CTkFrame(self, fg_color=COLORS['card'], corner_radius=12)
        auto_card.grid(row=1, column=0, padx=20, pady=10, sticky='ew')
        auto_card.columnconfigure(2, weight=1)

        ctk.CTkLabel(auto_card, text='⏰  Automatisk backup',
                     font=ctk.CTkFont(size=16, weight='bold'),
                     text_color=COLORS['accent']).grid(
            row=0, column=0, columnspan=4, padx=20, pady=(15, 8), sticky='w')

        ctk.CTkLabel(auto_card, text='Intervall (timmar):',
                     text_color='#888888').grid(
            row=1, column=0, padx=20, pady=(0, 15))

        self.interval_var = tk.DoubleVar(value=1.0)
        ctk.CTkSlider(auto_card, from_=0.5, to=24, variable=self.interval_var,
                      width=200, progress_color=COLORS['accent'],
                      button_color=COLORS['accent']).grid(
            row=1, column=1, padx=8, pady=(0, 15))

        self.interval_lbl = ctk.CTkLabel(auto_card, text='1.0h', width=40)
        self.interval_var.trace_add(
            'write', lambda *_: self.interval_lbl.configure(
                text=f'{self.interval_var.get():.1f}h'))
        self.interval_lbl.grid(row=1, column=2, padx=4)

        self.auto_btn = ctk.CTkButton(
            auto_card, text='▶  Starta schemaläggning',
            fg_color='#1B5E20', hover_color='#2E7D32',
            font=ctk.CTkFont(size=13, weight='bold'), height=36,
            command=self._toggle_schedule)
        self.auto_btn.grid(row=1, column=3, padx=12, pady=(0, 15))

        # ── Backup List ───────────────────────────────────────────────
        list_card = ctk.CTkFrame(self, fg_color=COLORS['card'], corner_radius=12)
        list_card.grid(row=2, column=0, padx=20, pady=10, sticky='nsew')
        list_card.columnconfigure(0, weight=1)
        list_card.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        header = ctk.CTkFrame(list_card, fg_color='transparent')
        header.grid(row=0, column=0, padx=20, pady=(15, 8), sticky='ew')
        header.columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text='📂  Tillgängliga backuper',
                     font=ctk.CTkFont(size=16, weight='bold'),
                     text_color=COLORS['accent']).grid(row=0, column=0, sticky='w')

        ctk.CTkButton(header, text='🔄 Uppdatera',
                      width=100, fg_color='#0D3322',
                      border_color=COLORS['accent'], border_width=1,
                      hover_color='#1A5235',
                      command=self._refresh_list).grid(row=0, column=1)

        ctk.CTkButton(header, text='🗑 Radera',
                      width=80, fg_color='#3E1414',
                      hover_color='#5E2020',
                      command=self._delete_selected).grid(
            row=0, column=2, padx=(8, 0))

        self.backup_list = ctk.CTkScrollableFrame(
            list_card, fg_color='#0A0F1E', corner_radius=8)
        self.backup_list.grid(row=1, column=0, padx=20, pady=(0, 20), sticky='nsew')
        self.backup_list.columnconfigure(0, weight=1)

        self._selected_backup = None
        self._refresh_list()

    # ── Actions ───────────────────────────────────────────────────────

    def _create_backup(self):
        base = self.base_path_var.get()
        label = self.label_entry.get().strip()

        def _run():
            create_backup(base, base, label=label, log_callback=self.log)
            self.after(0, self._refresh_list)

        threading.Thread(target=_run, daemon=True).start()

    def _restore_selected(self):
        if not self._selected_backup:
            self.log('[Backup] Ingen backup vald.')
            return
        base = self.base_path_var.get()

        def _run():
            restore_backup(self._selected_backup['path'], base, self.log)

        threading.Thread(target=_run, daemon=True).start()

    def _delete_selected(self):
        if not self._selected_backup:
            return
        delete_backup(self._selected_backup['path'])
        self.log(f"[Backup] Raderat: {self._selected_backup['name']}")
        self._selected_backup = None
        self._refresh_list()

    def _toggle_schedule(self):
        if self._schedule_stop:
            self._schedule_stop.set()
            self._schedule_stop = None
            self.auto_btn.configure(text='▶  Starta schemaläggning',
                                    fg_color='#1B5E20')
            self.log('[Backup] Schemaläggning stoppad.')
        else:
            base = self.base_path_var.get()
            hours = self.interval_var.get()
            self._schedule_stop = schedule_backup(
                base, base, hours, self.log)
            self.auto_btn.configure(
                text=f'⏸  Stoppa ({hours:.1f}h)',
                fg_color='#B71C1C')
            self.log(f'[Backup] Schemaläggning startad – var {hours:.1f} timme.')

    def _refresh_list(self):
        for w in self.backup_list.winfo_children():
            w.destroy()

        base = self.base_path_var.get()
        backups = list_backups(base)

        if not backups:
            ctk.CTkLabel(self.backup_list,
                         text='Inga backuper hittade.',
                         text_color='#555555').pack(padx=20, pady=20)
            return

        for b in backups:
            self._backup_row(b)

    def _backup_row(self, b: dict):
        row = ctk.CTkFrame(self.backup_list, fg_color=COLORS['card'],
                           corner_radius=8)
        row.pack(fill='x', padx=8, pady=4)
        row.columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text='💾', font=ctk.CTkFont(size=16)).grid(
            row=0, column=0, padx=(12, 8), pady=10)

        ctk.CTkLabel(row, text=b['name'], text_color=COLORS['text'],
                     anchor='w', font=ctk.CTkFont(size=12)).grid(
            row=0, column=1, sticky='w')

        ctk.CTkLabel(row,
                     text=f"{b['created']}  |  {b['size_mb']} MB",
                     text_color='#666688', font=ctk.CTkFont(size=11)).grid(
            row=0, column=2, padx=12)

        def _select(backup=b, frame=row):
            self._selected_backup = backup
            for w in self.backup_list.winfo_children():
                w.configure(fg_color=COLORS['card'])
            frame.configure(fg_color='#1A3A2A')

        row.bind('<Button-1>', lambda e, bk=b, fr=row: _select(bk, fr))
        for child in row.winfo_children():
            child.bind('<Button-1>', lambda e, bk=b, fr=row: _select(bk, fr))
