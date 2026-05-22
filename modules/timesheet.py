# Hype ERP - Timesheet Module (timesheet)
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
        CREATE TABLE IF NOT EXISTS timesheets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT,
            project_name TEXT,
            task_name TEXT,
            date TEXT,
            hours REAL DEFAULT 0,
            is_billable INTEGER DEFAULT 1,
            hourly_rate REAL DEFAULT 0,
            billable_amount REAL DEFAULT 0,
            description TEXT,
            status TEXT DEFAULT 'Draft',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit();conn.close()

class TimesheetModule:
    def __init__(self,parent,db_path):
        self.parent=parent;self.db_path=db_path;_init(db_path)

    def open(self):
        win=tk.Toplevel(self.parent);win.title('Hype ERP — Timesheet')
        win.geometry('1100x650');win.configure(bg=BG)
        set_icon(win)
        tk.Label(win,text='⏱ Hype ERP — Timesheet & Billable Hours',
                 font=('Arial',16,'bold'),bg=BG2,fg=ACC).pack(fill='x',ipady=10)

        # Summary bar
        sbar=tk.Frame(win,bg='#0f3460');sbar.pack(fill='x',padx=12,pady=4)
        self._total_lbl=tk.Label(sbar,text='Total: 0h | Billable: ₹0',bg='#0f3460',fg='#2ecc71',font=('Arial',10,'bold'))
        self._total_lbl.pack(side='left',padx=12)

        cols=('ID','Employee','Project','Task','Date','Hours','Billable','Rate/hr','Amount','Status')
        tree=ttk.Treeview(win,columns=cols,show='headings',height=16)
        for c,w in zip(cols,[50,130,150,150,100,70,70,80,90,80]):
            tree.heading(c,text=c);tree.column(c,width=w)
        sb=ttk.Scrollbar(win,orient='vertical',command=tree.yview)
        tree.configure(yscroll=sb.set)
        tree.pack(side='left',fill='both',expand=True,padx=(12,0),pady=6)
        sb.pack(side='right',fill='y',pady=6)

        def load():
            for i in tree.get_children(): tree.delete(i)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            total_h=0;total_amt=0
            try:
                c.execute('SELECT id,employee_name,project_name,task_name,date,hours,is_billable,hourly_rate,billable_amount,status FROM timesheets ORDER BY date DESC')
                for row in c.fetchall():
                    tree.insert('','end',values=(*row[:6],'✅ Yes' if row[6] else 'No',*row[7:]))
                    total_h+=row[5];total_amt+=row[8]
            except: pass
            conn.close()
            self._total_lbl.config(text=f'Total Hours: {total_h:.1f}h | Billable Amount: ₹{total_amt:,.2f}')

        def add_entry():
            d=tk.Toplevel(win);d.title('Add Timesheet Entry');d.geometry('420x460');d.configure(bg=BG)
            set_icon(d)
            tk.Label(d,text='+ Add Timesheet Entry',bg=BG2,fg=ACC,font=('Arial',11,'bold')).pack(fill='x',ipady=8)
            flds=[('Employee Name',tk.StringVar()),('Project',tk.StringVar()),
                  ('Task',tk.StringVar()),('Date',tk.StringVar(value=str(date.today()))),
                  ('Hours',tk.StringVar(value='8')),
                  ('Is Billable (1=Yes/0=No)',tk.StringVar(value='1')),
                  ('Hourly Rate (₹)',tk.StringVar(value='0')),
                  ('Description',tk.StringVar()),('Status',tk.StringVar(value='Confirmed'))]
            for lbl,var in flds:
                tk.Label(d,text=lbl,bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(4,0))
                tk.Entry(d,textvariable=var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            def save():
                vals=[v.get() for _,v in flds]
                try:
                    hrs=float(vals[4]);rate=float(vals[6])
                    amt=hrs*rate if vals[5]=='1' else 0
                    conn=sqlite3.connect(self.db_path)
                    conn.execute('INSERT INTO timesheets (employee_name,project_name,task_name,date,hours,is_billable,hourly_rate,billable_amount,description,status) VALUES (?,?,?,?,?,?,?,?,?,?)',
                                 (vals[0],vals[1],vals[2],vals[3],hrs,int(vals[5]),rate,amt,vals[7],vals[8]))
                    conn.commit();conn.close();load();d.destroy()
                    messagebox.showinfo('Hype ERP','Timesheet entry saved!')
                except Exception as e: messagebox.showerror('Error',str(e))
            tk.Button(d,text='💾 Save',bg=ACC,fg=FG,relief='flat',command=save,padx=14,pady=7,font=('Arial',10,'bold')).pack(pady=10)

        def delete_entry():
            sel=tree.selection()
            if not sel: return
            tid=tree.item(sel[0])['values'][0]
            if messagebox.askyesno('Delete','Delete this timesheet entry?'):
                conn=sqlite3.connect(self.db_path)
                conn.execute('DELETE FROM timesheets WHERE id=?',(tid,))
                conn.commit();conn.close();load()

        bf=tk.Frame(win,bg=BG);bf.pack(side='bottom',pady=6)
        tk.Button(bf,text='+ Add Entry',bg=ACC,fg=FG,relief='flat',command=add_entry,padx=12,pady=5).pack(side='left',padx=4)
        tk.Button(bf,text='🗑 Delete',bg='#c0392b',fg=FG,relief='flat',command=delete_entry,padx=12,pady=5).pack(side='left',padx=4)
        tk.Button(bf,text='🔄 Refresh',bg='#333355',fg=FG,relief='flat',command=load,padx=12,pady=5).pack(side='left',padx=4)
        tk.Label(win,text=FOOTER,bg=BG2,fg='#444466',font=('Arial',7)).pack(side='bottom',fill='x',ipady=3)
        load()
