# Hype ERP - Vendor Management Module
# Comprehensive vendor master data management
# ✅ CONNECTED TO DATA SERVICE - All vendor data now shared
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date
from modules.scrollable_frame import ScrollableFrame
from modules.window_utils import set_icon
from modules.data_service import get_data_service

BG = '#1a1a2e'
BG2 = '#16213e'
ACC = '#e94560'
FG = 'white'
FOOTER = 'Powered by Hype ERP v3.0.0'

def _init_db(db_path):
    """Initialize vendor tables via DataService"""
    # DataService creates the shared vendors table
    data_service = get_data_service(db_path)
    return data_service

class VendorModule:
    MODULE_NAME = "Vendor Management"
    MODULE_CODE = "vendor"

    def __init__(self, parent, db_path="hype_billing_system.db"):
        self.parent = parent
        self.db_path = db_path
        self.vendor_var = tk.StringVar()
        self.data_service = _init_db(db_path)
        self.data_service.register_module(self.MODULE_NAME, self.MODULE_CODE)

    def open(self):
        """Open vendor management window"""
        win = tk.Toplevel(self.parent)
        win.title('Hype ERP — Vendor Management')
        win.geometry('1200x680')
        win.configure(bg=BG)
        set_icon(win)

        # Header
        hdr = tk.Frame(win, bg=BG2)
        hdr.pack(fill='x')
        tk.Label(hdr, text='👥 Vendor Management', font=('Arial', 16, 'bold'),
                 bg=BG2, fg=ACC).pack(side='left', padx=16, pady=12)
        tk.Label(hdr, text='Manage vendors, credit terms, and payment history',
                 font=('Arial', 9), bg=BG2, fg='#7a7a9a').pack(side='right', padx=16, pady=12)

        # Toolbar
        toolbar = tk.Frame(win, bg=BG, pady=8)
        toolbar.pack(fill='x', padx=12)
        
        def add_vendor():
            self._add_vendor_dialog(win)
        
        def edit_vendor():
            self._edit_vendor_dialog(win, tree)
        
        def delete_vendor():
            self._delete_vendor(win, tree)
        
        def view_bills():
            self._view_vendor_bills(win, tree)

        tk.Button(toolbar, text='+ Add Vendor', bg=ACC, fg=FG, relief='flat',
                  command=add_vendor, padx=12, pady=5, font=('Arial', 9, 'bold')).pack(side='left', padx=4)
        tk.Button(toolbar, text='✏ Edit', bg='#2563eb', fg=FG, relief='flat',
                  command=edit_vendor, padx=12, pady=5, font=('Arial', 9, 'bold')).pack(side='left', padx=4)
        tk.Button(toolbar, text='👤 View Bills', bg='#16a34a', fg=FG, relief='flat',
                  command=view_bills, padx=12, pady=5, font=('Arial', 9, 'bold')).pack(side='left', padx=4)
        tk.Button(toolbar, text='🗑 Delete', bg='#e74c3c', fg=FG, relief='flat',
                  command=delete_vendor, padx=12, pady=5, font=('Arial', 9, 'bold')).pack(side='left', padx=4)

        # Treeview
        cols = ('ID', 'Name', 'Company', 'Email', 'Phone', 'City', 'GSTIN', 'Credit Limit', 'Payment Terms', 'Status')
        frame = tk.Frame(win, bg=BG)
        frame.pack(fill='both', expand=True, padx=12, pady=8)
        
        tree = ttk.Treeview(frame, columns=cols, show='headings', height=20)
        for col, width in zip(cols, [40, 140, 130, 120, 100, 80, 100, 90, 80, 70]):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor='center' if col in ('Credit Limit', 'Payment Terms', 'Status') else 'w')
        
        sb = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscroll=sb.set)
        tree.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')

        def refresh_vendors():
            for i in tree.get_children():
                tree.delete(i)
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute("""SELECT id, name, company, email, phone, city, gstin, credit_limit, payment_terms, status 
                           FROM vendors ORDER BY name""")
                for row in c.fetchall():
                    tag = 'active' if row[9] == 'Active' else 'inactive'
                    tree.insert('', 'end', values=row, tags=(tag,))
                tree.tag_configure('active', foreground='#2ecc71')
                tree.tag_configure('inactive', foreground='#e74c3c')
                conn.close()
            except Exception as e:
                messagebox.showerror('Error', str(e))

        refresh_vendors()
        
        # Store refresh function for dialogs
        self.refresh_vendors = refresh_vendors

    def _add_vendor_dialog(self, parent):
        """Add new vendor dialog"""
        d = tk.Toplevel(parent)
        d.title('Add New Vendor')
        d.geometry('500x700')
        d.configure(bg=BG)
        set_icon(d)

        tk.Label(d, text='+ Add New Vendor', bg=BG2, fg=ACC,
                 font=('Arial', 12, 'bold')).pack(fill='x', ipady=8)

        fields = [
            ('Vendor Name *', 'name', tk.StringVar()),
            ('Company', 'company', tk.StringVar()),
            ('Email', 'email', tk.StringVar()),
            ('Phone *', 'phone', tk.StringVar()),
            ('Address', 'address', tk.StringVar()),
            ('City', 'city', tk.StringVar()),
            ('State', 'state', tk.StringVar()),
            ('Postal Code', 'postal_code', tk.StringVar()),
            ('GSTIN', 'gstin', tk.StringVar()),
            ('PAN', 'pan', tk.StringVar()),
            ('Bank Account', 'bank_account', tk.StringVar()),
            ('Bank Name', 'bank_name', tk.StringVar()),
            ('IFSC Code', 'ifsc_code', tk.StringVar()),
            ('Credit Limit', 'credit_limit', tk.StringVar(value='0.0')),
            ('Payment Terms (days)', 'payment_terms', tk.StringVar(value='30')),
            ('Contact Person', 'contact_person', tk.StringVar()),
            ('Contact Phone', 'contact_phone', tk.StringVar()),
            ('Notes', 'notes', tk.StringVar()),
        ]

        sf = ScrollableFrame(d, bg=BG)
        sf.pack(fill='both', expand=True, padx=12, pady=10)
        frm = sf.scrollable_frame

        field_widgets = {}
        for lbl, key, var in fields:
            tk.Label(frm, text=lbl, bg=BG, fg='#94a3b8',
                    font=('Arial', 9)).pack(anchor='w', pady=(4, 0))
            if key == 'notes':
                entry = tk.Text(frm, bg=BG2, fg=FG, insertbackground=FG,
                               relief='flat', height=4, width=40)
                entry.pack(fill='x', ipady=4, pady=(0, 6))
                field_widgets[key] = entry
            else:
                entry = tk.Entry(frm, textvariable=var, bg=BG2, fg=FG,
                                insertbackground=FG, relief='flat')
                entry.pack(fill='x', ipady=5, pady=(0, 6))
                field_widgets[key] = entry

        def save():
            try:
                values = []
                for lbl, key, var in fields:
                    if key == 'notes':
                        values.append(field_widgets[key].get('1.0', 'end').strip())
                    else:
                        values.append(var.get())
                
                values.append('Active')  # status
                
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute("""INSERT INTO vendors (name, company, email, phone, address, city, state, postal_code,
                           gstin, pan, bank_account, bank_name, ifsc_code, credit_limit, payment_terms,
                           contact_person, contact_phone, notes, status)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", values)
                conn.commit()
                conn.close()
                self.refresh_vendors()
                d.destroy()
                messagebox.showinfo('Success', 'Vendor added successfully.')
            except Exception as e:
                messagebox.showerror('Error', str(e))

        btn_frame = tk.Frame(d, bg=BG)
        btn_frame.pack(fill='x', padx=12, pady=(0, 12))
        tk.Button(btn_frame, text='💾 Save Vendor', bg=ACC, fg=FG, relief='flat',
                  command=save, padx=12, pady=8, font=('Arial', 10, 'bold')).pack(side='right')

    def _edit_vendor_dialog(self, parent, tree):
        """Edit vendor dialog"""
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Select', 'Select a vendor to edit.')
            return
        
        vendor_id = tree.item(sel[0])['values'][0]
        
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,))
            vendor = c.fetchone()
            conn.close()
            
            if not vendor:
                messagebox.showerror('Error', 'Vendor not found.')
                return
        except Exception as e:
            messagebox.showerror('Error', str(e))
            return

        d = tk.Toplevel(parent)
        d.title(f'Edit Vendor: {vendor[1]}')
        d.geometry('500x700')
        d.configure(bg=BG)
        set_icon(d)

        tk.Label(d, text=f'✏ Edit Vendor: {vendor[1]}', bg=BG2, fg=ACC,
                 font=('Arial', 12, 'bold')).pack(fill='x', ipady=8)

        fields = [
            ('Company', 'company', tk.StringVar(value=vendor[3] or '')),
            ('Email', 'email', tk.StringVar(value=vendor[4] or '')),
            ('Phone', 'phone', tk.StringVar(value=vendor[5] or '')),
            ('Address', 'address', tk.StringVar(value=vendor[6] or '')),
            ('City', 'city', tk.StringVar(value=vendor[7] or '')),
            ('State', 'state', tk.StringVar(value=vendor[8] or '')),
            ('Postal Code', 'postal_code', tk.StringVar(value=vendor[9] or '')),
            ('GSTIN', 'gstin', tk.StringVar(value=vendor[10] or '')),
            ('Credit Limit', 'credit_limit', tk.StringVar(value=str(vendor[14] or 0))),
            ('Payment Terms (days)', 'payment_terms', tk.StringVar(value=str(vendor[15] or 30))),
            ('Contact Person', 'contact_person', tk.StringVar(value=vendor[17] or '')),
            ('Notes', 'notes', tk.StringVar(value=vendor[20] or '')),
        ]

        frm = tk.Frame(d, bg=BG)
        frm.pack(fill='both', expand=True, padx=20, pady=10)

        for lbl, key, var in fields:
            tk.Label(frm, text=lbl, bg=BG, fg='#94a3b8',
                    font=('Arial', 9)).pack(anchor='w', pady=(4, 0))
            tk.Entry(frm, textvariable=var, bg=BG2, fg=FG,
                    insertbackground=FG, relief='flat').pack(fill='x', ipady=5, pady=(0, 6))

        def save():
            try:
                updates = {}
                for lbl, key, var in fields:
                    updates[key] = var.get()
                
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values()) + [vendor_id]
                c.execute(f"UPDATE vendors SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
                conn.commit()
                conn.close()
                self.refresh_vendors()
                d.destroy()
                messagebox.showinfo('Hype ERP', 'Vendor updated!')
            except Exception as e:
                messagebox.showerror('Error', str(e))

        tk.Button(d, text='💾 Save Changes', bg=ACC, fg=FG, relief='flat',
                 command=save, padx=14, pady=8, font=('Arial', 10, 'bold')).pack(pady=12)

    def _delete_vendor(self, parent, tree):
        """Delete vendor"""
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Select', 'Select a vendor to delete.')
            return
        
        vendor_name = tree.item(sel[0])['values'][1]
        vendor_id = tree.item(sel[0])['values'][0]
        
        if messagebox.askyesno('Confirm', f'Delete vendor "{vendor_name}"? This cannot be undone.'):
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute("DELETE FROM vendors WHERE id = ?", (vendor_id,))
                conn.commit()
                conn.close()
                self.refresh_vendors()
                messagebox.showinfo('Hype ERP', f'Vendor "{vendor_name}" deleted!')
            except Exception as e:
                messagebox.showerror('Error', str(e))

    def _view_vendor_bills(self, parent, tree):
        """View vendor bills from purchase orders"""
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Select', 'Select a vendor to view bills.')
            return
        
        vendor_id = tree.item(sel[0])['values'][0]
        vendor_name = tree.item(sel[0])['values'][1]
        
        d = tk.Toplevel(parent)
        d.title(f'Vendor Bills: {vendor_name}')
        d.geometry('1000x550')
        d.configure(bg=BG)
        set_icon(d)
        
        # Header
        hdr = tk.Frame(d, bg=BG2)
        hdr.pack(fill='x', ipady=8)
        tk.Label(hdr, text=f'📋 Purchase Bills - {vendor_name}', bg=BG2, fg=ACC,
                 font=('Arial', 12, 'bold')).pack(side='left', padx=16, pady=8)
        
        cols = ('PO#', 'Date', 'Amount', 'Status', 'Notes')
        frame = tk.Frame(d, bg=BG)
        frame.pack(fill='both', expand=True, padx=12, pady=8)
        
        tree_bills = ttk.Treeview(frame, columns=cols, show='headings', height=15)
        for col, width in zip(cols, [120, 100, 120, 100, 300]):
            tree_bills.heading(col, text=col)
            tree_bills.column(col, width=width, anchor='center' if col != 'Notes' else 'w')
        
        sb = ttk.Scrollbar(frame, orient='vertical', command=tree_bills.yview)
        tree_bills.configure(yscroll=sb.set)
        tree_bills.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            # Query from purchase_orders table
            c.execute("""SELECT po_number, date, total, status, notes
                       FROM purchase_orders WHERE vendor_id = ? ORDER BY date DESC""", (vendor_id,))
            for row in c.fetchall():
                tag = 'received' if row[3] == 'Received' else 'pending'
                amount_str = f'₹{float(row[2]):.2f}' if row[2] else '₹0.00'
                tree_bills.insert('', 'end', values=(row[0], row[1], amount_str, row[3], row[4] or ''), tags=(tag,))
            tree_bills.tag_configure('received', foreground='#2ecc71', background='#0a2a0a')
            tree_bills.tag_configure('pending', foreground='#f39c12', background='#2a2a0a')
            conn.close()
        except Exception as e:
            messagebox.showerror('Error', f'Error loading bills: {str(e)}')
        
        # Summary footer
        footer = tk.Frame(d, bg=BG2)
        footer.pack(fill='x', pady=6)
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""SELECT COUNT(*), SUM(total) FROM purchase_orders WHERE vendor_id = ?""", (vendor_id,))
            count, total = c.fetchone()
            total_str = f'₹{float(total):.2f}' if total else '₹0.00'
            tk.Label(footer, text=f'Total Bills: {count} | Total Amount: {total_str}', 
                    bg=BG2, fg=ACC, font=('Arial', 10, 'bold')).pack(padx=16, pady=4)
            conn.close()
        except:
            pass
