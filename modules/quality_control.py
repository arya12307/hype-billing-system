# Hype ERP - Quality Control Module (quality_control)
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
        CREATE TABLE IF NOT EXISTS qc_checklists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checklist_name TEXT NOT NULL,
            product_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS qc_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checklist_id INTEGER,
            check_item TEXT NOT NULL,
            is_required INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS qc_inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inspection_number TEXT,
            checklist_id INTEGER,
            product_name TEXT,
            batch_number TEXT,
            inspector TEXT,
            date TEXT,
            result TEXT DEFAULT 'Pending',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit();conn.close()

class QualityControlModule:
    def __init__(self,parent,db_path):
        self.parent=parent;self.db_path=db_path;_init(db_path)

    def open(self):
        win=tk.Toplevel(self.parent);win.title('Hype ERP — Quality Control')
        win.geometry('1050x640');win.configure(bg=BG)
        set_icon(win)
        tk.Label(win,text='✅ Hype ERP — Quality Control',
                 font=('Arial',16,'bold'),bg=BG2,fg=ACC).pack(fill='x',ipady=10)

        nb=ttk.Notebook(win);nb.pack(fill='both',expand=True,padx=10,pady=6)

        # Inspections Tab
        t1=tk.Frame(nb,bg=BG);nb.add(t1,text='🔍 Inspections')
        cols=('ID','Inspection No','Product','Batch','Inspector','Date','Result')
        tree=ttk.Treeview(t1,columns=cols,show='headings',height=14)
        for c,w in zip(cols,[50,130,160,100,120,100,100]):
            tree.heading(c,text=c);tree.column(c,width=w)
        tree.pack(fill='both',expand=True,padx=8,pady=6)

        def load_insp():
            for i in tree.get_children(): tree.delete(i)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try:
                c.execute('SELECT id,inspection_number,product_name,batch_number,inspector,date,result FROM qc_inspections ORDER BY id DESC')
                for row in c.fetchall():
                    tree.insert('','end',values=row,
                                tags=('pass',) if row[6]=='Pass' else (('fail',) if row[6]=='Fail' else ()))
            except: pass
            conn.close()
            tree.tag_configure('pass',foreground='#2ecc71')
            tree.tag_configure('fail',foreground='#e74c3c')

        def new_inspection():
            d=tk.Toplevel(win);d.title('New Inspection');d.geometry('400x400');d.configure(bg=BG);set_icon(d)
            tk.Label(d,text='🔍 New QC Inspection',bg=BG2,fg=ACC,font=('Arial',11,'bold')).pack(fill='x',ipady=8)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try: c.execute('SELECT COUNT(*) FROM qc_inspections');cnt=c.fetchone()[0]+1
            except: cnt=1
            conn.close()
            flds=[('Inspection No',tk.StringVar(value=f'QC-{date.today().strftime("%Y%m")}-{cnt:04d}')),
                  ('Product Name',tk.StringVar()),('Batch No',tk.StringVar()),
                  ('Inspector',tk.StringVar()),('Date',tk.StringVar(value=str(date.today()))),
                  ('Result',tk.StringVar(value='Pass')),('Notes',tk.StringVar())]
            for lbl,var in flds:
                tk.Label(d,text=lbl,bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(4,0))
                tk.Entry(d,textvariable=var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            def save():
                vals=[v.get() for _,v in flds]
                try:
                    conn=sqlite3.connect(self.db_path)
                    conn.execute('INSERT INTO qc_inspections (inspection_number,product_name,batch_number,inspector,date,result,notes) VALUES (?,?,?,?,?,?,?)',vals)
                    conn.commit();conn.close();load_insp();d.destroy()
                    messagebox.showinfo('Hype ERP','Inspection recorded!')
                except Exception as e: messagebox.showerror('Error',str(e))
            tk.Button(d,text='💾 Save',bg=ACC,fg=FG,relief='flat',command=save,padx=14,pady=7,font=('Arial',10,'bold')).pack(pady=10)

        tk.Button(t1,text='+ New Inspection',bg=ACC,fg=FG,relief='flat',command=new_inspection,padx=12,pady=5).pack(pady=4)
        tk.Button(t1,text='🔄 Refresh',bg='#333355',fg=FG,relief='flat',command=load_insp,padx=12,pady=5).pack()

        # Checklists Tab
        t2=tk.Frame(nb,bg=BG);nb.add(t2,text='📝 Checklists')
        clcols=('ID','Checklist Name','Product')
        cl_tree=ttk.Treeview(t2,columns=clcols,show='headings',height=16)
        for c,w in zip(clcols,[60,260,200]):
            cl_tree.heading(c,text=c);cl_tree.column(c,width=w)
        cl_tree.pack(fill='both',expand=True,padx=8,pady=6)
        def load_cl():
            for i in cl_tree.get_children(): cl_tree.delete(i)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try:
                c.execute('SELECT id,checklist_name,product_name FROM qc_checklists ORDER BY id DESC')
                for row in c.fetchall(): cl_tree.insert('','end',values=row)
            except: pass
            conn.close()
        def add_cl():
            d=tk.Toplevel(win);d.title('Add Checklist');d.geometry('360x240');d.configure(bg=BG)
            set_icon(d)
            n=tk.StringVar();p=tk.StringVar()
            tk.Label(d,text='Checklist Name',bg=BG,fg=FG).pack(anchor='w',padx=16,pady=(12,0))
            tk.Entry(d,textvariable=n,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            tk.Label(d,text='Product (optional)',bg=BG,fg=FG).pack(anchor='w',padx=16,pady=(8,0))
            tk.Entry(d,textvariable=p,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            def save():
                conn=sqlite3.connect(self.db_path)
                conn.execute('INSERT INTO qc_checklists (checklist_name,product_name) VALUES (?,?)',(n.get(),p.get()))
                conn.commit();conn.close();load_cl();d.destroy()
            tk.Button(d,text='💾 Save',bg=ACC,fg=FG,relief='flat',command=save,padx=14,pady=6).pack(pady=12)
        tk.Button(t2,text='+ Add Checklist',bg=ACC,fg=FG,relief='flat',command=add_cl,padx=12,pady=5).pack(pady=4)
        tk.Button(t2,text='🔄 Refresh',bg='#333355',fg=FG,relief='flat',command=load_cl,padx=12,pady=5).pack()

        nb.bind('<<NotebookTabChanged>>',lambda e: load_insp() if nb.index('current')==0 else load_cl())
        load_insp()
        tk.Label(win,text=FOOTER,bg=BG2,fg='#444466',font=('Arial',7)).pack(side='bottom',fill='x',ipady=3)
