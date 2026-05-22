import tkinter as tk
from tkinter import ttk
import webbrowser
from modules.window_utils import set_icon

APP_NAME = "Hype ERP"
APP_VERSION = "3.0.0"
APP_DESCRIPTION = """Hype ERP is a full-featured, offline-first Enterprise Resource Planning
system built with Python. It supports both online (Firebase) and offline
(SQLite) modes with GST-compliant invoices, complete stock management,
dead stock analysis, low stock alerts, sales reporting, HR, Payroll,
CRM, Projects, Manufacturing, POS, and 19+ integrated ERP modules.

Previously known as Hype Billing System — now evolved into a
complete ERP solution for modern businesses."""
APP_AUTHOR = "David"
APP_GITHUB = "https://github.com/david0154/hype-billing-system"
APP_LICENSE = "MIT License"
BRANDING_NOTE = "All invoices, bills, and PDFs are permanently branded as Hype ERP."

MODULES = [
    ("Accounting", "account"),
    ("Invoice", "account_invoice"),
    ("Asset Management", "account_asset"),
    ("Tax", "account_tax"),
    ("Banking", "account_statement"),
    ("Sales", "sale"),
    ("Purchase", "purchase"),
    ("Inventory & Stock", "stock"),
    ("Manufacturing", "production"),
    ("HR", "company_employee"),
    ("Payroll", "payroll"),
    ("CRM", "crm"),
    ("Projects", "project"),
    ("Timesheet", "timesheet"),
    ("POS", "sale_point"),
    ("Shipping", "stock_package"),
    ("Quality Control", "quality_control"),
    ("Marketing", "marketing"),
    ("Reporting & Analytics", "analytic_account"),
]


def show_about(parent=None):
    win = tk.Toplevel(parent) if parent else tk.Tk()
    win.title(f"About {APP_NAME}")
    win.geometry("600x700")
    win.configure(bg="#1a1a2e")
    win.resizable(False, False)
    set_icon(win)

    # Header
    header = tk.Frame(win, bg="#16213e", pady=20)
    header.pack(fill="x")
    tk.Label(header, text="🏢", font=("Arial", 40), bg="#16213e", fg="white").pack()
    tk.Label(header, text=APP_NAME, font=("Arial", 26, "bold"), bg="#16213e", fg="#e94560").pack()
    tk.Label(header, text=f"Version {APP_VERSION}", font=("Arial", 12), bg="#16213e", fg="#a0a0b0").pack()
    tk.Label(header, text="Enterprise Resource Planning System", font=("Arial", 11, "italic"), bg="#16213e", fg="#7a7a9a").pack(pady=(4, 0))

    # Scrollable body
    container = tk.Frame(win, bg="#1a1a2e")
    container.pack(fill="both", expand=True, padx=12, pady=8)

    canvas = tk.Canvas(container, bg="#1a1a2e", highlightthickness=0)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    body = tk.Frame(canvas, bg="#1a1a2e", padx=24, pady=16)
    canvas.create_window((0, 0), window=body, anchor="nw")

    def _on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    body.bind("<Configure>", _on_configure)
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas.bind("<MouseWheel>", _on_mousewheel)
    canvas.bind("<Enter>", lambda e: canvas.focus_set())

    desc_frame = tk.LabelFrame(body, text=" About ", bg="#1a1a2e", fg="#e94560", font=("Arial", 10, "bold"), bd=1, relief="groove")
    desc_frame.pack(fill="x", pady=(0, 12))
    tk.Label(desc_frame, text=APP_DESCRIPTION, bg="#1a1a2e", fg="#c0c0d0", font=("Arial", 9), justify="left", wraplength=520).pack(padx=12, pady=8)

    # Modules
    mod_frame = tk.LabelFrame(body, text=" ERP Modules (19) ", bg="#1a1a2e", fg="#e94560", font=("Arial", 10, "bold"), bd=1, relief="groove")
    mod_frame.pack(fill="x", pady=(0, 12))
    cols = 3
    for i, (name, code) in enumerate(MODULES):
        r, c = divmod(i, cols)
        frm = tk.Frame(mod_frame, bg="#16213e", padx=6, pady=3)
        frm.grid(row=r, column=c, padx=4, pady=2, sticky="ew")
        tk.Label(frm, text=f"● {name}", bg="#16213e", fg="#7fdbff", font=("Arial", 8)).pack(anchor="w")
    for c in range(cols):
        mod_frame.columnconfigure(c, weight=1)

    # Branding
    brand_frame = tk.Frame(body, bg="#2d1b2e", pady=8, padx=12)
    brand_frame.pack(fill="x", pady=(0, 10))
    tk.Label(brand_frame, text="🔒 " + BRANDING_NOTE, bg="#2d1b2e", fg="#ffcc00", font=("Arial", 9, "bold"), wraplength=520).pack()

    # Info
    info_frame = tk.Frame(body, bg="#1a1a2e")
    info_frame.pack(fill="x")
    tk.Label(info_frame, text=f"👨‍💻 Developers: David", bg="#1a1a2e", fg="#00d4ff", font=("Arial", 10, "bold")).pack(anchor="w")
    tk.Label(info_frame, text=f"Email: davidk76011@gmail.com", bg="#1a1a2e", fg="#a0a0b0", font=("Arial", 9)).pack(anchor="w", padx=(20, 0))
    github_label = tk.Label(info_frame, text=f"GitHub: {APP_GITHUB}", bg="#1a1a2e", fg="#a0a0b0", font=("Arial", 9), cursor="hand2")
    github_label.pack(anchor="w", padx=(20, 0))
    tk.Label(info_frame, text=f"Repository: {APP_GITHUB}", bg="#1a1a2e", fg="#a0a0b0", font=("Arial", 9)).pack(anchor="w", padx=(20, 0))
    tk.Label(info_frame, text=f"License: {APP_LICENSE}", bg="#1a1a2e", fg="#a0a0b0", font=("Arial", 9)).pack(anchor="w")

    def open_github(event=None):
        webbrowser.open(APP_GITHUB)

    github_label.bind("<Button-1>", open_github)

    tk.Button(body, text="🌐 View on GitHub", command=open_github,
              bg="#e94560", fg="white", font=("Arial", 10, "bold"),
              relief="flat", padx=16, pady=6, cursor="hand2").pack(pady=(8, 0))
    tk.Button(body, text="Close", command=win.destroy,
              bg="#333355", fg="white", font=("Arial", 9),
              relief="flat", padx=12, pady=4).pack(pady=(6, 0))

    if parent is None:
        win.mainloop()


if __name__ == "__main__":
    show_about()
