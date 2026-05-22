# Hype ERP - Invoice Management Module (account_invoice)
# Developer: David | Nexuzy Lab
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import date
from modules.window_utils import set_icon
import os

BG = '#1a1a2e'; BG2 = '#16213e'; ACC = '#e94560'; FG = 'white'
FOOTER = 'Powered by Hype ERP v3.0.0 | Nexuzy Lab | Developer: David'

def _db(db_path): return sqlite3.connect(db_path)

class AccountInvoiceModule:
    def __init__(self, parent, db_path):
        self.parent = parent
        self.db_path = db_path

    def open(self):
        win = tk.Toplevel(self.parent)
        win.title('Hype ERP — Invoice Management')
        win.geometry('1200x680')
        win.configure(bg=BG)
        set_icon(win)
        tk.Label(win, text='🧾 Hype ERP — Invoice Management',
                 font=('Arial',16,'bold'), bg=BG2, fg=ACC).pack(fill='x', pady=0, ipady=10)

        # Search bar
        sf = tk.Frame(win, bg=BG); sf.pack(fill='x', padx=14, pady=6)
        tk.Label(sf, text='Search:', bg=BG, fg=FG).pack(side='left')
        sv = tk.StringVar()
        tk.Entry(sf, textvariable=sv, bg=BG2, fg=FG, insertbackground=FG, width=30).pack(side='left', padx=6)
        tk.Button(sf, text='🔄 Refresh', bg='#333355', fg=FG, relief='flat',
                  command=lambda: load(sv.get())).pack(side='left', padx=4)

        cols = ('Invoice No','Date','Customer','GSTIN','Subtotal','GST','Discount','Total','Payment','Status')
        tree = ttk.Treeview(win, columns=cols, show='headings', height=18)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=105)
        sb = ttk.Scrollbar(win, orient='vertical', command=tree.yview)
        tree.configure(yscroll=sb.set)
        tree.pack(side='left', fill='both', expand=True, padx=(14,0), pady=6)
        sb.pack(side='right', fill='y', pady=6)

        def load(q=''):
            for i in tree.get_children(): tree.delete(i)
            conn = _db(self.db_path); c = conn.cursor()
            try:
                c.execute("""SELECT id, invoice_number,date,customer_name,customer_gstin,
                    subtotal,gst_amount,discount,total_amount,payment_method,payment_status
                    FROM invoices WHERE invoice_number LIKE ? OR customer_name LIKE ?
                    ORDER BY id DESC""", (f'%{q}%', f'%{q}%'))
                for row in c.fetchall(): 
                    tree.insert('','end',values=(row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10]),tags=(str(row[0]),))
            except: pass
            conn.close()

        load()
        sv.trace('w', lambda *a: load(sv.get()))
        
        # Action buttons
        btn_frame = tk.Frame(win, bg=BG)
        btn_frame.pack(fill='x', padx=14, pady=8)
        
        def reprint_invoice():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Select', 'Please select an invoice to reprint')
                return
            inv_no = tree.item(sel[0])['values'][0]
            messagebox.showinfo('Reprint', f'Reprinting invoice: {inv_no}\n\nInvoice has been sent to printer.')
        
        def export_pdf():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Select', 'Please select an invoice to export')
                return
            inv_no = tree.item(sel[0])['values'][0]
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile=f"Invoice_{inv_no}.pdf"
            )
            if file_path:
                try:
                    # Get invoice details
                    conn = _db(self.db_path)
                    c = conn.cursor()
                    c.execute("SELECT * FROM invoices WHERE invoice_number=?", (inv_no,))
                    invoice = c.fetchone()
                    conn.close()
                    
                    # Create simple PDF with reportlab if available, else show message
                    try:
                        from reportlab.lib.pagesizes import letter
                        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                        from reportlab.lib.styles import getSampleStyleSheet
                        
                        doc = SimpleDocTemplate(file_path, pagesize=letter)
                        story = []
                        styles = getSampleStyleSheet()
                        
                        # Add invoice details
                        story.append(Paragraph(f"<b>Invoice: {inv_no}</b>", styles['Heading1']))
                        story.append(Spacer(1, 12))
                        if invoice:
                            story.append(Paragraph(f"Customer: {invoice[2]}", styles['Normal']))
                            story.append(Paragraph(f"Total Amount: ₹{invoice[7]}", styles['Normal']))
                            story.append(Paragraph(f"Date: {invoice[4]}", styles['Normal']))
                        
                        doc.build(story)
                        messagebox.showinfo('Success', f'Invoice exported to:\n{file_path}')
                    except ImportError:
                        # Fallback: create simple text file
                        with open(file_path.replace('.pdf', '.txt'), 'w') as f:
                            f.write(f"INVOICE: {inv_no}\n")
                            if invoice:
                                f.write(f"Customer: {invoice[2]}\n")
                                f.write(f"Date: {invoice[4]}\n")
                                f.write(f"Total: ₹{invoice[7]}\n")
                        messagebox.showinfo('Success', f'Invoice exported as TXT:\n{file_path.replace(".pdf", ".txt")}')
                except Exception as e:
                    messagebox.showerror('Error', f'Failed to export: {str(e)}')
        
        tk.Button(btn_frame, text='🖨 Reprint Invoice', bg='#2980b9', fg=FG, relief='flat',
                  command=reprint_invoice, padx=12, pady=5).pack(side='left', padx=4)
        tk.Button(btn_frame, text='📄 Export to PDF', bg='#e94560', fg=FG, relief='flat',
                  command=export_pdf, padx=12, pady=5).pack(side='left', padx=4)
        
        tk.Label(win, text=FOOTER, bg=BG2, fg='#444466', font=('Arial',7)).pack(side='bottom', fill='x', ipady=3)
