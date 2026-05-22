# Hype ERP - Inventory Analysis Module
# Dead Stock Detection & Low Stock Alerts
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
from modules.erp_branding import HYPE_ERP_BRAND
from modules.window_utils import set_icon

DEFAULT_LOW_STOCK_THRESHOLD = 10
DEAD_STOCK_DAYS = 90  # items not sold in 90 days


class InventoryAnalysisModule:
    MODULE_NAME = "Inventory & Stock Analysis"
    MODULE_CODE = "stock"

    def __init__(self, parent, db_path="hype_billing_system.db"):
        self.parent = parent
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            sku TEXT UNIQUE,
            quantity INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 10,
            cost_price REAL DEFAULT 0.0,
            sale_price REAL DEFAULT 0.0,
            last_sold_date TEXT,
            category TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.commit()
        conn.close()

    def open(self):
        win = tk.Toplevel(self.parent)
        win.title(f"{HYPE_ERP_BRAND} - Inventory & Stock Analysis")
        win.geometry("1100x700")
        win.configure(bg="#1a1a2e")
        set_icon(win)
        self._build_ui(win)

    def _build_ui(self, win):
        tk.Label(win, text=f"📦 {HYPE_ERP_BRAND} — Inventory & Stock Analysis",
                 font=("Arial", 18, "bold"), bg="#1a1a2e", fg="#e94560").pack(pady=12)
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=16, pady=6)

        # All Stock
        all_frame = tk.Frame(nb, bg="#16213e")
        nb.add(all_frame, text="📋 All Stock")
        self._build_stock_table(all_frame)

        # Dead Stock
        dead_frame = tk.Frame(nb, bg="#16213e")
        nb.add(dead_frame, text="💀 Dead Stock Analysis")
        self._build_dead_stock(dead_frame)

        # Low Stock Alerts
        low_frame = tk.Frame(nb, bg="#16213e")
        nb.add(low_frame, text="⚠️ Low Stock Alerts")
        self._build_low_stock(low_frame)

        # Add Stock
        add_frame = tk.Frame(nb, bg="#16213e")
        nb.add(add_frame, text="➕ Add Product")
        self._build_add_product(add_frame)

    def _build_stock_table(self, frame):
        cols = ("ID", "Product", "SKU", "Qty", "Min Stock", "Cost", "Price", "Last Sold", "Category")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=16)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=110)
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=sb.set)
        tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        sb.pack(side="right", fill="y", pady=10)
        self._refresh_stock(tree)
        tk.Button(frame, text="🔄 Refresh", bg="#333355", fg="white",
                  command=lambda: self._refresh_stock(tree), relief="flat", padx=10, pady=4).pack(pady=4)

    def _refresh_stock(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, product_name, sku, quantity, min_stock, cost_price, sale_price, last_sold_date, category FROM inventory")
        for row in c.fetchall():
            tags = ()
            qty, min_s = row[3], row[4]
            if qty <= 0:
                tags = ("zero",)
            elif qty < min_s:
                tags = ("low",)
            tree.insert("", "end", values=row, tags=tags)
        tree.tag_configure("low", background="#3d2a00", foreground="#ffcc00")
        tree.tag_configure("zero", background="#3d0000", foreground="#ff6b6b")
        conn.close()

    def _build_dead_stock(self, frame):
        tk.Label(frame, text=f"Dead Stock: Items not sold in the last {DEAD_STOCK_DAYS} days",
                 bg="#16213e", fg="#ffcc00", font=("Arial", 11)).pack(pady=(12, 4))
        cols = ("Product", "SKU", "Qty", "Last Sold", "Days Idle", "Value (Cost)")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        tree.pack(fill="both", expand=True, padx=10, pady=6)
        self._load_dead_stock(tree)
        tk.Button(frame, text="🔄 Refresh", bg="#333355", fg="white",
                  command=lambda: self._load_dead_stock(tree), relief="flat", padx=10, pady=4).pack(pady=4)

    def _load_dead_stock(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        cutoff = (datetime.date.today() - datetime.timedelta(days=DEAD_STOCK_DAYS)).isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT product_name, sku, quantity, last_sold_date, cost_price
            FROM inventory
            WHERE (last_sold_date IS NULL OR last_sold_date < ?) AND quantity > 0
            ORDER BY last_sold_date ASC
        """, (cutoff,))
        today = datetime.date.today()
        for row in c.fetchall():
            name, sku, qty, last_sold, cost = row
            if last_sold:
                days_idle = (today - datetime.date.fromisoformat(last_sold)).days
            else:
                days_idle = "Never Sold"
            value = f"{qty * cost:.2f}" if isinstance(qty, int) else "N/A"
            tree.insert("", "end", values=(name, sku or "", qty, last_sold or "Never", days_idle, value))
        conn.close()

    def _build_low_stock(self, frame):
        summary_frame = tk.Frame(frame, bg="#2d1b2e", pady=10)
        summary_frame.pack(fill="x", padx=10, pady=(10, 0))
        tk.Label(summary_frame, text="⚠️ LOW STOCK ALERT DASHBOARD",
                 bg="#2d1b2e", fg="#ff6b6b", font=("Arial", 13, "bold")).pack()
        tk.Label(summary_frame, text="Items below minimum threshold are highlighted.",
                 bg="#2d1b2e", fg="#a0a0b0", font=("Arial", 9)).pack()
        cols = ("Product", "SKU", "Current Qty", "Min Stock", "Shortage", "Status")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        tree.pack(fill="both", expand=True, padx=10, pady=8)
        self._load_low_stock(tree)
        tk.Button(frame, text="🔄 Refresh Alerts", bg="#e94560", fg="white",
                  command=lambda: self._load_low_stock(tree), relief="flat", padx=12, pady=5).pack(pady=4)

    def _load_low_stock(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT product_name, sku, quantity, min_stock
            FROM inventory
            WHERE quantity < min_stock
            ORDER BY quantity ASC
        """)
        for row in c.fetchall():
            name, sku, qty, min_s = row
            shortage = min_s - qty
            status = "🔴 OUT OF STOCK" if qty <= 0 else "🟡 LOW STOCK"
            tree.insert("", "end", values=(name, sku or "", qty, min_s, shortage, status))
        conn.close()

    def _build_add_product(self, frame):
        tk.Label(frame, text="Add New Product to Inventory",
                 bg="#16213e", fg="#e94560", font=("Arial", 13, "bold")).pack(pady=16)
        fields = [
            ("Product Name", tk.StringVar()), ("SKU / Barcode", tk.StringVar()),
            ("Quantity", tk.StringVar(value="0")), ("Min Stock Alert", tk.StringVar(value="10")),
            ("Cost Price", tk.StringVar(value="0.0")), ("Sale Price", tk.StringVar(value="0.0")),
            ("Category", tk.StringVar()),
        ]
        frm = tk.Frame(frame, bg="#16213e")
        frm.pack(padx=40)
        for i, (label, var) in enumerate(fields):
            tk.Label(frm, text=label, bg="#16213e", fg="white", font=("Arial", 9), width=18, anchor="e").grid(row=i, column=0, pady=6, padx=(0, 8), sticky="e")
            tk.Entry(frm, textvariable=var, bg="#1a1a2e", fg="white", insertbackground="white", width=28).grid(row=i, column=1, pady=6)

        def save():
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("""
                    INSERT INTO inventory (product_name, sku, quantity, min_stock, cost_price, sale_price, category)
                    VALUES (?,?,?,?,?,?,?)
                """, tuple(v.get() for _, v in fields))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "Product added to inventory!")
                for _, var in fields:
                    var.set("")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(frame, text="💾 Add Product", bg="#e94560", fg="white",
                  command=save, relief="flat", padx=16, pady=7, font=("Arial", 10, "bold")).pack(pady=16)
