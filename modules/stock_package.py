# Hype ERP - Shipping / Package Module (stock_package)
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
        CREATE TABLE IF NOT EXISTS shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_number TEXT UNIQUE,
            invoice_number TEXT,
            customer_name TEXT,
            customer_address TEXT,
            courier TEXT,
            status TEXT DEFAULT 'Pending',
            dispatch_date TEXT,
            expected_date TEXT,
            delivered_date TEXT,
            weight_kg REAL DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit();conn.close()

class StockPackageModule:
    def __init__(self,parent,db_path):
        self.parent=parent;self.db_path=db_path;_init(db_path)

    def open(self):
        win=tk.Toplevel(self.parent);win.title('Hype ERP — Shipping & Delivery')
        win.geometry('1100x640');win.configure(bg=BG)
        set_icon(win)
        tk.Label(win,text='🚚 Hype ERP — Shipping & Delivery Management',
                 font=('Arial',16,'bold'),bg=BG2,fg=ACC).pack(fill='x',ipady=10)

        sf=tk.Frame(win,bg=BG);sf.pack(fill='x',padx=12,pady=4)
        tk.Label(sf,text='Search:',bg=BG,fg=FG).pack(side='left')
        sv=tk.StringVar()
        tk.Entry(sf,textvariable=sv,bg=BG2,fg=FG,insertbackground=FG,width=28).pack(side='left',padx=6)

        cols=('ID','Tracking No','Invoice','Customer','Courier','Status','Dispatch','Expected','Weight(kg)')
        tree=ttk.Treeview(win,columns=cols,show='headings',height=16)
        for c,w in zip(cols,[50,130,110,160,100,100,110,110,90]):
            tree.heading(c,text=c);tree.column(c,width=w)
        sb=ttk.Scrollbar(win,orient='vertical',command=tree.yview)
        tree.configure(yscroll=sb.set)
        tree.pack(side='left',fill='both',expand=True,padx=(12,0),pady=6)
        sb.pack(side='right',fill='y',pady=6)

        def load(q=''):
            for i in tree.get_children(): tree.delete(i)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try:
                c.execute("""SELECT id,tracking_number,invoice_number,customer_name,courier,
                    status,dispatch_date,expected_date,weight_kg FROM shipments
                    WHERE tracking_number LIKE ? OR customer_name LIKE ? ORDER BY id DESC""",
                    (f'%{q}%',f'%{q}%'))
                for row in c.fetchall():
                    tree.insert('','end',values=row,
                                tags=('del',) if row[5]=='Delivered' else (('ship',) if row[5]=='Shipped' else ()))
            except: pass
            conn.close()
            tree.tag_configure('del',foreground='#2ecc71')
            tree.tag_configure('ship',foreground='#3498db')

        sv.trace('w',lambda *a: load(sv.get()))

        def new_shipment():
            d=tk.Toplevel(win);d.title('New Shipment');d.geometry('420x480');d.configure(bg=BG);set_icon(d)
            tk.Label(d,text='🚚 New Shipment',bg=BG2,fg=ACC,font=('Arial',11,'bold')).pack(fill='x',ipady=8)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try: c.execute('SELECT COUNT(*) FROM shipments');cnt=c.fetchone()[0]+1
            except: cnt=1
            conn.close()
            flds=[('Tracking No',tk.StringVar(value=f'SHIP-{date.today().strftime("%Y%m")}-{cnt:04d}')),
                  ('Invoice No',tk.StringVar()),('Customer Name',tk.StringVar()),
                  ('Customer Address',tk.StringVar()),('Courier',tk.StringVar(value='DTDC')),
                  ('Status',tk.StringVar(value='Pending')),
                  ('Dispatch Date',tk.StringVar(value=str(date.today()))),
                  ('Expected Date',tk.StringVar()),
                  ('Weight (kg)',tk.StringVar(value='0')),('Notes',tk.StringVar())]
            for lbl,var in flds:
                tk.Label(d,text=lbl,bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(3,0))
                tk.Entry(d,textvariable=var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            def save():
                vals=[v.get() for _,v in flds]
                try:
                    conn=sqlite3.connect(self.db_path)
                    conn.execute('INSERT INTO shipments (tracking_number,invoice_number,customer_name,customer_address,courier,status,dispatch_date,expected_date,weight_kg,notes) VALUES (?,?,?,?,?,?,?,?,?,?)',vals)
                    conn.commit();conn.close();load();d.destroy()
                    messagebox.showinfo('Hype ERP','Shipment created!')
                except Exception as e: messagebox.showerror('Error',str(e))
            tk.Button(d,text='💾 Save',bg=ACC,fg=FG,relief='flat',command=save,padx=14,pady=7,font=('Arial',10,'bold')).pack(pady=10)

        def mark_delivered():
            sel=tree.selection()
            if not sel: return
            sid=tree.item(sel[0])['values'][0]
            conn=sqlite3.connect(self.db_path)
            conn.execute("UPDATE shipments SET status='Delivered', delivered_date=? WHERE id=?",(str(date.today()),sid))
            conn.commit();conn.close();load()
            messagebox.showinfo('Hype ERP','Marked as Delivered!')

        bf=tk.Frame(win,bg=BG);bf.pack(side='bottom',pady=6)
        tk.Button(bf,text='+ New Shipment',bg=ACC,fg=FG,relief='flat',command=new_shipment,padx=12,pady=5).pack(side='left',padx=4)
        tk.Button(bf,text='✅ Mark Delivered',bg='#27ae60',fg=FG,relief='flat',command=mark_delivered,padx=12,pady=5).pack(side='left',padx=4)
        tk.Button(bf,text='🔄 Refresh',bg='#333355',fg=FG,relief='flat',command=load,padx=12,pady=5).pack(side='left',padx=4)
        tk.Label(win,text=FOOTER,bg=BG2,fg='#444466',font=('Arial',7)).pack(side='bottom',fill='x',ipady=3)
        load()
