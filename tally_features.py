# =============================================================================
# HYPE BILLING SYSTEM - TALLY-LIKE FEATURES MODULE
# Developer: David | GitHub: david0154
# Implements: Ledger, Party A/c, Day Book, Trial Balance, P&L, Balance Sheet
# =============================================================================

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
import csv
import os
from modules.window_utils import set_icon
from modules.scrollable_frame import add_treeview_scroll, ScrollableFrame

DB_PATH = "hype_billing_system.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_tally_tables():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS ledger_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            parent TEXT,
            nature TEXT CHECK(nature IN ('Asset','Liability','Income','Expense')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ledger_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            group_id INTEGER REFERENCES ledger_groups(id),
            opening_balance REAL DEFAULT 0,
            balance_type TEXT CHECK(balance_type IN ('Dr','Cr')),
            mobile TEXT,
            email TEXT,
            address TEXT,
            gstin TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL,
            voucher_type TEXT NOT NULL,
            voucher_no TEXT NOT NULL,
            narration TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS journal_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            journal_id INTEGER REFERENCES journal_entries(id) ON DELETE CASCADE,
            ledger_id INTEGER REFERENCES ledger_accounts(id),
            dr_amount REAL DEFAULT 0,
            cr_amount REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS cost_centers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            parent TEXT
        );

        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ledger_id INTEGER REFERENCES ledger_accounts(id),
            period TEXT,
            budgeted_amount REAL DEFAULT 0
        );
    """)
    # Seed default groups
    default_groups = [
        ("Capital Account", None, "Liability"),
        ("Loans (Liability)", None, "Liability"),
        ("Current Liabilities", None, "Liability"),
        ("Sundry Creditors", "Current Liabilities", "Liability"),
        ("Fixed Assets", None, "Asset"),
        ("Current Assets", None, "Asset"),
        ("Sundry Debtors", "Current Assets", "Asset"),
        ("Cash-in-Hand", "Current Assets", "Asset"),
        ("Bank Accounts", "Current Assets", "Asset"),
        ("Stock-in-Hand", "Current Assets", "Asset"),
        ("Sales Accounts", None, "Income"),
        ("Purchase Accounts", None, "Expense"),
        ("Direct Expenses", None, "Expense"),
        ("Indirect Expenses", None, "Expense"),
        ("Direct Income", None, "Income"),
        ("Indirect Income", None, "Income"),
    ]
    for name, parent, nature in default_groups:
        c.execute("INSERT OR IGNORE INTO ledger_groups(name,parent,nature) VALUES(?,?,?)",
                  (name, parent, nature))
    conn.commit()
    conn.close()


def get_ledger_balance(ledger_id, from_date=None, to_date=None):
    conn = get_conn()
    c = conn.cursor()
    q = """
        SELECT COALESCE(SUM(jl.dr_amount),0) - COALESCE(SUM(jl.cr_amount),0)
        FROM journal_lines jl
        JOIN journal_entries je ON jl.journal_id = je.id
        WHERE jl.ledger_id = ?
    """
    params = [ledger_id]
    if from_date:
        q += " AND je.entry_date >= ?"
        params.append(from_date)
    if to_date:
        q += " AND je.entry_date <= ?"
        params.append(to_date)
    c.execute(q, params)
    val = c.fetchone()[0] or 0
    conn.close()
    return val


def get_trial_balance(from_date=None, to_date=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT la.name, lg.nature,
               COALESCE(SUM(jl.dr_amount),0) as total_dr,
               COALESCE(SUM(jl.cr_amount),0) as total_cr,
               la.opening_balance, la.balance_type
        FROM ledger_accounts la
        LEFT JOIN ledger_groups lg ON la.group_id = lg.id
        LEFT JOIN journal_lines jl ON jl.ledger_id = la.id
        LEFT JOIN journal_entries je ON jl.journal_id = je.id
        GROUP BY la.id
        ORDER BY lg.nature, la.name
    """)
    rows = c.fetchall()
    conn.close()
    return rows


def get_daybook(entry_date=None):
    if not entry_date:
        entry_date = date.today().isoformat()
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT je.entry_date, je.voucher_type, je.voucher_no,
               la.name, jl.dr_amount, jl.cr_amount, je.narration
        FROM journal_entries je
        JOIN journal_lines jl ON jl.journal_id = je.id
        JOIN ledger_accounts la ON jl.ledger_id = la.id
        WHERE je.entry_date = ?
        ORDER BY je.id
    """, (entry_date,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_pnl(from_date, to_date):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT lg.nature, la.name,
               COALESCE(SUM(jl.cr_amount),0) - COALESCE(SUM(jl.dr_amount),0) as net
        FROM ledger_accounts la
        JOIN ledger_groups lg ON la.group_id = lg.id
        JOIN journal_lines jl ON jl.ledger_id = la.id
        JOIN journal_entries je ON jl.journal_id = je.id
        WHERE lg.nature IN ('Income','Expense')
          AND je.entry_date BETWEEN ? AND ?
        GROUP BY la.id
        ORDER BY lg.nature, la.name
    """, (from_date, to_date))
    rows = c.fetchall()
    conn.close()
    return rows


# ─── Tally Features UI ───────────────────────────────────────────────────────

class TallyWindow:
    def __init__(self, parent):
        init_tally_tables()
        self.win = tk.Toplevel(parent)
        self.win.title("📒 Hype Accounting")
        self.win.geometry("900x620")
        self.win.configure(bg="#0f0f1a")
        set_icon(self.win)
        self._build_ui()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.win, bg="#1a1a2e", pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📒 Hype Accounting Suite", font=("Segoe UI", 16, "bold"),
                 bg="#1a1a2e", fg="#ffd700").pack(side="left", padx=16)
        tk.Label(hdr, text="Developer: David | Tally-like Features",
                 font=("Segoe UI", 9), bg="#1a1a2e", fg="#888").pack(side="right", padx=16)

        # Tabs
        nb = ttk.Notebook(self.win)
        nb.pack(fill="both", expand=True, padx=10, pady=8)

        self._build_ledger_tab(nb)
        self._build_daybook_tab(nb)
        self._build_trial_balance_tab(nb)
        self._build_pnl_tab(nb)
        self._build_voucher_tab(nb)
        self._build_party_tab(nb)

    def _build_ledger_tab(self, nb):
        frame = tk.Frame(nb, bg="#0f0f1a")
        nb.add(frame, text="📘 Ledger Master")
        tree_frame = tk.Frame(frame, bg="#0f0f1a")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(4, 0))
        cols = ("Name", "Group", "Opening Balance", "Type", "GSTIN")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=18)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=140)
        tree.pack(side="left", fill="both", expand=True)
        vsb, hsb = add_treeview_scroll(tree_frame, tree)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self._load_ledgers(tree)

        btn_frame = tk.Frame(frame, bg="#0f0f1a")
        btn_frame.pack(fill="x", padx=10, pady=6)
        tk.Button(btn_frame, text="+ Add Ledger", bg="#00aa44", fg="white",
                  font=("Segoe UI", 9, "bold"), relief="flat",
                  command=self._add_ledger_dialog).pack(side="left", padx=4)
        tk.Button(btn_frame, text="✏ Edit Ledger", bg="#16a34a", fg="white",
                  font=("Segoe UI", 9), relief="flat",
                  command=lambda: self._edit_ledger(tree)).pack(side="left", padx=4)
        tk.Button(btn_frame, text="🗑 Delete Ledger", bg="#e74c3c", fg="white",
                  font=("Segoe UI", 9), relief="flat",
                  command=lambda: self._delete_ledger(tree)).pack(side="left", padx=4)
        tk.Button(btn_frame, text="🔄 Refresh", bg="#4a90d9", fg="white",
                  font=("Segoe UI", 9), relief="flat",
                  command=lambda: self._load_ledgers(tree)).pack(side="left", padx=4)
        tk.Button(btn_frame, text="📤 Export CSV", bg="#888", fg="white",
                  font=("Segoe UI", 9), relief="flat",
                  command=lambda: self._export_tree(tree, "ledgers.csv")).pack(side="right", padx=4)

    def _load_ledgers(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT la.name, lg.name, la.opening_balance, la.balance_type, la.gstin
            FROM ledger_accounts la
            LEFT JOIN ledger_groups lg ON la.group_id = lg.id
            ORDER BY la.name
        """)
        for row in cur.fetchall():
            tree.insert("", "end", values=row)
        conn.close()

    def _edit_ledger(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Select', 'Select a ledger first.', parent=self.win)
            return
        name = tree.item(sel[0])['values'][0]
        conn = get_conn()
        c = conn.cursor()
        c.execute('SELECT id, name, group_id, opening_balance, balance_type, mobile, email, address, gstin FROM ledger_accounts WHERE name=?', (name,))
        ledger = c.fetchone()
        conn.close()
        if not ledger:
            messagebox.showerror('Error', 'Ledger not found.', parent=self.win)
            return

        d = tk.Toplevel(self.win)
        d.title(f'Edit Ledger — {ledger[1]}')
        d.geometry('460x520')
        d.configure(bg='#0f0f1a')
        set_icon(d)
        tk.Label(d, text='✏ Edit Ledger', bg='#0f0f1a', fg='#ffd700',
                 font=('Segoe UI', 12, 'bold')).pack(pady=10)
        sf = ScrollableFrame(d, bg='#0f0f1a')
        sf.pack(fill='both', expand=True, padx=10, pady=4)
        frm = sf.scrollable_frame

        fields = [
            ('Ledger Name', 'name', ledger[1]),
            ('Mobile', 'mobile', ledger[5] or ''),
            ('Email', 'email', ledger[6] or ''),
            ('GSTIN', 'gstin', ledger[8] or ''),
            ('Address', 'address', ledger[7] or ''),
            ('Opening Balance', 'ob', str(ledger[3] or 0)),
        ]
        vars_ = {}
        for label, key, value in fields:
            row = tk.Frame(frm, bg='#0f0f1a')
            row.pack(fill='x', padx=4, pady=6)
            tk.Label(row, text=label, bg='#0f0f1a', fg='#ccc',
                     font=('Segoe UI', 9), width=18, anchor='w').pack(side='left')
            e = tk.Entry(row, bg='#1a1a2e', fg='white', relief='flat', font=('Segoe UI', 9))
            e.insert(0, value)
            e.pack(side='left', fill='x', expand=True, padx=4)
            vars_[key] = e

        conn = get_conn()
        groups = [r[0] for r in conn.execute('SELECT name FROM ledger_groups ORDER BY name').fetchall()]
        conn.close()
        gf = tk.Frame(frm, bg='#0f0f1a')
        gf.pack(fill='x', padx=4, pady=6)
        tk.Label(gf, text='Group', bg='#0f0f1a', fg='#ccc',
                 font=('Segoe UI', 9), width=18, anchor='w').pack(side='left')
        gvar = tk.StringVar(value='')
        box = ttk.Combobox(gf, textvariable=gvar, values=groups, width=22)
        box.pack(side='left')
        if ledger[2]:
            c2 = get_conn().cursor()
            c2.execute('SELECT name FROM ledger_groups WHERE id=?', (ledger[2],))
            row = c2.fetchone()
            if row:
                gvar.set(row[0])
            c2.connection.close()

        btf = tk.Frame(frm, bg='#0f0f1a')
        btf.pack(fill='x', padx=4, pady=6)
        tk.Label(btf, text='Balance Type', bg='#0f0f1a', fg='#ccc',
                 font=('Segoe UI', 9), width=18, anchor='w').pack(side='left')
        btvar = tk.StringVar(value=ledger[4] or 'Dr')
        ttk.Combobox(btf, textvariable=btvar, values=['Dr', 'Cr'], width=10).pack(side='left')

        def save():
            conn2 = get_conn()
            c2 = conn2.cursor()
            c2.execute('SELECT id FROM ledger_groups WHERE name=?', (gvar.get(),))
            group = c2.fetchone()
            if not group:
                messagebox.showerror('Error', 'Invalid group.', parent=d)
                conn2.close()
                return
            try:
                c2.execute('''UPDATE ledger_accounts SET name=?, group_id=?, opening_balance=?, balance_type=?, mobile=?, email=?, address=?, gstin=? WHERE id=?''',
                           (vars_['name'].get(), group[0], float(vars_['ob'].get() or 0), btvar.get(),
                            vars_['mobile'].get(), vars_['email'].get(), vars_['address'].get(), vars_['gstin'].get(), ledger[0]))
                conn2.commit()
                messagebox.showinfo('Success', 'Ledger updated!', parent=d)
                d.destroy()
                self._load_ledgers(tree)
            except Exception as e:
                messagebox.showerror('Error', str(e), parent=d)
            finally:
                conn2.close()

        tk.Button(d, text='💾 Save Changes', bg='#00aa44', fg='white',
                  font=('Segoe UI', 10, 'bold'), relief='flat', command=save).pack(pady=10)

    def _delete_ledger(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Select', 'Select a ledger first.', parent=self.win)
            return
        name = tree.item(sel[0])['values'][0]
        if not messagebox.askyesno('Confirm', f'Delete ledger "{name}"?', parent=self.win):
            return
        conn = get_conn()
        c = conn.cursor()
        try:
            c.execute('DELETE FROM ledger_accounts WHERE name=?', (name,))
            conn.commit()
            self._load_ledgers(tree)
            messagebox.showinfo('Deleted', 'Ledger removed.', parent=self.win)
        except Exception as e:
            messagebox.showerror('Error', str(e), parent=self.win)
        finally:
            conn.close()

    def _add_ledger_dialog(self):
        d = tk.Toplevel(self.win)
        d.title("Add Ledger")
        d.geometry("460x520")
        d.configure(bg="#0f0f1a")
        set_icon(d)
        tk.Label(d, text="+ Add Ledger", bg="#0f0f1a", fg="#ffd700",
                 font=("Segoe UI", 12, "bold")).pack(pady=10)
        sf = ScrollableFrame(d, bg="#0f0f1a")
        sf.pack(fill="both", expand=True, padx=10, pady=4)
        frm = sf.scrollable_frame
        fields = [("Ledger Name", "name"), ("Mobile", "mobile"),
                  ("Email", "email"), ("GSTIN", "gstin"),
                  ("Address", "address"), ("Opening Balance", "ob")]
        vars_ = {}
        for label, key in fields:
            row = tk.Frame(frm, bg="#0f0f1a")
            row.pack(fill="x", padx=4, pady=6)
            tk.Label(row, text=label, bg="#0f0f1a", fg="#ccc",
                     font=("Segoe UI", 9), width=18, anchor="w").pack(side="left")
            e = tk.Entry(row, bg="#1a1a2e", fg="white", relief="flat", font=("Segoe UI", 9))
            e.pack(side="left", fill="x", expand=True, padx=4)
            vars_[key] = e
        # Group dropdown
        gf = tk.Frame(d, bg="#0f0f1a")
        gf.pack(fill="x", padx=14, pady=3)
        tk.Label(gf, text="Group", bg="#0f0f1a", fg="#ccc",
                 font=("Segoe UI", 9), width=18, anchor="w").pack(side="left")
        conn = get_conn()
        groups = [r[0] for r in conn.execute("SELECT name FROM ledger_groups ORDER BY name").fetchall()]
        conn.close()
        gvar = tk.StringVar(value=groups[0] if groups else "")
        ttk.Combobox(gf, textvariable=gvar, values=groups, width=22).pack(side="left")
        # Balance type
        btf = tk.Frame(frm, bg="#0f0f1a")
        btf.pack(fill="x", padx=4, pady=6)
        tk.Label(btf, text="Balance Type", bg="#0f0f1a", fg="#ccc",
                 font=("Segoe UI", 9), width=18, anchor="w").pack(side="left")
        btvar = tk.StringVar(value="Dr")
        ttk.Combobox(btf, textvariable=btvar, values=["Dr", "Cr"], width=10).pack(side="left")

        def save():
            conn2 = get_conn()
            c2 = conn2.cursor()
            c2.execute("SELECT id FROM ledger_groups WHERE name=?", (gvar.get(),))
            gid = c2.fetchone()
            if not gid:
                messagebox.showerror("Error", "Invalid group", parent=d)
                conn2.close()
                return
            try:
                c2.execute("""
                    INSERT INTO ledger_accounts(name,group_id,opening_balance,
                    balance_type,mobile,email,address,gstin)
                    VALUES(?,?,?,?,?,?,?,?)
                """, (vars_["name"].get(), gid[0],
                       float(vars_["ob"].get() or 0), btvar.get(),
                       vars_["mobile"].get(), vars_["email"].get(),
                       vars_["address"].get(), vars_["gstin"].get()))
                conn2.commit()
                messagebox.showinfo("Success", "Ledger created!", parent=d)
                d.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=d)
            finally:
                conn2.close()
        btn = tk.Button(d, text="💾 Save Ledger", bg="#00aa44", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  command=save)
        btn.pack(pady=10)

    def _build_daybook_tab(self, nb):
        frame = tk.Frame(nb, bg="#0f0f1a")
        nb.add(frame, text="📅 Day Book")
        tf = tk.Frame(frame, bg="#0f0f1a")
        tf.pack(fill="x", padx=10, pady=6)
        tk.Label(tf, text="Date:", bg="#0f0f1a", fg="#ccc", font=("Segoe UI", 9)).pack(side="left")
        date_var = tk.StringVar(value=date.today().isoformat())
        tk.Entry(tf, textvariable=date_var, bg="#1a1a2e", fg="white",
                 font=("Segoe UI", 9), width=14).pack(side="left", padx=6)
        cols = ("Date", "Voucher Type", "Voucher No", "Ledger", "Dr", "Cr", "Narration")
        tree_frame = tk.Frame(frame, bg="#0f0f1a")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=6)
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=18)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=110)
        tree.pack(side="left", fill="both", expand=True)
        vsb, hsb = add_treeview_scroll(tree_frame, tree)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')

        def load():
            for i in tree.get_children():
                tree.delete(i)
            for row in get_daybook(date_var.get()):
                tree.insert("", "end", values=row)
        tk.Button(tf, text="Load", bg="#4a90d9", fg="white", relief="flat",
                  font=("Segoe UI", 9), command=load).pack(side="left")
        load()

    def _build_trial_balance_tab(self, nb):
        frame = tk.Frame(nb, bg="#0f0f1a")
        nb.add(frame, text="⚖️ Trial Balance")
        cols = ("Ledger", "Nature", "Total Dr", "Total Cr", "Opening Bal", "Bal Type")
        tree_frame = tk.Frame(frame, bg="#0f0f1a")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=6)
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=20)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=130)
        tree.pack(side="left", fill="both", expand=True)
        vsb, hsb = add_treeview_scroll(tree_frame, tree)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        btn_f = tk.Frame(frame, bg="#0f0f1a")
        btn_f.pack(fill="x", padx=10, pady=4)
        tk.Button(btn_f, text="🔄 Refresh", bg="#4a90d9", fg="white", relief="flat",
                  command=lambda: self._load_trial_balance(tree)).pack(side="left")
        tk.Button(btn_f, text="📤 Export CSV", bg="#888", fg="white", relief="flat",
                  command=lambda: self._export_tree(tree, "trial_balance.csv")).pack(side="left", padx=4)
        self._load_trial_balance(tree)

    def _load_trial_balance(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        for row in get_trial_balance():
            tree.insert("", "end", values=(
                row[0], row[1] or "",
                f"₹{row[2]:,.2f}", f"₹{row[3]:,.2f}",
                f"₹{row[4]:,.2f}", row[5] or ""
            ))

    def _build_pnl_tab(self, nb):
        frame = tk.Frame(nb, bg="#0f0f1a")
        nb.add(frame, text="📊 P&L Statement")
        tf = tk.Frame(frame, bg="#0f0f1a")
        tf.pack(fill="x", padx=10, pady=6)
        tk.Label(tf, text="From:", bg="#0f0f1a", fg="#ccc", font=("Segoe UI", 9)).pack(side="left")
        from_var = tk.StringVar(value=f"{date.today().year}-04-01")
        tk.Entry(tf, textvariable=from_var, bg="#1a1a2e", fg="white",
                 font=("Segoe UI", 9), width=12).pack(side="left", padx=4)
        tk.Label(tf, text="To:", bg="#0f0f1a", fg="#ccc", font=("Segoe UI", 9)).pack(side="left")
        to_var = tk.StringVar(value=date.today().isoformat())
        tk.Entry(tf, textvariable=to_var, bg="#1a1a2e", fg="white",
                 font=("Segoe UI", 9), width=12).pack(side="left", padx=4)
        cols = ("Nature", "Ledger", "Net Amount")
        tree_frame = tk.Frame(frame, bg="#0f0f1a")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=6)
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=18)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=220)
        tree.pack(side="left", fill="both", expand=True)
        vsb, hsb = add_treeview_scroll(tree_frame, tree)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        chart = tk.Canvas(frame, height=140, bg="#111111", highlightthickness=0)
        chart.pack(fill="x", padx=10, pady=(0, 8))
        summary = tk.Label(frame, text="", bg="#0f0f1a", fg="#ffd700",
                           font=("Segoe UI", 10, "bold"))
        summary.pack(pady=4)

        def draw_chart(income, expense):
            chart.delete('all')
            width = max(chart.winfo_width(), 600)
            height = 120
            chart.create_text(80, 16, text='Income', fill='#7CFC00', anchor='w', font=('Segoe UI', 9, 'bold'))
            chart.create_text(80, 60, text='Expense', fill='#ff6b6b', anchor='w', font=('Segoe UI', 9, 'bold'))
            total = max(income, expense, 1)
            bar_width = min(520, int((income / total) * 520))
            chart.create_rectangle(130, 6, 130 + bar_width, 30, fill='#7CFC00', outline='')
            chart.create_rectangle(130, 50, 130 + min(520, int((expense / total) * 520)), 74, fill='#ff6b6b', outline='')
            chart.create_text(660, 16, text=f'₹{income:,.2f}', fill='#7CFC00', anchor='w', font=('Segoe UI', 9))
            chart.create_text(660, 60, text=f'₹{expense:,.2f}', fill='#ff6b6b', anchor='w', font=('Segoe UI', 9))

        def load():
            for i in tree.get_children():
                tree.delete(i)
            income = expense = 0
            for row in get_pnl(from_var.get(), to_var.get()):
                tree.insert("", "end", values=(row[0], row[1], f"₹{row[2]:,.2f}"))
                if row[0] == "Income":
                    income += row[2]
                else:
                    expense -= row[2]
            profit = income - expense
            color = "#00ff88" if profit >= 0 else "#ff4444"
            summary.config(
                text=f"Total Income: ₹{income:,.2f}  |  Total Expense: ₹{expense:,.2f}  |  "
                     f"Net Profit: ₹{profit:,.2f}",
                fg=color
            )
        tk.Button(tf, text="Load", bg="#4a90d9", fg="white", relief="flat",
                  font=("Segoe UI", 9), command=load).pack(side="left", padx=6)
        load()

    def _build_voucher_tab(self, nb):
        frame = tk.Frame(nb, bg="#0f0f1a")
        nb.add(frame, text="📝 Voucher Entry")
        tk.Label(frame, text="Quick Voucher Entry (Journal / Payment / Receipt / Sales / Purchase)",
                 bg="#0f0f1a", fg="#00d4ff", font=("Segoe UI", 11, "bold")).pack(pady=10)

        mf = tk.Frame(frame, bg="#0f0f1a")
        mf.pack(padx=16, fill="x")

        def lbl_ent(parent, label, row, col, default=""):
            tk.Label(parent, text=label, bg="#0f0f1a", fg="#ccc",
                     font=("Segoe UI", 9)).grid(row=row, column=col*2, padx=6, pady=4, sticky="e")
            v = tk.StringVar(value=default)
            tk.Entry(parent, textvariable=v, bg="#1a1a2e", fg="white",
                     font=("Segoe UI", 9), width=18).grid(row=row, column=col*2+1, padx=6, pady=4)
            return v

        date_v = lbl_ent(mf, "Date", 0, 0, date.today().isoformat())
        vtype_v = tk.StringVar(value="Journal")
        tk.Label(mf, text="Type", bg="#0f0f1a", fg="#ccc",
                 font=("Segoe UI", 9)).grid(row=0, column=2, padx=6, pady=4, sticky="e")
        ttk.Combobox(mf, textvariable=vtype_v,
                     values=["Journal", "Payment", "Receipt", "Sales", "Purchase"],
                     width=16).grid(row=0, column=3, padx=6)
        vno_v = lbl_ent(mf, "Voucher No", 1, 0)
        nar_v = lbl_ent(mf, "Narration", 1, 1)

        # Debit/Credit ledger selectors
        conn = get_conn()
        ldgrs = [r[0] for r in conn.execute("SELECT name FROM ledger_accounts ORDER BY name").fetchall()]
        conn.close()

        tk.Label(mf, text="Dr Ledger", bg="#0f0f1a", fg="#ccc",
                 font=("Segoe UI", 9)).grid(row=2, column=0, padx=6, pady=4, sticky="e")
        dr_var = tk.StringVar()
        ttk.Combobox(mf, textvariable=dr_var, values=ldgrs, width=20).grid(row=2, column=1)
        dr_amt = lbl_ent(mf, "Dr Amount", 2, 1)

        tk.Label(mf, text="Cr Ledger", bg="#0f0f1a", fg="#ccc",
                 font=("Segoe UI", 9)).grid(row=3, column=0, padx=6, pady=4, sticky="e")
        cr_var = tk.StringVar()
        ttk.Combobox(mf, textvariable=cr_var, values=ldgrs, width=20).grid(row=3, column=1)
        cr_amt = lbl_ent(mf, "Cr Amount", 3, 1)

        def post_voucher():
            conn2 = get_conn()
            c2 = conn2.cursor()
            try:
                c2.execute("INSERT INTO journal_entries(entry_date,voucher_type,voucher_no,narration) VALUES(?,?,?,?)",
                           (date_v.get(), vtype_v.get(), vno_v.get(), nar_v.get()))
                jid = c2.lastrowid
                for ldgr, dr, cr in [(dr_var.get(), float(dr_amt.get() or 0), 0),
                                      (cr_var.get(), 0, float(cr_amt.get() or 0))]:
                    if ldgr:
                        c2.execute("SELECT id FROM ledger_accounts WHERE name=?", (ldgr,))
                        lid = c2.fetchone()
                        if lid:
                            c2.execute("INSERT INTO journal_lines(journal_id,ledger_id,dr_amount,cr_amount) VALUES(?,?,?,?)",
                                       (jid, lid[0], dr, cr))
                conn2.commit()
                messagebox.showinfo("✓", "Voucher posted successfully!", parent=frame)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=frame)
            finally:
                conn2.close()

        tk.Button(mf, text="📮 Post Voucher", bg="#00aa44", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  command=post_voucher).grid(row=4, column=0, columnspan=4, pady=12)

    def _build_party_tab(self, nb):
        frame = tk.Frame(nb, bg="#0f0f1a")
        nb.add(frame, text="👥 Party Statement")
        tk.Label(frame, text="Select Party / Ledger to view outstanding & transactions",
                 bg="#0f0f1a", fg="#ccc", font=("Segoe UI", 9)).pack(pady=6)
        tf = tk.Frame(frame, bg="#0f0f1a")
        tf.pack(fill="x", padx=10)
        conn = get_conn()
        ldgrs = [r[0] for r in conn.execute("SELECT name FROM ledger_accounts ORDER BY name").fetchall()]
        conn.close()
        lvar = tk.StringVar()
        ttk.Combobox(tf, textvariable=lvar, values=ldgrs, width=30).pack(side="left", padx=6)
        cols = ("Date", "Voucher", "Dr", "Cr", "Balance")
        tree_frame = tk.Frame(frame, bg="#0f0f1a")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=6)
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=18)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=140)
        tree.pack(side="left", fill="both", expand=True)
        vsb, hsb = add_treeview_scroll(tree_frame, tree)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')

        def load_party():
            for i in tree.get_children():
                tree.delete(i)
            conn2 = get_conn()
            c2 = conn2.cursor()
            c2.execute("SELECT id FROM ledger_accounts WHERE name=?", (lvar.get(),))
            lid = c2.fetchone()
            if not lid:
                conn2.close()
                return
            c2.execute("""
                SELECT je.entry_date, je.voucher_type||"/"||je.voucher_no,
                       jl.dr_amount, jl.cr_amount
                FROM journal_lines jl
                JOIN journal_entries je ON jl.journal_id=je.id
                WHERE jl.ledger_id=?
                ORDER BY je.entry_date
            """, (lid[0],))
            balance = 0
            for row in c2.fetchall():
                balance += row[2] - row[3]
                tree.insert("", "end", values=(
                    row[0], row[1],
                    f"₹{row[2]:,.2f}" if row[2] else "",
                    f"₹{row[3]:,.2f}" if row[3] else "",
                    f"₹{balance:,.2f} {'Dr' if balance>=0 else 'Cr'}"
                ))
            conn2.close()
        tk.Button(tf, text="Load", bg="#4a90d9", fg="white", relief="flat",
                  font=("Segoe UI", 9), command=load_party).pack(side="left")

    def _export_tree(self, tree, filename):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile=filename,
            filetypes=[("CSV", "*.csv")], parent=self.win)
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(tree["columns"])
            for iid in tree.get_children():
                w.writerow(tree.item(iid)["values"])
        messagebox.showinfo("Exported", f"Saved to {path}", parent=self.win)
