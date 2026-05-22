# Hype ERP - Tax Configuration Module (account_tax)
# Developer: David | Nexuzy Lab
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from modules.window_utils import set_icon

BG = '#1a1a2e'; BG2 = '#16213e'; ACC = '#e94560'; FG = 'white'
FOOTER = 'Powered by Hype ERP v3.0.0 | Nexuzy Lab | Developer: David'

GST_RATES = {
    'Cosmetics':{'SGST':6,'CGST':6,'IGST':12},'Grocery':{'SGST':2.5,'CGST':2.5,'IGST':5},
    'Drinks':{'SGST':6,'CGST':6,'IGST':12},'Electronics':{'SGST':9,'CGST':9,'IGST':18},
    'Clothing':{'SGST':6,'CGST':6,'IGST':12},'Food & Beverage':{'SGST':2.5,'CGST':2.5,'IGST':5},
    'Dairy':{'SGST':2.5,'CGST':2.5,'IGST':5},'Pharmaceuticals':{'SGST':2.5,'CGST':2.5,'IGST':5},
    'Automotive':{'SGST':9,'CGST':9,'IGST':18},'Furniture':{'SGST':12,'CGST':12,'IGST':24},
    'Books':{'SGST':0,'CGST':0,'IGST':0},'Education Services':{'SGST':0,'CGST':0,'IGST':0},
    'Healthcare':{'SGST':0,'CGST':0,'IGST':0},'Agriculture':{'SGST':0,'CGST':0,'IGST':0},
    'Construction':{'SGST':12,'CGST':12,'IGST':24},'Metals':{'SGST':18,'CGST':18,'IGST':36},
    'Chemicals':{'SGST':18,'CGST':18,'IGST':36},'Tobacco':{'SGST':28,'CGST':28,'IGST':56},
    'Services':{'SGST':18,'CGST':18,'IGST':36},'Petroleum Products':{'SGST':0,'CGST':0,'IGST':0},
}

class AccountTaxModule:
    def __init__(self, parent, db_path):
        self.parent = parent
        self.db_path = db_path
        self.tax_data = dict(GST_RATES)  # Make a copy for modifications

    def open(self):
        win = tk.Toplevel(self.parent)
        win.title('Hype ERP — Tax Configuration')
        win.geometry('850x600')
        win.configure(bg=BG)
        set_icon(win)
        tk.Label(win, text='💰 Hype ERP — GST Tax Rate Configuration',
                 font=('Arial',16,'bold'), bg=BG2, fg=ACC).pack(fill='x', ipady=10)
        tk.Label(win, text='All GST rates are India-compliant (CGST+SGST for intra-state, IGST for inter-state)',
                 bg=BG, fg='#aaaacc', font=('Arial',9,'italic')).pack(pady=(4,0))

        cols = ('Category','SGST %','CGST %','IGST %','Total (Intra)','Total (Inter)')
        tree = ttk.Treeview(win, columns=cols, show='headings', height=18)
        for c,w in zip(cols,[200,80,80,80,110,110]):
            tree.heading(c, text=c); tree.column(c, width=w)
        
        # Add scrollbars
        sb = ttk.Scrollbar(win, orient='vertical', command=tree.yview)
        tree.configure(yscroll=sb.set)
        tree.pack(side='left', fill='both', expand=True, padx=12, pady=8)
        sb.pack(side='right', fill='y', pady=8)

        for cat, r in self.tax_data.items():
            tree.insert('','end', values=(cat, r['SGST'], r['CGST'], r['IGST'],
                                          f"{r['SGST']+r['CGST']}%", f"{r['IGST']}%"),
                        tags=('zero',) if r['IGST']==0 else ())
        tree.tag_configure('zero', foreground='#2ecc71')

        # Buttons for Edit and Delete
        btn_frame = tk.Frame(win, bg=BG)
        btn_frame.pack(fill='x', padx=12, pady=6)
        
        def edit_tax():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Select', 'Please select a tax category to edit')
                return
            cat = tree.item(sel[0])['values'][0]
            self._edit_tax_dialog(win, tree, cat)
        
        def delete_tax():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Select', 'Please select a tax category to delete')
                return
            cat = tree.item(sel[0])['values'][0]
            if messagebox.askyesno('Confirm', f'Delete tax configuration for {cat}?'):
                del self.tax_data[cat]
                tree.delete(sel[0])
                messagebox.showinfo('Success', f'Tax configuration deleted for {cat}')
        
        def add_tax():
            self._add_tax_dialog(win, tree)
        
        tk.Button(btn_frame, text='➕ Add Tax Category', bg='#27ae60', fg=FG, relief='flat',
                  command=add_tax, padx=12, pady=5).pack(side='left', padx=4)
        tk.Button(btn_frame, text='✏ Edit Selected', bg='#2980b9', fg=FG, relief='flat',
                  command=edit_tax, padx=12, pady=5).pack(side='left', padx=4)
        tk.Button(btn_frame, text='🗑 Delete Selected', bg='#e74c3c', fg=FG, relief='flat',
                  command=delete_tax, padx=12, pady=5).pack(side='left', padx=4)

        # Summary
        sf = tk.Frame(win, bg=BG2, pady=6); sf.pack(fill='x', padx=12)
        tk.Label(sf, text=f'Total Categories: {len(self.tax_data)}  |  Zero-rated: {sum(1 for r in self.tax_data.values() if r["IGST"]==0)}  |  Highest: 56% (Tobacco)',
                 bg=BG2, fg='#aaaacc', font=('Arial',9)).pack()
        tk.Label(win, text=FOOTER, bg=BG2, fg='#444466', font=('Arial',7)).pack(side='bottom', fill='x', ipady=3)
    
    def _add_tax_dialog(self, parent, tree):
        d = tk.Toplevel(parent)
        d.title('Add Tax Category')
        d.geometry('400x320')
        d.configure(bg=BG)
        set_icon(d)
        
        tk.Label(d, text='Add New Tax Category', font=('Arial', 12, 'bold'), bg=BG, fg=ACC).pack(pady=12)
        
        fields = {}
        for lbl in ['Category Name', 'SGST %', 'CGST %', 'IGST %']:
            tk.Label(d, text=lbl, bg=BG, fg=FG, font=('Arial', 9)).pack(anchor='w', padx=20, pady=(8, 0))
            var = tk.StringVar()
            tk.Entry(d, textvariable=var, bg=BG2, fg=FG, insertbackground=FG).pack(fill='x', padx=20)
            fields[lbl] = var
        
        def save():
            try:
                cat = fields['Category Name'].get()
                if cat in self.tax_data:
                    messagebox.showerror('Error', 'Category already exists')
                    return
                self.tax_data[cat] = {
                    'SGST': float(fields['SGST %'].get()),
                    'CGST': float(fields['CGST %'].get()),
                    'IGST': float(fields['IGST %'].get())
                }
                r = self.tax_data[cat]
                tree.insert('', 'end', values=(cat, r['SGST'], r['CGST'], r['IGST'],
                                               f"{r['SGST']+r['CGST']}%", f"{r['IGST']}%"),
                            tags=('zero',) if r['IGST']==0 else ())
                messagebox.showinfo('Success', f'Tax category {cat} added')
                d.destroy()
            except ValueError:
                messagebox.showerror('Error', 'Please enter valid numbers for tax rates')
        
        tk.Button(d, text='Save', bg=ACC, fg=FG, relief='flat', command=save, padx=14, pady=6).pack(pady=12)
    
    def _edit_tax_dialog(self, parent, tree, category):
        d = tk.Toplevel(parent)
        d.title(f'Edit Tax: {category}')
        d.geometry('400x320')
        d.configure(bg=BG)
        set_icon(d)
        
        tk.Label(d, text=f'Edit Tax Category: {category}', font=('Arial', 12, 'bold'), bg=BG, fg=ACC).pack(pady=12)
        
        current = self.tax_data[category]
        fields = {}
        for lbl, val in [('SGST %', current['SGST']), ('CGST %', current['CGST']), ('IGST %', current['IGST'])]:
            tk.Label(d, text=lbl, bg=BG, fg=FG, font=('Arial', 9)).pack(anchor='w', padx=20, pady=(8, 0))
            var = tk.StringVar(value=str(val))
            tk.Entry(d, textvariable=var, bg=BG2, fg=FG, insertbackground=FG).pack(fill='x', padx=20)
            fields[lbl] = var
        
        def save():
            try:
                self.tax_data[category] = {
                    'SGST': float(fields['SGST %'].get()),
                    'CGST': float(fields['CGST %'].get()),
                    'IGST': float(fields['IGST %'].get())
                }
                # Update tree
                for item in tree.get_children():
                    if tree.item(item)['values'][0] == category:
                        r = self.tax_data[category]
                        tree.item(item, values=(category, r['SGST'], r['CGST'], r['IGST'],
                                               f"{r['SGST']+r['CGST']}%", f"{r['IGST']}%"))
                        break
                messagebox.showinfo('Success', f'Tax category {category} updated')
                d.destroy()
            except ValueError:
                messagebox.showerror('Error', 'Please enter valid numbers for tax rates')
        
        tk.Button(d, text='Save', bg=ACC, fg=FG, relief='flat', command=save, padx=14, pady=6).pack(pady=12)
