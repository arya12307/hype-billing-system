# Hype ERP - Asset Management Module (account_asset)
# Developer: David | Nexuzy Lab
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date
from modules.window_utils import set_icon

BG = '#1a1a2e'; BG2 = '#16213e'; ACC = '#e94560'; FG = 'white'
FOOTER = 'Powered by Hype ERP v3.0.0 | Nexuzy Lab | Developer: David'

def _init_asset_table(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("""CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_name TEXT NOT NULL,
        category TEXT,
        purchase_date TEXT,
        purchase_value REAL DEFAULT 0,
        current_value REAL DEFAULT 0,
        depreciation_rate REAL DEFAULT 10,
        location TEXT,
        status TEXT DEFAULT 'Active',
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit(); conn.close()

class AccountAssetModule:
    def __init__(self, parent, db_path):
        self.parent = parent
        self.db_path = db_path
        _init_asset_table(db_path)

    def open(self):
        win = tk.Toplevel(self.parent)
        win.title('Hype ERP — Asset Management')
        win.geometry('1000x620')
        win.configure(bg=BG)
        set_icon(win)
        tk.Label(win, text='🏛 Hype ERP — Fixed Asset Register',
                 font=('Arial',16,'bold'), bg=BG2, fg=ACC).pack(fill='x', ipady=10)

        cols = ('ID','Asset Name','Category','Purchase Date','Purchase Value','Current Value','Depreciation%','Location','Status')
        tree = ttk.Treeview(win, columns=cols, show='headings', height=16)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=110)
        sb = ttk.Scrollbar(win, orient='vertical', command=tree.yview)
        tree.configure(yscroll=sb.set)
        tree.pack(side='left', fill='both', expand=True, padx=(12,0), pady=8)
        sb.pack(side='right', fill='y', pady=8)

        def load():
            for i in tree.get_children(): tree.delete(i)
            conn = sqlite3.connect(self.db_path); c = conn.cursor()
            c.execute("SELECT id,asset_name,category,purchase_date,purchase_value,current_value,depreciation_rate,location,status FROM assets ORDER BY id DESC")
            for row in c.fetchall(): tree.insert('','end',values=row)
            conn.close()

        def add_dialog():
            d = tk.Toplevel(win); d.title('Add Asset'); d.geometry('400x520'); d.configure(bg=BG)
            set_icon(d)
            tk.Label(d, text='+ Add Asset — Hype ERP', bg=BG2, fg=ACC, font=('Arial',12,'bold')).pack(fill='x', ipady=8)
            fields = [('Asset Name',tk.StringVar()),('Category',tk.StringVar(value='Equipment')),
                      ('Purchase Date',tk.StringVar(value=str(date.today()))),
                      ('Purchase Value',tk.StringVar(value='0')),('Current Value',tk.StringVar(value='0')),
                      ('Depreciation %',tk.StringVar(value='10')),('Location',tk.StringVar()),
                      ('Status',tk.StringVar(value='Active')),('Notes',tk.StringVar())]
            for lbl,var in fields:
                tk.Label(d, text=lbl, bg=BG, fg=FG, font=('Arial',9)).pack(anchor='w', padx=18, pady=(4,0))
                tk.Entry(d, textvariable=var, bg=BG2, fg=FG, insertbackground=FG).pack(fill='x', padx=18)
            def save():
                vals = [v.get() for _,v in fields]
                try:
                    conn = sqlite3.connect(self.db_path)
                    conn.execute("INSERT INTO assets (asset_name,category,purchase_date,purchase_value,current_value,depreciation_rate,location,status,notes) VALUES (?,?,?,?,?,?,?,?,?)", vals)
                    conn.commit(); conn.close(); load(); d.destroy()
                    messagebox.showinfo('Hype ERP','Asset added!')
                except Exception as e: messagebox.showerror('Error',str(e))
            tk.Button(d, text='💾 Save', bg=ACC, fg=FG, relief='flat', command=save, padx=14, pady=6, font=('Arial',10,'bold')).pack(pady=12)

        def delete_asset():
            sel = tree.selection()
            if not sel: return
            aid = tree.item(sel[0])['values'][0]
            if messagebox.askyesno('Delete','Delete this asset?'):
                conn = sqlite3.connect(self.db_path)
                conn.execute('DELETE FROM assets WHERE id=?',(aid,)); conn.commit(); conn.close(); load()

        bf = tk.Frame(win, bg=BG); bf.pack(side='bottom', pady=6)
        tk.Button(bf, text='+ Add Asset', bg=ACC, fg=FG, relief='flat', command=add_dialog, padx=12, pady=5).pack(side='left', padx=4)
        tk.Button(bf, text='🗑 Delete', bg='#c0392b', fg=FG, relief='flat', command=delete_asset, padx=12, pady=5).pack(side='left', padx=4)
        tk.Button(bf, text='🔄 Refresh', bg='#333355', fg=FG, relief='flat', command=load, padx=12, pady=5).pack(side='left', padx=4)
        tk.Label(win, text=FOOTER, bg=BG2, fg='#444466', font=('Arial',7)).pack(side='bottom', fill='x', ipady=3)
        load()
