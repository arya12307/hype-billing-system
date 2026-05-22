# Hype ERP - HR Module (company_employee)
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
from modules.erp_branding import HYPE_ERP_BRAND
from modules.window_utils import set_icon


class HRModule:
    MODULE_NAME = "Human Resources"
    MODULE_CODE = "company_employee"

    def __init__(self, parent, db_path="hype_billing_system.db"):
        self.parent = parent
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT,
            designation TEXT,
            email TEXT,
            phone TEXT,
            join_date TEXT,
            salary REAL DEFAULT 0.0,
            status TEXT DEFAULT 'Active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT NOT NULL,
            date TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            status TEXT DEFAULT 'Present'
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT NOT NULL,
            leave_type TEXT,
            from_date TEXT,
            to_date TEXT,
            reason TEXT,
            status TEXT DEFAULT 'Pending'
        )""")
        conn.commit()
        conn.close()

    def open(self):
        win = tk.Toplevel(self.parent)
        win.title(f"{HYPE_ERP_BRAND} - HR Management")
        win.geometry("1000x680")
        win.configure(bg="#1a1a2e")
        set_icon(win)
        self._build_ui(win)

    def _build_ui(self, win):
        tk.Label(win, text=f"👥 {HYPE_ERP_BRAND} — Human Resources",
                 font=("Arial", 18, "bold"), bg="#1a1a2e", fg="#e94560").pack(pady=12)
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=16, pady=6)

        emp_frame = tk.Frame(nb, bg="#16213e")
        nb.add(emp_frame, text="👤 Employees")
        self._build_employees(emp_frame)

        att_frame = tk.Frame(nb, bg="#16213e")
        nb.add(att_frame, text="📅 Attendance")
        self._build_attendance(att_frame)

        leave_frame = tk.Frame(nb, bg="#16213e")
        nb.add(leave_frame, text="🏖️ Leave Management")
        self._build_leaves(leave_frame)

    def _build_employees(self, frame):
        cols = ("Emp ID", "Name", "Department", "Designation", "Email", "Phone", "Salary", "Status")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        self._refresh_employees(tree)
        btn_frame = tk.Frame(frame, bg="#16213e")
        btn_frame.pack(pady=4)
        tk.Button(btn_frame, text="+ Add Employee", bg="#e94560", fg="white",
                  command=lambda: self._add_employee_dialog(tree), relief="flat", padx=10, pady=4).pack(side="left", padx=4)
        tk.Button(btn_frame, text="🔄 Refresh", bg="#333355", fg="white",
                  command=lambda: self._refresh_employees(tree), relief="flat", padx=10, pady=4).pack(side="left", padx=4)

    def _refresh_employees(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT emp_id, name, department, designation, email, phone, salary, status FROM employees")
        for row in c.fetchall():
            tree.insert("", "end", values=row)
        conn.close()

    def _add_employee_dialog(self, tree):
        d = tk.Toplevel()
        d.title("Add Employee")
        d.geometry("420x500")
        d.configure(bg="#1a1a2e")
        set_icon(d)
        fields = [
            ("Employee ID", tk.StringVar()), ("Full Name", tk.StringVar()),
            ("Department", tk.StringVar()), ("Designation", tk.StringVar()),
            ("Email", tk.StringVar()), ("Phone", tk.StringVar()),
            ("Join Date (YYYY-MM-DD)", tk.StringVar(value=datetime.date.today().isoformat())),
            ("Monthly Salary", tk.StringVar(value="0.0")),
        ]
        for label, var in fields:
            tk.Label(d, text=label, bg="#1a1a2e", fg="white", font=("Arial", 9)).pack(anchor="w", padx=20, pady=(6, 0))
            tk.Entry(d, textvariable=var, bg="#16213e", fg="white", insertbackground="white").pack(fill="x", padx=20)

        def save():
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("""
                    INSERT INTO employees (emp_id, name, department, designation, email, phone, join_date, salary)
                    VALUES (?,?,?,?,?,?,?,?)
                """, tuple(v.get() for _, v in fields))
                conn.commit()
                conn.close()
                self._refresh_employees(tree)
                d.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(d, text="💾 Save Employee", bg="#e94560", fg="white",
                  command=save, relief="flat", padx=14, pady=5).pack(pady=14)

    def _build_attendance(self, frame):
        tk.Label(frame, text="Mark Today's Attendance", bg="#16213e", fg="#e94560",
                 font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(frame, text=f"Date: {datetime.date.today().isoformat()}",
                 bg="#16213e", fg="white", font=("Arial", 10)).pack()
        cols = ("Emp ID", "Date", "Check In", "Check Out", "Status")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=13)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=160)
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        self._refresh_attendance(tree)
        tk.Button(frame, text="+ Mark Attendance", bg="#e94560", fg="white",
                  command=lambda: self._mark_attendance_dialog(tree), relief="flat", padx=10, pady=4).pack()

    def _refresh_attendance(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT emp_id, date, check_in, check_out, status FROM attendance ORDER BY date DESC LIMIT 100")
        for row in c.fetchall():
            tree.insert("", "end", values=row)
        conn.close()

    def _mark_attendance_dialog(self, tree):
        d = tk.Toplevel()
        d.title("Mark Attendance")
        d.geometry("380x320")
        d.configure(bg="#1a1a2e")
        set_icon(d)
        fields = [
            ("Employee ID", tk.StringVar()), ("Date", tk.StringVar(value=datetime.date.today().isoformat())),
            ("Check In (HH:MM)", tk.StringVar()), ("Check Out (HH:MM)", tk.StringVar()),
        ]
        status_var = tk.StringVar(value="Present")
        for label, var in fields:
            tk.Label(d, text=label, bg="#1a1a2e", fg="white", font=("Arial", 9)).pack(anchor="w", padx=20, pady=(6, 0))
            tk.Entry(d, textvariable=var, bg="#16213e", fg="white", insertbackground="white").pack(fill="x", padx=20)
        tk.Label(d, text="Status", bg="#1a1a2e", fg="white", font=("Arial", 9)).pack(anchor="w", padx=20, pady=(6, 0))
        ttk.Combobox(d, textvariable=status_var, values=["Present", "Absent", "Half Day", "Leave"]).pack(fill="x", padx=20)

        def save():
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("INSERT INTO attendance (emp_id, date, check_in, check_out, status) VALUES (?,?,?,?,?)",
                             (fields[0][1].get(), fields[1][1].get(), fields[2][1].get(), fields[3][1].get(), status_var.get()))
                conn.commit()
                conn.close()
                self._refresh_attendance(tree)
                d.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(d, text="Save", bg="#e94560", fg="white", command=save, relief="flat", padx=14, pady=5).pack(pady=12)

    def _build_leaves(self, frame):
        cols = ("Emp ID", "Leave Type", "From", "To", "Reason", "Status")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        self._refresh_leaves(tree)
        tk.Button(frame, text="+ Apply Leave", bg="#e94560", fg="white",
                  command=lambda: self._apply_leave_dialog(tree), relief="flat", padx=10, pady=4).pack()

    def _refresh_leaves(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT emp_id, leave_type, from_date, to_date, reason, status FROM leaves ORDER BY from_date DESC")
        for row in c.fetchall():
            tree.insert("", "end", values=row)
        conn.close()

    def _apply_leave_dialog(self, tree):
        d = tk.Toplevel()
        d.title("Apply Leave")
        d.geometry("380x360")
        d.configure(bg="#1a1a2e")
        set_icon(d)
        fields = [
            ("Employee ID", tk.StringVar()),
            ("Leave Type", tk.StringVar(value="Annual")),
            ("From Date", tk.StringVar(value=datetime.date.today().isoformat())),
            ("To Date", tk.StringVar(value=datetime.date.today().isoformat())),
            ("Reason", tk.StringVar()),
        ]
        for label, var in fields:
            tk.Label(d, text=label, bg="#1a1a2e", fg="white", font=("Arial", 9)).pack(anchor="w", padx=20, pady=(6, 0))
            tk.Entry(d, textvariable=var, bg="#16213e", fg="white", insertbackground="white").pack(fill="x", padx=20)

        def save():
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("INSERT INTO leaves (emp_id, leave_type, from_date, to_date, reason) VALUES (?,?,?,?,?)",
                             tuple(v.get() for _, v in fields))
                conn.commit()
                conn.close()
                self._refresh_leaves(tree)
                d.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(d, text="Submit Leave", bg="#e94560", fg="white",
                  command=save, relief="flat", padx=14, pady=5).pack(pady=12)
