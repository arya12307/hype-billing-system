# Hype ERP - ERP Main Module Launcher (scrollable + full keyboard support)
# Developer: David | Nexuzy Lab
import os
import sys
import tkinter as tk
from tkinter import messagebox
from modules.scrollable_frame import ScrollableFrame

BG  = '#1a1a2e'
BG2 = '#16213e'
ACC = '#e94560'
FG  = 'white'
FOOTER = 'Powered by Hype ERP v3.0.0 | Nexuzy Lab | Developer: David'


def get_icon_path():
    base = getattr(sys, '_MEIPASS', None) or os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    ico = os.path.join(base, 'icon.ico')
    return ico if os.path.exists(ico) else None


def set_icon(win):
    ico = get_icon_path()
    if ico:
        try:
            win.iconbitmap(ico)
        except Exception:
            pass

MODULES = [
    ('Accounting',      '🏦', 'modules.account',           'AccountingModule',       '#1a3a5c'),
    ('Invoice',         '🧾', 'modules.account_invoice',   'AccountInvoiceModule',   '#2c1a3a'),
    ('Asset',           '🏛', 'modules.account_asset',     'AccountAssetModule',     '#1a3a2a'),
    ('Tax / GST',       '💰', 'modules.account_tax',       'AccountTaxModule',       '#3a1a1a'),
    ('Banking',         '🏦', 'modules.account_statement', 'AccountStatementModule', '#1a2a3a'),
    ('Sales',           '📈', 'modules.sale',              'SaleModule',             '#2a3a1a'),
    ('Purchase',        '🛍', 'modules.purchase',          'PurchaseModule',         '#3a2a1a'),
    ('Vendors',         '👥', 'modules.vendor_module',     'VendorModule',           '#2a1a3a'),
    ('Inventory',       '📦', 'modules.stock',             'StockModule',            '#1a1a3a'),
    ('Manufacturing',   '🏭', 'modules.production',        'ProductionModule',       '#2a1a3a'),
    ('HR',              '👥', 'modules.hr_module',         'HRModule',               '#3a1a2a'),
    ('Payroll',         '💰', 'modules.payroll_module',    'PayrollModule',          '#1a3a3a'),
    ('CRM',             '🤝', 'modules.crm_module',        'CRMModule',              '#3a3a1a'),
    ('Projects',        '📁', 'modules.projects_module',   'ProjectsModule',         '#1a2a2a'),
    ('Timesheet',       '⏱',  'modules.timesheet',         'TimesheetModule',        '#2a1a2a'),
    ('POS',             '🔵', 'modules.pos_module',        'POSModule',              '#3a1a3a'),
    ('Shipping',        '🚚', 'modules.stock_package',     'StockPackageModule',     '#1a3a1a'),
    ('Quality Control', '✅',  'modules.quality_control',   'QualityControlModule',   '#2a2a1a'),
    ('Marketing',       '📣', 'modules.marketing',         'MarketingModule',        '#3a2a2a'),
    ('Reporting',       '📊', 'modules.reporting_module',  'ReportingModule',        '#1a1a2a'),
]


class ERPMainMenu:
    def __init__(self, parent, db_path):
        self.parent   = parent
        self.db_path  = db_path
        self._focused = 0   # for keyboard navigation
        self._btns    = []  # list of (card_frame, open_button)

    def open(self):
        win = tk.Toplevel(self.parent)
        win.title('Hype ERP — All ERP Modules')
        win.geometry('1050x700')
        win.configure(bg=BG)
        win.resizable(True, True)
        win.focus_set()
        set_icon(win)

        # ── Header ──────────────────────────────────────────────────────
        hdr = tk.Frame(win, bg=BG2, pady=12)
        hdr.pack(fill='x')
        tk.Label(hdr, text='🏢  Hype ERP — All Modules',
                 font=('Arial', 18, 'bold'), bg=BG2, fg=ACC).pack(side='left', padx=20)
        tk.Label(hdr, text=f'20 Enterprise Modules | Nexuzy Lab | David',
                 font=('Arial', 9, 'italic'), bg=BG2, fg='#7a7a9a').pack(side='right', padx=20)

        # ── Search bar ──────────────────────────────────────────────────
        sf_bar = tk.Frame(win, bg=BG2)
        sf_bar.pack(fill='x', padx=0)
        tk.Label(sf_bar, text='🔍  Search module:',
                 bg=BG2, fg='#aaaacc', font=('Arial', 9)).pack(side='left', padx=12, pady=6)
        search_var = tk.StringVar()
        search_entry = tk.Entry(sf_bar, textvariable=search_var,
                                bg='#0f3460', fg=FG, insertbackground=FG,
                                font=('Arial', 10), relief='flat', width=28)
        search_entry.pack(side='left', padx=6, pady=6, ipady=4)
        result_count = tk.Label(sf_bar, text=f'{len(MODULES)} modules available',
                                bg=BG2, fg='#aaaacc', font=('Arial', 9))
        result_count.pack(side='right', padx=12)
        tk.Label(sf_bar, text='⌨️  Tab/Arrows: Navigate  |  Enter: Open  |  Esc: Back',
                 bg=BG2, fg='#555577', font=('Arial', 8)).pack(side='right', padx=14)

        # ── Scrollable card grid ─────────────────────────────────────────
        scroll_container = ScrollableFrame(win, bg=BG)
        scroll_container.pack(fill='both', expand=True, padx=0, pady=0)
        grid_frame = scroll_container.scrollable_frame

        COLS = 4
        self._btns = []

        def render_grid(query=''):
            for w in grid_frame.winfo_children():
                w.destroy()
            self._btns.clear()
            self._focused = 0

            filtered = [(n,ic,mp,cn,col) for n,ic,mp,cn,col in MODULES
                        if query.lower() in n.lower()]
            result_count.config(text=f'{len(filtered)} module(s) found' if query else f'{len(filtered)} module(s) available')

            if not filtered:
                tk.Label(grid_frame, text='No modules match your search. Try a different keyword.',
                         bg=BG, fg='#c0c0c0', font=('Arial', 12, 'italic')).grid(
                             row=0, column=0, columnspan=COLS, pady=60, padx=16)
                return

            for idx, (name, icon, mod_path, cls_name, color) in enumerate(filtered):
                row, col = divmod(idx, COLS)

                card = tk.Frame(grid_frame, bg=color, padx=10, pady=14,
                                relief='flat', bd=0, cursor='hand2')
                card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
                grid_frame.columnconfigure(col, weight=1)
                grid_frame.rowconfigure(row, weight=1)

                tk.Label(card, text=icon, font=('Arial', 28),
                         bg=color, fg=FG).pack()
                tk.Label(card, text=name,
                         font=('Arial', 10, 'bold'), bg=color, fg=FG).pack(pady=(2, 0))

                def make_cmd(mp=mod_path, cn=cls_name):
                    def cmd():
                        try:
                            mod = __import__(mp, fromlist=[cn])
                            cls = getattr(mod, cn)
                            cls(win, self.db_path).open()
                        except ImportError as e:
                            messagebox.showerror('Module Error',
                                                 f'Cannot load {cn}:\n{e}')
                        except Exception as e:
                            messagebox.showerror('Error', str(e))
                    return cmd

                cmd_fn = make_cmd()
                btn = tk.Button(card, text='Open', bg=ACC, fg=FG,
                                relief='flat', padx=10, pady=4,
                                font=('Arial', 8, 'bold'), cursor='hand2',
                                command=cmd_fn,
                                activebackground='#c0392b')
                btn.pack(pady=(6, 0))

                def _on_hover(e, frame=card, base=color):
                    frame.configure(bg='#243455')
                def _on_leave(e, frame=card, base=color):
                    frame.configure(bg=base)

                self._btns.append((card, btn, cmd_fn))

                card.bind('<Enter>', _on_hover)
                card.bind('<Leave>', _on_leave)
                card.bind('<Button-1>', lambda e, c=cmd_fn: c())
                for child in card.winfo_children():
                    if not isinstance(child, tk.Button):
                        child.bind('<Button-1>', lambda e, c=cmd_fn: c())

            _highlight(0)

        def _highlight(idx):
            for i, (card, btn, _) in enumerate(self._btns):
                if i == idx:
                    card.configure(highlightbackground=ACC,
                                   highlightthickness=2, highlightcolor=ACC)
                    btn.configure(bg='#c0392b')
                    card.update_idletasks()
                    # auto-scroll to visible
                    scroll_container.canvas.update_idletasks()
                    bbox = scroll_container.canvas.bbox('all')
                    if bbox:
                        card_y = card.winfo_y()
                        canvas_h = scroll_container.canvas.winfo_height()
                        total_h = bbox[3]
                        frac = max(0, (card_y - canvas_h//2) / max(1, total_h))
                        scroll_container.canvas.yview_moveto(frac)
                else:
                    try:
                        card.configure(highlightthickness=0)
                        btn.configure(bg=ACC)
                    except: pass

        def nav_key(event):
            if not self._btns: return
            cols_now = COLS
            n = len(self._btns)
            if event.keysym in ('Down', 'j'):
                self._focused = min(self._focused + cols_now, n - 1)
            elif event.keysym in ('Up', 'k'):
                self._focused = max(self._focused - cols_now, 0)
            elif event.keysym in ('Right', 'l', 'Tab'):
                self._focused = min(self._focused + 1, n - 1)
            elif event.keysym in ('Left', 'h', 'ISO_Left_Tab'):
                self._focused = max(self._focused - 1, 0)
            elif event.keysym == 'Home':
                self._focused = 0
            elif event.keysym == 'End':
                self._focused = n - 1
            elif event.keysym == 'Return':
                _, _, cmd = self._btns[self._focused]
                cmd(); return
            elif event.keysym == 'Escape':
                win.destroy(); return
            _highlight(self._focused)

        win.bind('<Up>',              nav_key)
        win.bind('<Down>',            nav_key)
        win.bind('<Left>',            nav_key)
        win.bind('<Right>',           nav_key)
        win.bind('<Tab>',             nav_key)
        win.bind('<Shift-Tab>',       nav_key)
        win.bind('<Return>',          nav_key)
        win.bind('<Escape>',          nav_key)
        win.bind('<Home>',            nav_key)
        win.bind('<End>',             nav_key)
        win.bind('<j>',               nav_key)
        win.bind('<k>',               nav_key)
        win.bind('<h>',               nav_key)
        win.bind('<l>',               nav_key)

        # Number keys 1-9 open module directly
        for i in range(1, 10):
            win.bind(f'<Key-{i}>',
                     lambda e, idx=i-1: (self._btns[idx][2]() if idx < len(self._btns) else None))

        def _fake_event(key):
            class Fake:
                pass
            ev = Fake(); ev.keysym = key
            return ev

        # Live search filter
        search_var.trace('w', lambda *a: render_grid(search_var.get()))
        search_entry.bind('<Escape>', lambda e: (search_var.set(''), win.focus_set()))
        search_entry.bind('<Down>',   lambda e: (win.focus_set(), nav_key(_fake_event('Down'))))

        # Focus search with Ctrl+F
        win.bind('<Control-f>', lambda e: search_entry.focus_set())
        win.bind('<Control-F>', lambda e: search_entry.focus_set())

        tk.Label(win, text=FOOTER,
                 bg=BG2, fg='#444466', font=('Arial', 7)).pack(
                     side='bottom', fill='x', ipady=3)

        render_grid()
