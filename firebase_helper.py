"""
Firebase Firestore Complete ERP Data Sync & Configuration
Version: 1.0
Developer: David

Stores all ERP modules data:
- Products, Invoices, Accounts
- Stock Movements, Users, Settings
- Tax Configurations, Journal Entries
- All transactions and operations
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from datetime import datetime
import sqlite3
from typing import Tuple, Optional

def initialize_firestore_collections(db):
    """Initialize all Firestore collections for ERP data storage"""
    try:
        collections_to_init = {
            'system': {'app': 'Hype ERP', 'version': '3.0.0', 'created': datetime.now().isoformat()},
            'shops': {'default': {'name': 'Default Shop', 'status': 'active'}},
        }
        
        for col, doc_data in collections_to_init.items():
            db.collection(col).document('config').set(doc_data, merge=True)
        
        print("✅ Firestore collections initialized")
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def sync_all_erp_data(sqlite_db_path, credentials_path, shop_id='default'):
    """
    Comprehensive sync of ALL ERP data to Firebase:
    ✓ Products
    ✓ Invoices & Bill Items
    ✓ Stock Movements
    ✓ Accounts & Journal Entries
    ✓ Users & Roles
    ✓ Tax Configurations
    ✓ Settings & Configurations
    ✓ Customers & Vendors
    """
    try:
        try:
            firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        conn = sqlite3.connect(sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        def table_exists_sql(cursor, name):
            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
                return cursor.fetchone() is not None
            except Exception:
                return False

        # Resolve common billing table name variations (bills vs invoices)
        def resolve_table(options):
            for opt in options:
                if table_exists_sql(cursor, opt):
                    return opt
            return None

        invoices_table = resolve_table(['invoices', 'bills'])
        invoice_items_table = resolve_table(['invoice_items', 'bill_items'])

        tables_to_sync = [
            ('products', f'shops/{shop_id}/products'),
            (invoices_table, f'shops/{shop_id}/invoices') if invoices_table else None,
            ('accounts', f'shops/{shop_id}/accounts'),
            ('journal_entries', f'shops/{shop_id}/journal_entries'),
            ('stock_movements', f'shops/{shop_id}/stock_movements'),
            ('users', 'system/users'),
            (invoice_items_table, f'shops/{shop_id}/invoice_items') if invoice_items_table else None,
            ('customers', f'shops/{shop_id}/customers'),
            ('vendors', f'shops/{shop_id}/vendors'),
            ('settings', 'system/settings'),
            ('gst_config', 'system/gst_config'),
        ]

        # Remove None entries and ensure unique tables
        tables_to_sync = [t for t in tables_to_sync if t]
        
        synced_count = 0
        
        for table_name, collection_path in tables_to_sync:
            try:
                cursor.execute(f'SELECT * FROM {table_name} LIMIT 1000')
                records = cursor.fetchall()
                
                if not records:
                    print(f"⊘ {table_name}: No data")
                    continue
                
                batch = db.batch()
                batch_count = 0
                
                for record in records:
                    record_dict = dict(record)
                    record_id = record_dict.get('id') or record_dict.get(f'{table_name[:-1]}_id') or str(hash(str(record_dict)))
                    
                    ref = db.collection(collection_path).document(str(record_id))
                    batch.set(ref, record_dict, merge=True)
                    batch_count += 1
                    synced_count += 1
                
                if batch_count > 0:
                    batch.commit()
                    print(f"✅ {table_name}: {batch_count} records synced")
            
            except sqlite3.OperationalError:
                print(f"⊘ {table_name}: Table doesn't exist (skipped)")
            except Exception as e:
                print(f"⚠ {table_name}: {str(e)}")
        
        conn.close()
        print(f"\n✅ Total synced: {synced_count} records to Firebase")
        return True
    
    except Exception as e:
        print(f"✗ Sync failed: {str(e)}")
        return False


def initialize_firestore_client(credentials_path: str):
    """Initialize Firebase app and return Firestore client."""
    try:
        try:
            app = firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate(credentials_path)
            app = firebase_admin.initialize_app(cred)
        db = firestore.client()
        return app, db
    except Exception as e:
        print(f"✗ Firebase init failed: {str(e)}")
        return None, None


def save_document(db, collection_path: str, doc_id: str, data: dict, merge: bool = True) -> bool:
    """Save a single document to Firestore."""
    try:
        if db is None:
            raise ValueError("Firestore client is not initialized")
        db.collection(collection_path).document(str(doc_id)).set(data, merge=merge)
        return True
    except Exception as e:
        print(f"✗ save_document failed: {str(e)}")
        return False


def save_table_from_sqlite(db, conn: sqlite3.Connection, table_name: str, collection_path: str, limit: Optional[int] = None) -> int:
    """Save rows from an SQLite table into a Firestore collection. Returns number of records saved."""
    cursor = conn.cursor()
    try:
        q = f"SELECT * FROM {table_name}"
        if limit:
            q += f" LIMIT {limit}"
        cursor.execute(q)
        rows = cursor.fetchall()
        if not rows:
            print(f"⊘ {table_name}: No data")
            return 0

        batch = db.batch()
        count = 0
        for row in rows:
            # Convert sqlite Row or tuple to dict if possible
            if hasattr(row, 'keys'):
                record = dict(row)
            else:
                # Fallback: map by column names
                cols = [c[0] for c in cursor.description]
                record = dict(zip(cols, row))

            record_id = record.get('id') or record.get(f'{table_name[:-1]}_id') or str(hash(str(record)))
            ref = db.collection(collection_path).document(str(record_id))
            batch.set(ref, record, merge=True)
            count += 1
            # Commit in batches of 500
            if count % 500 == 0:
                batch.commit()
                batch = db.batch()

        if count % 500 != 0:
            batch.commit()

        print(f"✅ {table_name}: {count} records saved to {collection_path}")
        return count

    except sqlite3.OperationalError:
        print(f"⊘ {table_name}: Table doesn't exist (skipped)")
        return 0
    except Exception as e:
        print(f"⚠ {table_name}: {str(e)}")
        return 0


def save_settings(credentials_path: str, sqlite_db_path: str, shop_id: str = 'default') -> bool:
    """Convenience wrapper to save `settings` and `gst_config` tables."""
    app, db = initialize_firestore_client(credentials_path)
    if db is None:
        return False
    conn = sqlite3.connect(sqlite_db_path)
    conn.row_factory = sqlite3.Row
    total = 0
    total += save_table_from_sqlite(db, conn, 'settings', 'system/settings')
    total += save_table_from_sqlite(db, conn, 'gst_config', 'system/gst_config')
    conn.close()
    print(f"📦 Total settings records saved: {total}")
    return True


def save_billing_tables(credentials_path: str, sqlite_db_path: str, shop_id: str = 'default') -> int:
    """Save invoices/bills and invoice items for a shop."""
    app, db = initialize_firestore_client(credentials_path)
    if db is None:
        return 0
    conn = sqlite3.connect(sqlite_db_path)
    conn.row_factory = sqlite3.Row
    def resolve(cursor, options):
        for o in options:
            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (o,))
                if cursor.fetchone():
                    return o
            except Exception:
                continue
        return None

    cursor = conn.cursor()
    invoices_table = resolve(cursor, ['invoices', 'bills'])
    invoice_items_table = resolve(cursor, ['invoice_items', 'bill_items'])
    saved = 0
    if invoices_table:
        saved += save_table_from_sqlite(db, conn, invoices_table, f'shops/{shop_id}/invoices')
    if invoice_items_table:
        saved += save_table_from_sqlite(db, conn, invoice_items_table, f'shops/{shop_id}/invoice_items')
    conn.close()
    print(f"📊 Billing records saved: {saved}")
    return saved

def validate_firebase_config(credentials_path):
    """Validate Firebase credentials"""
    try:
        if not os.path.exists(credentials_path):
            print(f"✗ Credentials not found: {credentials_path}")
            return False, "File not found"
        
        with open(credentials_path, 'r') as f:
            config = json.load(f)
        
        required = ['type', 'project_id', 'private_key', 'client_email']
        if not all(k in config for k in required):
            print(f"✗ Missing required fields in credentials")
            return False, "Invalid credentials"
        
        print(f"✅ Valid Firebase credentials for project: {config['project_id']}")
        return True, config['project_id']
    
    except Exception as e:
        print(f"✗ Validation error: {str(e)}")
        return False, str(e)

def test_firebase_write(db):
    """Test Firebase write capability"""
    try:
        test_data = {'test': True, 'timestamp': datetime.now().isoformat()}
        db.collection('_tests').document('write_test').set(test_data)
        print("✅ Firebase write test successful")
        return True
    except Exception as e:
        print(f"✗ Write test failed: {str(e)}")
        return False

def get_firestore_rules():
    """Return Firestore security rules (v2)"""
    return """rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow authenticated users to read all data
    match /{document=**} {
      allow read: if request.auth != null;
    }
    
    // Shop data - only owner can write
    match /shops/{shopId} {
      allow read: if request.auth != null;
      allow write: if request.auth.uid == resource.data.owner_uid || request.auth.uid == request.resource.data.owner_uid;
      
      // All sub-collections
      match /{document=**} {
        allow read: if request.auth != null;
        allow create, update, delete: if request.auth != null && get(/databases/$(database)/documents/shops/$(shopId)).data.owner_uid == request.auth.uid;
      }
    }
    
    // User profiles
    match /users/{userId} {
      allow read: if request.auth.uid == userId;
      allow write: if request.auth.uid == userId;
    }
    
    // System settings
    match /system/{document=**} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && request.auth.token.admin == true;
    }
  }
}"""

if __name__ == '__main__':
    print("Hype ERP Firebase Helper v3.0.0")
    print("="*50)
    
    creds_path = 'serviceAccountKey.json'
    db_path = 'hype_billing_system.db'
    
    # Step 1: Validate credentials
    valid, project = validate_firebase_config(creds_path)
    if not valid:
        exit(1)
    
    # Step 2: Initialize Firebase
    try:
        cred = credentials.Certificate(creds_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
    except Exception as e:
        print(f"✗ Firebase init failed: {str(e)}")
        exit(1)
    
    # Step 3: Test write
    if not test_firebase_write(db):
        exit(1)
    
    # Step 4: Initialize collections
    if not initialize_firestore_collections(db):
        exit(1)
    
    # Step 5: Sync all ERP data
    print("\n📊 Starting comprehensive ERP data sync...")
    sync_all_erp_data(db_path, creds_path)
    
    print("\n✅ Firebase setup complete!")
