# Hype ERP - Purchase Order Module (purchase)
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
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT UNIQUE,
            date TEXT,
            vendor_name TEXT,
            vendor_phone TEXT,
            vendor_gstin TEXT,
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
    conn.commit();conn.close()

class PurchaseModule:
    def __init__(self,parent,db_path):
        self.parent=parent;self.db_path=db_path;_init(db_path)

    def open(self):
        win=tk.Toplevel(self.parent);win.title('Hype ERP — Purchase Orders')
        win.geometry('1050x620');win.configure(bg=BG);set_icon(win)
        tk.Label(win,text='🛍 Hype ERP — Purchase Orders & Vendor Bills',
                 font=('Arial',16,'bold'),bg=BG2,fg=ACC).pack(fill='x',ipady=10)

        cols=('ID','PO Number','Date','Vendor','Phone','GSTIN','Status','Subtotal','Tax','Total')
        tree=ttk.Treeview(win,columns=cols,show='headings',height=16)
        for c in cols: tree.heading(c,text=c);tree.column(c,width=100)
        sb=ttk.Scrollbar(win,orient='vertical',command=tree.yview)
        tree.configure(yscroll=sb.set)
        tree.pack(side='left',fill='both',expand=True,padx=(12,0),pady=8)
        sb.pack(side='right',fill='y',pady=8)

        def load():
            for i in tree.get_children(): tree.delete(i)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try:
                c.execute('SELECT id,po_number,date,vendor_name,vendor_phone,vendor_gstin,status,subtotal,tax,total FROM purchase_orders ORDER BY id DESC')
                for row in c.fetchall():
                    tree.insert('','end',values=row,tags=('recv',) if row[6]=='Received' else ())
            except: pass
            conn.close()
            tree.tag_configure('recv',foreground='#2ecc71')

        def new_po():
            d=tk.Toplevel(win);d.title('New Purchase Order');d.geometry('420x460');d.configure(bg=BG);set_icon(d)
            tk.Label(d,text='+ New Purchase Order',bg=BG2,fg=ACC,font=('Arial',12,'bold')).pack(fill='x',ipady=8)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try: c.execute('SELECT COUNT(*) FROM purchase_orders');cnt=c.fetchone()[0]+1
            except: cnt=1
            conn.close()
            flds=[('PO Number',tk.StringVar(value=f'PO-{date.today().strftime("%Y%m")}-{cnt:04d}')),
                  ('Date',tk.StringVar(value=str(date.today()))),
                  ('Vendor Name',tk.StringVar()),('Vendor Phone',tk.StringVar()),
                  ('Vendor GSTIN',tk.StringVar()),
                  ('Status',tk.StringVar(value='Pending')),
                  ('Subtotal',tk.StringVar(value='0')),('Tax',tk.StringVar(value='0')),
                  ('Total',tk.StringVar(value='0')),('Notes',tk.StringVar())]
            for lbl,var in flds:
                tk.Label(d,text=lbl,bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
                tk.Entry(d,textvariable=var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            def save():
                vals=[v.get() for _,v in flds]
                try:
                    conn=sqlite3.connect(self.db_path)
                    conn.execute('INSERT INTO purchase_orders (po_number,date,vendor_name,vendor_phone,vendor_gstin,status,subtotal,tax,total,notes) VALUES (?,?,?,?,?,?,?,?,?,?)',vals)
                    conn.commit();conn.close();load();d.destroy()
                    messagebox.showinfo('Hype ERP','Purchase order saved!')
                except Exception as e: messagebox.showerror('Error',str(e))
            tk.Button(d,text='💾 Save PO',bg=ACC,fg=FG,relief='flat',command=save,padx=14,pady=7,font=('Arial',10,'bold')).pack(pady=10)

        def delete_po():
            sel=tree.selection()
            if not sel: return
            pid=tree.item(sel[0])['values'][0]
            if messagebox.askyesno('Delete','Delete this purchase order?'):
                conn=sqlite3.connect(self.db_path)
                conn.execute('DELETE FROM purchase_orders WHERE id=?',(pid,))
                conn.commit();conn.close();load()

        bf=tk.Frame(win,bg=BG);bf.pack(side='bottom',pady=6)
        tk.Button(bf,text='+ New PO',bg=ACC,fg=FG,relief='flat',command=new_po,padx=12,pady=5).pack(side='left',padx=4)
        tk.Button(bf,text='🗑 Delete',bg='#c0392b',fg=FG,relief='flat',command=delete_po,padx=12,pady=5).pack(side='left',padx=4)
        tk.Button(bf,text='🔄 Refresh',bg='#333355',fg=FG,relief='flat',command=load,padx=12,pady=5).pack(side='left',padx=4)
        tk.Label(win,text=FOOTER,bg=BG2,fg='#444466',font=('Arial',7)).pack(side='bottom',fill='x',ipady=3)
        load()
