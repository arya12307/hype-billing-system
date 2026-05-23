# Hype ERP - Purchase Order Module (purchase)
# Developer: David | Nexuzy Lab
# ✅ CONNECTED TO DATA SERVICE - All vendor data now shared
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date
from modules.window_utils import set_icon
from modules.data_service import get_data_service

BG='#1a1a2e';BG2='#16213e';ACC='#e94560';FG='white'
FOOTER='Powered by Hype ERP v3.0.0 | Nexuzy Lab | Developer: David'

def _init(db_path):
    import time
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn=sqlite3.connect(db_path)
            conn.execute("PRAGMA journal_mode=WAL")
            c = conn.cursor()
            
            # Create tables
            c.executescript("""
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    po_number TEXT UNIQUE,
                    date TEXT,
                    vendor_id INTEGER,
                    status TEXT DEFAULT 'Pending',
                    subtotal REAL DEFAULT 0,
                    tax REAL DEFAULT 0,
                    total REAL DEFAULT 0,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS purchase_order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    po_id INTEGER,
                    product_name TEXT,
                    qty INTEGER DEFAULT 1,
                    unit_price REAL DEFAULT 0,
                    gst_rate REAL DEFAULT 0,
                    total REAL DEFAULT 0
                );
            """)
            
            # Schema migration - add vendor_id and bill_number columns if they don't exist
            c.execute("PRAGMA table_info(purchase_orders)")
            columns = [col[1] for col in c.fetchall()]
            if 'vendor_id' not in columns:
                try:
                    c.execute("ALTER TABLE purchase_orders ADD COLUMN vendor_id INTEGER")
                except sqlite3.OperationalError:
                    pass  # Column might already exist
            if 'bill_number' not in columns:
                try:
                    c.execute("ALTER TABLE purchase_orders ADD COLUMN bill_number TEXT")
                except sqlite3.OperationalError:
                    pass  # Column might already exist
            
            conn.commit()
            conn.close()
            return
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(0.5)
                else:
                    print(f"Database lock timeout after {max_retries} retries: {e}")
                    raise
            else:
                raise
        except Exception as e:
            print(f"Error in database init: {e}")
            return

class PurchaseModule:
    MODULE_NAME = "Purchase Orders"
    MODULE_CODE = "purchase"
    
    def __init__(self,parent,db_path):
        self.parent=parent
        self.db_path=db_path
        self.data_service=get_data_service(db_path)
        self.data_service.register_module(self.MODULE_NAME, self.MODULE_CODE)
        _init(db_path)

    def open(self):
        win=tk.Toplevel(self.parent);win.title('Hype ERP — Purchase Orders')
        win.geometry('1200x720');win.configure(bg=BG);set_icon(win)
        
        # Professional Header
        hdr = tk.Frame(win, bg=BG2)
        hdr.pack(fill='x')
        tk.Label(hdr, text='🛍 Hype ERP — Purchase Orders & Vendor Bills',
                 font=('Arial',16,'bold'), bg=BG2, fg=ACC).pack(side='left', padx=16, pady=12)
        tk.Label(hdr, text='Manage purchase orders, vendor bills, and procurement',
                 font=('Arial', 9), bg=BG2, fg='#7a7a9a').pack(side='right', padx=16, pady=12)
        
        # Create tabs
        nb=ttk.Notebook(win);nb.pack(fill='both',expand=True,padx=8,pady=8)
        
        # ─── TAB 1: PURCHASE ORDERS ───
        po_frame=tk.Frame(nb,bg=BG);nb.add(po_frame,text='📦 Purchase Orders')

        cols=('ID','PO Number','Bill #','Date','Vendor','Phone','Status','Subtotal','Tax','Total')
        tree=ttk.Treeview(po_frame,columns=cols,show='headings',height=16)
        for c in cols: tree.heading(c,text=c);tree.column(c,width=95)
        sb=ttk.Scrollbar(po_frame,orient='vertical',command=tree.yview)
        tree.configure(yscroll=sb.set)
        tree.pack(side='left',fill='both',expand=True,padx=(12,0),pady=8)
        sb.pack(side='right',fill='y',pady=8)

        def load():
            for i in tree.get_children(): tree.delete(i)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try:
                c.execute('''SELECT po.id, po.po_number, po.bill_number, po.date, v.name as vendor_name, v.phone, po.status, po.subtotal, po.tax, po.total 
                            FROM purchase_orders po
                            LEFT JOIN vendors v ON po.vendor_id = v.id
                            ORDER BY po.id DESC''')
                for row in c.fetchall():
                    display_bill = row[2] if row[2] else '-'
                    display_row = (row[0], row[1], display_bill, row[3], row[4] or 'Unknown', row[5] or '', row[6], f'{row[7]:.2f}', f'{row[8]:.2f}', f'{row[9]:.2f}')
                    tree.insert('','end',values=display_row,tags=('recv',) if row[6]=='Received' else ())
            except sqlite3.OperationalError as e:
                if 'no such column: po.vendor_id' in str(e) or 'no such column: po.bill_number' in str(e):
                    # Try without bill_number and vendor_id columns
                    try:
                        c.execute('''SELECT id, po_number, '', date, 'Unknown', '', status, subtotal, tax, total
                                    FROM purchase_orders ORDER BY id DESC''')
                        for row in c.fetchall():
                            tree.insert('','end',values=row,tags=('recv',) if row[6]=='Received' else ())
                    except Exception as e2:
                        print(f"Error loading POs (fallback): {e2}")
                else:
                    print(f"Error loading POs: {e}")
            except Exception as e:
                print(f"Error loading POs: {e}")
            conn.close()
            tree.tag_configure('recv',foreground='#2ecc71')

        def new_po():
            d=tk.Toplevel(win);d.title('New Purchase Order');d.geometry('520x680');d.configure(bg=BG);set_icon(d)
            tk.Label(d,text='+ New Purchase Order',bg=BG2,fg=ACC,font=('Arial',12,'bold')).pack(fill='x',ipady=8)
            
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try: c.execute('SELECT COUNT(*) FROM purchase_orders');cnt=c.fetchone()[0]+1
            except: cnt=1
            conn.close()
            
            # ✅ Load Vendor List from DataService
            vendors = self.data_service.get_vendors()
            vendor_list = [v['name'] for v in vendors]
            vendor_map = {v['name']: v['id'] for v in vendors}
            
            # ─── PO Header ────────────────────────────────────────
            po_num_var=tk.StringVar(value=f'PO-{date.today().strftime("%Y%m")}-{cnt:04d}')
            bill_num_var=tk.StringVar()  # Bill/Invoice number entry
            po_date_var=tk.StringVar(value=str(date.today()))
            vendor_var=tk.StringVar()
            subtotal_var=tk.StringVar(value='0')
            tax_var=tk.StringVar(value='0')
            total_var=tk.StringVar(value='0')
            notes_var=tk.StringVar()
            
            frame=tk.Frame(d,bg=BG)
            canvas=tk.Canvas(frame,bg=BG,highlightthickness=0)
            scrollbar=tk.Scrollbar(frame,orient='vertical',command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side='right',fill='y')
            canvas.pack(side='left',fill='both',expand=True)
            
            inner=tk.Frame(canvas,bg=BG)
            canvas.create_window((0,0),window=inner,anchor='nw')
            
            # PO Number (read-only)
            tk.Label(inner,text='PO Number',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
            tk.Entry(inner,textvariable=po_num_var,bg=BG2,fg=FG,insertbackground=FG,state='readonly').pack(fill='x',padx=16)
            
            # Bill/Invoice Number (optional)
            tk.Label(inner,text='Bill/Invoice Number (Optional)',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
            tk.Entry(inner,textvariable=bill_num_var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            
            # Date
            tk.Label(inner,text='Date',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
            tk.Entry(inner,textvariable=po_date_var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            
            # ✅ Vendor Selection (Dropdown) - Auto-fetches all details
            tk.Label(inner,text='🏢 Select Vendor *',bg=BG,fg=ACC,font=('Arial',9,'bold')).pack(anchor='w',padx=16,pady=(6,0))
            vendor_combo=ttk.Combobox(inner,textvariable=vendor_var,values=vendor_list,state='readonly',width=40)
            vendor_combo.pack(fill='x',padx=16,ipady=5)
            
            # Status
            tk.Label(inner,text='Status',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
            status_var=tk.StringVar(value='Pending')
            ttk.Combobox(inner,textvariable=status_var,values=['Pending','Received'],state='readonly',width=40).pack(fill='x',padx=16,ipady=5)
            
            # Subtotal (editable)
            tk.Label(inner,text='Subtotal ₹ *',bg=BG,fg=ACC,font=('Arial',9,'bold')).pack(anchor='w',padx=16,pady=(3,0))
            subtotal_entry=tk.Entry(inner,textvariable=subtotal_var,bg=BG2,fg=FG,insertbackground=FG)
            subtotal_entry.pack(fill='x',padx=16)
            
            # Tax % (auto-calculated at 18%)
            tk.Label(inner,text='Tax % (Auto 18%)',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
            tax_rate_var=tk.StringVar(value='18')
            ttk.Combobox(inner,textvariable=tax_rate_var,values=['0','5','12','18','28'],state='readonly',width=40).pack(fill='x',padx=16,ipady=5)
            
            # Tax Amount (read-only - calculated)
            tk.Label(inner,text='Tax Amount ₹ (Auto)',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
            tax_amount_display=tk.Entry(inner,textvariable=tax_var,bg=BG2,fg='#888888',insertbackground=FG,state='readonly')
            tax_amount_display.pack(fill='x',padx=16)
            
            # Total (read-only - calculated)
            tk.Label(inner,text='Total ₹ (Auto)',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
            total_display=tk.Entry(inner,textvariable=total_var,bg=BG2,fg='#888888',insertbackground=FG,state='readonly')
            total_display.pack(fill='x',padx=16)
            
            # Notes
            tk.Label(inner,text='Notes',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
            tk.Entry(inner,textvariable=notes_var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            
            # ✅ Automatic calculation function
            def calculate_totals(e=None):
                try:
                    subtotal = float(subtotal_var.get() or 0)
                    tax_rate = float(tax_rate_var.get() or 18)
                    tax_amount = round(subtotal * tax_rate / 100, 2)
                    total = round(subtotal + tax_amount, 2)
                    tax_var.set(str(tax_amount))
                    total_var.set(str(total))
                except:
                    pass
            
            subtotal_entry.bind('<KeyRelease>', calculate_totals)
            tax_rate_var.trace('w', lambda *args: calculate_totals())
            calculate_totals()  # Initial calculation
            
            def _on_frame_configure(e):
                canvas.configure(scrollregion=canvas.bbox('all'))
            inner.bind('<Configure>',_on_frame_configure)
            
            frame.pack(fill='both',expand=True,padx=0,pady=6)
            
            # ─── Items Section ────────────────────────────────────────
            tk.Label(d,text='📦 Line Items (Optional)',bg=BG2,fg=ACC,font=('Arial',10,'bold')).pack(fill='x',ipady=6,padx=12,pady=(6,2))
            
            items_list=[]
            
            items_frame=tk.Frame(d,bg=BG);items_frame.pack(fill='x',padx=12,pady=4)
            item_cols=('Product','Qty','Unit Price','GST %')
            items_tree=ttk.Treeview(items_frame,columns=item_cols,show='headings',height=4)
            for col in item_cols: items_tree.heading(col,text=col);items_tree.column(col,width=100)
            items_tree.pack(side='left',fill='both',expand=True)
            
            sb=ttk.Scrollbar(items_frame,orient='vertical',command=items_tree.yview)
            items_tree.configure(yscroll=sb.set)
            sb.pack(side='right',fill='y')
            
            def add_item():
                di=tk.Toplevel(d);di.title('Add Item');di.geometry('400x320');di.configure(bg=BG);set_icon(di)
                tk.Label(di,text='➕ Add Line Item',bg=BG2,fg=ACC,font=('Arial',11,'bold')).pack(fill='x',ipady=6)
                
                # ✅ Load Products from DataService
                products = self.data_service.get_products()
                product_list = [p['name'] for p in products]
                product_map = {p['name']: p for p in products}
                
                prod_var=tk.StringVar()
                qty_var=tk.StringVar(value='1')
                price_var=tk.StringVar(value='0')
                gst_var=tk.StringVar(value='18')
                
                # Product Selection (dropdown with manual entry option)
                tk.Label(di,text='📦 Product *',bg=BG,fg=ACC,font=('Arial',9,'bold')).pack(anchor='w',padx=16,pady=(3,0))
                prod_combo=ttk.Combobox(di,textvariable=prod_var,values=product_list,state='normal',width=35)
                prod_combo.pack(fill='x',padx=16,ipady=5)
                
                # Auto-fill price when product selected
                def on_product_select(e=None):
                    sel_prod = prod_var.get().strip()
                    if sel_prod in product_map:
                        price_var.set(str(product_map[sel_prod].get('selling_price', 0)))
                        gst_var.set(str(product_map[sel_prod].get('gst_rate', 18)))
                
                prod_combo.bind('<<ComboboxSelected>>', on_product_select)
                
                # Quick button to create new product
                def create_new_product():
                    cp=tk.Toplevel(di);cp.title('New Product');cp.geometry('380x280');cp.configure(bg=BG);set_icon(cp)
                    tk.Label(cp,text='➕ Create New Product',bg=BG2,fg=ACC,font=('Arial',10,'bold')).pack(fill='x',ipady=6)
                    
                    pname=tk.StringVar()
                    psku=tk.StringVar()
                    pprice=tk.StringVar(value='0')
                    pgst=tk.StringVar(value='18')
                    
                    tk.Label(cp,text='Product Name *',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
                    tk.Entry(cp,textvariable=pname,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
                    
                    tk.Label(cp,text='SKU',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
                    tk.Entry(cp,textvariable=psku,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
                    
                    tk.Label(cp,text='Selling Price ₹ *',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
                    tk.Entry(cp,textvariable=pprice,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
                    
                    tk.Label(cp,text='GST %',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
                    ttk.Combobox(cp,textvariable=pgst,values=['0','5','12','18','28'],state='readonly',width=32).pack(fill='x',padx=16,ipady=5)
                    
                    def save_product():
                        try:
                            pn=pname.get().strip()
                            if not pn:
                                messagebox.showwarning('Error','Product name required',parent=cp)
                                return
                            sk=psku.get().strip() or pn
                            pr=float(pprice.get())
                            if pr<=0:
                                messagebox.showwarning('Error','Price must be > 0',parent=cp)
                                return
                            
                            # Add to database
                            self.data_service.add_product({
                                'sku': sk, 'name': pn, 'selling_price': pr,
                                'gst_rate': float(pgst.get()), 'quantity': 0
                            })
                            
                            # Add to combo
                            product_list.append(pn)
                            product_map[pn] = {'name': pn, 'selling_price': pr, 'gst_rate': float(pgst.get())}
                            prod_combo['values'] = product_list
                            prod_var.set(pn)
                            on_product_select()
                            
                            cp.destroy()
                            messagebox.showinfo('✓','Product created!',parent=di)
                        except Exception as e:
                            messagebox.showerror('Error',str(e),parent=cp)
                    
                    tk.Button(cp,text='✅ Create',bg='#27ae60',fg=FG,relief='flat',command=save_product,padx=14,pady=6,font=('Arial',9,'bold')).pack(pady=10)
                
                tk.Button(di,text='➕ New Product',bg='#3498db',fg=FG,relief='flat',command=create_new_product,padx=8,pady=3,font=('Arial',8)).pack(anchor='w',padx=16,pady=(2,0))
                
                # Quantity
                tk.Label(di,text='Quantity *',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
                tk.Entry(di,textvariable=qty_var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
                
                # Unit Price
                tk.Label(di,text='Unit Price ₹ *',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
                tk.Entry(di,textvariable=price_var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
                
                # GST %
                tk.Label(di,text='GST %',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
                ttk.Combobox(di,textvariable=gst_var,values=['0','5','12','18','28'],state='readonly',width=35).pack(fill='x',padx=16,ipady=5)
                
                def save_item():
                    try:
                        p=prod_var.get().strip()
                        if not p: 
                            messagebox.showwarning('Error','Please select a product',parent=di)
                            return
                        q=int(qty_var.get())
                        pr=float(price_var.get())
                        g=float(gst_var.get())
                        if q<=0 or pr<=0: 
                            messagebox.showwarning('Error','Quantity and Price must be > 0',parent=di)
                            return
                        
                        items_list.append({'prod':p,'qty':q,'price':pr,'gst':g})
                        item_total = round(q * pr * (1 + g/100), 2)
                        items_tree.insert('','end',values=(p,q,f'₹{pr:.2f}',f'{g:.1f}%'))
                        
                        # ✅ Update subtotal automatically
                        current_subtotal = float(subtotal_var.get() or 0)
                        new_subtotal = round(current_subtotal + (q * pr), 2)
                        subtotal_var.set(str(new_subtotal))
                        calculate_totals()
                        
                        di.destroy()
                    except Exception as e: messagebox.showerror('Error',str(e),parent=di)
                
                tk.Button(di,text='✅ Add Item',bg='#27ae60',fg=FG,relief='flat',command=save_item,padx=14,pady=6,font=('Arial',10,'bold')).pack(pady=10)
            
            def remove_item():
                sel=items_tree.selection()
                if not sel: return
                idx=items_tree.index(sel[0])
                items_tree.delete(sel[0])
                if 0<=idx<len(items_list): items_list.pop(idx)
            
            btn_frame=tk.Frame(d,bg=BG);btn_frame.pack(fill='x',padx=12,pady=4)
            tk.Button(btn_frame,text='➕ Add Item',bg='#3498db',fg=FG,relief='flat',command=add_item,padx=10,pady=4,font=('Arial',9)).pack(side='left',padx=2)
            tk.Button(btn_frame,text='🗑 Remove',bg='#e74c3c',fg=FG,relief='flat',command=remove_item,padx=10,pady=4,font=('Arial',9)).pack(side='left',padx=2)
            
            def save():
                vendor=vendor_var.get().strip()
                if not vendor:
                    messagebox.showwarning('Error','Please select a vendor',parent=d)
                    return
                try:
                    conn=sqlite3.connect(self.db_path)
                    c=conn.cursor()
                    
                    # ✅ Get vendor ID from DataService
                    vendor_id = vendor_map.get(vendor)
                    if not vendor_id:
                        messagebox.showerror('Error','Vendor not found',parent=d)
                        return
                    
                    # Insert PO with vendor_id and bill number
                    bill_num = bill_num_var.get().strip() or None
                    c.execute('INSERT INTO purchase_orders (po_number, bill_number, date, vendor_id, status, subtotal, tax, total, notes) VALUES (?,?,?,?,?,?,?,?,?)',
                                (po_num_var.get(), bill_num, po_date_var.get(), vendor_id, status_var.get(), subtotal_var.get(), tax_var.get(), total_var.get(), notes_var.get()))
                    po_id=c.lastrowid
                    conn.commit()
                    
                    # Save items
                    for item in items_list:
                        item_total=round(item['qty']*item['price']*(1+item['gst']/100),2)
                        c.execute('INSERT INTO purchase_order_items (po_id, product_name, qty, unit_price, gst_rate, total) VALUES (?,?,?,?,?,?)',
                                    (po_id, item['prod'], item['qty'], item['price'], item['gst'], item_total))
                    
                    conn.commit();conn.close();load();d.destroy()
                    messagebox.showinfo('Hype ERP',f'✅ PO created for {vendor} with {len(items_list)} items!')
                except Exception as e: 
                    messagebox.showerror('Error',str(e),parent=d)
                    print(f"Error saving PO: {e}")
            
            tk.Button(d,text='💾 Save PO',bg=ACC,fg=FG,relief='flat',command=save,padx=14,pady=7,font=('Arial',10,'bold')).pack(pady=10)

        def receive_po():
            """✅ Mark PO as received and update stock"""
            sel=tree.selection()
            if not sel: messagebox.showwarning('Select','Select a PO to receive');return
            po_id=tree.item(sel[0])['values'][0]
            po_status=tree.item(sel[0])['values'][6]
            if po_status=='Received':
                messagebox.showinfo('Already Received','This PO is already marked as received.');return
            
            d=tk.Toplevel(win);d.title('Receive Purchase Order');d.geometry('420x380');d.configure(bg=BG);from modules.window_utils import set_icon;set_icon(d)
            tk.Label(d,text='📦 Receive PO Items',bg=BG2,fg=ACC,font=('Arial',12,'bold')).pack(fill='x',ipady=8)
            
            # Load PO items
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            c.execute('SELECT po_number FROM purchase_orders WHERE id=?',(po_id,))
            po_no=c.fetchone()[0]
            tk.Label(d,text=f'PO: {po_no}',bg=BG,fg=FG,font=('Arial',10)).pack(anchor='w',padx=14,pady=(6,2))
            
            c.execute('SELECT id,product_name,qty FROM purchase_order_items WHERE po_id=?',(po_id,))
            items=c.fetchall();conn.close()
            
            if not items:
                messagebox.showinfo('No Items','No items in this PO');d.destroy();return
            
            received_qty={}
            for item_id,prod_name,qty in items:
                f=tk.Frame(d,bg=BG);f.pack(fill='x',padx=14,pady=4)
                tk.Label(f,text=f'{prod_name}:',bg=BG,fg=FG,font=('Arial',9),width=20).pack(side='left')
                rv=tk.StringVar(value=str(qty))
                tk.Entry(f,textvariable=rv,bg=BG2,fg=FG,insertbackground=FG,width=10).pack(side='left',padx=4)
                tk.Label(f,text=f'/ {qty}',bg=BG,fg='#888',font=('Arial',8)).pack(side='left')
                received_qty[item_id]=(prod_name,rv)
            
            def save_receive():
                try:
                    conn=sqlite3.connect(self.db_path);c=conn.cursor()
                    # Update PO status
                    c.execute('UPDATE purchase_orders SET status=? WHERE id=?',('Received',po_id))
                    # Update stock for each item
                    for item_id,(prod_name,rv) in received_qty.items():
                        try:
                            recv_qty=int(rv.get())
                            c.execute('UPDATE products SET stock=stock+? WHERE name=?',(recv_qty,prod_name))
                        except: pass
                    conn.commit();conn.close();load();d.destroy()
                    messagebox.showinfo('Hype ERP',f'PO {po_no} received! Stock updated.');
                except Exception as e: messagebox.showerror('Error',str(e))
            tk.Button(d,text='✅ Confirm Receipt',bg='#27ae60',fg=FG,relief='flat',command=save_receive,padx=14,pady=7,font=('Arial',10,'bold')).pack(pady=10)

        def delete_po():
            sel=tree.selection()
            if not sel: return
            pid=tree.item(sel[0])['values'][0]
            if messagebox.askyesno('Delete','Delete this purchase order?'):
                conn=sqlite3.connect(self.db_path)
                conn.execute('DELETE FROM purchase_orders WHERE id=?',(pid,))
                conn.commit();conn.close();load()

        btn_frame=tk.Frame(po_frame,bg=BG);btn_frame.pack(side='bottom',pady=6)
        tk.Button(btn_frame,text='+ New PO',bg=ACC,fg=FG,relief='flat',command=new_po,padx=12,pady=5).pack(side='left',padx=4)
        tk.Button(btn_frame,text='📦 Receive',bg='#27ae60',fg=FG,relief='flat',command=receive_po,padx=12,pady=5).pack(side='left',padx=4)
        tk.Button(btn_frame,text='🗑 Delete',bg='#c0392b',fg=FG,relief='flat',command=delete_po,padx=12,pady=5).pack(side='left',padx=4)
        tk.Button(btn_frame,text='🔄 Refresh',bg='#333355',fg=FG,relief='flat',command=load,padx=12,pady=5).pack(side='left',padx=4)
        
        # ─── TAB 2: VENDOR BILLS ───
        bills_frame=tk.Frame(nb,bg=BG);nb.add(bills_frame,text='💳 Vendor Bills Summary')
        
        bill_cols=('Vendor Name','Total POs','Total Amount Due','Pending Amount','Received Amount')
        bills_tree=ttk.Treeview(bills_frame,columns=bill_cols,show='headings',height=18)
        for col in bill_cols: bills_tree.heading(col,text=col);bills_tree.column(col,width=150)
        bills_sb=ttk.Scrollbar(bills_frame,orient='vertical',command=bills_tree.yview)
        bills_tree.configure(yscroll=bills_sb.set)
        bills_tree.pack(side='left',fill='both',expand=True,padx=(12,0),pady=8)
        bills_sb.pack(side='right',fill='y',pady=8)
        
        def load_vendor_bills():
            for i in bills_tree.get_children(): bills_tree.delete(i)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try:
                c.execute('''SELECT v.name, COUNT(po.id) as total_pos, SUM(po.total) as total_amount,
                            SUM(CASE WHEN po.status='Pending' THEN po.total ELSE 0 END) as pending,
                            SUM(CASE WHEN po.status='Received' THEN po.total ELSE 0 END) as received
                            FROM vendors v
                            LEFT JOIN purchase_orders po ON v.id = po.vendor_id
                            WHERE v.status='Active' OR v.status IS NULL
                            GROUP BY v.id, v.name ORDER BY total_amount DESC NULLS LAST''')
                for row in c.fetchall():
                    vendor_name, total_pos, total_amt, pending_amt, received_amt = row
                    if vendor_name:
                        bills_tree.insert('','end',values=(
                            vendor_name or 'Unknown',
                            int(total_pos or 0),
                            f'₹{float(total_amt or 0):.2f}',
                            f'₹{float(pending_amt or 0):.2f}',
                            f'₹{float(received_amt or 0):.2f}'
                        ))
            except Exception as e:
                print(f"Error loading vendor bills: {e}")
            conn.close()
        
        bills_btn_frame=tk.Frame(bills_frame,bg=BG);bills_btn_frame.pack(side='bottom',pady=6)
        tk.Button(bills_btn_frame,text='🔄 Refresh Bills',bg='#333355',fg=FG,relief='flat',command=load_vendor_bills,padx=12,pady=5).pack(side='left',padx=4)
        tk.Button(bills_btn_frame,text='📄 Export',bg='#3498db',fg=FG,relief='flat',padx=12,pady=5).pack(side='left',padx=4)
        
        footer_label=tk.Label(win,text=FOOTER,bg=BG2,fg='#444466',font=('Arial',7))
        footer_label.pack(side='bottom',fill='x',ipady=3)
        
        load()
        load_vendor_bills()
