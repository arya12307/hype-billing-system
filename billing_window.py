# =============================================================================
# HYPE ERP v3.0.0 - Professional Billing / POS Window
# Developer: David | GitHub: david0154
# Full retail billing: barcode scan, cart, GST, discount, print, hold bill
# =============================================================================

import sqlite3
import os
import sys
from tkinter import *
from tkinter import ttk, messagebox
from datetime import date, datetime


def get_icon_path():
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    ico = os.path.join(base, 'icon.ico')
    return ico if os.path.exists(ico) else None


def set_icon(win):
    ico = get_icon_path()
    if ico:
        try:
            win.iconbitmap(ico)
        except Exception:
            pass


CURRENCY = '\u20b9'


class BillingWindow:
    """
    Full professional POS billing window for Hype ERP.
    Features:
      - Barcode / name product search
      - Add / remove / edit qty in cart
      - Per-item GST breakdown (SGST + CGST)
      - Discount (% or flat) on whole bill
      - Payment method selector (Cash / Card / UPI / Credit)
      - Hold bill & retrieve held bills
      - Invoice summary popup
      - Keyboard shortcuts: F2=search, F4=checkout, Del=remove item
    """

    def __init__(self, parent, db_path, current_user='admin',
                 get_setting_fn=None, generate_invoice_fn=None):
        self.parent = parent
        self.DB = db_path
        self.current_user = current_user
        self.get_setting = get_setting_fn or (lambda k, d='': d)
        self.gen_invoice_no = generate_invoice_fn or self._default_invoice_no
        self.cart = []           # list of dicts
        self.held_bills = []     # list of saved carts

        self.win = Toplevel(parent)
        self.win.title('Hype ERP \u2014 Billing')
        self.win.geometry('1200x750')
        self.win.configure(bg='#0d0d1a')
        self.win.state('zoomed') if sys.platform == 'win32' else None
        set_icon(self.win)
        self._build()
        self._bind_keys()
        self._refresh_products()

    def _default_invoice_no(self):
        prefix = self.get_setting('invoice_prefix', 'INV')
        conn = sqlite3.connect(self.DB)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM invoices')
        n = c.fetchone()[0] + 1
        conn.close()
        return f"{prefix}-{datetime.now().strftime('%Y%m')}-{n:04d}"

    # ---------------------------------------------------------------- BUILD UI
    def _build(self):
        # ── Top bar ──────────────────────────────────────────────────────────
        top = Frame(self.win, bg='#16213e', pady=8)
        top.pack(fill='x')
        Label(top, text='\U0001f9fe  Hype ERP \u2014 Billing',
              font=('Segoe UI', 16, 'bold'), bg='#16213e', fg='#e94560').pack(side='left', padx=16)
        Label(top, text=f'Cashier: {self.current_user}',
              font=('Segoe UI', 9), bg='#16213e', fg='#aaaacc').pack(side='right', padx=16)
        Label(top, text=datetime.now().strftime('%d %b %Y  %H:%M'),
              font=('Segoe UI', 9), bg='#16213e', fg='#aaaacc').pack(side='right', padx=8)

        body = Frame(self.win, bg='#0d0d1a')
        body.pack(fill='both', expand=True, padx=10, pady=6)

        # ── LEFT: product search ──────────────────────────────────────────────
        left = Frame(body, bg='#12122a', width=370)
        left.pack(side='left', fill='y', padx=(0, 6))
        left.pack_propagate(False)

        Label(left, text='\U0001f50d  Product / Barcode Search',
              font=('Segoe UI', 10, 'bold'), bg='#12122a', fg='#00d4ff').pack(pady=(10, 4), padx=8, anchor='w')

        search_frame = Frame(left, bg='#12122a')
        search_frame.pack(fill='x', padx=8, pady=(0, 6))
        self.search_var = StringVar()
        search_entry = Entry(search_frame, textvariable=self.search_var,
                             bg='#1e1e3a', fg='white', insertbackground='white',
                             font=('Segoe UI', 11), relief='flat', bd=2)
        search_entry.pack(side='left', fill='x', expand=True, ipady=7)
        self.search_var.trace_add('write', lambda *a: self._refresh_products())
        search_entry.focus_set()
        
        # Add manual entry button
        Button(search_frame, text='➕ Manual', bg='#e94560', fg='white',
               relief='flat', font=('Segoe UI', 9, 'bold'),
               command=self._manual_product_entry, padx=8).pack(side='left', padx=(4, 0), ipady=6)

        # Product treeview
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Billing.Treeview', background='#1a1a2e', foreground='white',
                        fieldbackground='#1a1a2e', rowheight=28, font=('Segoe UI', 9))
        style.configure('Billing.Treeview.Heading', background='#16213e',
                        foreground='#00d4ff', font=('Segoe UI', 9, 'bold'))
        style.map('Billing.Treeview', background=[('selected', '#e94560')])

        cols = ('Name', 'Price', 'Stock', 'GST%')
        self.prod_tree = ttk.Treeview(left, columns=cols, show='headings',
                                       height=20, style='Billing.Treeview')
        for col, w in [('Name', 180), ('Price', 72), ('Stock', 56), ('GST%', 50)]:
            self.prod_tree.heading(col, text=col)
            self.prod_tree.column(col, width=w, anchor='center' if col != 'Name' else 'w')
        sb = ttk.Scrollbar(left, orient='vertical', command=self.prod_tree.yview)
        self.prod_tree.configure(yscroll=sb.set)
        self.prod_tree.pack(side='left', fill='both', expand=True, padx=(8, 0), pady=4)
        sb.pack(side='right', fill='y', pady=4)
        self.prod_tree.bind('<Double-1>', lambda e: self._add_selected())
        self.prod_tree.bind('<Return>', lambda e: self._add_selected())

        # ── CENTER: cart ──────────────────────────────────────────────────────
        center = Frame(body, bg='#0d0d1a')
        center.pack(side='left', fill='both', expand=True)

        # Customer row
        cust_frame = Frame(center, bg='#12122a')
        cust_frame.pack(fill='x', pady=(0, 6))
        for lbl, attr, w in [('Customer Name', 'cust_name', 22),
                              ('Phone', 'cust_phone', 14),
                              ('GSTIN', 'cust_gstin', 18)]:
            Label(cust_frame, text=lbl, bg='#12122a', fg='#aaaacc',
                  font=('Segoe UI', 9)).pack(side='left', padx=(10, 2))
            var = StringVar()
            setattr(self, attr, var)
            Entry(cust_frame, textvariable=var, bg='#1e1e3a', fg='white',
                  insertbackground='white', font=('Segoe UI', 10),
                  relief='flat', width=w).pack(side='left', ipady=5, padx=(0, 6))

        # Cart treeview
        Label(center, text='\U0001f6d2  Cart', font=('Segoe UI', 11, 'bold'),
              bg='#0d0d1a', fg='#e94560').pack(anchor='w', padx=6)

        cart_cols = ('#', 'Product', 'Qty', 'Rate', 'SGST%', 'CGST%', 'GST\u20b9', 'Amount')
        self.cart_tree = ttk.Treeview(center, columns=cart_cols, show='headings',
                                       height=14, style='Billing.Treeview')
        widths = [30, 200, 55, 80, 55, 55, 70, 90]
        for col, w in zip(cart_cols, widths):
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, width=w,
                                   anchor='center' if col not in ('Product',) else 'w')
        csb = ttk.Scrollbar(center, orient='vertical', command=self.cart_tree.yview)
        self.cart_tree.configure(yscroll=csb.set)
        self.cart_tree.pack(side='left' if False else 'top', fill='both',
                             expand=True, padx=6, pady=4)

        # Cart action buttons
        cart_btns = Frame(center, bg='#0d0d1a')
        cart_btns.pack(fill='x', padx=6, pady=2)
        for txt, cmd, col in [
            ('\u2795 Add Item', self._add_selected, '#27ae60'),
            ('\u2212 Remove', self._remove_item, '#e74c3c'),
            ('\u270f Edit Qty', self._edit_qty, '#2980b9'),
            ('\U0001f4cb Hold Bill', self._hold_bill, '#8e44ad'),
            ('\U0001f4c2 Retrieve', self._retrieve_bill, '#16a085'),
            ('\U0001f5d1 Clear All', self._clear_cart, '#555577'),
        ]:
            Button(cart_btns, text=txt, bg=col, fg='white', command=cmd,
                   font=('Segoe UI', 9, 'bold'), relief='flat',
                   padx=8, pady=5, cursor='hand2').pack(side='left', padx=3)

        # ── RIGHT: totals + payment ───────────────────────────────────────────
        right = Frame(body, bg='#12122a', width=250)
        right.pack(side='right', fill='y', padx=(6, 0))
        right.pack_propagate(False)

        Label(right, text='\U0001f4b0  Bill Summary',
              font=('Segoe UI', 12, 'bold'), bg='#12122a', fg='#00d4ff').pack(pady=(12, 8))

        def sumrow(lbl, attr, fg='white'):
            f = Frame(right, bg='#12122a')
            f.pack(fill='x', padx=14, pady=2)
            Label(f, text=lbl, bg='#12122a', fg='#aaaacc',
                  font=('Segoe UI', 9), anchor='w', width=14).pack(side='left')
            lv = Label(f, text=f'{CURRENCY}0.00', bg='#12122a', fg=fg,
                       font=('Segoe UI', 10, 'bold'), anchor='e')
            lv.pack(side='right')
            setattr(self, attr, lv)

        sumrow('Subtotal', 'lbl_sub')
        sumrow('SGST', 'lbl_sgst', '#f39c12')
        sumrow('CGST', 'lbl_cgst', '#f39c12')
        sumrow('Total GST', 'lbl_gst', '#e67e22')

        # Discount row
        disc_f = Frame(right, bg='#12122a')
        disc_f.pack(fill='x', padx=14, pady=4)
        Label(disc_f, text='Discount', bg='#12122a', fg='#aaaacc',
              font=('Segoe UI', 9), width=9).pack(side='left')
        self.disc_var = StringVar(value='0')
        Entry(disc_f, textvariable=self.disc_var, bg='#1e1e3a', fg='white',
              insertbackground='white', font=('Segoe UI', 10),
              relief='flat', width=8).pack(side='left', ipady=4, padx=4)
        self.disc_type = StringVar(value='%')
        ttk.Combobox(disc_f, textvariable=self.disc_type, values=['%', CURRENCY],
                     width=3, state='readonly').pack(side='left')
        self.disc_var.trace_add('write', lambda *a: self._refresh_totals())

        Frame(right, bg='#333355', height=1).pack(fill='x', padx=14, pady=6)
        sumrow('Grand Total', 'lbl_total', '#2ecc71')
        self.lbl_total.config(font=('Segoe UI', 16, 'bold'))

        # Payment method
        Label(right, text='Payment Method', bg='#12122a', fg='#aaaacc',
              font=('Segoe UI', 9)).pack(pady=(10, 2))
        self.pay_method = StringVar(value='Cash')
        pay_frame = Frame(right, bg='#12122a')
        pay_frame.pack(fill='x', padx=14)
        for method in ['Cash', 'Card', 'UPI', 'Credit']:
            Radiobutton(pay_frame, text=method, variable=self.pay_method,
                        value=method, bg='#12122a', fg='white',
                        selectcolor='#e94560', activebackground='#12122a',
                        font=('Segoe UI', 9)).pack(anchor='w')

        # Amount tendered (for cash change calc)
        Label(right, text='Amount Tendered', bg='#12122a', fg='#aaaacc',
              font=('Segoe UI', 9)).pack(pady=(8, 2))
        self.tendered_var = StringVar(value='0')
        Entry(right, textvariable=self.tendered_var, bg='#1e1e3a', fg='white',
              insertbackground='white', font=('Segoe UI', 11),
              relief='flat').pack(fill='x', padx=14, ipady=6)
        self.tendered_var.trace_add('write', lambda *a: self._calc_change())
        self.lbl_change = Label(right, text='Change: \u20b90.00',
                                 bg='#12122a', fg='#2ecc71',
                                 font=('Segoe UI', 10, 'bold'))
        self.lbl_change.pack(pady=4)

        # Checkout button
        Button(right, text='\U0001f4b3  CHECKOUT  (F4)',
               bg='#e94560', fg='white', font=('Segoe UI', 13, 'bold'),
               relief='flat', pady=12, cursor='hand2',
               command=self._checkout).pack(fill='x', padx=14, pady=(10, 4))

        # Status bar
        self.status_var = StringVar(value='Ready — Scan or search a product')
        Label(self.win, textvariable=self.status_var,
              bg='#16213e', fg='#aaaacc', font=('Segoe UI', 8),
              anchor='w').pack(side='bottom', fill='x', ipady=3)

    # ---------------------------------------------------------- KEYBOARD BINDS
    def _bind_keys(self):
        self.win.bind('<F2>', lambda e: self.search_var.set(''))
        self.win.bind('<F4>', lambda e: self._checkout())
        self.win.bind('<Delete>', lambda e: self._remove_item())
        self.win.bind('<F5>', lambda e: self._clear_cart())

    # --------------------------------------------------------- PRODUCT REFRESH
    def _refresh_products(self):
        q = self.search_var.get().strip()
        for i in self.prod_tree.get_children():
            self.prod_tree.delete(i)
        try:
            conn = sqlite3.connect(self.DB)
            c = conn.cursor()
            c.execute("""
                SELECT id, name, selling_price, stock, gst_rate, category, barcode
                FROM products
                WHERE (name LIKE ? OR barcode LIKE ?) AND stock >= 0
                ORDER BY name
            """, (f'%{q}%', f'%{q}%'))
            for row in c.fetchall():
                # Store full data but display only name, price, stock, gst
                tag = 'low' if row[3] < 5 else ''
                # Display: name, price, stock, gst (hide id, category, barcode in tree)
                self.prod_tree.insert('', 'end', values=(row[1], row[2], row[3], row[4]), tags=(tag,), iid=str(row[0]))
            self.prod_tree.tag_configure('low', foreground='#ffaa00')
            conn.close()
        except Exception as e:
            self._status(f'DB error: {e}')

    def _status(self, msg):
        self.status_var.set(msg)
    
    def _manual_product_entry(self):
        """Manually add a product not in database"""
        d = Toplevel(self.win)
        d.title('Manual Product Entry')
        d.geometry('400x350')
        d.configure(bg='#0d0d1a')
        
        Label(d, text='Add Product Manually', bg='#16213e', fg='#e94560',
              font=('Segoe UI', 12, 'bold')).pack(fill='x', ipady=8)
        
        fields = {}
        for lbl, key, default in [
            ('Product Name *', 'name', ''),
            ('Selling Price *', 'price', '0.00'),
            ('Quantity', 'qty', '1'),
            ('GST Rate (%)', 'gst', '18'),
            ('Category', 'category', ''),
        ]:
            Frame(d, bg='#0d0d1a', height=1).pack(pady=2)
            Label(d, text=lbl, bg='#0d0d1a', fg='#aaaacc',
                  font=('Segoe UI', 9)).pack(anchor='w', padx=16)
            var = StringVar(value=default)
            Entry(d, textvariable=var, bg='#1e1e3a', fg='white',
                  font=('Segoe UI', 10), relief='flat', bd=2).pack(fill='x', padx=16, ipady=5)
            fields[key] = var
        
        def save():
            name = fields['name'].get().strip()
            try:
                price = float(fields['price'].get())
                qty = int(fields['qty'].get())
                gst = float(fields['gst'].get())
            except ValueError:
                messagebox.showerror('Input Error', 'Enter valid numbers', parent=d)
                return
            
            if not name or price <= 0 or qty <= 0:
                messagebox.showwarning('Input Error', 'Name and price required', parent=d)
                return
            
            category = fields['category'].get().strip() or 'Manual Entry'
            
            # Add to cart
            for item in self.cart:
                if item['name'].lower() == name.lower():
                    item['qty'] += qty
                    self._refresh_cart()
                    d.destroy()
                    self._status(f'Updated: {name}')
                    return
            
            self.cart.append({
                'name': name, 'price': price, 'qty': qty, 'gst': gst,
                'stock': qty, 'category': category, 'sku': 'MANUAL', 'product_id': 0
            })
            self._refresh_cart()
            d.destroy()
            self._status(f'Added manually: {name}')
        
        Frame(d, bg='#0d0d1a', height=8).pack()
        Button(d, text='Add to Cart', bg='#00d4ff', fg='#0d0d1a',
               relief='flat', font=('Segoe UI', 10, 'bold'),
               command=save, padx=16).pack(ipady=7)
        Button(d, text='Cancel', bg='#44444d', fg='white',
               relief='flat', font=('Segoe UI', 9),
               command=d.destroy, padx=16).pack(ipady=6, pady=(4, 10))

    # ----------------------------------------------------------------- CART OPS
    def _add_selected(self):
        sel = self.prod_tree.selection()
        if not sel:
            self._status('Select a product first')
            return
        vals = self.prod_tree.item(sel[0])['values']
        product_id = int(sel[0])
        name, price, stock, gst = str(vals[0]), float(vals[1]), int(vals[2]), float(vals[3])
        if stock <= 0:
            messagebox.showwarning('Out of Stock', f'{name} is out of stock.', parent=self.win)
            return
        # Fetch additional product info
        try:
            conn = sqlite3.connect(self.DB)
            c = conn.cursor()
            c.execute('SELECT category, barcode FROM products WHERE id = ?', (product_id,))
            row = c.fetchone()
            category = row[0] if row else ''
            sku = row[1] if row else ''
            conn.close()
        except Exception:
            category, sku = '', ''
        
        for item in self.cart:
            if item['name'] == name:
                if item['qty'] >= stock:
                    messagebox.showwarning('Stock Limit',
                                           f'Only {stock} units available.', parent=self.win)
                    return
                item['qty'] += 1
                self._refresh_cart()
                self._status(f'Updated qty: {name} x{item["qty"]}')
                return
        self.cart.append({'name': name, 'price': price, 'qty': 1, 'gst': gst, 'stock': stock, 'category': category, 'sku': sku, 'product_id': product_id})
        self._refresh_cart()
        self._status(f'Added: {name}')

    def _remove_item(self):
        sel = self.cart_tree.selection()
        if not sel:
            self._status('Select cart item to remove')
            return
        idx = self.cart_tree.index(sel[0])
        if 0 <= idx < len(self.cart):
            removed = self.cart.pop(idx)
            self._refresh_cart()
            self._status(f'Removed: {removed["name"]}')

    def _edit_qty(self):
        sel = self.cart_tree.selection()
        if not sel:
            self._status('Select item to edit quantity')
            return
        idx = self.cart_tree.index(sel[0])
        if not (0 <= idx < len(self.cart)):
            return
        item = self.cart[idx]
        d = Toplevel(self.win)
        d.title('Edit Quantity')
        d.geometry('260x140')
        d.configure(bg='#1a1a2e')
        d.resizable(False, False)
        set_icon(d)
        Label(d, text=f'Qty for: {item["name"]}', bg='#1a1a2e',
              fg='white', font=('Segoe UI', 10, 'bold')).pack(pady=(14, 6))
        qty_var = StringVar(value=str(item['qty']))
        Entry(d, textvariable=qty_var, bg='#16213e', fg='white',
              insertbackground='white', font=('Segoe UI', 12),
              justify='center').pack(ipady=6, padx=30, fill='x')

        def apply():
            try:
                q = int(qty_var.get())
                if q <= 0:
                    self.cart.pop(idx)
                elif q > item['stock']:
                    messagebox.showwarning('Stock', f'Max stock: {item["stock"]}', parent=d)
                    return
                else:
                    self.cart[idx]['qty'] = q
                self._refresh_cart()
                d.destroy()
            except ValueError:
                pass

        Button(d, text='\u2714 Apply', bg='#e94560', fg='white',
               command=apply, relief='flat', pady=6).pack(pady=8)
        d.bind('<Return>', lambda e: apply())
        qty_var.get() and None  # ensure focus

    def _clear_cart(self):
        if self.cart and not messagebox.askyesno('Clear Cart', 'Clear all items?', parent=self.win):
            return
        self.cart.clear()
        self._refresh_cart()
        self._status('Cart cleared')

    def _hold_bill(self):
        if not self.cart:
            self._status('Nothing to hold')
            return
        self.held_bills.append({
            'cart': [dict(i) for i in self.cart],
            'customer': self.cust_name.get(),
            'phone': self.cust_phone.get(),
            'time': datetime.now().strftime('%H:%M:%S')
        })
        self.cart.clear()
        self._refresh_cart()
        self._status(f'Bill held. Total held: {len(self.held_bills)}')

    def _retrieve_bill(self):
        if not self.held_bills:
            messagebox.showinfo('Hold', 'No held bills.', parent=self.win)
            return
        d = Toplevel(self.win)
        d.title('Retrieve Held Bill')
        d.geometry('380x260')
        d.configure(bg='#1a1a2e')
        set_icon(d)
        Label(d, text='Held Bills', bg='#1a1a2e', fg='#e94560',
              font=('Segoe UI', 12, 'bold')).pack(pady=10)
        lb = Listbox(d, bg='#16213e', fg='white', font=('Segoe UI', 10),
                     selectbackground='#e94560')
        lb.pack(fill='both', expand=True, padx=10)
        for i, b in enumerate(self.held_bills):
            items_count = len(b['cart'])
            lb.insert('end', f"#{i+1}  {b['time']}  {b['customer'] or 'Walk-in'}  ({items_count} items)")

        def load():
            sel = lb.curselection()
            if not sel:
                return
            idx = sel[0]
            bill = self.held_bills.pop(idx)
            self.cart = bill['cart']
            self.cust_name.set(bill['customer'])
            self.cust_phone.set(bill['phone'])
            self._refresh_cart()
            d.destroy()
            self._status('Bill retrieved')

        Button(d, text='\u2714 Load Bill', bg='#27ae60', fg='white',
               command=load, relief='flat', pady=6).pack(pady=8)

    # -------------------------------------------------------------- CART RENDER
    def _refresh_cart(self):
        for i in self.cart_tree.get_children():
            self.cart_tree.delete(i)
        for idx, item in enumerate(self.cart, 1):
            sgst = item['gst'] / 2
            cgst = item['gst'] / 2
            gst_amt = round(item['price'] * item['qty'] * item['gst'] / 100, 2)
            amount = round(item['price'] * item['qty'] + gst_amt, 2)
            self.cart_tree.insert('', 'end', values=(
                idx,
                item['name'],
                item['qty'],
                f"{item['price']:.2f}",
                f"{sgst:.1f}",
                f"{cgst:.1f}",
                f"{gst_amt:.2f}",
                f"{amount:.2f}"
            ))
        self._refresh_totals()

    def _refresh_totals(self):
        subtotal = sum(i['price'] * i['qty'] for i in self.cart)
        total_gst = sum(round(i['price'] * i['qty'] * i['gst'] / 100, 2) for i in self.cart)
        sgst = total_gst / 2
        cgst = total_gst / 2

        # Discount
        try:
            disc_val = float(self.disc_var.get() or 0)
        except ValueError:
            disc_val = 0
        if self.disc_type.get() == '%':
            disc_amt = round((subtotal + total_gst) * disc_val / 100, 2)
        else:
            disc_amt = disc_val

        grand = round(subtotal + total_gst - disc_amt, 2)

        self.lbl_sub.config(text=f'{CURRENCY}{subtotal:.2f}')
        self.lbl_sgst.config(text=f'{CURRENCY}{sgst:.2f}')
        self.lbl_cgst.config(text=f'{CURRENCY}{cgst:.2f}')
        self.lbl_gst.config(text=f'{CURRENCY}{total_gst:.2f}')
        self.lbl_total.config(text=f'{CURRENCY}{grand:.2f}')
        self._calc_change(grand)
        return subtotal, total_gst, disc_amt, grand

    def _calc_change(self, grand=None):
        try:
            tendered = float(self.tendered_var.get() or 0)
            if grand is None:
                _, _, _, grand = self._refresh_totals()
            change = round(tendered - grand, 2)
            col = '#2ecc71' if change >= 0 else '#e74c3c'
            self.lbl_change.config(
                text=f'Change: {CURRENCY}{change:.2f}' if change >= 0 else f'Due: {CURRENCY}{abs(change):.2f}',
                fg=col
            )
        except Exception:
            pass

    # ---------------------------------------------------------------- CHECKOUT
    def _checkout(self):
        if not self.cart:
            messagebox.showwarning('Empty Cart', 'Add products before checkout.', parent=self.win)
            return

        subtotal, total_gst, disc_amt, grand = self._refresh_totals()
        inv_no = self.gen_invoice_no()
        today = date.today().isoformat()
        pay = self.pay_method.get()

        try:
            conn = sqlite3.connect(self.DB)
            c = conn.cursor()
            
            # ✅ Save/Update customer in customers table
            cust_name = self.cust_name.get().strip()
            cust_phone = self.cust_phone.get().strip()
            cust_gstin = self.cust_gstin.get().strip()
            
            if cust_name:  # Only save if customer name exists
                c.execute("""
                    SELECT id, total_purchases, visit_count FROM customers 
                    WHERE phone = ? AND name = ?
                """, (cust_phone, cust_name))
                existing = c.fetchone()
                
                if existing:
                    # Update existing customer
                    cust_id, prev_purchases, prev_visits = existing
                    c.execute("""
                        UPDATE customers 
                        SET total_purchases = ?, visit_count = ? 
                        WHERE id = ?
                    """, (prev_purchases + grand, prev_visits + 1, cust_id))
                else:
                    # Create new customer
                    c.execute("""
                        INSERT INTO customers 
                        (name, phone, email, gstin, total_purchases, visit_count)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (cust_name, cust_phone, '', cust_gstin, grand, 1))
            
            c.execute("""
                INSERT INTO invoices
                (invoice_number, date, customer_name, customer_phone, customer_gstin,
                 subtotal, gst_amount, discount, total_amount, payment_method, created_by)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (inv_no, today, cust_name, cust_phone,
                   cust_gstin, subtotal, total_gst, disc_amt, grand,
                   pay, self.current_user))
            inv_id = c.lastrowid
            conn.commit()
            for item in self.cart:
                gst_amt = round(item['price'] * item['qty'] * item['gst'] / 100, 2)
                total = round(item['price'] * item['qty'] + gst_amt, 2)
                c.execute("""
                    INSERT INTO invoice_items
                    (invoice_id, product_name, quantity, unit_price, gst_rate, gst_amount, total)
                    VALUES (?,?,?,?,?,?,?)
                """, (inv_id, item['name'], item['qty'], item['price'],
                       item['gst'], gst_amt, total))
                c.execute("UPDATE products SET stock=stock-?, last_sold=? WHERE name=?",
                          (item['qty'], today, item['name']))
            conn.commit()
            conn.close()
            
            # Immediate sync to Firebase: invoices, invoice_items, products (stock updates)
            try:
                from firebase_sync import get_firebase_sync_manager, trigger_immediate_sync, sync_all_data_immediately, queue_operation_if_offline, process_offline_queue
                import logging as logging_module
                logger_sync = logging_module.getLogger(__name__)
                
                fsm = get_firebase_sync_manager()
                try:
                    store_id = int(self.get_setting('store_id', '1'))
                except Exception:
                    try: store_id = int(get_setting('store_id', '1'))
                    except Exception: store_id = 1
                
                if fsm and getattr(fsm, 'db', None):
                    try:
                        # Try to sync immediately
                        logger_sync.info(f'📤 Syncing new bill {inv_no} to Firebase (store_id={store_id})')
                        fsm.sync_table_to_firestore('invoices', f'stores/{store_id}/invoices')
                        fsm.sync_table_to_firestore('invoice_items', f'stores/{store_id}/invoice_items')
                        fsm.sync_table_to_firestore('products', f'stores/{store_id}/products')
                        logger_sync.info(f'✅ Bill {inv_no} synced to Firebase successfully')
                        
                        # Process any queued operations from when internet was offline
                        try:
                            processed = process_offline_queue()
                            if processed > 0:
                                logger_sync.info(f'📤 Processed {processed} queued operations')
                        except Exception as e:
                            logger_sync.warning(f'Could not process offline queue: {e}')
                        
                        # Trigger immediate sync in background thread
                        trigger_immediate_sync(store_id)
                    except Exception as e:
                        logger_sync.error(f'❌ Error syncing bill {inv_no} to Firebase: {str(e)}')
                        # Queue this operation for later
                        try:
                            queue_operation_if_offline('create_invoice', {
                                'invoice_no': inv_no,
                                'total_amount': grand,
                                'date': str(today)
                            }, store_id)
                        except Exception as qe:
                            logger_sync.warning(f'Could not queue operation: {qe}')
                else:
                    logger_sync.warning(f'Firebase sync manager not available for bill {inv_no}')
                    # Queue operation for when Firebase comes online
                    try:
                        queue_operation_if_offline('create_invoice', {
                            'invoice_no': inv_no,
                            'total_amount': grand,
                            'date': str(today)
                        }, store_id)
                    except Exception as e:
                        logger_sync.warning(f'Could not queue operation: {e}')
            except Exception as e:
                import logging as logging_module
                logging_module.getLogger(__name__).warning(f'Firebase import error: {str(e)}')
        except Exception as e:
            messagebox.showerror('DB Error', str(e), parent=self.win)
            return

        # ── Invoice summary popup ────────────────────────────────────────────
        self._show_invoice_popup(inv_no, today, subtotal, total_gst, disc_amt, grand, pay)

        # Reset
        self.cart.clear()
        self._refresh_cart()
        self.cust_name.set('')
        self.cust_phone.set('')
        self.cust_gstin.set('')
        self.disc_var.set('0')
        self.tendered_var.set('0')
        self._refresh_products()
        self._status(f'Invoice {inv_no} saved — {CURRENCY}{grand:.2f} via {pay}')

    def _show_invoice_popup(self, inv_no, today, subtotal, gst, disc, grand, pay):
        d = Toplevel(self.win)
        d.title(f'Invoice {inv_no}')
        d.geometry('420x500')
        d.configure(bg='#0d0d1a')
        d.resizable(False, False)
        set_icon(d)

        shop = self.get_setting('shop_name', 'Hype Retail Store')
        addr = self.get_setting('shop_address', '')
        gstin = self.get_setting('shop_gstin', '')
        phone = self.get_setting('shop_phone', '')

        txt = Text(d, bg='#0d0d1a', fg='white', font=('Consolas', 9),
                   relief='flat', padx=12, pady=8)
        txt.pack(fill='both', expand=True, padx=8, pady=8)

        def line(s='', bold=False):
            txt.insert('end', s + '\n')

        line('=' * 50)
        line(f'  {shop}'.center(50))
        if addr: line(f'  {addr}')
        if phone: line(f'  Ph: {phone}')
        if gstin: line(f'  GSTIN: {gstin}')
        line('=' * 50)
        line(f'  Invoice : {inv_no}')
        line(f'  Date    : {today}')
        line(f'  Customer: {self.cust_name.get() or "Walk-in"}')
        if self.cust_phone.get(): line(f'  Phone   : {self.cust_phone.get()}')
        line('-' * 50)
        line(f'  {"Product":<22} {"Qty":>4} {"Rate":>8} {"Amt":>9}')
        line(f'  {"[Category | SKU]":<22} {"":>4} {"GST%":>8} {"":>9}')
        line('-' * 50)
        for item in self.cart if self.cart else []:
            amt = item['price'] * item['qty']
            line(f'  {item["name"][:22]:<22} {item["qty"]:>4} {item["price"]:>8.2f} {amt:>9.2f}')
            cat = item.get('category', '').replace('|', '-')[:10]
            sku = item.get('sku', '')[:10]
            gst_rate = item.get('gst', 0)
            line(f'  {f"[{cat} | {sku}]":<22} {"":>4} {gst_rate:>8.1f} {"":>9}')
        line('-' * 50)
        line(f'  {"Subtotal":<30} {CURRENCY}{subtotal:>10.2f}')
        line(f'  {"GST (SGST+CGST)":<30} {CURRENCY}{gst:>10.2f}')
        if disc > 0:
            line(f'  {"Discount":<30} -{CURRENCY}{disc:>9.2f}')
        line('=' * 50)
        line(f'  {"GRAND TOTAL":<30} {CURRENCY}{grand:>10.2f}')
        line('=' * 50)
        line(f'  Payment : {pay}')
        line()
        line('  Thank you for shopping!')
        line('  Powered by Hype ERP')
        line('=' * 50)
        txt.config(state='disabled')

        bf = Frame(d, bg='#0d0d1a')
        bf.pack(pady=8)
        Button(bf, text='\U0001f5a8 Print', bg='#2980b9', fg='white',
               command=lambda: self._print_invoice(txt.get('1.0', 'end')),
               relief='flat', padx=14, pady=6).pack(side='left', padx=6)
        Button(bf, text='\u2714 Close', bg='#27ae60', fg='white',
               command=d.destroy, relief='flat', padx=14, pady=6).pack(side='left', padx=6)

    def _print_invoice(self, text_content):
        try:
            import tempfile, subprocess
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8')
            tmp.write(text_content)
            tmp.close()
            if sys.platform == 'win32':
                os.startfile(tmp.name, 'print')
            else:
                subprocess.call(['lpr', tmp.name])
        except Exception as e:
            messagebox.showwarning('Print', f'Print error: {e}', parent=self.win)
