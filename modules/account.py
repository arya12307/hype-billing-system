# Hype ERP - Accounting Module (account)
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import os
import sqlite3
from modules.erp_branding import HYPE_ERP_BRAND
from modules.window_utils import set_icon


class AccountingModule:
    MODULE_NAME = "Accounting"
    MODULE_CODE = "account"

    def __init__(self, parent, db_path="hype_billing_system.db"):
        self.parent = parent
        self.db_path = self._resolve_db_path(db_path)
        self._init_db()

    def _resolve_db_path(self, db_path):
        if os.path.isabs(db_path):
            return db_path

        candidates = [
            os.path.abspath(db_path),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), db_path),
            os.path.join(os.path.dirname(__file__), '..', db_path),
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        return os.path.abspath(candidates[0])

    def _ensure_column(self, conn, table_name, column_name, column_def):
        existing_cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table_name})")]
        if column_name not in existing_cols:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_def}")

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            balance REAL DEFAULT 0.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            ref TEXT,
            description TEXT,
            debit_account TEXT,
            credit_account TEXT,
            amount REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        self._ensure_column(conn, 'journal_entries', 'date', 'date TEXT NOT NULL DEFAULT CURRENT_DATE')
        self._ensure_column(conn, 'journal_entries', 'ref', 'ref TEXT')
        self._ensure_column(conn, 'journal_entries', 'description', 'description TEXT')
        self._ensure_column(conn, 'journal_entries', 'debit_account', 'debit_account TEXT')
        self._ensure_column(conn, 'journal_entries', 'credit_account', 'credit_account TEXT')
        self._ensure_column(conn, 'journal_entries', 'amount', 'amount REAL NOT NULL DEFAULT 0.0')
        self._ensure_column(conn, 'journal_entries', 'created_at', 'created_at TEXT DEFAULT CURRENT_TIMESTAMP')
        conn.commit()
        conn.close()

    def _get_store_id(self):
        try:
            conn = sqlite3.connect(self.db_path)
            row = conn.execute("SELECT value FROM settings WHERE key='store_id'").fetchone()
            conn.close()
            return int(row[0]) if row and str(row[0]).isdigit() else 1
        except Exception:
            return 1

    def _sync_account_tables(self):
        try:
            from firebase_sync import get_firebase_sync_manager
            fsm = get_firebase_sync_manager()
            if not fsm or not getattr(fsm, 'db', None):
                return
            store_id = self._get_store_id()
            fsm.sync_table_to_firestore('accounts', f'stores/{store_id}/accounts')
            fsm.sync_table_to_firestore('journal_entries', f'stores/{store_id}/journal_entries')
        except Exception:
            pass

    def open(self):
        win = tk.Toplevel(self.parent)
        win.title(f"{HYPE_ERP_BRAND} - Accounting")
        win.geometry("900x600")
        win.configure(bg="#1a1a2e")
        set_icon(win)
        self._build_ui(win)

    def _build_ui(self, win):
        # Title
        tk.Label(win, text=f"🏦 {HYPE_ERP_BRAND} — Accounting",
                 font=("Arial", 18, "bold"), bg="#1a1a2e", fg="#e94560").pack(pady=16)
        # Tabs
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=16, pady=8)
        # Chart of Accounts tab
        coa_frame = tk.Frame(nb, bg="#16213e")
        nb.add(coa_frame, text="Chart of Accounts")
        self._build_coa(coa_frame)
        # Journal tab
        jrn_frame = tk.Frame(nb, bg="#16213e")
        nb.add(jrn_frame, text="Journal Entries")
        self._build_journal(jrn_frame)
        # Trial Balance tab
        tb_frame = tk.Frame(nb, bg="#16213e")
        nb.add(tb_frame, text="Trial Balance")
        self._build_trial_balance(tb_frame)

    def _build_coa(self, frame):
        cols = ("Code", "Name", "Type", "Balance")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=180)
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        self._refresh_accounts(tree)
        btn_frame = tk.Frame(frame, bg="#16213e")
        btn_frame.pack()
        tk.Button(btn_frame, text="+ Add Account", bg="#e94560", fg="white",
                  command=lambda: self._add_account_dialog(tree), relief="flat", padx=10, pady=4).pack(side="left", padx=4)
        tk.Button(btn_frame, text="🔄 Refresh", bg="#333355", fg="white",
                  command=lambda: self._refresh_accounts(tree), relief="flat", padx=10, pady=4).pack(side="left", padx=4)

    def _refresh_accounts(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT code, name, type, balance FROM accounts ORDER BY code")
        for row in c.fetchall():
            tree.insert("", "end", values=row)
        conn.close()

    def _add_account_dialog(self, tree):
        d = tk.Toplevel()
        d.title("Add Account")
        d.geometry("380x280")
        d.configure(bg="#1a1a2e")
        set_icon(d)
        fields = [("Account Code", tk.StringVar()), ("Account Name", tk.StringVar()),
                  ("Type (Asset/Liability/Income/Expense)", tk.StringVar())]
        for label, var in fields:
            tk.Label(d, text=label, bg="#1a1a2e", fg="white", font=("Arial", 9)).pack(anchor="w", padx=20, pady=(8, 0))
            tk.Entry(d, textvariable=var, bg="#16213e", fg="white", insertbackground="white").pack(fill="x", padx=20)

        def save():
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("INSERT INTO accounts (code, name, type) VALUES (?,?,?)",
                             (fields[0][1].get(), fields[1][1].get(), fields[2][1].get()))
                conn.commit()
                conn.close()
                self._refresh_accounts(tree)
                self._sync_account_tables()
                d.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(d, text="Save", bg="#e94560", fg="white", command=save, relief="flat", padx=14, pady=5).pack(pady=14)

    def _build_journal(self, frame):
        cols = ("Date", "Ref", "Description", "Debit A/C", "Credit A/C", "Amount")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=130)
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        self._refresh_journal(tree)
        tk.Button(frame, text="+ New Entry", bg="#e94560", fg="white",
                  command=lambda: self._add_journal_dialog(tree), relief="flat", padx=10, pady=4).pack()

    def _refresh_journal(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT date, ref, description, debit_account, credit_account, amount FROM journal_entries ORDER BY date DESC")
        for row in c.fetchall():
            tree.insert("", "end", values=row)
        conn.close()

    def _add_journal_dialog(self, tree):
        d = tk.Toplevel()
        d.title("New Journal Entry")
        d.geometry("400x380")
        d.configure(bg="#1a1a2e")
        set_icon(d)
        today = datetime.date.today().isoformat()
        fields = [("Date", tk.StringVar(value=today)), ("Reference", tk.StringVar()),
                  ("Description", tk.StringVar()), ("Debit Account", tk.StringVar()),
                  ("Credit Account", tk.StringVar()), ("Amount", tk.StringVar())]
        for label, var in fields:
            tk.Label(d, text=label, bg="#1a1a2e", fg="white", font=("Arial", 9)).pack(anchor="w", padx=20, pady=(6, 0))
            tk.Entry(d, textvariable=var, bg="#16213e", fg="white", insertbackground="white").pack(fill="x", padx=20)

        def save():
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("INSERT INTO journal_entries (date, ref, description, debit_account, credit_account, amount) VALUES (?,?,?,?,?,?)",
                             tuple(v.get() for _, v in fields))
                conn.commit()
                conn.close()
                self._refresh_journal(tree)
                self._sync_account_tables()
                d.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(d, text="Save", bg="#e94560", fg="white", command=save, relief="flat", padx=14, pady=5).pack(pady=10)

    def _build_trial_balance(self, frame):
        tk.Label(frame, text="Trial Balance", bg="#16213e", fg="#e94560",
                 font=("Arial", 14, "bold")).pack(pady=12)
        cols = ("Account", "Type", "Debit", "Credit")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=200)
        tree.pack(fill="both", expand=True, padx=10, pady=6)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT name, type, balance FROM accounts ORDER BY type")
        for row in c.fetchall():
            name, typ, bal = row
            debit = f"{bal:.2f}" if bal >= 0 else ""
            credit = f"{abs(bal):.2f}" if bal < 0 else ""
            tree.insert("", "end", values=(name, typ, debit, credit))
        conn.close()
