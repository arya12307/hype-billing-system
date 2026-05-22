# Hype ERP - POS Module (sale_point)
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
from modules.erp_branding import HYPE_ERP_BRAND
from modules.scrollable_frame import add_treeview_scroll
from modules.window_utils import set_icon


class POSModule:
    MODULE_NAME = "Point of Sale"
    MODULE_CODE = "sale_point"

    def __init__(self, parent, db_path="hype_billing_system.db"):
        self.parent = parent
        self.db_path = db_path
        self.cart = []
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS pos_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_date TEXT NOT NULL,
            total_sales REAL DEFAULT 0.0,
            total_orders INTEGER DEFAULT 0,
            opened_at TEXT,
            closed_at TEXT,
            status TEXT DEFAULT 'Open'
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS pos_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT NOT NULL,
            date TEXT NOT NULL,
            items TEXT,
            subtotal REAL,
            gst REAL,
            discount REAL DEFAULT 0.0,
            total REAL,
            payment_method TEXT DEFAULT 'Cash',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.commit()
        conn.close()

    def open(self):
        win = tk.Toplevel(self.parent)
        win.title(f"{HYPE_ERP_BRAND} - Point of Sale")
        win.geometry("1100x700")
        win.configure(bg="#1a1a2e")
        set_icon(win)
        self._build_pos_ui(win)

    def _build_pos_ui(self, win):
        tk.Label(win, text=f"🛒 {HYPE_ERP_BRAND} — Point of Sale",
                 font=("Arial", 18, "bold"), bg="#1a1a2e", fg="#e94560").pack(pady=8)
        main = tk.Frame(win, bg="#1a1a2e")
        main.pack(fill="both", expand=True, padx=16, pady=4)

        # Left: Product Search
        left = tk.Frame(main, bg="#16213e", width=420)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tk.Label(left, text="🔍 Search Products", bg="#16213e", fg="white", font=("Arial", 11, "bold")).pack(pady=8)
        search_var = tk.StringVar()
        tk.Entry(left, textvariable=search_var, bg="#1a1a2e", fg="white",
                 insertbackground="white", font=("Arial", 12), width=30).pack(padx=10, pady=4)
        prod_frame = tk.Frame(left, bg="#16213e")
        prod_frame.pack(fill="both", expand=True, padx=10, pady=4)
        prod_tree = ttk.Treeview(prod_frame, columns=("Product", "Price", "Stock"), show="headings", height=16)
        for col in ("Product", "Price", "Stock"):
            prod_tree.heading(col, text=col)
            prod_tree.column(col, width=120)
        prod_tree.pack(side="left", fill="both", expand=True)
        prod_vsb, prod_hsb = add_treeview_scroll(prod_frame, prod_tree)
        prod_vsb.pack(side='right', fill='y')
        prod_hsb.pack(side='bottom', fill='x')
        self._load_pos_products(prod_tree)

        def on_search(*args):
            self._load_pos_products(prod_tree, search_var.get())
        search_var.trace("w", on_search)

        # Right: Cart
        right = tk.Frame(main, bg="#0f3460", width=380)
        right.pack(side="right", fill="both", padx=(8, 0))
        tk.Label(right, text="🛒 Cart", bg="#0f3460", fg="white", font=("Arial", 13, "bold")).pack(pady=8)
        cart_frame = tk.Frame(right, bg="#0f3460")
        cart_frame.pack(fill="both", expand=True, padx=10, pady=4)
        cart_tree = ttk.Treeview(cart_frame, columns=("Product", "Qty", "Price", "Total"), show="headings", height=12)
        for col in ("Product", "Qty", "Price", "Total"):
            cart_tree.heading(col, text=col)
            cart_tree.column(col, width=85)
        cart_tree.pack(side="left", fill="both", expand=True)
        cart_vsb, cart_hsb = add_treeview_scroll(cart_frame, cart_tree)
        cart_vsb.pack(side='right', fill='y')
        cart_hsb.pack(side='bottom', fill='x')
        total_label = tk.Label(right, text="Total: ₹0.00", bg="#0f3460", fg="#2ecc71", font=("Arial", 16, "bold"))
        total_label.pack(pady=6)

        def add_to_cart():
            sel = prod_tree.selection()
            if not sel:
                return
            vals = prod_tree.item(sel[0])["values"]
            name, price = vals[0], float(vals[1])
            for item in self.cart:
                if item["name"] == name:
                    item["qty"] += 1
                    break
            else:
                self.cart.append({"name": name, "qty": 1, "price": price})
            self._refresh_cart(cart_tree, total_label)

        def clear_cart():
            self.cart.clear()
            self._refresh_cart(cart_tree, total_label)

        def checkout():
            if not self.cart:
                messagebox.showwarning("Empty Cart", "Add items to cart first.")
                return
            subtotal = sum(i["qty"] * i["price"] for i in self.cart)
            gst = round(subtotal * 0.18, 2)
            total = round(subtotal + gst, 2)
            order_no = f"POS-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            items_str = "; ".join(f"{i['name']} x{i['qty']}" for i in self.cart)
            conn = sqlite3.connect(self.db_path)
            conn.execute("INSERT INTO pos_orders (order_no, date, items, subtotal, gst, total) VALUES (?,?,?,?,?,?)",
                         (order_no, datetime.date.today().isoformat(), items_str, subtotal, gst, total))
            conn.commit()
            conn.close()
            messagebox.showinfo("Hype ERP — POS",
                f"✅ Order: {order_no}\nItems: {items_str}\nSubtotal: ₹{subtotal:.2f}\nGST (18%): ₹{gst:.2f}\nTotal: ₹{total:.2f}\n\nPowered by Hype ERP")
            self.cart.clear()
            self._refresh_cart(cart_tree, total_label)

        btn_frame = tk.Frame(right, bg="#0f3460")
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="+ Add to Cart", bg="#2ecc71", fg="black",
                  command=add_to_cart, relief="flat", padx=10, pady=5, font=("Arial", 9, "bold")).pack(side="left", padx=4)
        tk.Button(btn_frame, text="🗑 Clear", bg="#e74c3c", fg="white",
                  command=clear_cart, relief="flat", padx=10, pady=5).pack(side="left", padx=4)
        tk.Button(right, text="💳 Checkout & Print", bg="#e94560", fg="white",
                  command=checkout, relief="flat", padx=16, pady=8, font=("Arial", 11, "bold")).pack(pady=6)

    def _load_pos_products(self, tree, search=""):
        for i in tree.get_children():
            tree.delete(i)
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()
            c.execute("SELECT name, selling_price, stock FROM products WHERE name LIKE ? AND stock > 0",
                      (f"%{search}%",))
            for row in c.fetchall():
                tree.insert("", "end", values=row)
        except Exception:
            pass
        conn.close()

    def _refresh_cart(self, tree, label):
        for i in tree.get_children():
            tree.delete(i)
        total = 0
        for item in self.cart:
            line_total = item["qty"] * item["price"]
            total += line_total
            tree.insert("", "end", values=(item["name"], item["qty"], f"{item['price']:.2f}", f"{line_total:.2f}"))
        label.config(text=f"Total: ₹{total:.2f}")
