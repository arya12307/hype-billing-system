# Hype ERP - CRM Module (crm) - Customer & Vendor CRM
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
from modules.erp_branding import HYPE_ERP_BRAND
from modules.window_utils import set_icon


class CRMModule:
    MODULE_NAME = "CRM"
    MODULE_CODE = "crm"

    def __init__(self, parent, db_path="hype_billing_system.db"):
        self.parent = parent
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS crm_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT DEFAULT 'Customer',
            name TEXT NOT NULL,
            company TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            gst_number TEXT,
            credit_limit REAL DEFAULT 0.0,
            outstanding REAL DEFAULT 0.0,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS crm_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER,
            title TEXT NOT NULL,
            stage TEXT DEFAULT 'New',
            expected_value REAL DEFAULT 0.0,
            probability INTEGER DEFAULT 0,
            assigned_to TEXT,
            close_date TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.commit()
        conn.close()

    def open(self):
        win = tk.Toplevel(self.parent)
        win.title(f"{HYPE_ERP_BRAND} - CRM")
        win.geometry("1050x680")
        win.configure(bg="#1a1a2e")
        set_icon(win)
        self._build_ui(win)

    def _build_ui(self, win):
        tk.Label(win, text=f"🤝 {HYPE_ERP_BRAND} — CRM (Customer & Vendor)",
                 font=("Arial", 18, "bold"), bg="#1a1a2e", fg="#e94560").pack(pady=12)
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=16, pady=6)

        cust_frame = tk.Frame(nb, bg="#16213e")
        nb.add(cust_frame, text="🧑 Customers")
        self._build_contacts(cust_frame, "Customer")

        vendor_frame = tk.Frame(nb, bg="#16213e")
        nb.add(vendor_frame, text="🏭 Vendors")
        self._build_contacts(vendor_frame, "Vendor")

        leads_frame = tk.Frame(nb, bg="#16213e")
        nb.add(leads_frame, text="📊 Leads & Pipeline")
        self._build_leads(leads_frame)

    def _build_contacts(self, frame, contact_type):
        cols = ("ID", "Name", "Company", "Email", "Phone", "GST No.", "Outstanding")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=130)
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        self._refresh_contacts(tree, contact_type)
        btn_frame = tk.Frame(frame, bg="#16213e")
        btn_frame.pack(pady=4)
        tk.Button(btn_frame, text=f"+ Add {contact_type}", bg="#e94560", fg="white",
                  command=lambda: self._add_contact_dialog(tree, contact_type), relief="flat", padx=10, pady=4).pack(side="left", padx=4)
        tk.Button(btn_frame, text="🔄 Refresh", bg="#333355", fg="white",
                  command=lambda: self._refresh_contacts(tree, contact_type), relief="flat", padx=10, pady=4).pack(side="left", padx=4)

    def _refresh_contacts(self, tree, contact_type):
        for i in tree.get_children():
            tree.delete(i)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, name, company, email, phone, gst_number, outstanding FROM crm_contacts WHERE type=?", (contact_type,))
        for row in c.fetchall():
            tree.insert("", "end", values=row)
        conn.close()

    def _add_contact_dialog(self, tree, contact_type):
        d = tk.Toplevel()
        d.title(f"Add {contact_type}")
        d.geometry("400x480")
        d.configure(bg="#1a1a2e")
        set_icon(d)
        fields = [
            ("Name", tk.StringVar()), ("Company", tk.StringVar()),
            ("Email", tk.StringVar()), ("Phone", tk.StringVar()),
            ("Address", tk.StringVar()), ("GST Number", tk.StringVar()),
            ("Credit Limit", tk.StringVar(value="0.0")), ("Notes", tk.StringVar()),
        ]
        for label, var in fields:
            tk.Label(d, text=label, bg="#1a1a2e", fg="white", font=("Arial", 9)).pack(anchor="w", padx=20, pady=(5, 0))
            tk.Entry(d, textvariable=var, bg="#16213e", fg="white", insertbackground="white").pack(fill="x", padx=20)

        def save():
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("""
                    INSERT INTO crm_contacts (type, name, company, email, phone, address, gst_number, credit_limit, notes)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (contact_type,) + tuple(v.get() for _, v in fields))
                conn.commit()
                conn.close()
                self._refresh_contacts(tree, contact_type)
                d.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(d, text="💾 Save", bg="#e94560", fg="white",
                  command=save, relief="flat", padx=14, pady=5).pack(pady=12)

    def _build_leads(self, frame):
        pipeline_stages = ["New", "Qualified", "Proposal", "Negotiation", "Won", "Lost"]
        stage_colors = {"New": "#16213e", "Qualified": "#1a3a2a", "Proposal": "#2a2a1e",
                        "Negotiation": "#2a1a1e", "Won": "#1a3a1a", "Lost": "#3a1a1a"}
        cols = ("ID", "Title", "Stage", "Value", "Probability", "Assigned To", "Close Date")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=130)
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        self._refresh_leads(tree)
        tk.Button(frame, text="+ New Lead", bg="#e94560", fg="white",
                  command=lambda: self._add_lead_dialog(tree, pipeline_stages), relief="flat", padx=10, pady=4).pack()

    def _refresh_leads(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, title, stage, expected_value, probability, assigned_to, close_date FROM crm_leads ORDER BY created_at DESC")
        for row in c.fetchall():
            tree.insert("", "end", values=row)
        conn.close()

    def _add_lead_dialog(self, tree, stages):
        d = tk.Toplevel()
        d.title("New Lead")
        d.geometry("400x420")
        d.configure(bg="#1a1a2e")
        set_icon(d)
        stage_var = tk.StringVar(value="New")
        fields = [
            ("Lead Title", tk.StringVar()), ("Expected Value", tk.StringVar(value="0.0")),
            ("Probability (%)", tk.StringVar(value="50")), ("Assigned To", tk.StringVar()),
            ("Close Date", tk.StringVar(value=datetime.date.today().isoformat())),
            ("Notes", tk.StringVar()),
        ]
        tk.Label(d, text="Stage", bg="#1a1a2e", fg="white", font=("Arial", 9)).pack(anchor="w", padx=20, pady=(10, 0))
        ttk.Combobox(d, textvariable=stage_var, values=stages).pack(fill="x", padx=20)
        for label, var in fields:
            tk.Label(d, text=label, bg="#1a1a2e", fg="white", font=("Arial", 9)).pack(anchor="w", padx=20, pady=(5, 0))
            tk.Entry(d, textvariable=var, bg="#16213e", fg="white", insertbackground="white").pack(fill="x", padx=20)

        def save():
            try:
                conn = sqlite3.connect(self.db_path)
                vals = [fields[0][1].get(), stage_var.get()] + [v.get() for _, v in fields[1:]]
                conn.execute("""
                    INSERT INTO crm_leads (title, stage, expected_value, probability, assigned_to, close_date, notes)
                    VALUES (?,?,?,?,?,?,?)
                """, vals)
                conn.commit()
                conn.close()
                self._refresh_leads(tree)
                d.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(d, text="💾 Save Lead", bg="#e94560", fg="white",
                  command=save, relief="flat", padx=14, pady=5).pack(pady=12)
