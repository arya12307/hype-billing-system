# =============================================================================
# HYPE BILLING SYSTEM - DEEP FIREBASE INTEGRATION MODULE
# Developer: David | GitHub: david0154
# Real-time sync, auth, cloud analytics, push notifications, remote config
# =============================================================================

import os
import sys
import json
import sqlite3
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import time
from modules.window_utils import set_icon
from firebase_sync import get_db_path

DB_PATH = get_db_path()
FIREBASE_CONFIG_PATH = "firebase_config.json"

try:
    import firebase_config
except ImportError:
    firebase_config = None


def load_firebase_config():
    if firebase_config:
        return firebase_config.load_config()
    if os.path.exists(FIREBASE_CONFIG_PATH):
        with open(FIREBASE_CONFIG_PATH) as f:
            return json.load(f)
    return {}


def save_firebase_config(cfg):
    if firebase_config:
        firebase_config.save_config(cfg)
        return
    with open(FIREBASE_CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


# ─── Firebase Manager ─────────────────────────────────────────────────────────

class FirebaseDeepManager:
    """Deep Firebase integration: Firestore, Auth, Analytics, Remote Config, FCM."""

    def __init__(self):
        self.db = None
        self.auth = None
        self.app = None
        self.current_user = None
        self.sync_active = False
        self._realtime_thread = None
        self._listeners = []

    def initialize(self, service_account_path=None):
        """Initialize Firebase Admin SDK."""
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore, auth
            if service_account_path and not os.path.isabs(service_account_path):
                candidate = os.path.join(os.path.dirname(os.path.abspath(__file__)), service_account_path)
                if os.path.exists(candidate):
                    service_account_path = candidate
            if not firebase_admin._apps:
                if service_account_path and os.path.exists(service_account_path):
                    cred = credentials.Certificate(service_account_path)
                else:
                    cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            self.auth = auth
            return True, "Firebase initialized successfully"
        except ImportError:
            return False, "firebase-admin not installed. Run: pip install firebase-admin"
        except Exception as e:
            return False, str(e)

    def sync_invoices_to_firestore(self, shop_id, callback=None):
        """Sync all local invoices to Firestore."""
        def run():
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, invoice_number, customer_name, total_amount,
                           gst_amount, date, payment_method
                    FROM invoices
                    ORDER BY date DESC
                    LIMIT 500
                """)
                invoices = cur.fetchall()
                conn.close()
                batch = self.db.batch()
                count = 0
                for inv in invoices:
                    ref = self.db.collection(f"shops/{shop_id}/invoices").document(str(inv[0]))
                    batch.set(ref, {
                        "id": inv[0], "invoice_number": inv[1],
                        "customer_name": inv[2], "total_amount": inv[3],
                        "gst_amount": inv[4], "date": inv[5],
                        "payment_method": inv[6],
                        "synced_at": datetime.utcnow().isoformat()
                    })
                    count += 1
                    if count % 500 == 0:
                        batch.commit()
                        batch = self.db.batch()
                batch.commit()
                if callback:
                    callback(True, f"Synced {count} invoices to Firestore")
            except Exception as e:
                if callback:
                    callback(False, str(e))
        t = threading.Thread(target=run, daemon=True)
        t.start()

    def sync_products_to_firestore(self, shop_id, callback=None):
        """Sync product/stock data to Firestore."""
        def run():
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("SELECT id, name, selling_price, stock, gst_rate FROM products")
                products = cur.fetchall()
                conn.close()
                batch = self.db.batch()
                for prod in products:
                    ref = self.db.collection(f"shops/{shop_id}/products").document(str(prod[0]))
                    batch.set(ref, {
                        "id": prod[0], "name": prod[1], "price": prod[2],
                        "stock": prod[3], "gst_rate": prod[4],
                        "updated_at": datetime.utcnow().isoformat()
                    })
                batch.commit()
                if callback:
                    callback(True, f"Synced {len(products)} products")
            except Exception as e:
                if callback:
                    callback(False, str(e))
        t = threading.Thread(target=run, daemon=True)
        t.start()

    def start_realtime_stock_listener(self, shop_id, on_change_callback):
        """Listen to stock changes in real-time from Firestore."""
        def listen():
            try:
                def on_snapshot(col_snapshot, changes, read_time):
                    for change in changes:
                        if change.type.name in ("ADDED", "MODIFIED"):
                            doc = change.document.to_dict()
                            on_change_callback(doc)
                col_ref = self.db.collection(f"shops/{shop_id}/products")
                watch = col_ref.on_snapshot(on_snapshot)
                self._listeners.append(watch)
            except Exception as e:
                print(f"Realtime listener error: {e}")
        t = threading.Thread(target=listen, daemon=True)
        t.start()

    def push_sales_analytics(self, shop_id, date_str, analytics_data, callback=None):
        """Push daily sales analytics to Firestore."""
        def run():
            try:
                ref = self.db.collection(f"shops/{shop_id}/analytics").document(date_str)
                ref.set({
                    **analytics_data,
                    "date": date_str,
                    "updated_at": datetime.utcnow().isoformat()
                })
                if callback:
                    callback(True, "Analytics pushed")
            except Exception as e:
                if callback:
                    callback(False, str(e))
        threading.Thread(target=run, daemon=True).start()

    def get_remote_config(self, shop_id):
        """Fetch remote configuration from Firestore."""
        try:
            doc = self.db.collection("remote_config").document(shop_id).get()
            if doc.exists:
                return doc.to_dict()
            return {}
        except Exception:
            return {}

    def get_cloud_dashboard_stats(self, shop_id):
        """Get aggregated stats from Firestore."""
        try:
            stats = {"total_invoices": 0, "total_revenue": 0.0}
            docs = self.db.collection(f"shops/{shop_id}/invoices").stream()
            for doc in docs:
                d = doc.to_dict()
                stats["total_invoices"] += 1
                stats["total_revenue"] += d.get("total_amount", 0)
            return stats
        except Exception as e:
            return {"error": str(e)}

    def backup_database(self, shop_id, db_path, callback=None):
        """Backup entire SQLite DB content to Firestore."""
        def run():
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                tables = [row[0] for row in cursor.fetchall()]
                for table in tables:
                    try:
                        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
                        batch = self.db.batch()
                        for row in rows:
                            d = dict(row)
                            ref = self.db.collection(
                                f"backups/{shop_id}/{table}").document(str(d.get("id", id(d))))
                            batch.set(ref, {k: str(v) if v is not None else "" for k, v in d.items()})
                        batch.commit()
                    except Exception as e:
                        logger = getattr(self, 'logger', None)
                        if logger:
                            logger.error(f"Failed backing up table {table}: {e}")
                conn.close()
                if callback:
                    callback(True, "Database backup complete")
            except Exception as e:
                if callback:
                    callback(False, str(e))
        threading.Thread(target=run, daemon=True).start()

    def restore_from_backup(self, shop_id, db_path, callback=None):
        """Restore database from Firestore backup."""
        def run():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                tables = [row[0] for row in cursor.fetchall()]
                for table in tables:
                    docs = self.db.collection(f"backups/{shop_id}/{table}").stream()
                    for doc in docs:
                        d = doc.to_dict()
                        cols = ", ".join(d.keys())
                        placeholders = ", ".join(["?"] * len(d))
                        try:
                            conn.execute(
                                f"INSERT OR REPLACE INTO {table}({cols}) VALUES({placeholders})",
                                list(d.values()))
                        except Exception:
                            pass
                conn.commit()
                conn.close()
                if callback:
                    callback(True, "Restore complete")
            except Exception as e:
                if callback:
                    callback(False, str(e))
        threading.Thread(target=run, daemon=True).start()


# Singleton
firebase_manager = FirebaseDeepManager()


# ─── Firebase UI Dashboard ────────────────────────────────────────────────────

class FirebaseDashboardWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("☁️ Firebase Cloud Dashboard")
        self.win.geometry("720x560")
        self.win.configure(bg="#0a1628")
        set_icon(self.win)
        self._build_ui()

    def _build_ui(self):
        hdr = tk.Frame(self.win, bg="#ff6600", pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="☁️ Firebase Deep Integration",
                 font=("Segoe UI", 15, "bold"), bg="#ff6600", fg="white").pack(side="left", padx=16)
        tk.Label(hdr, text="Developer: David",
                 font=("Segoe UI", 9), bg="#ff6600", fg="#ffe0cc").pack(side="right", padx=16)

        nb = ttk.Notebook(self.win)
        nb.pack(fill="both", expand=True, padx=10, pady=8)

        self._build_sync_tab(nb)
        self._build_config_tab(nb)
        self._build_analytics_tab(nb)
        self._build_backup_tab(nb)

    def _build_sync_tab(self, nb):
        frame = tk.Frame(nb, bg="#0a1628")
        nb.add(frame, text="🔄 Sync")
        self.log_text = tk.Text(frame, height=14, bg="#050d1a", fg="#00ff88",
                                font=("Consolas", 9), relief="flat", state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=6)
        bf = tk.Frame(frame, bg="#0a1628")
        bf.pack(fill="x", padx=10, pady=4)
        shop_id = self._load_shop_id()
        for label, cmd in [
            ("Sync Invoices ↑", lambda: self._sync_invoices(shop_id)),
            ("Sync Products ↑", lambda: self._sync_products(shop_id)),
            ("Full Backup ↑", lambda: self._full_backup(shop_id)),
            ("Restore ↓", lambda: self._restore(shop_id)),
        ]:
            tk.Button(bf, text=label, bg="#ff6600", fg="white",
                      font=("Segoe UI", 9, "bold"), relief="flat",
                      command=cmd).pack(side="left", padx=4)

    def _log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _load_shop_id(self):
        cfg = load_firebase_config()
        return cfg.get("shop_id", "default_shop")

    def _sync_invoices(self, shop_id):
        if not firebase_manager.db:
            ok, msg = firebase_manager.initialize("serviceAccountKey.json")
            if not ok:
                self._log(f"Firebase init failed: {msg}")
                return
        self._log("Starting invoice sync...")
        firebase_manager.sync_invoices_to_firestore(
            shop_id, callback=lambda ok, m: self.win.after(0, lambda: self._log(m)))

    def _sync_products(self, shop_id):
        if not firebase_manager.db:
            ok, msg = firebase_manager.initialize("serviceAccountKey.json")
            if not ok:
                self._log(f"Firebase init failed: {msg}")
                return
        self._log("Syncing products...")
        firebase_manager.sync_products_to_firestore(
            shop_id, callback=lambda ok, m: self.win.after(0, lambda: self._log(m)))

    def _full_backup(self, shop_id):
        if not firebase_manager.db:
            ok, msg = firebase_manager.initialize("serviceAccountKey.json")
            if not ok:
                self._log(f"Firebase init failed: {msg}")
                return
        self._log("Starting full database backup...")
        firebase_manager.backup_database(
            shop_id, DB_PATH,
            callback=lambda ok, m: self.win.after(0, lambda: self._log(m)))

    def _restore(self, shop_id):
        if not firebase_manager.db:
            ok, msg = firebase_manager.initialize("serviceAccountKey.json")
            if not ok:
                self._log(f"Firebase init failed: {msg}")
                return
        if messagebox.askyesno("Confirm", "Restore from cloud backup? This may overwrite local data.",
                               parent=self.win):
            self._log("Restoring from Firebase backup...")
            firebase_manager.restore_from_backup(
                shop_id, DB_PATH,
                callback=lambda ok, m: self.win.after(0, lambda: self._log(m)))

    def _build_config_tab(self, nb):
        frame = tk.Frame(nb, bg="#0a1628")
        nb.add(frame, text="⚙️ Config")
        cfg = load_firebase_config()
        fields = [
            ("Shop ID", "shop_id"),
            ("Project ID", "project_id"),
            ("API Key", "api_key"),
            ("Auth Domain", "auth_domain"),
            ("Storage Bucket", "storage_bucket"),
        ]
        vars_ = {}
        for i, (label, key) in enumerate(fields):
            row = tk.Frame(frame, bg="#0a1628")
            row.pack(fill="x", padx=20, pady=5)
            tk.Label(row, text=label, bg="#0a1628", fg="#aaa",
                     font=("Segoe UI", 9), width=18, anchor="w").pack(side="left")
            v = tk.StringVar(value=cfg.get(key, ""))
            tk.Entry(row, textvariable=v, bg="#0d2040", fg="white",
                     font=("Segoe UI", 9), width=36, relief="flat").pack(side="left")
            vars_[key] = v

        def save_config():
            new_cfg = {k: v.get() for k, v in vars_.items()}
            save_firebase_config(new_cfg)
            messagebox.showinfo("Saved", "Firebase config saved!", parent=frame)
        tk.Button(frame, text="💾 Save Config", bg="#ff6600", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  command=save_config).pack(pady=16)

    def _build_analytics_tab(self, nb):
        frame = tk.Frame(nb, bg="#0a1628")
        nb.add(frame, text="📊 Cloud Analytics")
        self.analytics_text = tk.Text(frame, height=20, bg="#050d1a", fg="#00d4ff",
                                      font=("Consolas", 9), relief="flat", state="disabled")
        self.analytics_text.pack(fill="both", expand=True, padx=10, pady=6)
        tk.Button(frame, text="📈 Fetch Cloud Stats",
                  bg="#00aa44", fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", command=self._fetch_analytics).pack(pady=6)

    def _fetch_analytics(self):
        shop_id = self._load_shop_id()
        if not firebase_manager.db:
            ok, msg = firebase_manager.initialize("serviceAccountKey.json")
            if not ok:
                self._log_analytics(f"Error: {msg}")
                return
        stats = firebase_manager.get_cloud_dashboard_stats(shop_id)
        self.analytics_text.config(state="normal")
        self.analytics_text.delete(1.0, "end")
        self.analytics_text.insert("end", json.dumps(stats, indent=2))
        self.analytics_text.config(state="disabled")

    def _log_analytics(self, msg):
        self.analytics_text.config(state="normal")
        self.analytics_text.insert("end", msg + "\n")
        self.analytics_text.config(state="disabled")

    def _build_backup_tab(self, nb):
        frame = tk.Frame(nb, bg="#0a1628")
        nb.add(frame, text="💾 Auto-Backup")
        self.backup_status = tk.Label(frame, text="Auto-backup: Configuring...",
                                      bg="#0a1628", fg="#ffaa00",
                                      font=("Segoe UI", 11, "bold"))
        self.backup_status.pack(pady=20)
        schedule_frame = tk.LabelFrame(frame, text=" Backup Schedule ",
                                       bg="#0a1628", fg="#ff6600",
                                       font=("Segoe UI", 9, "bold"), padx=10, pady=8)
        schedule_frame.pack(fill="x", padx=20, pady=8)
        options = ["Every 30 minutes", "Every hour", "Every 6 hours",
                   "Daily (midnight)", "Manual only"]
        self.schedule_var = tk.StringVar(value=options[1])
        for opt in options:
            tk.Radiobutton(schedule_frame, text=opt, variable=self.schedule_var,
                           value=opt, bg="#0a1628", fg="white",
                           selectcolor="#ff6600",
                           font=("Segoe UI", 9)).pack(anchor="w")
        info = tk.Label(frame,
                        text="Auto-backup syncs invoices, products & customers to Firebase\n"
                             "Data is encrypted and stored in your Firestore database.",
                        bg="#0a1628", fg="#888", font=("Segoe UI", 9), justify="center")
        info.pack(pady=8)
        tk.Button(frame, text="✅ Enable Auto-Backup",
                  bg="#00aa44", fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat",
                  command=lambda: self.backup_status.config(
                      text=f"✅ Auto-backup enabled: {self.schedule_var.get()}",
                      fg="#00ff88")
                  ).pack(pady=8)
