# Hype ERP - Payroll Module (payroll)
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
from modules.erp_branding import HYPE_ERP_BRAND
from modules.window_utils import set_icon


class PayrollModule:
    MODULE_NAME = "Payroll"
    MODULE_CODE = "payroll"

    def __init__(self, parent, db_path="hype_billing_system.db"):
        self.parent = parent
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS payroll (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT NOT NULL,
            month TEXT NOT NULL,
            basic REAL DEFAULT 0.0,
            hra REAL DEFAULT 0.0,
            allowances REAL DEFAULT 0.0,
            deductions REAL DEFAULT 0.0,
            pf REAL DEFAULT 0.0,
            tds REAL DEFAULT 0.0,
            net_salary REAL DEFAULT 0.0,
            status TEXT DEFAULT 'Pending',
            paid_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.commit()
        conn.close()

    def open(self):
        win = tk.Toplevel(self.parent)
        win.title(f"{HYPE_ERP_BRAND} - Payroll")
        win.geometry("1000x650")
        win.configure(bg="#1a1a2e")
        set_icon(win)
        self._build_ui(win)

    def _build_ui(self, win):
        tk.Label(win, text=f"💰 {HYPE_ERP_BRAND} — Payroll Management",
                 font=("Arial", 18, "bold"), bg="#1a1a2e", fg="#e94560").pack(pady=12)
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=16, pady=6)

        list_frame = tk.Frame(nb, bg="#16213e")
        nb.add(list_frame, text="📋 Payroll Records")
        self._build_payroll_list(list_frame)

        gen_frame = tk.Frame(nb, bg="#16213e")
        nb.add(gen_frame, text="➕ Generate Payslip")
        self._build_generate_payslip(gen_frame)

    def _build_payroll_list(self, frame):
        cols = ("ID", "Emp ID", "Month", "Basic", "HRA", "Allowances", "PF", "TDS", "Net Salary", "Status")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        self._refresh_payroll(tree)
        tk.Button(frame, text="🔄 Refresh", bg="#333355", fg="white",
                  command=lambda: self._refresh_payroll(tree), relief="flat", padx=10, pady=4).pack()

    def _refresh_payroll(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, emp_id, month, basic, hra, allowances, pf, tds, net_salary, status FROM payroll ORDER BY month DESC")
        for row in c.fetchall():
            tree.insert("", "end", values=row)
        conn.close()

    def _build_generate_payslip(self, frame):
        tk.Label(frame, text="Generate Payslip", bg="#16213e", fg="#e94560",
                 font=("Arial", 13, "bold")).pack(pady=14)
        fields = [
            ("Employee ID", tk.StringVar()), ("Month (YYYY-MM)", tk.StringVar(value=datetime.date.today().strftime("%Y-%m"))),
            ("Basic Salary", tk.StringVar(value="0.0")), ("HRA", tk.StringVar(value="0.0")),
            ("Allowances", tk.StringVar(value="0.0")), ("Deductions", tk.StringVar(value="0.0")),
            ("PF", tk.StringVar(value="0.0")), ("TDS", tk.StringVar(value="0.0")),
        ]
        frm = tk.Frame(frame, bg="#16213e")
        frm.pack(padx=40)
        for i, (label, var) in enumerate(fields):
            tk.Label(frm, text=label, bg="#16213e", fg="white", font=("Arial", 9), width=22, anchor="e").grid(row=i, column=0, pady=5, padx=(0, 8))
            tk.Entry(frm, textvariable=var, bg="#1a1a2e", fg="white", insertbackground="white", width=24).grid(row=i, column=1, pady=5)

        def generate():
            try:
                vals = {k: float(v.get()) if i > 1 else v.get() for i, (k, v) in enumerate(fields)}
                basic = float(fields[2][1].get())
                hra = float(fields[3][1].get())
                allw = float(fields[4][1].get())
                deductions = float(fields[5][1].get())
                pf = float(fields[6][1].get())
                tds = float(fields[7][1].get())
                net = basic + hra + allw - deductions - pf - tds
                conn = sqlite3.connect(self.db_path)
                conn.execute("""
                    INSERT INTO payroll (emp_id, month, basic, hra, allowances, deductions, pf, tds, net_salary)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (fields[0][1].get(), fields[1][1].get(), basic, hra, allw, deductions, pf, tds, net))
                conn.commit()
                conn.close()
                messagebox.showinfo("Hype ERP", f"Payslip generated!\nNet Salary: ₹{net:.2f}")
                # Try immediate push to Firebase for near-zero data loss
                try:
                    import firebase_sync
                    fsm = getattr(firebase_sync, 'firebase_sync_manager', None)
                    if fsm and getattr(fsm, 'db', None):
                        try:
                            from main import get_setting
                            store_id = int(get_setting('store_id', '1'))
                        except Exception:
                            store_id = 1
                        try:
                            fsm.sync_table_to_firestore('payroll', f'stores/{store_id}/payroll')
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(frame, text="💾 Generate & Save Payslip", bg="#e94560", fg="white",
                  command=generate, relief="flat", padx=16, pady=8, font=("Arial", 10, "bold")).pack(pady=16)
