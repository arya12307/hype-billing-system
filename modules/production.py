# Hype ERP - Manufacturing / Production Module (production)
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
        CREATE TABLE IF NOT EXISTS bom (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            component_name TEXT NOT NULL,
            qty_required REAL DEFAULT 1,
            unit TEXT DEFAULT 'pcs'
        );
        CREATE TABLE IF NOT EXISTS production_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE,
            product_name TEXT,
            quantity INTEGER DEFAULT 1,
            status TEXT DEFAULT 'Draft',
            start_date TEXT,
            end_date TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit();conn.close()

class ProductionModule:
    def __init__(self,parent,db_path):
        self.parent=parent;self.db_path=db_path;_init(db_path)

    def open(self):
        win=tk.Toplevel(self.parent);win.title('Hype ERP — Manufacturing & Production')
        win.geometry('1050x640');win.configure(bg=BG)
        set_icon(win)
        tk.Label(win,text='🏭 Hype ERP — Manufacturing & Production Orders',
                 font=('Arial',16,'bold'),bg=BG2,fg=ACC).pack(fill='x',ipady=10)

        nb=ttk.Notebook(win);nb.pack(fill='both',expand=True,padx=10,pady=6)

        # Production Orders Tab
        t1=tk.Frame(nb,bg=BG);nb.add(t1,text='⚙️ Production Orders')
        cols=('ID','Order No','Product','Qty','Status','Start Date','End Date')
        tree=ttk.Treeview(t1,columns=cols,show='headings',height=14)
        for c,w in zip(cols,[50,120,180,70,100,110,110]):
            tree.heading(c,text=c);tree.column(c,width=w)
        tree.pack(fill='both',expand=True,padx=8,pady=6)

        def load_orders():
            for i in tree.get_children(): tree.delete(i)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try:
                c.execute('SELECT id,order_number,product_name,quantity,status,start_date,end_date FROM production_orders ORDER BY id DESC')
                for row in c.fetchall():
                    tree.insert('','end',values=row,tags=('done',) if row[4]=='Done' else ())
            except: pass
            conn.close()
            tree.tag_configure('done',foreground='#2ecc71')

        def new_order():
            d=tk.Toplevel(win);d.title('New Production Order');d.geometry('400x380');d.configure(bg=BG)
            set_icon(d)
            tk.Label(d,text='⚙️ New Production Order',bg=BG2,fg=ACC,font=('Arial',11,'bold')).pack(fill='x',ipady=8)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try: c.execute('SELECT COUNT(*) FROM production_orders');cnt=c.fetchone()[0]+1
            except: cnt=1
            conn.close()
            flds=[('Order No',tk.StringVar(value=f'MO-{date.today().strftime("%Y%m")}-{cnt:04d}')),
                  ('Product Name',tk.StringVar()),('Quantity',tk.StringVar(value='1')),
                  ('Status',tk.StringVar(value='In Progress')),
                  ('Start Date',tk.StringVar(value=str(date.today()))),
                  ('End Date',tk.StringVar()),('Notes',tk.StringVar())]
            for lbl,var in flds:
                tk.Label(d,text=lbl,bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(4,0))
                tk.Entry(d,textvariable=var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            def save():
                vals=[v.get() for _,v in flds]
                try:
                    conn=sqlite3.connect(self.db_path)
                    conn.execute('INSERT INTO production_orders (order_number,product_name,quantity,status,start_date,end_date,notes) VALUES (?,?,?,?,?,?,?)',vals)
                    conn.commit();conn.close();load_orders();d.destroy()
                    messagebox.showinfo('Hype ERP','Production order created!')
                except Exception as e: messagebox.showerror('Error',str(e))
            tk.Button(d,text='💾 Save',bg=ACC,fg=FG,relief='flat',command=save,padx=14,pady=6,font=('Arial',10,'bold')).pack(pady=10)

        tk.Button(t1,text='+ New Order',bg=ACC,fg=FG,relief='flat',command=new_order,padx=12,pady=5).pack(pady=4)
        tk.Button(t1,text='🔄 Refresh',bg='#333355',fg=FG,relief='flat',command=load_orders,padx=12,pady=5).pack()

        # BOM Tab
        t2=tk.Frame(nb,bg=BG);nb.add(t2,text='📝 Bill of Materials')
        bcols=('ID','Product','Component','Qty Required','Unit')
        bt=ttk.Treeview(t2,columns=bcols,show='headings',height=16)
        for c,w in zip(bcols,[50,180,180,110,80]):
            bt.heading(c,text=c);bt.column(c,width=w)
        bt.pack(fill='both',expand=True,padx=8,pady=6)
        def load_bom():
            for i in bt.get_children(): bt.delete(i)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try:
                c.execute('SELECT id,product_name,component_name,qty_required,unit FROM bom ORDER BY product_name')
                for row in c.fetchall(): bt.insert('','end',values=row)
            except: pass
            conn.close()
        def add_bom():
            d=tk.Toplevel(win);d.title('Add BOM Entry');d.geometry('380x300');d.configure(bg=BG)
            set_icon(d)
            flds=[('Finished Product',tk.StringVar()),('Component',tk.StringVar()),
                  ('Qty Required',tk.StringVar(value='1')),('Unit',tk.StringVar(value='pcs'))]
            for lbl,var in flds:
                tk.Label(d,text=lbl,bg=BG,fg=FG).pack(anchor='w',padx=16,pady=(6,0))
                tk.Entry(d,textvariable=var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            def save():
                vals=[v.get() for _,v in flds]
                conn=sqlite3.connect(self.db_path)
                conn.execute('INSERT INTO bom (product_name,component_name,qty_required,unit) VALUES (?,?,?,?)',vals)
                conn.commit();conn.close();load_bom();d.destroy()
            tk.Button(d,text='💾 Save',bg=ACC,fg=FG,relief='flat',command=save,padx=14,pady=6).pack(pady=10)
        tk.Button(t2,text='+ Add BOM',bg=ACC,fg=FG,relief='flat',command=add_bom,padx=12,pady=5).pack(pady=4)
        tk.Button(t2,text='🔄 Refresh',bg='#333355',fg=FG,relief='flat',command=load_bom,padx=12,pady=5).pack()

        nb.bind('<<NotebookTabChanged>>',lambda e: load_orders() if nb.index('current')==0 else load_bom())
        load_orders()
        tk.Label(win,text=FOOTER,bg=BG2,fg='#444466',font=('Arial',7)).pack(side='bottom',fill='x',ipady=3)
