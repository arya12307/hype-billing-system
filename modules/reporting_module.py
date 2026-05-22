# Hype ERP - Reporting & Analytics Module (analytic_account)
import tkinter as tk
from tkinter import ttk
import sqlite3
import datetime
from modules.erp_branding import HYPE_ERP_BRAND
from modules.window_utils import set_icon


class ReportingModule:
    MODULE_NAME = "Reporting & Analytics"
    MODULE_CODE = "analytic_account"

    def __init__(self, parent, db_path="hype_billing_system.db"):
        self.parent = parent
        self.db_path = db_path

    def open(self):
        win = tk.Toplevel(self.parent)
        win.title(f"{HYPE_ERP_BRAND} - Reporting & Analytics")
        win.geometry("1100x700")
        win.configure(bg="#1a1a2e")
        set_icon(win)
        self._build_ui(win)

    def _build_ui(self, win):
        tk.Label(win, text=f"📊 {HYPE_ERP_BRAND} — Reporting & Analytics",
                 font=("Arial", 18, "bold"), bg="#1a1a2e", fg="#e94560").pack(pady=12)
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=16, pady=6)

        # KPI Dashboard
        kpi_frame = tk.Frame(nb, bg="#16213e")
        nb.add(kpi_frame, text="📈 KPI Dashboard")
        self._build_kpi(kpi_frame)

        # Dead Stock Report
        ds_frame = tk.Frame(nb, bg="#16213e")
        nb.add(ds_frame, text="💀 Dead Stock Report")
        self._build_dead_stock_report(ds_frame)

        # Sales Report
        sales_frame = tk.Frame(nb, bg="#16213e")
        nb.add(sales_frame, text="💹 Sales Report")
        self._build_sales_report(sales_frame)

        # Employee Report
        emp_frame = tk.Frame(nb, bg="#16213e")
        nb.add(emp_frame, text="👥 HR Report")
        self._build_hr_report(emp_frame)

    def _build_kpi(self, frame):
        tk.Label(frame, text="Key Performance Indicators", bg="#16213e", fg="#e94560",
                 font=("Arial", 14, "bold")).pack(pady=14)
        kpi_frame = tk.Frame(frame, bg="#16213e")
        kpi_frame.pack(fill="x", padx=24)

        kpis = self._get_kpis()
        colors = ["#e94560", "#7fdbff", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]
        for i, (label, value) in enumerate(kpis):
            card = tk.Frame(kpi_frame, bg=colors[i % len(colors)], padx=16, pady=12)
            card.grid(row=i // 3, column=i % 3, padx=10, pady=10, sticky="ew")
            tk.Label(card, text=value, font=("Arial", 22, "bold"), bg=colors[i % len(colors)], fg="white").pack()
            tk.Label(card, text=label, font=("Arial", 9), bg=colors[i % len(colors)], fg="white").pack()
        for c in range(3):
            kpi_frame.columnconfigure(c, weight=1)

    def _get_kpis(self):
        kpis = []
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute("SELECT COUNT(*) FROM employees")
            kpis.append(("Total Employees", str(c.fetchone()[0])))
        except Exception:
            kpis.append(("Total Employees", "N/A"))
        try:
            c.execute("SELECT COUNT(*) FROM inventory")
            kpis.append(("Total Products", str(c.fetchone()[0])))
        except Exception:
            kpis.append(("Total Products", "N/A"))
        try:
            c.execute("SELECT COUNT(*) FROM inventory WHERE quantity < min_stock")
            kpis.append(("Low Stock Items", str(c.fetchone()[0])))
        except Exception:
            kpis.append(("Low Stock Items", "N/A"))
        try:
            c.execute("SELECT COUNT(*) FROM crm_contacts WHERE type='Customer'")
            kpis.append(("Total Customers", str(c.fetchone()[0])))
        except Exception:
            kpis.append(("Total Customers", "N/A"))
        try:
            c.execute("SELECT COUNT(*) FROM crm_contacts WHERE type='Vendor'")
            kpis.append(("Total Vendors", str(c.fetchone()[0])))
        except Exception:
            kpis.append(("Total Vendors", "N/A"))
        try:
            cutoff = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
            c.execute("SELECT COUNT(*) FROM inventory WHERE (last_sold_date IS NULL OR last_sold_date < ?) AND quantity > 0", (cutoff,))
            kpis.append(("Dead Stock Items", str(c.fetchone()[0])))
        except Exception:
            kpis.append(("Dead Stock Items", "N/A"))
        conn.close()
        return kpis

    def _build_dead_stock_report(self, frame):
        tk.Label(frame, text="Dead Stock Analysis Report", bg="#16213e", fg="#e94560",
                 font=("Arial", 13, "bold")).pack(pady=12)
        tk.Label(frame, text="Items not sold in 90+ days with remaining stock (carrying cost risk)",
                 bg="#16213e", fg="#a0a0b0", font=("Arial", 9)).pack()
        cols = ("Product", "SKU", "Qty", "Cost Price", "Total Value", "Last Sold", "Days Idle")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=140)
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        cutoff = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()
            c.execute("""
                SELECT product_name, sku, quantity, cost_price, last_sold_date
                FROM inventory
                WHERE (last_sold_date IS NULL OR last_sold_date < ?) AND quantity > 0
                ORDER BY last_sold_date ASC
            """, (cutoff,))
            today = datetime.date.today()
            for row in c.fetchall():
                name, sku, qty, cost, last_sold = row
                total_val = f"{qty * cost:.2f}"
                if last_sold:
                    days_idle = (today - datetime.date.fromisoformat(last_sold)).days
                else:
                    days_idle = "Never Sold"
                tree.insert("", "end", values=(name, sku or "", qty, f"{cost:.2f}", total_val, last_sold or "Never", days_idle))
        except Exception:
            pass
        conn.close()

    def _build_sales_report(self, frame):
        tk.Label(frame, text="Sales Overview Report", bg="#16213e", fg="#e94560",
                 font=("Arial", 13, "bold")).pack(pady=12)
        cols = ("Invoice No", "Date", "Customer", "Amount", "GST", "Total", "Status")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=145)
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()
            c.execute("SELECT invoice_number, date, customer_name, subtotal, gst_amount, total_amount, payment_status FROM invoices ORDER BY date DESC LIMIT 100")
            for row in c.fetchall():
                tree.insert("", "end", values=row)
        except Exception:
            pass
        conn.close()

    def _build_hr_report(self, frame):
        tk.Label(frame, text="HR Summary Report", bg="#16213e", fg="#e94560",
                 font=("Arial", 13, "bold")).pack(pady=12)
        cols = ("Emp ID", "Name", "Department", "Designation", "Salary", "Status")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=160)
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()
            c.execute("SELECT emp_id, name, department, designation, salary, status FROM employees ORDER BY name")
            for row in c.fetchall():
                tree.insert("", "end", values=row)
        except Exception:
            pass
        conn.close()
