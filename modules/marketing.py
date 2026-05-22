# Hype ERP - Marketing Module (marketing)
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
        CREATE TABLE IF NOT EXISTS marketing_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_name TEXT NOT NULL,
            type TEXT DEFAULT 'Email',
            status TEXT DEFAULT 'Draft',
            start_date TEXT,
            end_date TEXT,
            budget REAL DEFAULT 0,
            spent REAL DEFAULT 0,
            target_audience TEXT,
            reach INTEGER DEFAULT 0,
            conversions INTEGER DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit();conn.close()

class MarketingModule:
    def __init__(self,parent,db_path):
        self.parent=parent;self.db_path=db_path;_init(db_path)

    def open(self):
        win=tk.Toplevel(self.parent);win.title('Hype ERP — Marketing')
        win.geometry('1050x620');win.configure(bg=BG)
        set_icon(win)
        tk.Label(win,text='📣 Hype ERP — Marketing Campaigns',
                 font=('Arial',16,'bold'),bg=BG2,fg=ACC).pack(fill='x',ipady=10)

        cols=('ID','Campaign','Type','Status','Start','End','Budget','Spent','Audience','Reach','Conversions')
        tree=ttk.Treeview(win,columns=cols,show='headings',height=16)
        for c,w in zip(cols,[40,160,80,80,100,100,90,90,120,70,90]):
            tree.heading(c,text=c);tree.column(c,width=w)
        sb=ttk.Scrollbar(win,orient='vertical',command=tree.yview)
        tree.configure(yscroll=sb.set)
        tree.pack(side='left',fill='both',expand=True,padx=(12,0),pady=8)
        sb.pack(side='right',fill='y',pady=8)

        def load():
            for i in tree.get_children(): tree.delete(i)
            conn=sqlite3.connect(self.db_path);c=conn.cursor()
            try:
                c.execute('SELECT id,campaign_name,type,status,start_date,end_date,budget,spent,target_audience,reach,conversions FROM marketing_campaigns ORDER BY id DESC')
                for row in c.fetchall():
                    tree.insert('','end',values=row,tags=('active',) if row[3]=='Active' else ())
            except: pass
            conn.close()
            tree.tag_configure('active',foreground='#2ecc71')

        def new_campaign():
            d=tk.Toplevel(win);d.title('New Campaign');d.geometry('420x520');d.configure(bg=BG)
            set_icon(d)
            tk.Label(d,text='📣 New Marketing Campaign',bg=BG2,fg=ACC,font=('Arial',11,'bold')).pack(fill='x',ipady=8)
            flds=[('Campaign Name',tk.StringVar()),
                  ('Type',tk.StringVar(value='Email')),
                  ('Status',tk.StringVar(value='Active')),
                  ('Start Date',tk.StringVar(value=str(date.today()))),
                  ('End Date',tk.StringVar()),
                  ('Budget',tk.StringVar(value='0')),
                  ('Spent',tk.StringVar(value='0')),
                  ('Target Audience',tk.StringVar()),
                  ('Expected Reach',tk.StringVar(value='0')),
                  ('Notes',tk.StringVar())]
            for lbl,var in flds:
                tk.Label(d,text=lbl,bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(4,0))
                tk.Entry(d,textvariable=var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            def save():
                vals=[v.get() for _,v in flds]
                try:
                    conn=sqlite3.connect(self.db_path)
                    conn.execute('INSERT INTO marketing_campaigns (campaign_name,type,status,start_date,end_date,budget,spent,target_audience,reach,notes) VALUES (?,?,?,?,?,?,?,?,?,?)',vals)
                    conn.commit();conn.close();load();d.destroy()
                    messagebox.showinfo('Hype ERP','Campaign created!')
                except Exception as e: messagebox.showerror('Error',str(e))
            tk.Button(d,text='💾 Save',bg=ACC,fg=FG,relief='flat',command=save,padx=14,pady=7,font=('Arial',10,'bold')).pack(pady=10)

        def delete_campaign():
            sel=tree.selection()
            if not sel: return
            cid=tree.item(sel[0])['values'][0]
            if messagebox.askyesno('Delete','Delete this campaign?'):
                conn=sqlite3.connect(self.db_path)
                conn.execute('DELETE FROM marketing_campaigns WHERE id=?',(cid,))
                conn.commit();conn.close();load()

        bf=tk.Frame(win,bg=BG);bf.pack(side='bottom',pady=6)
        tk.Button(bf,text='+ New Campaign',bg=ACC,fg=FG,relief='flat',command=new_campaign,padx=12,pady=5).pack(side='left',padx=4)
        tk.Button(bf,text='🗑 Delete',bg='#c0392b',fg=FG,relief='flat',command=delete_campaign,padx=12,pady=5).pack(side='left',padx=4)
        tk.Button(bf,text='🔄 Refresh',bg='#333355',fg=FG,relief='flat',command=load,padx=12,pady=5).pack(side='left',padx=4)
        tk.Label(win,text=FOOTER,bg=BG2,fg='#444466',font=('Arial',7)).pack(side='bottom',fill='x',ipady=3)
        load()
