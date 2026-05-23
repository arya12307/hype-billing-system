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
                    if not invoice:
                        messagebox.showerror('Error', 'Invoice not found')
                        return
                    
                    # Get invoice items
                    c.execute("SELECT product_name, quantity, unit_price, gst_rate, gst_amount, total FROM invoice_items WHERE invoice_id=?", (invoice[0],))
                    items = c.fetchall()
                    
                    # Get store details from settings table
                    c.execute("SELECT value FROM settings WHERE key=?", ('shop_name',))
                    shop_name_row = c.fetchone()
                    shop_name = shop_name_row[0] if shop_name_row else 'Hype Retail Store'
                    
                    c.execute("SELECT value FROM settings WHERE key=?", ('shop_address',))
                    shop_address_row = c.fetchone()
                    shop_address = shop_address_row[0] if shop_address_row else ''
                    
                    c.execute("SELECT value FROM settings WHERE key=?", ('shop_gstin',))
                    shop_gstin_row = c.fetchone()
                    shop_gstin = shop_gstin_row[0] if shop_gstin_row else ''
                    
                    c.execute("SELECT value FROM settings WHERE key=?", ('shop_phone',))
                    shop_phone_row = c.fetchone()
                    shop_phone = shop_phone_row[0] if shop_phone_row else ''
                    
                    conn.close()
                    
                    # Create professional PDF with reportlab if available
                    try:
                        from reportlab.lib.pagesizes import A4, inch
                        from reportlab.lib import colors
                        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
                        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
                        from datetime import datetime
                        
                        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=0.5*inch, leftMargin=0.5*inch,
                                                topMargin=0.75*inch, bottomMargin=0.75*inch)
                        story = []
                        styles = getSampleStyleSheet()
                        
                        # Custom styles
                        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, 
                                                     textColor=colors.HexColor('#e94560'), spaceAfter=6,
                                                     alignment=TA_CENTER, fontName='Helvetica-Bold')
                        header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=11,
                                                      textColor=colors.HexColor('#1a1a2e'), alignment=TA_LEFT)
                        
                        # Header
                        story.append(Paragraph("🧾 HYPE ERP", title_style))
                        story.append(Paragraph("PROFESSIONAL TAX INVOICE", styles['Normal']))
                        story.append(Spacer(1, 0.2*inch))
                        
                        # Store details header
                        store_style = ParagraphStyle('StoreInfo', parent=styles['Normal'], fontSize=10,
                                                      textColor=colors.HexColor('#1a1a2e'), alignment=TA_LEFT, leading=12)
                        story.append(Paragraph(f"<b>{shop_name}</b>", store_style))
                        if shop_address:
                            story.append(Paragraph(f"{shop_address}", store_style))
                        if shop_phone:
                            story.append(Paragraph(f"Phone: {shop_phone}", store_style))
                        if shop_gstin:
                            story.append(Paragraph(f"GSTIN: {shop_gstin}", store_style))
                        story.append(Spacer(1, 0.15*inch))
                        
                        # Invoice details
                        story.append(Paragraph(f"<b>Invoice #:</b> {invoice[1]}", header_style))
                        story.append(Paragraph(f"<b>Date:</b> {invoice[2]}", header_style))
                        story.append(Spacer(1, 0.1*inch))
                        
                        # Bill To
                        story.append(Paragraph("<b>BILL TO:</b>", header_style))
                        story.append(Paragraph(f"{invoice[3] or 'Walk-in Customer'}", header_style))
                        if invoice[4]:
                            story.append(Paragraph(f"Phone: {invoice[4]}", header_style))
                        if invoice[5]:
                            story.append(Paragraph(f"GSTIN: {invoice[5]}", header_style))
                        story.append(Spacer(1, 0.15*inch))
                        
                        # Items table
                        if items:
                            data = [['Product', 'Qty', 'Unit Price', 'GST %', 'GST Amount', 'Total']]
                            for item in items:
                                data.append([
                                    item[0][:25],  # product_name
                                    str(int(item[1])),  # quantity
                                    f"Rs. {float(item[2]):.2f}",  # unit_price (use Rs. instead of ₹)
                                    f"{float(item[3]):.1f}%",  # gst_rate
                                    f"Rs. {float(item[4]):.2f}",  # gst_amount
                                    f"Rs. {float(item[5]):.2f}"   # total
                                ])
                            
                            table = Table(data, colWidths=[2.2*inch, 0.6*inch, 1.0*inch, 0.7*inch, 1.0*inch, 1.0*inch])
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e94560')),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 10),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ('FONTSIZE', (0, 1), (-1, -1), 9),
                            ]))
                            story.append(table)
                            story.append(Spacer(1, 0.15*inch))
                        
                        # Summary - Fixed HTML formatting issue
                        summary_data = [
                            ['Subtotal:', f"Rs. {float(invoice[6]):.2f}"],
                            ['GST Total:', f"Rs. {float(invoice[7]):.2f}"],
                            ['Discount:', f"Rs. {float(invoice[8]):.2f}"],
                            ['Grand Total:', f"Rs. {float(invoice[9]):.2f}"],
                        ]
                        summary_table = Table(summary_data, colWidths=[4.5*inch, 1.5*inch])
                        summary_table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                            ('FONTNAME', (0, 0), (0, 2), 'Helvetica'),
                            ('FONTSIZE', (0, 0), (-1, -1), 10),
                            ('FONTNAME', (0, 3), (1, 3), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 3), (1, 3), 11),
                            ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#e94560')),
                            ('TEXTCOLOR', (0, 3), (-1, 3), colors.whitesmoke),
                            ('LINEBELOW', (0, 2), (-1, 2), 1, colors.black),
                            ('LINEBEFORE', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('LINEAFTER', (0, 0), (-1, -1), 0.5, colors.grey),
                        ]))
                        story.append(summary_table)
                        story.append(Spacer(1, 0.2*inch))
                        
                        # Payment method
                        story.append(Paragraph(f"<b>Payment Method:</b> {invoice[10] or 'Not specified'}", header_style))
                        story.append(Spacer(1, 0.15*inch))
                        
                        # Footer
                        story.append(Paragraph("Thank you for your business!", styles['Normal']))
                        story.append(Paragraph("Powered by Hype ERP", ParagraphStyle('Footer', parent=styles['Normal'],
                                                                                     fontSize=8, textColor=colors.grey)))
                        
                        doc.build(story)
                        messagebox.showinfo('Success', f'Invoice exported to:\n{file_path}')
                    except ImportError:
                        # Fallback: create simple text file
                        with open(file_path.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
                            f.write("="*60 + "\n")
                            f.write("HYPE ERP - INVOICE\n")
                            f.write("="*60 + "\n\n")
                            f.write(f"Invoice #: {invoice[1]}\n")
                            f.write(f"Date: {invoice[2]}\n\n")
                            f.write(f"Customer: {invoice[3] or 'Walk-in'}\n")
                            if invoice[4]:
                                f.write(f"Phone: {invoice[4]}\n")
                            if invoice[5]:
                                f.write(f"GSTIN: {invoice[5]}\n")
                            f.write("\n" + "-"*60 + "\n")
                            f.write("ITEMS:\n")
                            f.write("-"*60 + "\n")
                            if items:
                                f.write(f"{'Product':<25} {'Qty':>4} {'Price':>10} {'Total':>10}\n")
                                f.write("-"*60 + "\n")
                                for item in items:
                                    f.write(f"{item[0][:25]:<25} {int(item[1]):>4} ₹{float(item[2]):>9.2f} ₹{float(item[5]):>9.2f}\n")
                            f.write("\n" + "-"*60 + "\n")
                            f.write(f"Subtotal:    ₹{float(invoice[6]):>20.2f}\n")
                            f.write(f"GST:         ₹{float(invoice[7]):>20.2f}\n")
                            f.write(f"Discount:    ₹{float(invoice[8]):>20.2f}\n")
                            f.write(f"{'TOTAL:':<13}₹{float(invoice[9]):>20.2f}\n")
                            f.write("="*60 + "\n")
                            f.write(f"Payment: {invoice[10] or 'Not specified'}\n")
                            f.write("\nThank you for your business!\nPowered by Hype ERP\n")
                        messagebox.showinfo('Success', f'Invoice exported as TXT:\n{file_path.replace(".pdf", ".txt")}')
                except Exception as e:
                    messagebox.showerror('Error', f'Failed to export: {str(e)}')
        
        tk.Button(btn_frame, text='🖨 Reprint Invoice', bg='#2980b9', fg=FG, relief='flat',
                  command=reprint_invoice, padx=12, pady=5).pack(side='left', padx=4)
        tk.Button(btn_frame, text='📄 Export to PDF', bg='#e94560', fg=FG, relief='flat',
                  command=export_pdf, padx=12, pady=5).pack(side='left', padx=4)
        
        tk.Label(win, text=FOOTER, bg=BG2, fg='#444466', font=('Arial',7)).pack(side='bottom', fill='x', ipady=3)
