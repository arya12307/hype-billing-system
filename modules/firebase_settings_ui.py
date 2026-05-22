# ===========================================================================
# Hype ERP v3.0.0 - Firebase Settings UI
# In-app GUI window to configure Firebase (no manual code editing needed)
# Open from: Settings → Firebase Setup
# Developer: David | Nexuzy Lab
# ===========================================================================
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import os
from modules.window_utils import set_icon

BG  = '#1a1a2e'
BG2 = '#16213e'
BG3 = '#0f3460'
ACC = '#e94560'
GRN = '#27ae60'
FG  = 'white'
FOOTER = 'Powered by Hype ERP v3.0.0 | Nexuzy Lab | Developer: David'


class FirebaseSettingsUI:
    """
    Full GUI window for Firebase configuration.
    Reads / writes to firebase_config.py (firebase_runtime_config.json).
    """

    def __init__(self, parent):
        self.parent = parent

    def open(self):
        try:
            import firebase_config as fc
        except ImportError:
            messagebox.showerror('Error', 'firebase_config.py not found!')
            return

        cfg = fc.load_config()

        win = tk.Toplevel(self.parent)
        win.title('Hype ERP — Firebase Setup')
        win.geometry('680x620')
        win.configure(bg=BG)
        set_icon(win)
        win.resizable(True, True)
        win.focus_set()

        # ─ Header
        hdr = tk.Frame(win, bg=BG2, pady=12)
        hdr.pack(fill='x')
        tk.Label(hdr, text='🔥  Firebase Setup',
                 font=('Arial', 17, 'bold'), bg=BG2, fg=ACC).pack(side='left', padx=20)
        tk.Label(hdr, text='Configure once — works everywhere',
                 font=('Arial', 9, 'italic'), bg=BG2, fg='#7a7aaa').pack(side='right', padx=20)

        # ─ Status badge
        status_color = GRN if fc.is_enabled() else '#c0392b'
        status_text  = '✅  Firebase CONNECTED' if fc.is_enabled() else '❌  Firebase NOT configured'
        tk.Label(win, text=status_text,
                 bg=status_color, fg=FG,
                 font=('Arial', 10, 'bold')).pack(fill='x', ipady=6)

        # ─ Form
        form = tk.Frame(win, bg=BG, padx=30, pady=10)
        form.pack(fill='both', expand=True)

        fields   = {}
        row_idx  = 0

        def add_field(label, key, placeholder='', browse=False):
            nonlocal row_idx
            tk.Label(form, text=label,
                     bg=BG, fg='#aaaacc',
                     font=('Arial', 9, 'bold')
                     ).grid(row=row_idx, column=0, sticky='w', pady=(10, 0))
            row_idx += 1

            var = tk.StringVar(value=cfg.get(key, ''))
            entry = tk.Entry(form, textvariable=var,
                             bg=BG3, fg=FG, insertbackground=FG,
                             font=('Arial', 10), relief='flat', width=54)
            entry.grid(row=row_idx, column=0, sticky='ew', ipady=5)

            if browse:
                tk.Button(form, text='📂',
                          bg=BG2, fg=FG, relief='flat',
                          font=('Arial', 11),
                          command=lambda v=var: _browse(v)
                          ).grid(row=row_idx, column=1, padx=(6, 0))

            if placeholder:
                tk.Label(form, text=f'ℹ️  {placeholder}',
                         bg=BG, fg='#555577',
                         font=('Arial', 8, 'italic')
                         ).grid(row=row_idx+1, column=0, sticky='w')
                row_idx += 1

            row_idx += 1
            fields[key] = var
            form.columnconfigure(0, weight=1)
            return var

        def _browse(var):
            path = filedialog.askopenfilename(
                title='Select serviceAccountKey.json',
                filetypes=[('JSON files', '*.json'), ('All files', '*.*')]
            )
            if path:
                var.set(path)

        add_field('Firebase Project ID',
                  'project_id',
                  'e.g.  my-shop-erp-12345   → Firebase Console → Project Settings')

        add_field('Realtime Database URL',
                  'database_url',
                  'e.g.  https://my-shop-12345-default-rtdb.firebaseio.com')

        add_field('Storage Bucket',
                  'storage_bucket',
                  'e.g.  my-shop-erp-12345.appspot.com')

        add_field('Shop ID  (unique key for this shop in Firestore)',
                  'shop_id',
                  'e.g.  david_shop_kolkata   (no spaces, use underscores)')

        add_field('Path to serviceAccountKey.json',
                  'service_account_key_path',
                  'Click 📂 to browse, or paste full path',
                  browse=True)

        # Enable toggle
        row_idx += 1
        enabled_var = tk.BooleanVar(value=bool(cfg.get('enabled', True)))
        tk.Checkbutton(
            form, text='  ✅  Enable Firebase Sync',
            variable=enabled_var,
            bg=BG, fg=FG, selectcolor=BG3,
            activebackground=BG, activeforeground=FG,
            font=('Arial', 10, 'bold')
        ).grid(row=row_idx, column=0, sticky='w', pady=(14, 0))

        # ─ Buttons
        btn_row = tk.Frame(win, bg=BG2, pady=10)
        btn_row.pack(fill='x', side='bottom')

        def save():
            new_cfg = {k: v.get().strip() for k, v in fields.items()}
            new_cfg['enabled'] = enabled_var.get()
            try:
                fc.save_config(new_cfg)
                messagebox.showinfo(
                    'Saved',
                    '✅ Firebase config saved!\n\n'
                    'Restart Hype ERP for changes to take effect.\n\n'
                    f'Project: {new_cfg.get("project_id") or "(not set)"}\n'
                    f'Shop ID: {new_cfg.get("shop_id") or "(not set)"}')
                win.destroy()
            except Exception as e:
                messagebox.showerror('Save Error', str(e))

        def test_connection():
            def _test():
                try:
                    import firebase_admin
                    from firebase_admin import credentials, firestore as fb_fs
                    import firebase_config as fc2
                    tmp_cfg = {k: v.get().strip() for k, v in fields.items()}
                    tmp_cfg['enabled'] = enabled_var.get()
                    key_path = tmp_cfg.get('service_account_key_path',
                                          'serviceAccountKey.json')
                    if not os.path.exists(key_path):
                        messagebox.showerror('Test Failed',
                                             f'serviceAccountKey.json not found at:\n{key_path}')
                        return
                    # Try init
                    app_name = '_hype_test_'
                    try:
                        app = firebase_admin.get_app(app_name)
                        firebase_admin.delete_app(app)
                    except Exception:
                        pass
                    cred = credentials.Certificate(key_path)
                    app  = firebase_admin.initialize_app(cred, name=app_name)
                    db   = fb_fs.client(app)
                    # Try a simple read
                    db.collection('_ping').document('test').set({'ping': True})
                    firebase_admin.delete_app(app)
                    messagebox.showinfo('Test Passed',
                                        '✅ Firebase connection successful!\n'
                                        f'Project: {tmp_cfg.get("project_id")}')
                except Exception as e:
                    messagebox.showerror('Test Failed',
                                         f'❌ Firebase connection failed:\n\n{e}\n\n'
                                         'Check your project ID, key file, and internet connection.')
            threading.Thread(target=_test, daemon=True).start()
            messagebox.showinfo('Testing...', 'Testing Firebase connection...\n(This may take a few seconds)')

        def clear_config():
            if messagebox.askyesno('Clear Config',
                                   'Are you sure you want to clear Firebase config?\n'
                                   'App will run offline (SQLite only).'):
                for v in fields.values():
                    v.set('')
                enabled_var.set(False)

        tk.Button(btn_row, text='💾  Save Config',
                  bg=GRN, fg=FG, relief='flat',
                  font=('Arial', 11, 'bold'), padx=16, pady=7,
                  cursor='hand2', command=save
                  ).pack(side='left', padx=14)

        tk.Button(btn_row, text='🔌  Test Connection',
                  bg=BG3, fg=FG, relief='flat',
                  font=('Arial', 10), padx=14, pady=7,
                  cursor='hand2', command=test_connection
                  ).pack(side='left', padx=4)

        tk.Button(btn_row, text='🗑  Clear',
                  bg='#3a1a1a', fg=FG, relief='flat',
                  font=('Arial', 10), padx=12, pady=7,
                  cursor='hand2', command=clear_config
                  ).pack(side='left', padx=4)

        tk.Button(btn_row, text='Cancel',
                  bg=BG2, fg='#888', relief='flat',
                  font=('Arial', 10), padx=12, pady=7,
                  cursor='hand2', command=win.destroy
                  ).pack(side='right', padx=14)

        tk.Label(win, text=FOOTER,
                 bg=BG2, fg='#444466',
                 font=('Arial', 7)).pack(side='bottom', fill='x', ipady=3)

        # Keyboard
        win.bind('<Return>', lambda e: save())
        win.bind('<Escape>', lambda e: win.destroy())
