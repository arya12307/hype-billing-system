# Hype ERP - Bank Statement / Banking Module (account_statement)
# Developer: David | Nexuzy Lab
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date
from modules.window_utils import set_icon

BG = '#1a1a2e'; BG2 = '#16213e'; ACC = '#e94560'; FG = 'white'
FOOTER = 'Powered by Hype ERP v3.0.0 | Nexuzy Lab | Developer: David'

def _init_bank_tables(db_path):
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS bank_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_name TEXT NOT NULL,
            bank_name TEXT,
            account_number TEXT,
            ifsc_code TEXT,
            opening_balance REAL DEFAULT 0,
            current_balance REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS bank_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            date TEXT,
            description TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            reference TEXT,
            reconciled INTEGER DEFAULT 0
        );
    """)
    conn.commit(); conn.close()

class AccountStatementModule:
    def __init__(self, parent, db_path):
        self.parent = parent
        self.db_path = db_path
        _init_bank_tables(db_path)

    def open(self):
        win = tk.Toplevel(self.parent)
        win.title('Hype ERP — Banking & Bank Statements')
        win.geometry('1100x650')
        win.configure(bg=BG)
        set_icon(win)
        tk.Label(win, text='🏦 Hype ERP — Banking & Bank Statement Reconciliation',
                 font=('Arial',16,'bold'), bg=BG2, fg=ACC).pack(fill='x', ipady=10)

        paned = tk.PanedWindow(win, orient='horizontal', bg=BG)
        paned.pack(fill='both', expand=True, padx=10, pady=8)

        # Left: bank accounts
        left = tk.Frame(paned, bg=BG2, width=280)
        paned.add(left)
        tk.Label(left, text='Bank Accounts', bg=BG2, fg=ACC, font=('Arial',11,'bold')).pack(pady=8)
        acc_list = tk.Listbox(left, bg='#0f3460', fg=FG, font=('Arial',10),
                              selectbackground=ACC, height=20)
        acc_list.pack(fill='both', expand=True, padx=8, pady=4)

        # Right: transactions
        right = tk.Frame(paned, bg=BG)
        paned.add(right)
        tk.Label(right, text='Transactions', bg=BG, fg=FG, font=('Arial',10,'bold')).pack(pady=4)
        cols = ('ID','Date','Description','Debit','Credit','Balance','Reference','Reconciled')
        txn_tree = ttk.Treeview(right, columns=cols, show='headings', height=18)
        for c,w in zip(cols,[50,100,200,90,90,90,100,90]):
            txn_tree.heading(c,text=c); txn_tree.column(c,width=w)
        txn_tree.pack(fill='both', expand=True, padx=6, pady=4)

        def load_accounts():
            acc_list.delete(0,'end')
            conn = sqlite3.connect(self.db_path); c = conn.cursor()
            c.execute('SELECT id,account_name,current_balance FROM bank_accounts')
            self._accounts = c.fetchall()
            for row in self._accounts:
                acc_list.insert('end', f"{row[1]} | ₹{row[2]:,.2f}")
            conn.close()

        def load_transactions(evt=None):
            sel = acc_list.curselection()
            if not sel or not hasattr(self,'_accounts'): return
            aid = self._accounts[sel[0]][0]
            for i in txn_tree.get_children(): txn_tree.delete(i)
            conn = sqlite3.connect(self.db_path); c = conn.cursor()
            c.execute('SELECT id,date,description,debit,credit,balance,reference,reconciled FROM bank_transactions WHERE account_id=? ORDER BY date DESC',(aid,))
            for row in c.fetchall():
                txn_tree.insert('','end',values=(*row[:7], '✅' if row[7] else '❌'))
            conn.close()

        acc_list.bind('<<ListboxSelect>>', load_transactions)

        def add_account():
            d = tk.Toplevel(win); d.title('Add Bank Account'); d.geometry('380x380'); d.configure(bg=BG)
            set_icon(d)
            tk.Label(d, text='+ Add Bank Account', bg=BG2, fg=ACC, font=('Arial',11,'bold')).pack(fill='x',ipady=8)
            flds = [('Account Name',tk.StringVar()),('Bank Name',tk.StringVar()),
                    ('Account Number',tk.StringVar()),('IFSC Code',tk.StringVar()),
                    ('Opening Balance',tk.StringVar(value='0'))]
            for lbl,var in flds:
                tk.Label(d,text=lbl,bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(4,0))
                tk.Entry(d,textvariable=var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            def save():
                try:
                    vals = [v.get() for _,v in flds]
                    conn = sqlite3.connect(self.db_path)
                    conn.execute('INSERT INTO bank_accounts (account_name,bank_name,account_number,ifsc_code,opening_balance,current_balance) VALUES (?,?,?,?,?,?)',
                                 (*vals[:4], float(vals[4]), float(vals[4])))
                    conn.commit(); conn.close(); load_accounts(); d.destroy()
                except Exception as e: messagebox.showerror('Error',str(e))
            tk.Button(d,text='💾 Save',bg=ACC,fg=FG,relief='flat',command=save,padx=14,pady=6).pack(pady=12)

        def add_transaction():
            sel = acc_list.curselection()
            if not sel: messagebox.showwarning('Select','Select a bank account first.'); return
            aid = self._accounts[sel[0]][0]
            d = tk.Toplevel(win); d.title('Add Transaction'); d.geometry('380x360'); d.configure(bg=BG)
            set_icon(d)
            tk.Label(d,text='+ Add Transaction',bg=BG2,fg=ACC,font=('Arial',11,'bold')).pack(fill='x',ipady=8)
            flds = [('Date',tk.StringVar(value=str(date.today()))),('Description',tk.StringVar()),
                    ('Debit',tk.StringVar(value='0')),('Credit',tk.StringVar(value='0')),
                    ('Reference',tk.StringVar())]
            for lbl,var in flds:
                tk.Label(d,text=lbl,bg=BG,fg=FG,font=('Arial',9)).pack(anchor='w',padx=16,pady=(4,0))
                tk.Entry(d,textvariable=var,bg=BG2,fg=FG,insertbackground=FG).pack(fill='x',padx=16)
            def save():
                try:
                    vals=[v.get() for _,v in flds]
                    debit,credit=float(vals[2]),float(vals[3])
                    conn=sqlite3.connect(self.db_path); c=conn.cursor()
                    c.execute('SELECT current_balance FROM bank_accounts WHERE id=?',(aid,))
                    bal=c.fetchone()[0]+credit-debit
                    c.execute('INSERT INTO bank_transactions (account_id,date,description,debit,credit,balance,reference) VALUES (?,?,?,?,?,?,?)',
                               (aid,vals[0],vals[1],debit,credit,bal,vals[4]))
                    c.execute('UPDATE bank_accounts SET current_balance=? WHERE id=?',(bal,aid))
                    conn.commit(); conn.close(); load_accounts(); load_transactions(); d.destroy()
                except Exception as e: messagebox.showerror('Error',str(e))
            tk.Button(d,text='💾 Save',bg=ACC,fg=FG,relief='flat',command=save,padx=14,pady=6).pack(pady=12)

        bf=tk.Frame(win,bg=BG); bf.pack(side='bottom',pady=6)
        tk.Button(bf,text='+ Add Account',bg=ACC,fg=FG,relief='flat',command=add_account,padx=10,pady=5).pack(side='left',padx=4)
        tk.Button(bf,text='+ Add Transaction',bg='#27ae60',fg=FG,relief='flat',command=add_transaction,padx=10,pady=5).pack(side='left',padx=4)
        tk.Button(bf,text='🔄 Refresh',bg='#333355',fg=FG,relief='flat',command=load_accounts,padx=10,pady=5).pack(side='left',padx=4)
        tk.Label(win,text=FOOTER,bg=BG2,fg='#444466',font=('Arial',7)).pack(side='bottom',fill='x',ipady=3)
        load_accounts()
