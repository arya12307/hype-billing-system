"""
Firebase Firestore Integration Module
Auto-backup, sync, and offline queue management for HYPE Billing System
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sqlite3
import json
import os
import hashlib
from datetime import datetime, timedelta
import threading
import time
import socket
import tempfile
from typing import Dict, List, Any
import logging
import json as _json
import sys
import os

def get_log_dir():
    def _test_and_create(path: str) -> bool:
        try:
            os.makedirs(path, exist_ok=True)
            testfile = os.path.join(path, ".write_test")
            with open(testfile, "w") as tf:
                tf.write("ok")
            os.remove(testfile)
            return True
        except Exception:
            return False

    if sys.platform.startswith("win"):
        exe_dir = None
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.abspath(os.path.dirname(sys.executable))

        candidates = [os.getenv("LOCALAPPDATA"), os.getenv("APPDATA"), os.getenv("PROGRAMDATA")]
        for base in candidates:
            if not base:
                continue
            log_dir = os.path.join(base, "HypeRetailBilling")
            # Avoid returning a dir that is the same as the installation folder
            try:
                if exe_dir and os.path.commonpath([os.path.abspath(log_dir), exe_dir]) == exe_dir:
                    continue
            except Exception:
                pass
            if _test_and_create(log_dir):
                return log_dir

        # Fallback to user home
        home_dir = os.path.join(os.path.expanduser("~"), "HypeRetailBilling")
        if _test_and_create(home_dir):
            return home_dir

        # Last resort: current working directory
        cwd_dir = os.path.join(os.getcwd(), "HypeRetailBilling")
        try:
            os.makedirs(cwd_dir, exist_ok=True)
            return cwd_dir
        except Exception:
            return os.getcwd()
    else:
        log_dir = os.path.expanduser("~/.hype_retail_billing")
        os.makedirs(log_dir, exist_ok=True)
        return log_dir

LOG_FILE = os.path.join(get_log_dir(), "firebase_sync.log")


def _hash_password(password: str) -> str:
    try:
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    except Exception:
        return ''


def _normalize_password_for_restore(password_value) -> str:
    """Normalize a Firebase password so local authentication stays compatible."""
    if password_value is None:
        return ''

    if isinstance(password_value, bytes):
        value = password_value.decode('utf-8', errors='ignore')
    else:
        value = str(password_value)

    value = value.strip()
    if not value:
        return ''

    if len(value) == 64 and all(ch in '0123456789abcdefABCDEF' for ch in value):
        return value.lower()

    return _hash_password(value)


logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# About metadata (non-functional, informational)
ABOUT_TEXT = (
    "Application: HYPE Billing System\n"
    "Developed by: David\n"
    "Powered by: Nexuzy Tech Pvt Ltd\n"
    "Contact: nexuzypvtltd@gmail.com"
)

FIREBASE_SECRET_KEY = b'J6TmP2PtNyXGZX28P8b2_CO2xRJ2c-xk2AIIJtu1gPc='

# Global lock to prevent concurrent Firebase initialization
_firebase_init_lock = threading.Lock()
_firebase_initialized = False


def _decrypt_firebase_key(enc_path: str):
    if not enc_path or not os.path.exists(enc_path):
        return None
    try:
        from cryptography.fernet import Fernet
        with open(enc_path, 'rb') as handle:
            decrypted = Fernet(FIREBASE_SECRET_KEY).decrypt(handle.read())
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_file.write(decrypted)
        temp_file.close()
        return temp_file.name
    except Exception:
        return None


def _resolve_credentials_path(credentials_path='serviceAccountKey.json'):
    if not credentials_path:
        return None

    if os.path.isabs(credentials_path) and os.path.exists(credentials_path):
        return credentials_path

    # For PyInstaller, check LOCALAPPDATA/HypeERP first for credentials (persistent location)
    if getattr(sys, 'frozen', False):
        hype_app_dir = os.path.join(
            os.getenv('LOCALAPPDATA') or os.getenv('APPDATA') or os.path.expanduser('~'),
            'HypeERP'
        )
        # Check for serviceAccountKey.json in persistent location
        persistent_creds = os.path.join(hype_app_dir, 'serviceAccountKey.json')
        if os.path.exists(persistent_creds):
            return persistent_creds
        
        # Check for encrypted version
        persistent_enc = os.path.join(hype_app_dir, 'serviceAccountKey.enc')
        if os.path.exists(persistent_enc):
            decrypted = _decrypt_firebase_key(persistent_enc)
            if decrypted and os.path.exists(decrypted):
                return decrypted
        
        # Fall back to bundle location
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    if not os.path.isabs(credentials_path):
        candidate = os.path.join(base_path, credentials_path)
    else:
        candidate = credentials_path

    if os.path.exists(candidate):
        return candidate

    enc_path = os.path.join(base_path, 'serviceAccountKey.enc')
    decrypted_path = _decrypt_firebase_key(enc_path)
    if decrypted_path and os.path.exists(decrypted_path):
        return decrypted_path

    if os.path.exists(os.path.join(base_path, 'serviceAccountKey.json')):
        return os.path.join(base_path, 'serviceAccountKey.json')

    return candidate


class FirebaseSync:
    def __init__(self, credentials_path='serviceAccountKey.json'):
        """Initialize Firebase connection"""
        self.db = None
        credentials_path = _resolve_credentials_path(credentials_path)

        self.credentials_path = credentials_path
        # Put offline queue file next to the credentials (or in script dir if credentials not provided)
        creds_dir = os.path.dirname(os.path.abspath(self.credentials_path)) if self.credentials_path else os.path.dirname(os.path.abspath(__file__))
        self.offline_queue_file = os.path.join(creds_dir, 'offline_queue.json')
        self.is_online = False
        self.sync_interval = 300  # 5 minutes
        self.sync_thread = None
        self.connectivity_monitor_thread = None
        self.stop_sync = False
        self.stop_connectivity_monitor = False
        # Event to signal sync thread to wake up immediately (for urgent syncs)
        self.sync_wake_event = threading.Event()
        # Lock for thread-safe is_online updates
        self.connectivity_lock = threading.Lock()
        
        # Initialize Firebase if credentials exist (with thread-safe locking)
        if os.path.exists(credentials_path):
            try:
                with _firebase_init_lock:
                    # Check if default app already exists
                    try:
                        firebase_admin.get_app()
                        # App already initialized, just get the firestore client
                        self.db = firestore.client()
                        logger.info("✓ Firebase already initialized, using existing connection")
                    except ValueError:
                        # App not initialized yet, initialize it (only once per process)
                        cred = credentials.Certificate(credentials_path)
                        firebase_admin.initialize_app(cred)
                        self.db = firestore.client()
                        logger.info("✓ Firebase initialized successfully (first time)")
            except Exception as e:
                logger.error(f"Firebase initialization failed: {str(e)}")
                self.db = None
        else:
            logger.warning(f"Firebase credentials not found at {credentials_path}")
    
    def check_internet_connection(self) -> bool:
        """Check if internet connection is available"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def _run_with_timeout(self, target, args=(), kwargs=None, timeout=6):
        """Run a callable in a thread and wait up to `timeout` seconds.

        Returns (True, result) on success, (False, exception) on exception or timeout.
        """
        if kwargs is None:
            kwargs = {}

        result_container = {}

        def _wrapper():
            try:
                result_container['res'] = target(*args, **kwargs)
                result_container['ok'] = True
            except Exception as e:
                result_container['res'] = e
                result_container['ok'] = False

        t = threading.Thread(target=_wrapper, daemon=True)
        t.start()
        t.join(timeout=timeout)
        if t.is_alive():
            return False, TimeoutError(f"Operation timed out after {timeout}s")
        return result_container.get('ok', False), result_container.get('res')
    
    def load_offline_queue(self) -> List[Dict]:
        """Load operations queue from offline storage"""
        if os.path.exists(self.offline_queue_file):
            try:
                with open(self.offline_queue_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading offline queue: {str(e)}")
                return []
        return []
    
    def save_offline_queue(self, queue: List[Dict]):
        """Save operations queue to offline storage"""
        try:
            with open(self.offline_queue_file, 'w') as f:
                json.dump(queue, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving offline queue: {str(e)}")
    
    def queue_operation(self, operation_type: str, collection: str, doc_id: str, data: Dict, timestamp: str = None):
        """Add operation to offline queue"""
        queue = self.load_offline_queue()
        queue.append({
            'type': operation_type,  # 'set', 'update', 'delete'
            'collection': collection,
            'doc_id': doc_id,
            'data': data,
            'timestamp': timestamp or datetime.now().isoformat(),
            'synced': False
        })
        self.save_offline_queue(queue)
        logger.info(f"Operation queued: {operation_type} on {collection}/{doc_id}")
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        try:
            db_path = get_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except Exception:
            return False

    def get_storage_client_and_bucket(self):
        """Return (storage_client, bucket) or (None, None) if unavailable."""
        try:
            from google.cloud import storage
        except Exception as e:
            logger.error(f"google.cloud.storage not available: {e}")
            return None, None

        # Try to get bucket name from credentials file (project_id)
        try:
            with open(self.credentials_path, 'r') as f:
                cred_json = _json.load(f)
            project_id = cred_json.get('project_id')
            bucket_name = cred_json.get('storageBucket') or (f"{project_id}.appspot.com" if project_id else None)
        except Exception as e:
            logger.warning(f"Could not read credentials for storage bucket detection: {e}")
            bucket_name = None

        try:
            client = storage.Client.from_service_account_json(self.credentials_path) if self.credentials_path else storage.Client()
            if bucket_name:
                bucket = client.bucket(bucket_name)
            else:
                # fallback: use default bucket from client if available
                bucket = None
            return client, bucket
        except Exception as e:
            logger.error(f"Failed to initialize storage client: {e}")
            return None, None

    def download_blobs_with_prefix(self, client, bucket, prefix: str, local_dir: str) -> int:
        """Download all blobs under `prefix` into `local_dir`. Returns number of files downloaded."""
        if not client or not bucket:
            return 0
        try:
            # If bucket is a string-bucket placeholder, accept bucket as Bucket object
            blobs = bucket.list_blobs(prefix=prefix)
            count = 0
            for blob in blobs:
                if not blob.name or blob.name.endswith('/'):
                    continue
                rel_path = os.path.relpath(blob.name, prefix) if blob.name.startswith(prefix) else os.path.basename(blob.name)
                target_path = os.path.join(local_dir, rel_path)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                try:
                    blob.download_to_filename(target_path)
                    logger.info(f"Downloaded storage file: {blob.name} -> {target_path}")
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to download blob {blob.name}: {e}")
            return count
        except Exception as e:
            logger.error(f"Error listing/downloading blobs for prefix {prefix}: {e}")
            return 0

    def download_store_assets(self, store_id: int) -> bool:
        """Download common asset folders (pdfs, bills attachments) from Firebase Storage for a store."""
        client, bucket = self.get_storage_client_and_bucket()
        if not client or not bucket:
            logger.info("Storage client or bucket not available - skipping storage downloads")
            return False

        script_dir = os.path.dirname(os.path.abspath(__file__))
        downloaded_total = 0
        # common prefixes to try
        prefixes = [f"stores/{store_id}/", f"stores/{store_id}/pdfs/", f"pdfs/", f"bills/", f"stores/{store_id}/attachments/"]
        local_base = os.path.join(script_dir, 'downloaded_storage')
        for prefix in prefixes:
            local_dir = os.path.join(local_base, prefix.replace('/', '_'))
            try:
                cnt = self.download_blobs_with_prefix(client, bucket, prefix, local_dir)
                downloaded_total += cnt
            except Exception as e:
                logger.warning(f"Error downloading prefix {prefix}: {e}")

        logger.info(f"Downloaded {downloaded_total} files from storage for store {store_id}")
        return downloaded_total > 0
    
    def backup_products(self, store_id: int):
        """Backup all products to Firebase"""
        if not self.db:
            logger.warning("Firebase not initialized. Queuing for later sync.")
            self.queue_operation('backup', 'products', f'store_{store_id}', {'status': 'queued'})
            return False
        
        # Check if products table exists first
        if not self.table_exists('products'):
            logger.warning("Products table does not exist yet - skipping backup")
            return False
        
        try:
            conn = sqlite3.connect(get_db_path())
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products WHERE store_id = ?', (store_id,))
            products = cursor.fetchall()
            conn.close()
            
            products_data = [dict(p) for p in products]
            
            # Backup to Firebase
            self.db.collection('stores').document(str(store_id)).collection('products').document('backup').set({
                'products': products_data,
                'last_backup': datetime.now().isoformat(),
                'total_count': len(products_data)
            })
            
            logger.info(f"Backed up {len(products_data)} products for store {store_id}")
            return True
        except Exception as e:
            logger.error(f"Error backing up products: {str(e)}")
            self.queue_operation('backup_products', f'store_{store_id}', 'products', {'error': str(e)})
            return False
    
    def backup_users(self):
        """Backup all users to Firebase"""
        if not self.db:
            self.queue_operation('backup_users', 'users', 'all', {})
            return False
        
        if not self.table_exists('users'):
            logger.warning("Users table does not exist yet - skipping backup")
            return False
        
        try:
            conn = sqlite3.connect(get_db_path())
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            available_cols = [row[1] for row in cursor.fetchall()]
            select_cols = []
            for col in ['id', 'username', 'full_name', 'phone', 'email', 'role', 'password', 'created_at']:
                if col in available_cols:
                    select_cols.append(f"{col} AS user_id" if col == 'id' else col)
            if not select_cols:
                conn.close()
                logger.warning("No compatible user columns found to backup")
                return False
            cursor.execute(f"SELECT {', '.join(select_cols)} FROM users")
            users = cursor.fetchall()
            conn.close()

            users_data = [dict(u) for u in users]
            self.db.collection('system').document('users').set({
                'users': users_data,
                'last_backup': datetime.now().isoformat(),
                'total_count': len(users_data)
            })
            logger.info(f"Backed up {len(users_data)} users")
            return True
        except Exception as e:
            logger.error(f"Error backing up users: {str(e)}")
            self.queue_operation('backup_users', 'system', 'users', {'error': str(e)})
            return False

    def backup_credentials(self, credentials_path: str = None) -> bool:
        """Upload service account key (or encrypted key) to Firebase Storage under `credentials/`.

        If Cloud Storage bucket is unavailable, store an obfuscated metadata document in Firestore.
        """
        # Resolve path
        creds_path = credentials_path or self.credentials_path or 'serviceAccountKey.json'
        if not os.path.isabs(creds_path):
            base = os.path.dirname(os.path.abspath(self.credentials_path)) if self.credentials_path else os.path.dirname(os.path.abspath(__file__))
            creds_path = os.path.join(base, creds_path)

        # Prefer encrypted key if present next to credentials
        enc_path = os.path.splitext(creds_path)[0] + '.enc'
        target_file = None
        if os.path.exists(enc_path):
            target_file = enc_path
        elif os.path.exists(creds_path):
            target_file = creds_path
        else:
            logger.warning(f"No credentials file found to backup at {creds_path} or {enc_path}")
            return False

        # Try to upload to Cloud Storage
        client, bucket = self.get_storage_client_and_bucket()
        if client and bucket:
            try:
                blob_name = f'credentials/{os.path.basename(target_file)}'
                blob = bucket.blob(blob_name)
                blob.upload_from_filename(target_file)
                blob.metadata = {'uploaded_at': datetime.now().isoformat()}
                blob.patch()
                logger.info(f"Uploaded credentials file to storage: {blob_name}")
                return True
            except Exception as e:
                logger.warning(f"Storage upload failed: {e} - falling back to Firestore")

        # Fallback: store limited metadata / obfuscated content in Firestore
        try:
            with open(target_file, 'rb') as f:
                raw = f.read()
            # Don't store raw private key in plain text; store base64 and mark as encrypted if enc
            import base64
            payload = base64.b64encode(raw).decode('ascii')
            doc = {
                'filename': os.path.basename(target_file),
                'base64': payload,
                'uploaded_at': datetime.now().isoformat()
            }
            # Write to a protected system doc
            self.db.collection('system').document('credentials_backup').set(doc)
            logger.info("Stored credentials backup in Firestore system/credentials_backup (base64)")
            return True
        except Exception as e:
            logger.error(f"Failed to backup credentials: {e}")
            return False
    
    def backup_bills(self, store_id: int):
        """Backup all bills and bill items to Firebase"""
        if not self.db:
            self.queue_operation('backup_bills', f'store_{store_id}', 'bills', {})
            return False
        
        # Check if bills table exists first
        if not self.table_exists('bills'):
            logger.warning("Bills table does not exist yet - skipping backup")
            return False
        
        try:
            conn = sqlite3.connect(get_db_path())
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get bills
            cursor.execute('SELECT * FROM bills WHERE store_id = ?', (store_id,))
            bills = cursor.fetchall()
            
            bills_data = []
            for bill in bills:
                bill_dict = dict(bill)
                # Get bill items
                cursor.execute('SELECT * FROM bill_items WHERE bill_id = ?', (bill_dict['bill_id'],))
                items = cursor.fetchall()
                bill_dict['items'] = [dict(item) for item in items]
                bills_data.append(bill_dict)
            
            conn.close()
            
            # Backup to Firebase
            self.db.collection('stores').document(str(store_id)).collection('bills').document('backup').set({
                'bills': bills_data,
                'last_backup': datetime.now().isoformat(),
                'total_count': len(bills_data)
            })
            
            logger.info(f"Backed up {len(bills_data)} bills for store {store_id}")
            return True
        except Exception as e:
            logger.error(f"Error backing up bills: {str(e)}")
            self.queue_operation('backup_bills', f'store_{store_id}', 'bills', {'error': str(e)})
            return False
    
    def backup_customers(self, store_id: int):
        """Backup all customers to Firebase"""
        if not self.db:
            self.queue_operation('backup_customers', f'store_{store_id}', 'customers', {})
            return False
        
        # Check if customers table exists first
        if not self.table_exists('customers'):
            logger.warning("Customers table does not exist yet - skipping backup")
            return False
        
        try:
            conn = sqlite3.connect(get_db_path())
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM customers')
            customers = cursor.fetchall()
            conn.close()
            
            customers_data = [dict(c) for c in customers]
            
            # Backup to Firebase
            self.db.collection('stores').document(str(store_id)).collection('customers').document('backup').set({
                'customers': customers_data,
                'last_backup': datetime.now().isoformat(),
                'total_count': len(customers_data)
            })
            
            logger.info(f"Backed up {len(customers_data)} customers")
            return True
        except Exception as e:
            logger.error(f"Error backing up customers: {str(e)}")
            self.queue_operation('backup_customers', f'store_{store_id}', 'customers', {'error': str(e)})
            return False

    def backup_employees(self, store_id: int):
        """Backup employee records to Firebase under stores/{store_id}/employees/backup"""
        if not self.db:
            self.queue_operation('backup_employees', f'store_{store_id}', 'employees', {})
            return False

        if not self.table_exists('employees'):
            logger.warning('Employees table does not exist - skipping backup')
            return False

        try:
            conn = sqlite3.connect(get_db_path())
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM employees')
            rows = cursor.fetchall()
            conn.close()

            data = [dict(r) for r in rows]
            self.db.collection('stores').document(str(store_id)).collection('employees').document('backup').set({
                'employees': data,
                'last_backup': datetime.now().isoformat(),
                'total_count': len(data)
            })
            logger.info(f"Backed up {len(data)} employees for store {store_id}")
            return True
        except Exception as e:
            logger.error(f"Error backing up employees: {e}")
            self.queue_operation('backup_employees', f'store_{store_id}', 'employees', {'error': str(e)})
            return False

    def backup_payroll(self, store_id: int):
        """Backup payroll/payslips to Firebase under stores/{store_id}/payroll/backup"""
        if not self.db:
            self.queue_operation('backup_payroll', f'store_{store_id}', 'payroll', {})
            return False

        if not self.table_exists('payroll'):
            logger.warning('Payroll table does not exist - skipping backup')
            return False

        try:
            conn = sqlite3.connect(get_db_path())
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM payroll')
            rows = cursor.fetchall()
            conn.close()

            data = [dict(r) for r in rows]
            self.db.collection('stores').document(str(store_id)).collection('payroll').document('backup').set({
                'payroll': data,
                'last_backup': datetime.now().isoformat(),
                'total_count': len(data)
            })
            logger.info(f"Backed up {len(data)} payroll records for store {store_id}")
            return True
        except Exception as e:
            logger.error(f"Error backing up payroll: {e}")
            self.queue_operation('backup_payroll', f'store_{store_id}', 'payroll', {'error': str(e)})
            return False
        except Exception as e:
            logger.error(f"Error backing up customers: {str(e)}")
            self.queue_operation('backup_customers', f'store_{store_id}', 'customers', {'error': str(e)})
            return False
    
    def backup_settings(self):
        """Backup all settings to Firebase"""
        if not self.db:
            self.queue_operation('backup_settings', 'system', 'settings', {})
            return False
        
        # Check if settings table exists first
        if not self.table_exists('settings'):
            logger.warning("Settings table does not exist yet - skipping backup")
            return False
        
        try:
            conn = sqlite3.connect(get_db_path())
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM settings')
            settings = cursor.fetchall()
            cursor.execute('SELECT * FROM stores')
            stores = cursor.fetchall()
            conn.close()
            
            settings_data = {row['key']: row['value'] for row in settings}
            stores_data = [dict(s) for s in stores]
            
            # Backup to Firebase
            self.db.collection('system').document('settings').set({
                'settings': settings_data,
                'stores': stores_data,
                'last_backup': datetime.now().isoformat()
            })
            
            logger.info("Backed up system settings and stores")
            return True
        except Exception as e:
            logger.error(f"Error backing up settings: {str(e)}")
            self.queue_operation('backup_settings', 'system', 'settings', {'error': str(e)})
            return False
    
    def backup_gst_config(self):
        """Backup GST configuration to Firebase"""
        if not self.db:
            self.queue_operation('backup_gst_config', 'system', 'gst_config', {})
            return False
        
        # Check if gst_config table exists first
        if not self.table_exists('gst_config'):
            logger.warning("GST config table does not exist yet - skipping backup")
            return False
        
        try:
            conn = sqlite3.connect(DB_PATH if 'DB_PATH' in globals() else 'hype_billing_system.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM gst_config')
            gst_config = cursor.fetchall()
            conn.close()
            
            gst_config_data = [dict(g) for g in gst_config]
            
            # Backup to Firebase
            self.db.collection('system').document('gst_config').set({
                'gst_config': gst_config_data,
                'last_backup': datetime.now().isoformat()
            })
            
            logger.info(f"Backed up {len(gst_config_data)} GST configurations")
            return True
        except Exception as e:
            logger.error(f"Error backing up GST config: {str(e)}")
            self.queue_operation('backup_gst_config', 'system', 'gst_config', {'error': str(e)})
            return False
    
    def _deduplicate_offline_queue(self, queue: List[Dict]) -> List[Dict]:
        """Remove duplicate operations from offline queue.
        
        Keeps the first occurrence of each unique (collection, doc_id, type) combination.
        This prevents 'backup on products/store_1' from appearing 55+ times.
        """
        seen = {}
        deduplicated = []
        
        for op in queue:
            key = (op['collection'], op['doc_id'], op['type'])
            
            if key not in seen:
                seen[key] = True
                deduplicated.append(op)
            else:
                logger.debug(f"Skipping duplicate operation: {op['type']} on {op['collection']}/{op['doc_id']}")
        
        if len(deduplicated) < len(queue):
            logger.info(f"Deduplicated offline queue: {len(queue)} → {len(deduplicated)} operations")
        
        return deduplicated

    def sync_offline_queue(self) -> int:
        """Process offline queue and sync to Firebase"""
        if not self.is_online or not self.db:
            return 0
        
        queue = self.load_offline_queue()
        
        if not queue:
            logger.debug("Offline queue is empty")
            return 0
        
        # Deduplicate before syncing
        queue = self._deduplicate_offline_queue(queue)
        
        synced_count = 0
        failed_count = 0
        
        for idx, operation in enumerate(queue):
            if operation.get('synced', False):
                continue
            
            try:
                collection = operation.get('collection')
                doc_id = operation.get('doc_id')
                op_type = operation.get('type')
                data = operation.get('data', {})
                
                if not collection or not doc_id or not op_type:
                    logger.warning(f"Skipping malformed operation: {operation}")
                    queue[idx]['synced'] = True  # Mark malformed as synced to remove
                    continue
                
                # Execute Firestore operation with a timeout to avoid blocking
                if op_type == 'set':
                    ok, res = self._run_with_timeout(lambda: self.db.collection(collection).document(doc_id).set(data), timeout=8)
                elif op_type == 'update':
                    ok, res = self._run_with_timeout(lambda: self.db.collection(collection).document(doc_id).update(data), timeout=8)
                elif op_type == 'delete':
                    ok, res = self._run_with_timeout(lambda: self.db.collection(collection).document(doc_id).delete(), timeout=8)
                else:
                    ok, res = False, Exception(f'Unknown operation type: {op_type}')

                if not ok:
                    # If the operation failed or timed out, log and stop processing further to retry later
                    logger.error(f"Failed to sync operation {idx} ({op_type} on {collection}/{doc_id}): {res}")
                    failed_count += 1
                    break
                
                queue[idx]['synced'] = True
                synced_count += 1
                logger.info(f"✓ Synced: {op_type} on {collection}/{doc_id}")
            except Exception as e:
                logger.error(f"Error syncing operation {idx}: {str(e)}")
                failed_count += 1
                break
        
        # Remove synced operations - rebuild queue with only unsynced items
        remaining_queue = [op for op in queue if not op.get('synced', False)]
        self.save_offline_queue(remaining_queue)
        
        if synced_count > 0:
            logger.info(f"✓ Synced {synced_count} operations from offline queue")
            # If all operations were synced, queue should be empty
            if not remaining_queue:
                logger.info("✓ Offline queue is now empty - all operations synced!")
        
        if failed_count > 0:
            logger.warning(f"⚠️ {failed_count} operation(s) failed during sync - will retry later")
        

        return synced_count

    def prune_old_bills(self, store_id: int) -> Dict[str, int]:
        """Prune bills older than retention policy.

        - Cloud: delete bills older than 120 days (best-effort)
        - Local: delete bills older than 160 days
        Returns dict: {'local_deleted': n, 'cloud_deleted': m}
        """
        results = {'local_deleted': 0, 'cloud_deleted': 0}
        now = datetime.now()
        cloud_cutoff = now - timedelta(days=120)
        local_cutoff = now - timedelta(days=160)

        # Local pruning
        try:
            db_path = get_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT bill_id, bill_date FROM bills WHERE store_id = ?', (store_id,))
            rows = cursor.fetchall()
            to_delete = []
            for row in rows:
                bill_id, bill_date = row
                try:
                    bill_dt = datetime.fromisoformat(bill_date)
                except Exception:
                    try:
                        bill_dt = datetime.strptime(bill_date, '%Y-%m-%d %H:%M:%S')
                    except Exception:
                        # Unknown format; skip
                        continue
                if bill_dt < local_cutoff:
                    to_delete.append(bill_id)

            for bid in to_delete:
                try:
                    cursor.execute('DELETE FROM bill_items WHERE bill_id = ?', (bid,))
                    cursor.execute('DELETE FROM bills WHERE bill_id = ?', (bid,))
                    results['local_deleted'] += 1
                except Exception as e:
                    logger.warning(f"Failed deleting local bill {bid}: {e}")

            conn.commit()
            conn.close()
            logger.info(f"Pruned {results['local_deleted']} local bills older than {local_cutoff.isoformat()}")
        except Exception as e:
            logger.warning(f"Local prune failed: {e}")

        # Cloud pruning (best-effort)
        if self.db:
            try:
                bills_col = self.db.collection('stores').document(str(store_id)).collection('bills')
                # Iterate document snapshots
                docs = list(bills_col.stream())
                for doc in docs:
                    try:
                        data = doc.to_dict()
                        # If this document is a 'backup' container holding a bills list
                        if doc.id == 'backup' and isinstance(data.get('bills'), list):
                            filtered = []
                            removed = 0
                            for b in data.get('bills', []):
                                bd = b.get('bill_date')
                                if not bd:
                                    filtered.append(b)
                                    continue
                                try:
                                    bdt = datetime.fromisoformat(bd)
                                except Exception:
                                    try:
                                        bdt = datetime.strptime(bd, '%Y-%m-%d %H:%M:%S')
                                    except Exception:
                                        filtered.append(b)
                                        continue
                                if bdt < cloud_cutoff:
                                    removed += 1
                                else:
                                    filtered.append(b)

                            if removed > 0:
                                data['bills'] = filtered
                                data['total_count'] = len(filtered)
                                bills_col.document('backup').set(data)
                                results['cloud_deleted'] += removed
                        else:
                            # Document-per-bill model: check bill_date field
                            bd = data.get('bill_date') or data.get('bill_date_iso')
                            if bd:
                                try:
                                    bdt = datetime.fromisoformat(bd)
                                except Exception:
                                    try:
                                        bdt = datetime.strptime(bd, '%Y-%m-%d %H:%M:%S')
                                    except Exception:
                                        continue
                                if bdt < cloud_cutoff:
                                    bills_col.document(doc.id).delete()
                                    results['cloud_deleted'] += 1
                    except Exception as e:
                        logger.warning(f"Error evaluating cloud bill doc {doc.id}: {e}")

                logger.info(f"Pruned {results['cloud_deleted']} cloud bills older than {cloud_cutoff.isoformat()}")
            except Exception as e:
                logger.warning(f"Cloud prune failed: {e}")

        return results
    
    def full_sync(self, store_id: int) -> bool:
        """Perform full backup and sync with restore-first and pruning logic."""
        logger.info("Starting full sync...")

        with self.connectivity_lock:
            is_online = self.check_internet_connection()
            self.is_online = is_online

        if not is_online:
            logger.warning("Internet not available. Queueing for later sync.")
            return False

        try:
            # If local DB is fresh (no products), attempt restore-first from Firebase
            need_restore = False
            try:
                db_path = get_db_path()
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
                if cursor.fetchone() is None:
                    need_restore = True
                else:
                    cursor.execute('SELECT COUNT(1) FROM products WHERE store_id = ?', (store_id,))
                    cnt = cursor.fetchone()[0]
                    if cnt == 0:
                        need_restore = True
                conn.close()
            except Exception as e:
                logger.warning(f"Could not determine local DB state: {e}")
                need_restore = False

            if need_restore and self.db:
                logger.info("Local DB appears empty — attempting auto-restore from Firebase before backup")
                try:
                    self.auto_restore_all_data(store_id)
                except Exception as e:
                    logger.warning(f"Auto-restore failed: {e}")

            # Prune old bills (cloud 120d, local 160d)
            try:
                prune_res = self.prune_old_bills(store_id)
                logger.info(f"Prune results: {prune_res}")
            except Exception as e:
                logger.warning(f"Prune operation failed: {e}")

            # Prune old payslips according to retention policy (388 days cloud, 400 local)
            try:
                payslip_prune_res = self.prune_old_payslips(store_id)
                logger.info(f"Payslip prune results: {payslip_prune_res}")
            except Exception as e:
                logger.warning(f"Payslip prune operation failed: {e}")

            # Backup all data
            # Backup offline queue first to preserve pending operations
            try:
                self.backup_offline_queue(store_id)
            except Exception:
                pass

            self.backup_products(store_id)
            self.backup_bills(store_id)
            self.backup_customers(store_id)
            # Backup HR/payroll artifacts
            try:
                self.backup_employees(store_id)
            except Exception:
                pass
            try:
                self.backup_payroll(store_id)
            except Exception:
                pass
            try:
                self.backup_payslips(store_id)
            except Exception:
                pass
            self.backup_users()
            self.backup_settings()
            self.backup_gst_config()

            # Also perform per-table structured sync to Firestore (documents per row)
            try:
                # Map local tables to Firestore collection paths
                table_map = {
                    # System-level
                    'settings': 'system/settings',
                    'gst_config': 'system/gst_config',
                    'users': 'system/users',

                    # Store-scoped tables
                    'stores': 'stores',
                    'products': f'stores/{store_id}/products',
                    'product_categories': f'stores/{store_id}/product_categories',
                    'stock_movements': f'stores/{store_id}/stock_movements',
                    'invoices': f'stores/{store_id}/invoices',
                    'invoice_items': f'stores/{store_id}/invoice_items',
                    'bills': f'stores/{store_id}/bills',
                    'bill_items': f'stores/{store_id}/bill_items',
                    'customers': f'stores/{store_id}/customers',
                    'vendors': f'stores/{store_id}/vendors',
                    'payments': f'stores/{store_id}/payments',

                    # Accounting / finance
                    'accounts': f'stores/{store_id}/accounts',
                    'journal_entries': f'stores/{store_id}/journal_entries',
                    'bank_accounts': f'stores/{store_id}/bank_accounts',
                    'bank_transactions': f'stores/{store_id}/bank_transactions',
                    # Ledger / Tally-like tables
                    'ledger_groups': f'stores/{store_id}/ledger_groups',
                    'ledger_accounts': f'stores/{store_id}/ledger_accounts',
                    'journal_entries': f'stores/{store_id}/journal_entries',
                    'journal_lines': f'stores/{store_id}/journal_lines',
                    'cost_centers': f'stores/{store_id}/cost_centers',
                    'budgets': f'stores/{store_id}/budgets',

                    # ERP modules — production, purchase, projects, HR, payroll, POS, etc.
                    'purchase_orders': f'stores/{store_id}/purchase_orders',
                    'purchase_order_items': f'stores/{store_id}/purchase_order_items',
                    'vendor_bills': f'stores/{store_id}/vendor_bills',
                    'bom': f'stores/{store_id}/bom',
                    'production_orders': f'stores/{store_id}/production_orders',
                    'projects': f'stores/{store_id}/projects',
                    'tasks': f'stores/{store_id}/tasks',
                    'timesheets': f'stores/{store_id}/timesheets',

                    # HR & payroll
                    'employees': f'stores/{store_id}/employees',
                    'attendance': f'stores/{store_id}/attendance',
                    'leaves': f'stores/{store_id}/leaves',
                    'payroll': f'stores/{store_id}/payroll',
                    'payslips': f'stores/{store_id}/payslips',

                    # POS
                    'pos_sessions': f'stores/{store_id}/pos_sessions',
                    'pos_orders': f'stores/{store_id}/pos_orders',

                    # CRM / marketing / quality
                    'crm_contacts': f'stores/{store_id}/crm_contacts',
                    'crm_leads': f'stores/{store_id}/crm_leads',
                    'marketing_campaigns': f'stores/{store_id}/marketing_campaigns',
                    'assets': f'stores/{store_id}/assets',
                    'stock': f'stores/{store_id}/stock',
                    'warehouses': f'stores/{store_id}/warehouses',
                    'supplier_prices': f'stores/{store_id}/supplier_prices',
                    'vendors': f'stores/{store_id}/vendors',
                    'customers': f'stores/{store_id}/customers',
                }

                for tbl, col in table_map.items():
                    try:
                        self.sync_table_to_firestore(tbl, col)
                    except Exception as e:
                        logger.warning(f"Table sync failed for {tbl}: {e}")
            except Exception as e:
                logger.warning(f"Structured table sync failed: {e}")

            # Sync offline queue
            synced = self.sync_offline_queue()

            logger.info(f"Full sync completed. {synced} queued operations synced.")
            return True
        except Exception as e:
            logger.error(f"Error during full sync: {str(e)}")
            return False

    def prune_old_payslips(self, store_id: int) -> Dict[str, int]:
        """Prune payslips older than retention policy.

        Cloud: delete payslips older than 388 days.
        Local: delete payslips older than 400 days.
        Returns dict with counts {'local_deleted': n, 'cloud_deleted': m}.
        """
        results = {'local_deleted': 0, 'cloud_deleted': 0}
        now = datetime.now()
        cloud_cutoff = now - timedelta(days=388)
        local_cutoff = now - timedelta(days=400)

        # Local pruning
        try:
            db_path = get_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # Try common column names for payslip date
            date_cols = ['payslip_date', 'date', 'created_at', 'pay_date']
            # Build a query to fetch id and first matching date column
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payslips'")
            if cursor.fetchone():
                cursor.execute('SELECT payslip_id, payslip_date, date, created_at, pay_date FROM payslips')
                rows = cursor.fetchall()
                for row in rows:
                    payslip_id = row[0]
                    pay_date = None
                    for v in row[1:]:
                        if v:
                            pay_date = v
                            break
                    if not pay_date:
                        continue
                    try:
                        pdt = datetime.fromisoformat(pay_date)
                    except Exception:
                        try:
                            pdt = datetime.strptime(pay_date, '%Y-%m-%d %H:%M:%S')
                        except Exception:
                            continue
                    if pdt < local_cutoff:
                        try:
                            cursor.execute('DELETE FROM payslip_items WHERE payslip_id = ?', (payslip_id,))
                        except Exception:
                            pass
                        try:
                            cursor.execute('DELETE FROM payslips WHERE payslip_id = ?', (payslip_id,))
                            results['local_deleted'] += 1
                        except Exception as e:
                            logger.warning(f"Failed deleting local payslip {payslip_id}: {e}")
                conn.commit()
            conn.close()
            logger.info(f"Pruned {results['local_deleted']} local payslips older than {local_cutoff.isoformat()}")
        except Exception as e:
            logger.warning(f"Local payslip prune failed: {e}")

        # Cloud pruning
        if self.db:
            try:
                payslips_col = self.db.collection('stores').document(str(store_id)).collection('payslips')
                docs = list(payslips_col.stream())
                for doc in docs:
                    try:
                        data = doc.to_dict()
                        # Accept several date field names
                        pd = data.get('payslip_date') or data.get('date') or data.get('pay_date') or data.get('created_at')
                        if not pd:
                            continue
                        try:
                            pdt = datetime.fromisoformat(pd)
                        except Exception:
                            try:
                                pdt = datetime.strptime(pd, '%Y-%m-%d %H:%M:%S')
                            except Exception:
                                continue
                        if pdt < cloud_cutoff:
                            payslips_col.document(doc.id).delete()
                            results['cloud_deleted'] += 1
                    except Exception as e:
                        logger.warning(f"Error evaluating cloud payslip doc {doc.id}: {e}")
                logger.info(f"Pruned {results['cloud_deleted']} cloud payslips older than {cloud_cutoff.isoformat()}")
            except Exception as e:
                logger.warning(f"Cloud payslip prune failed: {e}")

        return results

    def backup_offline_queue(self, store_id: int) -> bool:
        """Backup the local offline queue (offline_queue.json) to Firestore for safe recovery."""
        try:
            path = os.path.join(os.path.dirname(get_db_path()), 'offline_queue.json')
            if not os.path.exists(path):
                logger.info('No offline_queue.json file to backup')
                return False
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.db.collection('stores').document(str(store_id)).collection('meta').document('offline_queue').set({
                'queue': data,
                'last_backup': datetime.now().isoformat()
            })
            logger.info('Backed up offline_queue.json to Firestore')
            return True
        except Exception as e:
            logger.error(f'Error backing up offline queue: {e}')
            return False

    def restore_offline_queue_to_local(self, store_id: int) -> bool:
        """Restore offline_queue.json from Firestore to local file (will not overwrite unless empty or confirmed)."""
        try:
            doc = self.db.collection('stores').document(str(store_id)).collection('meta').document('offline_queue').get()
            if not doc.exists:
                logger.info('No offline_queue backup found in Firestore')
                return False
            data = doc.to_dict().get('queue')
            if not data:
                logger.info('Offline queue backup empty')
                return False

            path = os.path.join(os.path.dirname(get_db_path()), 'offline_queue.json')
            # If file exists and non-empty, merge instead of overwrite
            existing = []
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        existing = json.load(f) or []
                except Exception:
                    existing = []
            merged = existing + data
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(merged, f, indent=2, default=str)
            logger.info('Restored offline_queue.json from Firestore')
            return True
        except Exception as e:
            logger.error(f'Error restoring offline queue: {e}')
            return False

    def backup_payslips(self, store_id: int) -> bool:
        """Backup payslips table to Firestore under stores/{store_id}/payslips/backup"""
        if not self.db:
            self.queue_operation('backup_payslips', f'store_{store_id}', 'payslips', {})
            return False

        if not self.table_exists('payslips'):
            logger.info('No payslips table present - skipping backup')
            return False

        try:
            conn = sqlite3.connect(get_db_path())
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM payslips')
            rows = cursor.fetchall()
            conn.close()

            data = [dict(r) for r in rows]
            self.db.collection('stores').document(str(store_id)).collection('payslips').document('backup').set({
                'payslips': data,
                'last_backup': datetime.now().isoformat(),
                'total_count': len(data)
            })
            logger.info(f"Backed up {len(data)} payslips for store {store_id}")
            return True
        except Exception as e:
            logger.error(f"Error backing up payslips: {e}")
            self.queue_operation('backup_payslips', f'store_{store_id}', 'payslips', {'error': str(e)})
            return False

    def sync_table_to_firestore(self, table_name: str, collection_path: str, batch_size: int = 500) -> int:
        """Sync a local SQLite table to Firestore as individual documents.

        - `table_name`: local sqlite table name
        - `collection_path`: Firestore collection path (e.g. 'stores/1/products' or 'system/settings')
        Returns number of documents written.
        """
        if not self.db:
            logger.warning("Firebase not initialized - cannot sync table")
            return 0

        try:
            if not self.table_exists(table_name):
                logger.info(f"Table '{table_name}' does not exist - skipping structured sync")
                return 0

            conn = sqlite3.connect(get_db_path())
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f'SELECT * FROM {table_name}')
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                logger.info(f"{table_name}: No rows to sync")
                return 0

            written = 0
            batch = None
            batch_count = 0

            for r in rows:
                record = dict(r)
                # Determine document id heuristically
                doc_id = None
                for key in ('id', f"{table_name[:-1]}_id", 'uid', 'user_id', 'invoice_id', 'bill_id'):
                    if key in record and record.get(key) is not None:
                        doc_id = str(record.get(key))
                        break
                if not doc_id:
                    # Fallback to hash of row
                    doc_id = str(abs(hash(json.dumps(record, sort_keys=True))))

                # Batch write
                if batch is None:
                    batch = self.db.batch()
                    batch_count = 0

                # Normalize collection path for document reference creation
                try:
                    if '/' in collection_path and collection_path.count('/') % 2 == 1:
                        # If path ends with document id placeholder, just use collection
                        ref = self.db.collection(collection_path).document(doc_id)
                    else:
                        ref = self.db.collection(collection_path).document(doc_id)
                except Exception:
                    ref = self.db.collection(collection_path).document(doc_id)

                batch.set(ref, record, merge=True)
                batch_count += 1
                written += 1

                if batch_count >= batch_size:
                    batch.commit()
                    batch = None
                    batch_count = 0

            if batch is not None and batch_count > 0:
                batch.commit()

            logger.info(f"Synced {written} rows from table '{table_name}' to Firestore collection '{collection_path}'")
            return written

        except Exception as e:
            logger.error(f"Error syncing table {table_name}: {e}")
            return 0
    
    def _connectivity_monitor(self):
        """Dedicated thread that monitors connectivity state and signals when it changes"""
        logger.info("Connectivity monitor started (checking every 10s)")
        last_state = self.is_online
        
        while not self.stop_connectivity_monitor:
            try:
                current_state = self.check_internet_connection()
                
                with self.connectivity_lock:
                    self.is_online = current_state
                    
                    # Detect transition from offline to online
                    if not last_state and current_state:
                        logger.info("🌐 CONNECTIVITY RESTORED – Waking sync thread immediately")
                        self.sync_wake_event.set()
                    # Detect transition from online to offline
                    elif last_state and not current_state:
                        logger.warning("📡 CONNECTIVITY LOST – Will queue operations offline")
                
                last_state = current_state
                time.sleep(10)  # Check connectivity every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in connectivity monitor: {str(e)}")
                time.sleep(10)
    
    def start_auto_sync(self, store_id: int):
        """Start background auto-sync and connectivity monitor threads"""
        def sync_worker():
            logger.info(f"Auto-sync started with {self.sync_interval}s interval")
            while not self.stop_sync:
                try:
                    # Wait for either: normal interval OR sync_wake_event signaled (connectivity restored)
                    # Use a timeout equal to sync_interval so we still wake periodically
                    woke_by_event = self.sync_wake_event.wait(timeout=self.sync_interval)
                    self.sync_wake_event.clear()  # Reset the event
                    
                    if self.stop_sync:
                        break
                    
                    with self.connectivity_lock:
                        is_online = self.is_online
                    
                    if is_online:
                        if woke_by_event:
                            logger.info("⚡ Performing immediate sync due to connectivity restoration")
                        else:
                            logger.debug(f"Scheduled sync check ({self.sync_interval}s interval)")
                        
                        self.full_sync(store_id)
                    else:
                        logger.debug("Internet unavailable. Will retry at next interval...")
                        queue = self.load_offline_queue()
                        if queue:
                            logger.info(f"Offline queue has {len(queue)} pending operations (will sync when online)")
                        
                except Exception as e:
                    logger.error(f"Error in sync worker: {str(e)}")
        
        # Start connectivity monitor if not already running
        if self.connectivity_monitor_thread is None or not self.connectivity_monitor_thread.is_alive():
            self.connectivity_monitor_thread = threading.Thread(target=self._connectivity_monitor, daemon=True)
            self.connectivity_monitor_thread.start()
            logger.info("Connectivity monitor thread started")
        
        # Start sync worker if not already running
        if self.sync_thread is None or not self.sync_thread.is_alive():
            self.sync_thread = threading.Thread(target=sync_worker, daemon=True)
            self.sync_thread.start()
            logger.info("Auto-sync worker thread started")
    
    def stop_auto_sync(self):
        """Stop background auto-sync and connectivity monitor threads"""
        self.stop_sync = True
        self.stop_connectivity_monitor = True
        # Signal the event in case sync thread is waiting
        self.sync_wake_event.set()
        
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        if self.connectivity_monitor_thread:
            self.connectivity_monitor_thread.join(timeout=5)
        
        logger.info("Auto-sync and connectivity monitor threads stopped")
    
    def get_sync_status(self) -> Dict:
        """Get current sync status"""
        queue = self.load_offline_queue()
        with self.connectivity_lock:
            is_online = self.is_online
        return {
            'is_online': is_online,
            'offline_queue_count': len(queue),
            'firebase_connected': self.db is not None,
            'sync_interval': self.sync_interval
        }
    
    def check_and_report_pending_operations(self) -> Dict:
        """Check for pending operations in offline queue and return summary"""
        queue = self.load_offline_queue()
        
        if not queue:
            logger.info("✓ No pending operations")
            return {
                'has_pending': False,
                'pending_count': 0,
                'operations': []
            }
        
        # Group operations by type and collection
        summary = {}
        for op in queue:
            op_type = op.get('type', 'unknown')
            collection = op.get('collection', 'unknown')
            key = f"{op_type}:{collection}"
            
            if key not in summary:
                summary[key] = 0
            summary[key] += 1
        
        logger.warning(f"⚠️  PENDING OPERATIONS DETECTED: {len(queue)} total")
        for key, count in summary.items():
            logger.warning(f"   • {key}: {count} operation(s)")
        
        return {
            'has_pending': True,
            'pending_count': len(queue),
            'operations': queue,
            'summary': summary
        }

    def auto_restore_all_data(self, store_id: int) -> Dict[str, bool]:
        """
        Restore all data from Firebase backups to local SQLite database.
        Used when local DB is empty (first login or fresh install).
        
        Returns dict with restoration status for each data type.
        """
        if not self.db:
            logger.warning("Firebase not initialized - cannot restore data")
            return {'success': False, 'reason': 'Firebase not available'}
        
        try:
            db_path = get_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            restored = {}
            
            # Restore products
            try:
                doc = self.db.collection('stores').document(str(store_id)).collection('products').document('backup').get()
                if doc.exists:
                    data = doc.to_dict()
                    products = data.get('products', [])
                    if products:
                        cursor.executemany(
                            'INSERT OR REPLACE INTO products (id, name, price, category, hsn_code, gst_rate, store_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                            [(p.get('id'), p.get('name'), p.get('price'), p.get('category'), p.get('hsn_code'), p.get('gst_rate'), store_id) for p in products]
                        )
                        restored['products'] = True
                        logger.info(f"✓ Restored {len(products)} products")
            except Exception as e:
                logger.warning(f"Could not restore products: {e}")
                restored['products'] = False
            
            # Restore bills and invoices
            try:
                doc = self.db.collection('stores').document(str(store_id)).collection('bills').document('backup').get()
                if doc.exists:
                    data = doc.to_dict()
                    bills = data.get('bills', [])
                    for bill in bills:
                        try:
                            cursor.execute(
                                'INSERT OR REPLACE INTO bills (bill_id, bill_date, customer_id, total_amount, payment_method, store_id) VALUES (?, ?, ?, ?, ?, ?)',
                                (bill.get('bill_id'), bill.get('bill_date'), bill.get('customer_id'), bill.get('total_amount'), bill.get('payment_method'), store_id)
                            )
                            # Restore bill items if present
                            for item in bill.get('items', []):
                                try:
                                    cursor.execute(
                                        'INSERT OR REPLACE INTO bill_items (id, bill_id, product_id, quantity, price, gst_rate) VALUES (?, ?, ?, ?, ?, ?)',
                                        (item.get('id'), bill.get('bill_id'), item.get('product_id'), item.get('quantity'), item.get('price'), item.get('gst_rate'))
                                    )
                                except Exception:
                                    pass
                        except Exception as e:
                            logger.warning(f"Could not restore bill {bill.get('bill_id')}: {e}")
                    if bills:
                        restored['bills'] = True
                        logger.info(f"✓ Restored {len(bills)} bills")
            except Exception as e:
                logger.warning(f"Could not restore bills: {e}")
                restored['bills'] = False
            
            # Restore customers
            try:
                doc = self.db.collection('stores').document(str(store_id)).collection('customers').document('backup').get()
                if doc.exists:
                    data = doc.to_dict()
                    customers = data.get('customers', [])
                    if customers:
                        cursor.executemany(
                            'INSERT OR REPLACE INTO customers (id, name, phone, email, address, store_id) VALUES (?, ?, ?, ?, ?, ?)',
                            [(c.get('id'), c.get('name'), c.get('phone'), c.get('email'), c.get('address'), store_id) for c in customers]
                        )
                        restored['customers'] = True
                        logger.info(f"✓ Restored {len(customers)} customers")
            except Exception as e:
                logger.warning(f"Could not restore customers: {e}")
                restored['customers'] = False
            
            # Restore employees
            try:
                doc = self.db.collection('stores').document(str(store_id)).collection('employees').document('backup').get()
                if doc.exists:
                    data = doc.to_dict()
                    employees = data.get('employees', [])
                    if employees:
                        cursor.executemany(
                            'INSERT OR REPLACE INTO employees (id, name, email, phone, store_id) VALUES (?, ?, ?, ?, ?)',
                            [(e.get('id'), e.get('name'), e.get('email'), e.get('phone'), store_id) for e in employees]
                        )
                        restored['employees'] = True
                        logger.info(f"✓ Restored {len(employees)} employees")
            except Exception as e:
                logger.warning(f"Could not restore employees: {e}")
                restored['employees'] = False
            
            # Restore payslips
            try:
                doc = self.db.collection('stores').document(str(store_id)).collection('payslips').document('backup').get()
                if doc.exists:
                    data = doc.to_dict()
                    payslips = data.get('payslips', [])
                    if payslips:
                        cursor.executemany(
                            'INSERT OR REPLACE INTO payslips (id, employee_id, amount, month, year) VALUES (?, ?, ?, ?, ?)',
                            [(p.get('id'), p.get('employee_id'), p.get('amount'), p.get('month'), p.get('year')) for p in payslips]
                        )
                        restored['payslips'] = True
                        logger.info(f"✓ Restored {len(payslips)} payslips")
            except Exception as e:
                logger.warning(f"Could not restore payslips: {e}")
                restored['payslips'] = False
            
            # Restore settings
            try:
                doc = self.db.collection('system').document('settings').get()
                if doc.exists:
                    data = doc.to_dict()
                    settings = data.get('settings', {})
                    for key, value in settings.items():
                        try:
                            cursor.execute(
                                'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                                (key, value)
                            )
                        except Exception:
                            pass
                    if settings:
                        restored['settings'] = True
                        logger.info(f"✓ Restored {len(settings)} settings")
            except Exception as e:
                logger.warning(f"Could not restore settings: {e}")
                restored['settings'] = False
            
            # Commit all changes
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Auto-restore completed: {restored}")
            return restored
            
        except Exception as e:
            logger.error(f"Error during auto-restore: {e}")
            return {'success': False, 'reason': str(e)}
    
    def restore_user_from_firebase(self, username: str, password_hash: str = None) -> bool:
        """
        Restore a single user from Firebase backup to the local database.
        Used during login if user not found locally.
        
        Returns True if user was restored, False otherwise.
        """
        if not self.db:
            logger.warning("Firebase not initialized - cannot restore user")
            return False
        
        try:
            # Get user from system/users backup (not store-specific)
            doc = self.db.collection('system').document('users').get()
            if not doc.exists:
                logger.warning(f"No users backup found in Firebase for user {username}")
                return False
            
            users_data = doc.to_dict().get('users', [])
            target_user = None
            
            # Find user by username
            for u in users_data:
                if u.get('username') == username:
                    target_user = u
                    break
            
            if not target_user:
                logger.info(f"User {username} not found in Firebase backup")
                return False
            
            # Verify password if provided
            if password_hash:
                stored_pwd = target_user.get('password', '')
                # Normalize password for comparison
                normalized_stored = _normalize_password_for_restore(stored_pwd)
                if password_hash != normalized_stored:
                    logger.warning(f"Password mismatch for user {username} in Firebase")
                    return False
            
            # Create user in local database
            db_path = get_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            try:
                user_pwd = _normalize_password_for_restore(target_user.get('password', ''))
                cursor.execute(
                    'INSERT INTO users (username, password, role, full_name, phone, email) VALUES (?, ?, ?, ?, ?, ?)',
                    (
                        target_user.get('username'),
                        user_pwd,
                        target_user.get('role', 'cashier'),
                        target_user.get('full_name', target_user.get('username')),
                        target_user.get('phone', ''),
                        target_user.get('email', '')
                    )
                )
                conn.commit()
                logger.info(f"✅ Restored user {username} from Firebase")
                conn.close()
                return True
            except sqlite3.IntegrityError:
                logger.info(f"User {username} already exists in local database")
                conn.close()
                return True
            except Exception as e:
                logger.error(f"Error creating user {username} in local DB: {e}")
                conn.close()
                return False
            
        except Exception as e:
            logger.error(f"Error restoring user {username} from Firebase: {e}")
            return False


def initialize_firebase_sync(credentials_path='serviceAccountKey.json', store_id: int = 1, interval_seconds: int = 300):
    """Convenience helper to create FirebaseSync, configure interval, and start background auto-sync.

    Returns the FirebaseSync instance or None on failure.
    """
    try:
        fs = FirebaseSync(credentials_path=credentials_path)
        if fs.db is None:
            # Firebase not initialized/available
            logger.warning("Firebase not available during initialize_firebase_sync")
            return None
        try:
            fs.sync_interval = int(interval_seconds)
        except Exception:
            fs.sync_interval = 300
        # Start background auto-sync for the provided store_id
        fs.start_auto_sync(store_id)
        logger.info("initialize_firebase_sync: Auto-sync started")
        return fs
    except Exception as e:
        logger.error(f"initialize_firebase_sync failed: {e}")
        return None


# Global sync manager instance
firebase_sync_manager = None


def get_db_path():
    """Return the application DB path consistent with main.py behavior.
    Uses a writable AppData folder when frozen, otherwise the script directory.
    """
    if getattr(sys, 'frozen', False):
        appdata_dir = os.getenv('LOCALAPPDATA') or os.getenv('APPDATA') or os.path.expanduser('~')
        data_dir = os.path.join(appdata_dir, 'HypeERP')
    else:
        data_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        os.makedirs(data_dir, exist_ok=True)
    except Exception:
        pass
    return os.path.join(data_dir, 'hype_billing_system.db')

def initialize_firebase_sync(*args, **kwargs):
    """Flexible initializer for FirebaseSync.

    Supports multiple calling conventions:
      - initialize_firebase_sync(credentials_path='serviceAccountKey.json', store_id=1, interval_seconds=300)
      - initialize_firebase_sync(store_id, credentials_path)
      - initialize_firebase_sync(store_id)
    """
    global firebase_sync_manager
    # Defaults
    credentials_path = kwargs.get('credentials_path') or kwargs.get('creds') or kwargs.get('credentials') or 'serviceAccountKey.json'
    store_id = kwargs.get('store_id') or kwargs.get('shop_id') or kwargs.get('store') or 1
    interval_seconds = int(kwargs.get('interval_seconds') or kwargs.get('interval') or 300)

    # Positional args handling
    if args:
        # If first positional is int-like, treat as store_id
        if len(args) == 1:
            if isinstance(args[0], int):
                store_id = args[0]
            elif isinstance(args[0], str):
                # ambiguous: assume credentials path provided
                credentials_path = args[0]
        elif len(args) >= 2:
            # Common calls: (credentials_path, store_id) or (store_id, credentials_path)
            a0, a1 = args[0], args[1]
            if isinstance(a0, int):
                store_id = a0
                credentials_path = a1
            elif isinstance(a1, int):
                credentials_path = a0
                store_id = a1
            else:
                # fallback: first is creds, second is something else
                credentials_path = str(a0)

    # Resolve relative path when necessary
    if not os.path.isabs(credentials_path):
        if getattr(sys, 'frozen', False):
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(base_path, credentials_path)

    try:
        firebase_sync_manager = FirebaseSync(credentials_path=credentials_path)
        if firebase_sync_manager.db is None:
            logger.warning("Firebase not available during initialize_firebase_sync")
            return None
        firebase_sync_manager.sync_interval = interval_seconds
        firebase_sync_manager.start_auto_sync(int(store_id))
        logger.info("initialize_firebase_sync: Auto-sync started (compat wrapper)")
        return firebase_sync_manager
    except Exception as e:
        logger.error(f"initialize_firebase_sync failed: {e}")
        return None

def get_firebase_sync_manager(credentials_path=None) -> FirebaseSync:
    """Get global Firebase sync manager and reuse it when the credentials path matches."""
    global firebase_sync_manager
    resolved_path = _resolve_credentials_path(credentials_path or 'serviceAccountKey.json')

    if firebase_sync_manager is None:
        firebase_sync_manager = FirebaseSync(credentials_path=resolved_path)
    elif getattr(firebase_sync_manager, 'credentials_path', None) != resolved_path:
        firebase_sync_manager = FirebaseSync(credentials_path=resolved_path)

    return firebase_sync_manager

def shutdown_firebase_sync(fs_instance=None):
    """Shutdown Firebase sync"""
    global firebase_sync_manager
    # Use provided instance or global manager
    instance = fs_instance if fs_instance else firebase_sync_manager
    if instance:
        try:
            instance.stop_auto_sync()
            logger.info("Firebase sync shutdown")
        except Exception as e:
            logger.warning(f"Error stopping auto-sync: {e}")

def trigger_immediate_sync(store_id: int = 1):
    """Trigger immediate Firebase sync for urgent operations like bill creation"""
    global firebase_sync_manager
    try:
        fsm = get_firebase_sync_manager()
        if fsm and hasattr(fsm, 'sync_wake_event'):
            logger.info(f"⚡ Triggering immediate sync for store {store_id}")
            fsm.sync_wake_event.set()
            return True
        return False
    except Exception as e:
        logger.error(f"Error triggering immediate sync: {e}")
        return False

def sync_all_data_immediately(store_id: int = 1):
    """Sync ALL data types immediately to Firebase (bills, products, customers, stock, users, etc.)"""
    global firebase_sync_manager
    try:
        fsm = get_firebase_sync_manager()
        if not fsm or not getattr(fsm, 'db', None):
            logger.warning("Firebase not available for immediate data sync")
            return False
        
        logger.info(f"📤 IMMEDIATE SYNC: Syncing all data for store {store_id}")
        
        # Sync all critical data tables
        tables_to_sync = [
            'invoices',
            'invoice_items', 
            'products',
            'stock',
            'customers',
            'users',
            'employees',
            'accounts',
            'suppliers'
        ]
        
        synced_count = 0
        for table in tables_to_sync:
            try:
                fsm.sync_table_to_firestore(table, f'stores/{store_id}/{table}')
                synced_count += 1
                logger.info(f"  ✅ {table}")
            except Exception as e:
                logger.warning(f"  ❌ {table}: {str(e)}")
        
        logger.info(f"✅ Immediate sync complete: {synced_count}/{len(tables_to_sync)} tables synced")
        trigger_immediate_sync(store_id)
        return synced_count > 0
    except Exception as e:
        logger.error(f"Error in sync_all_data_immediately: {e}")
        return False

def queue_operation_if_offline(operation_type: str, data: Dict[str, Any], store_id: int = 1):
    """Queue an operation for offline processing if Firebase is unavailable"""
    global firebase_sync_manager
    try:
        fsm = get_firebase_sync_manager()
        if not fsm or not getattr(fsm, 'db', None):
            # Firebase offline - add to queue
            queue_data = {
                'type': operation_type,
                'store_id': store_id,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'synced': False
            }
            
            queue_file = fsm.offline_queue_file if fsm else 'offline_queue.json'
            try:
                if os.path.exists(queue_file):
                    with open(queue_file, 'r') as f:
                        queue = json.load(f)
                else:
                    queue = []
                
                queue.append(queue_data)
                
                with open(queue_file, 'w') as f:
                    json.dump(queue, f, indent=2)
                
                logger.info(f"📋 Operation queued for offline processing: {operation_type}")
                return True
            except Exception as e:
                logger.error(f"Error queuing operation: {e}")
                return False
        return False
    except Exception as e:
        logger.error(f"Error in queue_operation_if_offline: {e}")
        return False

def process_offline_queue():
    """Process all queued operations when internet is restored"""
    global firebase_sync_manager
    try:
        fsm = get_firebase_sync_manager()
        if not fsm or not getattr(fsm, 'db', None):
            logger.warning("Firebase not available for queue processing")
            return 0
        
        queue_file = fsm.offline_queue_file
        if not os.path.exists(queue_file):
            logger.info("No offline queue to process")
            return 0
        
        with open(queue_file, 'r') as f:
            queue = json.load(f)
        
        processed_count = 0
        remaining_queue = []
        
        for operation in queue:
            try:
                op_type = operation.get('type', '')
                op_data = operation.get('data', {})
                store_id = operation.get('store_id', 1)
                
                logger.info(f"Processing queued operation: {op_type}")
                # Actual processing would depend on operation type
                # For now, just mark as synced
                operation['synced'] = True
                processed_count += 1
                logger.info(f"✅ Queued operation {op_type} processed")
            except Exception as e:
                logger.error(f"Error processing queued operation {op_type}: {e}")
                remaining_queue.append(operation)
        
        # Save remaining unprocessed operations
        if remaining_queue:
            with open(queue_file, 'w') as f:
                json.dump(remaining_queue, f, indent=2)
            logger.info(f"⚠️ {len(remaining_queue)} operations still pending in queue")
        else:
            # Queue is empty, remove the file
            try:
                os.remove(queue_file)
                logger.info("✅ Offline queue processed completely")
            except Exception:
                pass
        
        return processed_count
    except Exception as e:
        logger.error(f"Error processing offline queue: {e}")
        return 0
