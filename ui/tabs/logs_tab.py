import customtkinter as ctk
import tkinter as tk
from datetime import datetime

COLORS = {
    'accent': '#00C853',
    'card':   '#16213E',
    'text':   '#E0E0E0',
}

LOG_COLORS = {
    '[INFO]':  '#00E5FF',
    '[WARN]':  '#FFD600',
    '[ERROR]': '#FF1744',
    '[Backup]':'#CE93D8',
    '[Config]':'#80CBC4',
    '[Firewall]': '#FFAB40',
    '[SteamCMD]': '#81C784',
}


class LogsTab(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color='transparent', **kwargs)
        self._autoscroll = True
        self._filter_var = tk.StringVar(value='ALL')
        self._all_lines = []
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # ── Toolbar ───────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(self, fg_color=COLORS['card'], corner_radius=10)
        toolbar.grid(row=0, column=0, padx=20, pady=(20, 8), sticky='ew')
        toolbar.columnconfigure(3, weight=1)

        ctk.CTkLabel(toolbar, text='📋  Loggar',
                     font=ctk.CTkFont(size=16, weight='bold'),
                     text_color=COLORS['accent']).grid(
            row=0, column=0, padx=16, pady=10)

        ctk.CTkLabel(toolbar, text='Filter:',
                     text_color='#888888').grid(row=0, column=1, padx=(16, 4))

        ctk.CTkOptionMenu(
            toolbar, variable=self._filter_var,
            values=['ALL', 'INFO', 'WARN', 'ERROR', 'Backup', 'Config'],
            width=120, fg_color='#0D1B2A',
            button_color=COLORS['accent'],
            command=lambda _: self._apply_filter()).grid(
            row=0, column=2, padx=4, pady=8)

        self._search_var = tk.StringVar()
        self._search_var.trace_add('write', lambda *_: self._apply_filter())
        ctk.CTkEntry(toolbar, textvariable=self._search_var,
                     placeholder_text='Sök...', width=180).grid(
            row=0, column=3, padx=8, pady=8, sticky='w')

        self._autoscroll_sw = ctk.CTkSwitch(
            toolbar, text='Auto-scroll',
            progress_color=COLORS['accent'],
            command=self._toggle_autoscroll)
        self._autoscroll_sw.select()
        self._autoscroll_sw.grid(row=0, column=4, padx=8)

        ctk.CTkButton(toolbar, text='🗑  Rensa',
                      width=80, fg_color='#3E1414',
                      hover_color='#5E2020',
                      command=self._clear).grid(
            row=0, column=5, padx=(4, 16), pady=8)

        # ── Log Text ──────────────────────────────────────────────────
        self.text = ctk.CTkTextbox(
            self, fg_color='#0A0F1E',
            font=ctk.CTkFont(family='Courier', size=12),
            text_color=COLORS['text'],
            corner_radius=10,
            wrap='word')
        self.text.grid(row=1, column=0, padx=20, pady=(0, 20), sticky='nsew')
        self.text.configure(state='disabled')

        # Tag colors
        self.text._textbox.tag_configure('INFO',  foreground='#00E5FF')
        self.text._textbox.tag_configure('WARN',  foreground='#FFD600')
        self.text._textbox.tag_configure('ERROR', foreground='#FF1744')
        self.text._textbox.tag_configure('Backup', foreground='#CE93D8')
        self.text._textbox.tag_configure('Config', foreground='#80CBC4')
        self.text._textbox.tag_configure('FIRE',  foreground='#FFAB40')
        self.text._textbox.tag_configure('ts',    foreground='#444466')

    def append(self, line: str):
        """Append a log line – called from any thread via .after()"""
        ts = datetime.now().strftime('%H:%M:%S')
        entry = f'[{ts}] {line}'
        self._all_lines.append(entry)

        flt = self._filter_var.get()
        srch = self._search_var.get().lower()

        if self._matches(entry, flt, srch):
            self._insert_line(entry)

    def _matches(self, line: str, flt: str, srch: str) -> bool:
        if flt != 'ALL' and f'[{flt}]' not in line and flt not in line:
            return False
        if srch and srch not in line.lower():
            return False
        return True

    def _insert_line(self, line: str):
        self.text.configure(state='normal')
        tag = None
        for key in ['ERROR', 'WARN', 'INFO', 'Backup', 'Config', 'Firewall']:
            if key in line:
                tag = key if key != 'Firewall' else 'FIRE'
                break

        if tag:
            self.text._textbox.insert('end', line + '\n', tag)
        else:
            self.text.insert('end', line + '\n')

        self.text.configure(state='disabled')
        if self._autoscroll:
            self.text._textbox.see('end')

    def _apply_filter(self):
        flt = self._filter_var.get()
        srch = self._search_var.get().lower()
        self.text.configure(state='normal')
        self.text.delete('0.0', 'end')
        self.text.configure(state='disabled')
        for line in self._all_lines:
            if self._matches(line, flt, srch):
                self._insert_line(line)

    def _clear(self):
        self._all_lines.clear()
        self.text.configure(state='normal')
        self.text.delete('0.0', 'end')
        self.text.configure(state='disabled')

    def _toggle_autoscroll(self):
        self._autoscroll = not self._autoscroll
