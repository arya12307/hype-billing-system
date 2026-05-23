# Hype ERP - Sales Order Module (sale)
# Developer: David | Nexuzy Lab
# ✅ CONNECTED TO DATA SERVICE - All customer data now shared
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date
from modules.window_utils import set_icon
from modules.data_service import get_data_service

BG='#1a1a2e';BG2='#16213e';ACC='#e94560';FG='white'
FOOTER='Powered by Hype ERP v3.0.0 | Nexuzy Lab | Developer: David'

def _init(db_path):
    conn=sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create tables
    c.executescript("""
        CREATE TABLE IF NOT EXISTS sale_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE,
            date TEXT,
            customer_id INTEGER,
            status TEXT DEFAULT 'Draft',
            subtotal REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            total REAL DEFAULT 0,
            notes TEXT,
            created_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS sale_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_name TEXT,
            qty INTEGER DEFAULT 1,
            unit_price REAL DEFAULT 0,
            gst_rate REAL DEFAULT 0,
            total REAL DEFAULT 0
        );
    """)
    
    # Schema migration - add customer_id column if it doesn't exist
    try:
        c.execute("PRAGMA table_info(sale_orders)")
        columns = [col[1] for col in c.fetchall()]
        if 'customer_id' not in columns:
            c.execute("ALTER TABLE sale_orders ADD COLUMN customer_id INTEGER")
    except:
        pass
    
    conn.commit()
    conn.close()

class SaleModule:
    MODULE_NAME = "Sales Orders"
    MODULE_CODE = "sales"
    
    def __init__(self,parent,db_path):
        self.parent=parent
        self.db_path=db_path
        self.data_service=get_data_service(db_path)
        self.data_service.register_module(self.MODULE_NAME, self.MODULE_CODE)
        _init(db_path)

    def open(self):
        win=tk.Toplevel(self.parent); win.title('Hype ERP — Sales Orders')
        win.geometry('1050x620'); win.configure(bg=BG)
        set_icon(win)
        tk.Label(win,text='📈 Hype ERP — Sales Orders',
                 font=('Arial',16,'bold'),bg=BG2,fg=ACC).pack(fill='x',ipady=10)

        cols=('ID','Order No','Date','Customer','Phone','Status','Subtotal','Tax','Discount','Total')
        tree=ttk.Treeview(win,columns=cols,show='headings',height=16)
        for c in cols: tree.heading(c,text=c); tree.column(c,width=100)
        sb=ttk.Scrollbar(win,orient='vertical',command=tree.yview)
        tree.configure(yscroll=sb.set)
        tree.pack(side='left',fill='both',expand=True,padx=(12,0),pady=8)
        sb.pack(side='right',fill='y',pady=8)

        def load():
            for i in tree.get_children(): tree.delete(i)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try:
                c.execute('''SELECT so.id, so.order_number, so.date, c.name as customer_name, c.phone, so.status, so.subtotal, so.tax, so.discount, so.total 
                            FROM sale_orders so
                            LEFT JOIN customers c ON so.customer_id = c.id
                            ORDER BY so.id DESC''')
                for row in c.fetchall():
                    tree.insert('','end',values=row,tags=('conf',) if row[5]=='Confirmed' else ())
            except Exception as e: print(f"Error loading orders: {e}")
            conn.close()
            tree.tag_configure('conf',foreground='#2ecc71')

        def new_order():
            d=tk.Toplevel(win);d.title('New Sale Order');d.geometry('420x440');d.configure(bg=BG);set_icon(d)
            tk.Label(d,text='+ New Sale Order',bg=BG2,fg=ACC,font=('Arial',12,'bold')).pack(fill='x',ipady=8)
            
            # ✅ Load Customer List from DataService
            customers = self.data_service.get_customers()
            customer_list = ['Walk-in Customer'] + [c['name'] for c in customers]
            customer_map = {'Walk-in Customer': 0}
            customer_map.update({c['name']: c['id'] for c in customers})
            
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try: c.execute('SELECT COUNT(*) FROM sale_orders'); cnt=c.fetchone()[0]+1
            except: cnt=1
            conn.close()
            
            order_no_var=tk.StringVar(value=f'SO-{date.today().strftime("%Y%m")}-{cnt:04d}')
            order_date_var=tk.StringVar(value=str(date.today()))
            customer_var=tk.StringVar()
            status_var=tk.StringVar(value='Confirmed')
            subtotal_var=tk.StringVar(value='0')
            tax_var=tk.StringVar(value='0')
            discount_var=tk.StringVar(value='0')
            total_var=tk.StringVar(value='0')
            notes_var=tk.StringVar()
            
            # Order Number (read-only)
            tk.Label(d,text='Order No',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
            tk.Entry(d,textvariable=order_no_var,bg=BG2,fg=FG,insertbackground=FG,state='readonly').pack(fill='x',padx=16)
            
            # Date
            tk.Label(d,text='Date',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
            tk.Entry(d,textvariable=order_date_var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            
            # ✅ Customer Selection (Dropdown)
            tk.Label(d,text='👥 Select Customer *',bg=BG,fg=ACC,font=('Arial',9,'bold')).pack(anchor='w',padx=16,pady=(6,0))
            customer_combo=ttk.Combobox(d,textvariable=customer_var,values=customer_list,state='readonly',width=35)
            customer_combo.pack(fill='x',padx=16,ipady=5)
            
            # Status
            tk.Label(d,text='Status',bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
            ttk.Combobox(d,textvariable=status_var,values=['Draft','Confirmed','Delivered'],state='readonly',width=35).pack(fill='x',padx=16,ipady=5)
            
            # Amounts and Notes
            for lbl,var in [('Subtotal',subtotal_var),('Tax',tax_var),('Discount',discount_var),('Total',total_var),('Notes',notes_var)]:
                tk.Label(d,text=lbl,bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
                tk.Entry(d,textvariable=var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            
            def save():
                customer=customer_var.get().strip()
                if not customer:
                    messagebox.showwarning('Error','Please select a customer',parent=d)
                    return
                try:
                    conn=sqlite3.connect(self.db_path)
                    customer_id = customer_map.get(customer)
                    if customer_id is None:
                        messagebox.showerror('Error','Customer not found',parent=d)
                        return
                    
                    # ✅ Insert with customer_id (not duplicate data)
                    conn.execute('INSERT INTO sale_orders (order_number, date, customer_id, status, subtotal, tax, discount, total, notes) VALUES (?,?,?,?,?,?,?,?,?)',
                                (order_no_var.get(), order_date_var.get(), customer_id, status_var.get(), subtotal_var.get(), tax_var.get(), discount_var.get(), total_var.get(), notes_var.get()))
                    conn.commit();conn.close();load();d.destroy()
                    messagebox.showinfo('Hype ERP',f'✅ Sale order created for {customer}!')
                except Exception as e: 
                    messagebox.showerror('Error',str(e),parent=d)
                    print(f"Error saving order: {e}")
            
            tk.Button(d,text='💾 Save Order',bg=ACC,fg=FG,relief='flat',command=save,padx=14,pady=7,font=('Arial',10,'bold')).pack(pady=10)

        def delete_order():
            sel=tree.selection()
            if not sel: return
            oid=tree.item(sel[0])['values'][0]
            if messagebox.askyesno('Delete','Delete this order?'):
                conn=sqlite3.connect(self.db_path)
                conn.execute('DELETE FROM sale_orders WHERE id=?',(oid,))
                conn.commit();conn.close();load()

        bf=tk.Frame(win,bg=BG);bf.pack(side='bottom',pady=6)
        tk.Button(bf,text='+ New Order',bg=ACC,fg=FG,relief='flat',command=new_order,padx=12,pady=5).pack(side='left',padx=4)
        tk.Button(bf,text='🗑 Delete',bg='#c0392b',fg=FG,relief='flat',command=delete_order,padx=12,pady=5).pack(side='left',padx=4)
        tk.Button(bf,text='🔄 Refresh',bg='#333355',fg=FG,relief='flat',command=load,padx=12,pady=5).pack(side='left',padx=4)
        tk.Label(win,text=FOOTER,bg=BG2,fg='#444466',font=('Arial',7)).pack(side='bottom',fill='x',ipady=3)
        load()
