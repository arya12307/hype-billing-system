# Hype ERP - Sales Order Module (sale)
# Developer: David | Nexuzy Lab
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date
from modules.window_utils import set_icon

BG='#1a1a2e';BG2='#16213e';ACC='#e94560';FG='white'
FOOTER='Powered by Hype ERP v3.0.0 | Nexuzy Lab | Developer: David'

def _init(db_path):
    conn=sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sale_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE,
            date TEXT,
            customer_name TEXT,
            customer_phone TEXT,
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
    conn.commit();conn.close()

class SaleModule:
    def __init__(self,parent,db_path):
        self.parent=parent; self.db_path=db_path; _init(db_path)

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
                c.execute('SELECT id,order_number,date,customer_name,customer_phone,status,subtotal,tax,discount,total FROM sale_orders ORDER BY id DESC')
                for row in c.fetchall():
                    tree.insert('','end',values=row,tags=('conf',) if row[5]=='Confirmed' else ())
            except: pass
            conn.close()
            tree.tag_configure('conf',foreground='#2ecc71')

        def new_order():
            d=tk.Toplevel(win);d.title('New Sale Order');d.geometry('420x440');d.configure(bg=BG);set_icon(d)
            tk.Label(d,text='+ New Sale Order',bg=BG2,fg=ACC,font=('Arial',12,'bold')).pack(fill='x',ipady=8)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try: c.execute('SELECT COUNT(*) FROM sale_orders'); cnt=c.fetchone()[0]+1
            except: cnt=1
            conn.close()
            flds=[('Order No',tk.StringVar(value=f'SO-{date.today().strftime("%Y%m")}-{cnt:04d}')),
                  ('Date',tk.StringVar(value=str(date.today()))),
                  ('Customer Name',tk.StringVar()),('Customer Phone',tk.StringVar()),
                  ('Status',tk.StringVar(value='Confirmed')),
                  ('Subtotal',tk.StringVar(value='0')),('Tax',tk.StringVar(value='0')),
                  ('Discount',tk.StringVar(value='0')),('Total',tk.StringVar(value='0')),
                  ('Notes',tk.StringVar())]
            for lbl,var in flds:
                tk.Label(d,text=lbl,bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
                tk.Entry(d,textvariable=var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            def save():
                vals=[v.get() for _,v in flds]
                try:
                    conn=sqlite3.connect(self.db_path)
                    conn.execute('INSERT INTO sale_orders (order_number,date,customer_name,customer_phone,status,subtotal,tax,discount,total,notes) VALUES (?,?,?,?,?,?,?,?,?,?)',vals)
                    conn.commit();conn.close();load();d.destroy()
                    messagebox.showinfo('Hype ERP','Sale order saved!')
                except Exception as e: messagebox.showerror('Error',str(e))
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
