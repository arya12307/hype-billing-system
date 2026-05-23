# Hype ERP - HSN Code Configuration Module
# Developer: David | Nexuzy Lab
# Automatically assigns HSN codes to product categories for GST compliance

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from modules.window_utils import set_icon

BG = '#1a1a2e'
BG2 = '#16213e'
ACC = '#e94560'
FG = 'white'
FOOTER = 'Powered by Hype ERP v3.0.0 | Nexuzy Lab | Developer: David'

# Default HSN Codes for Indian Product Categories (as per GST)
DEFAULT_HSN_MAPPING = {
    'Cosmetics': '3304',
    'Grocery': '0901',
    'Drinks': '2202',
    'Electronics': '8471',
    'Clothing': '6201',
    'Food & Beverage': '1905',
    'Dairy': '0401',
    'Pharmaceuticals': '3004',
    'Automotive': '8704',
    'Furniture': '9403',
    'Books': '4901',
    'Education Services': '9209',
    'Healthcare': '6211',
    'Agriculture': '1001',
    'Construction': '6810',
    'Metals': '7208',
    'Chemicals': '2817',
    'Tobacco': '2402',
    'Services': '9999',
    'Petroleum Products': '2710',
}

class HSNConfigModule:
    def __init__(self, parent, db_path="hype_billing_system.db"):
        self.parent = parent
        self.db_path = db_path
        self.hsn_data = dict(DEFAULT_HSN_MAPPING)
        self._init_db()
        self._load_hsn_config()

    def _init_db(self):
        """Initialize HSN configuration table"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS category_hsn_mapping (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT UNIQUE NOT NULL,
                    hsn_code TEXT NOT NULL,
                    description TEXT,
                    gst_rate REAL DEFAULT 18.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error initializing HSN database: {e}")

    def _load_hsn_config(self):
        """Load HSN configuration from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT category, hsn_code FROM category_hsn_mapping")
            for row in c.fetchall():
                self.hsn_data[row[0]] = row[1]
            conn.close()
        except Exception:
            pass

    def _save_to_db(self, category, hsn_code, description='', gst_rate=18.0):
        """Save HSN mapping to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO category_hsn_mapping 
                (category, hsn_code, description, gst_rate)
                VALUES (?, ?, ?, ?)
            """, (category, hsn_code, description, gst_rate))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Database error: {e}")
            return False

    def get_hsn_for_category(self, category):
        """Get HSN code for a specific category"""
        return self.hsn_data.get(category, '')

    def open(self):
        """Open HSN Configuration Window"""
        win = tk.Toplevel(self.parent)
        win.title('Hype ERP — HSN Code Configuration')
        win.geometry('950x650')
        win.configure(bg=BG)
        set_icon(win)

        # Header
        tk.Label(win, text='🔧 Hype ERP — HSN Code Configuration by Category',
                 font=('Arial', 16, 'bold'), bg=BG2, fg=ACC).pack(fill='x', ipady=10)
        tk.Label(win, text='Automatically assign HSN codes to all product categories for GST compliance',
                 bg=BG, fg='#aaaacc', font=('Arial', 9, 'italic')).pack(pady=(4, 0))

        # Tree view
        cols = ('Category', 'HSN Code', 'Description', 'GST Rate')
        tree = ttk.Treeview(win, columns=cols, show='headings', height=18)
        for c, w in zip(cols, [280, 150, 350, 100]):
            tree.heading(c, text=c)
            tree.column(c, width=w)

        # Scrollbars
        sb = ttk.Scrollbar(win, orient='vertical', command=tree.yview)
        hsb = ttk.Scrollbar(win, orient='horizontal', command=tree.xview)
        tree.configure(yscroll=sb.set, xscroll=hsb.set)
        tree.pack(side='left', fill='both', expand=True, padx=12, pady=8)
        sb.pack(side='right', fill='y', pady=8)
        hsb.pack(side='bottom', fill='x', padx=12)

        # Load HSN data
        self._refresh_tree(tree)

        # Buttons
        btn_frame = tk.Frame(win, bg=BG)
        btn_frame.pack(fill='x', padx=12, pady=6)

        def edit_hsn():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Select', 'Please select a category to edit')
                return
            cat = tree.item(sel[0])['values'][0]
            self._edit_hsn_dialog(win, tree, cat)

        def add_hsn():
            self._add_hsn_dialog(win, tree)

        def delete_hsn():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Select', 'Please select a category to delete')
                return
            cat = tree.item(sel[0])['values'][0]
            if messagebox.askyesno('Confirm', f'Remove HSN mapping for {cat}?'):
                try:
                    conn = sqlite3.connect(self.db_path)
                    c = conn.cursor()
                    c.execute("DELETE FROM category_hsn_mapping WHERE category = ?", (cat,))
                    conn.commit()
                    conn.close()
                    del self.hsn_data[cat]
                    tree.delete(sel[0])
                    messagebox.showinfo('Success', f'HSN mapping deleted for {cat}')
                except Exception as e:
                    messagebox.showerror('Error', str(e))

        def apply_to_products():
            """Apply HSN codes to all products based on category"""
            if messagebox.askyesno('Confirm', 'Apply HSN codes to all products matching their categories?\n\nThis will update products WITHOUT explicit HSN codes.'):
                try:
                    conn = sqlite3.connect(self.db_path)
                    c = conn.cursor()
                    c.execute("SELECT id, category FROM products WHERE hsn_code IS NULL OR hsn_code = ''")
                    products = c.fetchall()
                    count = 0
                    for prod_id, category in products:
                        hsn = self.get_hsn_for_category(category)
                        if hsn:
                            c.execute("UPDATE products SET hsn_code = ? WHERE id = ?", (hsn, prod_id))
                            count += 1
                    conn.commit()
                    conn.close()
                    messagebox.showinfo('Success', f'Applied HSN codes to {count} products!')
                except Exception as e:
                    messagebox.showerror('Error', str(e))

        def reset_to_defaults():
            """Reset HSN configuration to default values"""
            if messagebox.askyesno('Confirm', 'Reset HSN codes to default mapping?\n\nThis will replace all custom HSN codes.'):
                try:
                    conn = sqlite3.connect(self.db_path)
                    c = conn.cursor()
                    c.execute("DELETE FROM category_hsn_mapping")
                    for category, hsn in DEFAULT_HSN_MAPPING.items():
                        c.execute("""
                            INSERT INTO category_hsn_mapping (category, hsn_code)
                            VALUES (?, ?)
                        """, (category, hsn))
                    conn.commit()
                    conn.close()
                    self.hsn_data = dict(DEFAULT_HSN_MAPPING)
                    self._refresh_tree(tree)
                    messagebox.showinfo('Success', 'HSN configuration reset to defaults!')
                except Exception as e:
                    messagebox.showerror('Error', str(e))

        tk.Button(btn_frame, text='➕ Add Category HSN', bg='#27ae60', fg=FG, relief='flat',
                  command=add_hsn, padx=12, pady=5).pack(side='left', padx=4)
        tk.Button(btn_frame, text='✏ Edit Selected', bg='#2980b9', fg=FG, relief='flat',
                  command=edit_hsn, padx=12, pady=5).pack(side='left', padx=4)
        tk.Button(btn_frame, text='🗑 Delete Selected', bg='#e74c3c', fg=FG, relief='flat',
                  command=delete_hsn, padx=12, pady=5).pack(side='left', padx=4)
        tk.Button(btn_frame, text='⚡ Apply to Products', bg='#f39c12', fg=FG, relief='flat',
                  command=apply_to_products, padx=12, pady=5).pack(side='left', padx=4)
        tk.Button(btn_frame, text='🔄 Reset Defaults', bg='#95a5a6', fg=FG, relief='flat',
                  command=reset_to_defaults, padx=12, pady=5).pack(side='left', padx=4)

        # Summary
        sf = tk.Frame(win, bg=BG2, pady=6)
        sf.pack(fill='x', padx=12)
        tk.Label(sf, text=f'Total Categories: {len(self.hsn_data)}  |  HSN codes configured for automatic product assignment',
                 bg=BG2, fg='#aaaacc', font=('Arial', 9)).pack()

        tk.Label(win, text=FOOTER, bg=BG2, fg='#444466', font=('Arial', 7)).pack(side='bottom', fill='x', ipady=3)

    def _refresh_tree(self, tree):
        """Refresh tree view with current HSN data"""
        for i in tree.get_children():
            tree.delete(i)
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                SELECT category, hsn_code, description, gst_rate 
                FROM category_hsn_mapping 
                ORDER BY category
            """)
            for row in c.fetchall():
                tree.insert('', 'end', values=(row[0], row[1], row[2] or '', f"{row[3]}%"))
            conn.close()
        except Exception:
            pass

    def _add_hsn_dialog(self, parent, tree):
        """Dialog to add new HSN mapping"""
        d = tk.Toplevel(parent)
        d.title('Add HSN Code Mapping')
        d.geometry('450x300')
        d.configure(bg=BG)
        set_icon(d)

        tk.Label(d, text='Add Category HSN Code Mapping', font=('Arial', 12, 'bold'),
                 bg=BG2, fg=ACC).pack(fill='x', ipady=8)

        frm = tk.Frame(d, bg=BG)
        frm.pack(padx=20, pady=20, fill='both', expand=True)

        fields = [
            ('Category Name', 'category'),
            ('HSN Code (8-digit)', 'hsn'),
            ('Description', 'desc'),
            ('GST Rate (%)', 'gst'),
        ]

        vars = {}
        for lbl, key in fields:
            tk.Label(frm, text=lbl, bg=BG, fg='#94a3b8', font=('Arial', 10)).pack(anchor='w', pady=(10, 2))
            if key == 'desc':
                e = tk.Text(frm, bg=BG2, fg=FG, height=3, font=('Arial', 9))
                e.pack(fill='x', ipady=4)
                vars[key] = e
            else:
                e = tk.Entry(frm, bg=BG2, fg=FG, font=('Arial', 10))
                e.pack(fill='x', ipady=4)
                vars[key] = e

        def save():
            cat = vars['category'].get().strip()
            hsn = vars['hsn'].get().strip()
            desc = vars['desc'].get('1.0', 'end').strip() if isinstance(vars['desc'], tk.Text) else ''
            try:
                gst = float(vars['gst'].get() or '18.0')
            except:
                gst = 18.0

            if not cat or not hsn:
                messagebox.showwarning('Missing', 'Category and HSN code are required', parent=d)
                return

            if len(hsn) != 4 or not hsn.isdigit():
                messagebox.showwarning('Invalid', 'HSN code must be exactly 4 digits', parent=d)
                return

            if self._save_to_db(cat, hsn, desc, gst):
                self.hsn_data[cat] = hsn
                self._refresh_tree(tree)
                d.destroy()
                messagebox.showinfo('Success', f'HSN code added for {cat}')
            else:
                messagebox.showerror('Error', 'Failed to save HSN mapping')

        def cancel():
            d.destroy()

        tk.Button(frm, text='Save', bg='#27ae60', fg=FG, relief='flat', command=save, pady=8).pack(fill='x', pady=(20, 4))
        tk.Button(frm, text='Cancel', bg='#95a5a6', fg=FG, relief='flat', command=cancel, pady=8).pack(fill='x')

    def _edit_hsn_dialog(self, parent, tree, category):
        """Dialog to edit HSN mapping"""
        d = tk.Toplevel(parent)
        d.title('Edit HSN Code Mapping')
        d.geometry('450x300')
        d.configure(bg=BG)
        set_icon(d)

        tk.Label(d, text='Edit HSN Code Mapping', font=('Arial', 12, 'bold'),
                 bg=BG2, fg=ACC).pack(fill='x', ipady=8)

        frm = tk.Frame(d, bg=BG)
        frm.pack(padx=20, pady=20, fill='both', expand=True)

        # Get current data
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT category, hsn_code, description, gst_rate FROM category_hsn_mapping WHERE category = ?", (category,))
            row = c.fetchone()
            conn.close()
            if row:
                cat, hsn, desc, gst = row
            else:
                cat, hsn, desc, gst = category, '', '', 18.0
        except:
            cat, hsn, desc, gst = category, '', '', 18.0

        tk.Label(frm, text='Category Name', bg=BG, fg='#94a3b8', font=('Arial', 10)).pack(anchor='w', pady=(10, 2))
        cat_entry = tk.Entry(frm, bg=BG2, fg=FG, font=('Arial', 10))
        cat_entry.insert(0, cat)
        cat_entry.config(state='readonly')
        cat_entry.pack(fill='x', ipady=4)

        tk.Label(frm, text='HSN Code (8-digit)', bg=BG, fg='#94a3b8', font=('Arial', 10)).pack(anchor='w', pady=(10, 2))
        hsn_entry = tk.Entry(frm, bg=BG2, fg=FG, font=('Arial', 10))
        hsn_entry.insert(0, hsn)
        hsn_entry.pack(fill='x', ipady=4)

        tk.Label(frm, text='Description', bg=BG, fg='#94a3b8', font=('Arial', 10)).pack(anchor='w', pady=(10, 2))
        desc_text = tk.Text(frm, bg=BG2, fg=FG, height=3, font=('Arial', 9))
        desc_text.insert('1.0', desc or '')
        desc_text.pack(fill='x', ipady=4)

        tk.Label(frm, text='GST Rate (%)', bg=BG, fg='#94a3b8', font=('Arial', 10)).pack(anchor='w', pady=(10, 2))
        gst_entry = tk.Entry(frm, bg=BG2, fg=FG, font=('Arial', 10))
        gst_entry.insert(0, str(gst))
        gst_entry.pack(fill='x', ipady=4)

        def save():
            new_hsn = hsn_entry.get().strip()
            new_desc = desc_text.get('1.0', 'end').strip()
            try:
                new_gst = float(gst_entry.get() or '18.0')
            except:
                new_gst = 18.0

            if not new_hsn:
                messagebox.showwarning('Missing', 'HSN code is required', parent=d)
                return

            if len(new_hsn) != 4 or not new_hsn.isdigit():
                messagebox.showwarning('Invalid', 'HSN code must be exactly 4 digits', parent=d)
                return

            if self._save_to_db(cat, new_hsn, new_desc, new_gst):
                self.hsn_data[cat] = new_hsn
                self._refresh_tree(tree)
                d.destroy()
                messagebox.showinfo('Success', f'HSN code updated for {cat}')
            else:
                messagebox.showerror('Error', 'Failed to update HSN mapping')

        def cancel():
            d.destroy()

        tk.Button(frm, text='Update', bg='#2980b9', fg=FG, relief='flat', command=save, pady=8).pack(fill='x', pady=(20, 4))
        tk.Button(frm, text='Cancel', bg='#95a5a6', fg=FG, relief='flat', command=cancel, pady=8).pack(fill='x')
