# Hype ERP - Stock / Inventory Module (stock)
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
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            product_name TEXT,
            movement_type TEXT,
            quantity INTEGER DEFAULT 0,
            reason TEXT,
            reference TEXT,
            created_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit();conn.close()

class StockModule:
    def __init__(self,parent,db_path):
        self.parent=parent;self.db_path=db_path;_init(db_path)

    def open(self):
        win=tk.Toplevel(self.parent);win.title('Hype ERP — Stock Management')
        win.geometry('1100x660');win.configure(bg=BG)
        set_icon(win)
        tk.Label(win,text='📦 Hype ERP — Stock / Inventory Management',
                 font=('Arial',16,'bold'),bg=BG2,fg=ACC).pack(fill='x',ipady=10)

        nb=ttk.Notebook(win);nb.pack(fill='both',expand=True,padx=10,pady=6)

        # Tab 1: Current Stock
        t1=tk.Frame(nb,bg=BG);nb.add(t1,text='📊 Current Stock')
        cols=('ID','Product','Category','Stock Qty','Min Stock','Unit','Price','Status')
        st=ttk.Treeview(t1,columns=cols,show='headings',height=16)
        for c,w in zip(cols,[50,200,120,90,90,70,90,90]):
            st.heading(c,text=c);st.column(c,width=w)
        
        # Add scrollbars (vertical and horizontal)
        vsb=ttk.Scrollbar(t1,orient='vertical',command=st.yview)
        hsb=ttk.Scrollbar(t1,orient='horizontal',command=st.xview)
        st.configure(yscroll=vsb.set,xscroll=hsb.set)
        st.pack(side='left',fill='both',expand=True,padx=8,pady=6)
        vsb.pack(side='right',fill='y',pady=6)

        def load_stock():
            for i in st.get_children(): st.delete(i)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try:
                c.execute('SELECT id,name,category,stock,min_stock,unit,selling_price FROM products ORDER BY stock ASC')
                for row in c.fetchall():
                    status='🔴 Out of Stock' if row[3]==0 else ('🟡 Low' if row[3]<row[4] else '🟢 OK')
                    st.insert('','end',values=(*row,status),tags=('out',) if row[3]==0 else (('low',) if row[3]<row[4] else ()))
            except: pass
            conn.close()
            st.tag_configure('out',background='#3d0000',foreground='#ff6666')
            st.tag_configure('low',background='#3d2a00',foreground='#ffcc00')

        def adjust_stock():
            sel=st.selection()
            if not sel: messagebox.showwarning('Select','Select a product first.');return
            pid=st.item(sel[0])['values'][0];pname=st.item(sel[0])['values'][1]
            d=tk.Toplevel(win);d.title('Stock Adjustment');d.geometry('380x320');d.configure(bg=BG)
            set_icon(d)
            tk.Label(d,text=f'Adjust Stock: {pname}',bg=BG2,fg=ACC,font=('Arial',11,'bold')).pack(fill='x',ipady=8)
            mtype=tk.StringVar(value='IN');qty=tk.StringVar(value='0');reason=tk.StringVar();ref=tk.StringVar()
            for lbl,var,opts in [('Type',mtype,['IN','OUT','ADJUST']),('Quantity',qty,None),('Reason',reason,None),('Reference',ref,None)]:
                tk.Label(d,text=lbl,bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(6,0))
                if opts: ttk.Combobox(d,textvariable=var,values=opts,state='readonly').pack(fill='x',padx=16)
                else: tk.Entry(d,textvariable=var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            def save():
                try:
                    q=int(qty.get())
                    conn=sqlite3.connect(self.db_path);c=conn.cursor()
                    if mtype.get()=='IN': c.execute('UPDATE products SET stock=stock+? WHERE id=?',(q,pid))
                    elif mtype.get()=='OUT': c.execute('UPDATE products SET stock=MAX(0,stock-?) WHERE id=?',(q,pid))
                    else: c.execute('UPDATE products SET stock=? WHERE id=?',(q,pid))
                    c.execute('INSERT INTO stock_movements (date,product_name,movement_type,quantity,reason,reference) VALUES (?,?,?,?,?,?)',
                               (str(date.today()),pname,mtype.get(),q,reason.get(),ref.get()))
                    conn.commit();conn.close();load_stock();d.destroy()
                    messagebox.showinfo('Hype ERP','Stock adjusted!')
                except Exception as e: messagebox.showerror('Error',str(e))
            tk.Button(d,text='💾 Save',bg=ACC,fg=FG,relief='flat',command=save,padx=14,pady=6).pack(pady=10)

        # Buttons frame for Tab 1
        bf1=tk.Frame(t1,bg=BG);bf1.pack(fill='x',padx=8,pady=6)
        tk.Button(bf1,text='↕ Adjust Stock',bg=ACC,fg=FG,relief='flat',command=adjust_stock,padx=12,pady=5).pack(side='left',padx=2)
        tk.Button(bf1,text='🔄 Refresh',bg='#333355',fg=FG,relief='flat',command=load_stock,padx=12,pady=5).pack(side='left',padx=2)

        # Tab 2: Movements
        t2=tk.Frame(nb,bg=BG);nb.add(t2,text='📄 Movement History')
        cols2=('ID','Date','Product','Type','Qty','Reason','Reference')
        mt=ttk.Treeview(t2,columns=cols2,show='headings',height=18)
        for c,w in zip(cols2,[50,100,200,80,70,180,130]):
            mt.heading(c,text=c);mt.column(c,width=w)
        mt.pack(fill='both',expand=True,padx=8,pady=8)
        def load_movements():
            for i in mt.get_children(): mt.delete(i)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try:
                c.execute('SELECT id,date,product_name,movement_type,quantity,reason,reference FROM stock_movements ORDER BY id DESC')
                for row in c.fetchall():
                    mt.insert('','end',values=row,tags=('in',) if row[3]=='IN' else (('out',) if row[3]=='OUT' else ()))
            except: pass
            conn.close()
            mt.tag_configure('in',foreground='#2ecc71');mt.tag_configure('out',foreground='#e74c3c')
        tk.Button(t2,text='🔄 Refresh',bg='#333355',fg=FG,relief='flat',command=load_movements,padx=12,pady=5).pack(pady=6)

        nb.bind('<<NotebookTabChanged>>',lambda e: load_stock() if nb.index('current')==0 else load_movements())
        load_stock()
        tk.Label(win,text=FOOTER,bg=BG2,fg='#444466',font=('Arial',7)).pack(side='bottom',fill='x',ipady=3)
