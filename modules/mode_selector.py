# Hype ERP - Mode Selector (Role-Based Access)
# ─────────────────────────────────────────────────────────────────
#  ROLE ACCESS:
#    admin   → ModeSelector shown  (Billing + ERP)
#    manager → ModeSelector shown  (Billing + ERP)
#    owner   → ModeSelector shown  (Billing + ERP)
#    cashier / any other role → goes straight to Billing ONLY
# ─────────────────────────────────────────────────────────────────
# Developer: David | Nexuzy Lab

import tkinter as tk
from tkinter import messagebox
from modules.window_utils import set_icon

BG  = '#1a1a2e'
BG2 = '#16213e'
BG3 = '#0f3460'
ACC = '#e94560'
GRN = '#27ae60'
FG  = 'white'
FOOTER = 'Powered by Hype ERP v3.0.0 | Nexuzy Lab | Developer: David'

# Roles that are allowed to see the Mode Selector
ERP_ACCESS_ROLES = {'admin', 'manager', 'owner'}


def has_erp_access(role: str) -> bool:
    """Return True if this role should see the Mode Selector."""
    return str(role).strip().lower() in ERP_ACCESS_ROLES


def launch_after_login(parent, db_path, username, role,
                       open_billing_cb, open_erp_cb):
    """
    Call this right after a successful login.

    - If role is admin / manager / owner  → open ModeSelector
    - Any other role (cashier etc.)       → open Billing directly, silently
    """
    if has_erp_access(role):
        ModeSelector(parent, db_path, username, role,
                     open_billing_cb, open_erp_cb).open()
    else:
        # Cashier / restricted user → billing only, no ERP access
        try:
            open_billing_cb()
        except Exception as e:
            messagebox.showerror('Hype ERP', f'Failed to open Billing:\n{e}')


# ─── Role badge colours ──────────────────────────────────────────
ROLE_COLORS = {
    'admin':   ('#e94560', '👑'),
    'owner':   ('#f39c12', '💎'),
    'manager': ('#2980b9', '🏢'),
    'cashier': ('#27ae60', '🧾'),
}


class ModeSelector:
    """
    Full-screen mode chooser — only shown to admin / manager / owner.

    Billing Mode  → open_billing_cb()
    ERP Mode      → open_erp_cb()
    """

    def __init__(self, parent, db_path, username, role,
                 open_billing_cb, open_erp_cb):
        self.parent          = parent
        self.db_path         = db_path
        self.username        = username
        self.role            = role.strip().lower()
        self.open_billing_cb = open_billing_cb
        self.open_erp_cb     = open_erp_cb

    def open(self):
        win = tk.Toplevel(self.parent)
        win.title('Hype ERP — Select Mode')
        win.geometry('920x560')
        win.configure(bg=BG)
        set_icon(win)
        win.resizable(True, True)
        win.focus_set()

        role_color, role_icon = ROLE_COLORS.get(
            self.role, ('#9b59b6', '👤'))

        # ── Header ──────────────────────────────────────────────
        hdr = tk.Frame(win, bg=BG2, pady=14)
        hdr.pack(fill='x')

        tk.Label(hdr, text='🏢  Hype ERP v3.0.0',
                 font=('Arial', 20, 'bold'), bg=BG2, fg=ACC
                 ).pack(side='left', padx=22)

        # Role badge on the right
        badge_frame = tk.Frame(hdr, bg=role_color, padx=10, pady=4)
        badge_frame.pack(side='right', padx=18)
        tk.Label(badge_frame,
                 text=f'{role_icon}  {self.username}  [{self.role.upper()}]',
                 font=('Arial', 10, 'bold'), bg=role_color, fg=FG
                 ).pack()

        # ── Sub-title ────────────────────────────────────────────
        tk.Label(win,
                 text='Choose a mode to get started',
                 font=('Arial', 13, 'italic'), bg=BG, fg='#7a7aaa'
                 ).pack(pady=(20, 4))

        # ── Two big mode cards ───────────────────────────────────
        card_row = tk.Frame(win, bg=BG)
        card_row.pack(fill='both', expand=True, padx=40, pady=10)
        card_row.columnconfigure(0, weight=1)
        card_row.columnconfigure(1, weight=1)
        card_row.rowconfigure(0, weight=1)

        # ── Billing Mode card ────────────────────────────────────
        bc = tk.Frame(card_row, bg='#0f3460', padx=30, pady=26,
                      relief='flat', cursor='hand2')
        bc.grid(row=0, column=0, padx=16, pady=8, sticky='nsew')

        tk.Label(bc, text='🧾', font=('Arial', 52), bg='#0f3460').pack()
        tk.Label(bc, text='Billing Mode',
                 font=('Arial', 17, 'bold'), bg='#0f3460', fg=FG
                 ).pack(pady=(6, 2))
        tk.Label(bc,
                 text=(
                     '• GST Invoice Generation\n'
                     '• Barcode / SKU Product Lookup\n'
                     '• Cash  •  Card  •  UPI  •  Credit\n'
                     '• PDF Export  •  Customer History\n'
                     '• Low Stock Alerts'
                 ),
                 font=('Arial', 9), bg='#0f3460', fg='#aaccff',
                 justify='left').pack(pady=(4, 10))

        btn_bill = tk.Button(
            bc, text='🚀  Open Billing',
            bg=ACC, fg=FG, relief='flat',
            font=('Arial', 12, 'bold'), padx=18, pady=9,
            cursor='hand2', activebackground='#c0392b',
            command=lambda: self._launch(win, self.open_billing_cb)
        )
        btn_bill.pack(fill='x', pady=(4, 0))
        self._bind_card(bc, lambda: self._launch(win, self.open_billing_cb))

        # ── ERP Mode card ────────────────────────────────────────
        ec = tk.Frame(card_row, bg='#1a3a2a', padx=30, pady=26,
                      relief='flat', cursor='hand2')
        ec.grid(row=0, column=1, padx=16, pady=8, sticky='nsew')

        tk.Label(ec, text='🏢', font=('Arial', 52), bg='#1a3a2a').pack()
        tk.Label(ec, text='ERP Mode',
                 font=('Arial', 17, 'bold'), bg='#1a3a2a', fg=FG
                 ).pack(pady=(6, 2))
        tk.Label(ec,
                 text=(
                     '• 19 Enterprise Modules\n'
                     '• Accounting  •  Payroll  •  HR\n'
                     '• Inventory  •  Manufacturing  •  POS\n'
                     '• CRM  •  Projects  •  Marketing\n'
                     '• Shipping  •  QC  •  Reporting'
                 ),
                 font=('Arial', 9), bg='#1a3a2a', fg='#aaffcc',
                 justify='left').pack(pady=(4, 10))

        btn_erp = tk.Button(
            ec, text='🏢  Open ERP',
            bg=GRN, fg=FG, relief='flat',
            font=('Arial', 12, 'bold'), padx=18, pady=9,
            cursor='hand2', activebackground='#1e8449',
            command=lambda: self._launch(win, self.open_erp_cb)
        )
        btn_erp.pack(fill='x', pady=(4, 0))
        self._bind_card(ec, lambda: self._launch(win, self.open_erp_cb))

        # ── Keyboard shortcuts ───────────────────────────────────
        win.bind('<Key-1>', lambda e: self._launch(win, self.open_billing_cb))
        win.bind('<Key-2>', lambda e: self._launch(win, self.open_erp_cb))
        win.bind('<Return>', lambda e: self._launch(win, self.open_billing_cb))
        win.bind('<Escape>', lambda e: win.destroy())
        win.bind('<F1>', lambda e: self._launch(win, self.open_billing_cb))
        win.bind('<F2>', lambda e: self._launch(win, self.open_erp_cb))

        # ── Bottom hint bars ─────────────────────────────────────
        tk.Label(win,
                 text='⌨️  1 / F1 → Billing   |   2 / F2 → ERP   |   Esc → Close',
                 font=('Arial', 9), bg=BG3, fg='#7a9acc'
                 ).pack(fill='x', ipady=5, side='bottom')

        tk.Label(win, text=FOOTER,
                 bg=BG2, fg='#444466', font=('Arial', 7)
                 ).pack(side='bottom', fill='x', ipady=3)

    # ── Helpers ──────────────────────────────────────────────────
    def _bind_card(self, card, cb):
        """Make entire card clickable (not just button)."""
        card.bind('<Button-1>', lambda e: cb())
        for child in card.winfo_children():
            if not isinstance(child, tk.Button):
                child.bind('<Button-1>', lambda e: cb())

    def _launch(self, win, callback):
        try:
            callback()
        except Exception as e:
            messagebox.showerror('Hype ERP', f'Failed to open:\n{e}')
