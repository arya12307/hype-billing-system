# Hype ERP - Projects & Timesheet Module (project / timesheet)
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
from modules.erp_branding import HYPE_ERP_BRAND
from modules.window_utils import set_icon


class ProjectsModule:
    MODULE_NAME = "Projects & Timesheet"
    MODULE_CODE = "project"

    def __init__(self, parent, db_path="hype_billing_system.db"):
        self.parent = parent
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            client TEXT,
            manager TEXT,
            start_date TEXT,
            end_date TEXT,
            budget REAL DEFAULT 0.0,
            status TEXT DEFAULT 'Active',
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            title TEXT NOT NULL,
            assigned_to TEXT,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Todo',
            due_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS timesheets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            emp_id TEXT,
            date TEXT,
            hours REAL DEFAULT 0.0,
            description TEXT,
            billable INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.commit()
        conn.close()

    def open(self):
        win = tk.Toplevel(self.parent)
        win.title(f"{HYPE_ERP_BRAND} - Projects & Timesheet")
        win.geometry("1050x680")
        win.configure(bg="#1a1a2e")
        set_icon(win)
        self._build_ui(win)

    def _build_ui(self, win):
        tk.Label(win, text=f"📁 {HYPE_ERP_BRAND} — Projects & Timesheet",
                 font=("Arial", 18, "bold"), bg="#1a1a2e", fg="#e94560").pack(pady=12)
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=16, pady=6)

        proj_frame = tk.Frame(nb, bg="#16213e")
        nb.add(proj_frame, text="📁 Projects")
        self._build_projects(proj_frame)

        task_frame = tk.Frame(nb, bg="#16213e")
        nb.add(task_frame, text="✅ Tasks")
        self._build_tasks(task_frame)

        ts_frame = tk.Frame(nb, bg="#16213e")
        nb.add(ts_frame, text="⏱️ Timesheet")
        self._build_timesheet(ts_frame)

    def _build_projects(self, frame):
        cols = ("ID", "Name", "Client", "Manager", "Start", "End", "Budget", "Status")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        self._refresh_projects(tree)
        tk.Button(frame, text="+ New Project", bg="#e94560", fg="white",
                  command=lambda: self._add_project_dialog(tree), relief="flat", padx=10, pady=4).pack()

    def _refresh_projects(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, name, client, manager, start_date, end_date, budget, status FROM projects")
        for row in c.fetchall():
            tree.insert("", "end", values=row)
        conn.close()

    def _add_project_dialog(self, tree):
        d = tk.Toplevel()
        d.title("New Project")
        d.geometry("400x420")
        d.configure(bg="#1a1a2e")
        set_icon(d)
        fields = [
            ("Project Name", tk.StringVar()), ("Client", tk.StringVar()),
            ("Manager", tk.StringVar()), ("Start Date", tk.StringVar(value=datetime.date.today().isoformat())),
            ("End Date", tk.StringVar()), ("Budget", tk.StringVar(value="0.0")),
            ("Description", tk.StringVar()),
        ]
        for label, var in fields:
            tk.Label(d, text=label, bg="#1a1a2e", fg="white", font=("Arial", 9)).pack(anchor="w", padx=20, pady=(6, 0))
            tk.Entry(d, textvariable=var, bg="#16213e", fg="white", insertbackground="white").pack(fill="x", padx=20)

        def save():
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("INSERT INTO projects (name, client, manager, start_date, end_date, budget, description) VALUES (?,?,?,?,?,?,?)",
                             tuple(v.get() for _, v in fields))
                conn.commit()
                conn.close()
                self._refresh_projects(tree)
                d.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(d, text="💾 Save Project", bg="#e94560", fg="white",
                  command=save, relief="flat", padx=14, pady=5).pack(pady=12)

    def _build_tasks(self, frame):
        cols = ("ID", "Project ID", "Title", "Assigned To", "Priority", "Status", "Due Date")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=130)
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        self._refresh_tasks(tree)
        tk.Button(frame, text="+ Add Task", bg="#e94560", fg="white",
                  command=lambda: self._add_task_dialog(tree), relief="flat", padx=10, pady=4).pack()

    def _refresh_tasks(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, project_id, title, assigned_to, priority, status, due_date FROM tasks ORDER BY due_date")
        for row in c.fetchall():
            tree.insert("", "end", values=row)
        conn.close()

    def _add_task_dialog(self, tree):
        d = tk.Toplevel()
        d.title("Add Task")
        d.geometry("380x360")
        d.configure(bg="#1a1a2e")
        set_icon(d)
        priority_var = tk.StringVar(value="Medium")
        status_var = tk.StringVar(value="Todo")
        fields = [
            ("Project ID", tk.StringVar()), ("Task Title", tk.StringVar()),
            ("Assigned To", tk.StringVar()), ("Due Date", tk.StringVar(value=datetime.date.today().isoformat())),
        ]
        for label, var in fields:
            tk.Label(d, text=label, bg="#1a1a2e", fg="white", font=("Arial", 9)).pack(anchor="w", padx=20, pady=(6, 0))
            tk.Entry(d, textvariable=var, bg="#16213e", fg="white", insertbackground="white").pack(fill="x", padx=20)
        tk.Label(d, text="Priority", bg="#1a1a2e", fg="white", font=("Arial", 9)).pack(anchor="w", padx=20, pady=(6, 0))
        ttk.Combobox(d, textvariable=priority_var, values=["Low", "Medium", "High", "Critical"]).pack(fill="x", padx=20)
        tk.Label(d, text="Status", bg="#1a1a2e", fg="white", font=("Arial", 9)).pack(anchor="w", padx=20, pady=(6, 0))
        ttk.Combobox(d, textvariable=status_var, values=["Todo", "In Progress", "Done", "Blocked"]).pack(fill="x", padx=20)

        def save():
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("INSERT INTO tasks (project_id, title, assigned_to, due_date, priority, status) VALUES (?,?,?,?,?,?)",
                             (fields[0][1].get(), fields[1][1].get(), fields[2][1].get(),
                              fields[3][1].get(), priority_var.get(), status_var.get()))
                conn.commit()
                conn.close()
                self._refresh_tasks(tree)
                d.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(d, text="Save Task", bg="#e94560", fg="white",
                  command=save, relief="flat", padx=14, pady=5).pack(pady=10)

    def _build_timesheet(self, frame):
        cols = ("ID", "Project ID", "Emp ID", "Date", "Hours", "Description", "Billable")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=130)
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        self._refresh_timesheet(tree)
        tk.Button(frame, text="+ Log Time", bg="#e94560", fg="white",
                  command=lambda: self._log_time_dialog(tree), relief="flat", padx=10, pady=4).pack()

    def _refresh_timesheet(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, project_id, emp_id, date, hours, description, billable FROM timesheets ORDER BY date DESC")
        for row in c.fetchall():
            row = list(row)
            row[6] = "Yes" if row[6] else "No"
            tree.insert("", "end", values=row)
        conn.close()

    def _log_time_dialog(self, tree):
        d = tk.Toplevel()
        d.title("Log Time")
        d.geometry("380x340")
        d.configure(bg="#1a1a2e")
        set_icon(d)
        billable_var = tk.BooleanVar(value=True)
        fields = [
            ("Project ID", tk.StringVar()), ("Employee ID", tk.StringVar()),
            ("Date", tk.StringVar(value=datetime.date.today().isoformat())),
            ("Hours", tk.StringVar(value="1.0")), ("Description", tk.StringVar()),
        ]
        for label, var in fields:
            tk.Label(d, text=label, bg="#1a1a2e", fg="white", font=("Arial", 9)).pack(anchor="w", padx=20, pady=(6, 0))
            tk.Entry(d, textvariable=var, bg="#16213e", fg="white", insertbackground="white").pack(fill="x", padx=20)
        tk.Checkbutton(d, text="Billable", variable=billable_var, bg="#1a1a2e", fg="white", selectcolor="#16213e").pack(anchor="w", padx=20, pady=(6, 0))

        def save():
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("INSERT INTO timesheets (project_id, emp_id, date, hours, description, billable) VALUES (?,?,?,?,?,?)",
                             (fields[0][1].get(), fields[1][1].get(), fields[2][1].get(),
                              float(fields[3][1].get()), fields[4][1].get(), int(billable_var.get())))
                conn.commit()
                conn.close()
                self._refresh_timesheet(tree)
                d.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(d, text="💾 Log Time", bg="#e94560", fg="white",
                  command=save, relief="flat", padx=14, pady=5).pack(pady=12)
