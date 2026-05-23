#!/usr/bin/env python3
"""
Firebase Sync Verification Script
Tests all upload and download functionality
"""

import sqlite3
import json
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_db_path():
    """Get database path"""
    if getattr(sys, 'frozen', False):
        appdata_dir = os.getenv('LOCALAPPDATA') or os.path.expanduser('~')
        data_dir = os.path.join(appdata_dir, 'HypeERP')
    else:
        data_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(data_dir, 'hype_billing_system.db')

def test_firebase_upload():
    """Test Firebase upload functionality"""
    print("=" * 70)
    print("FIREBASE UPLOAD & LOAD TEST")
    print("=" * 70)
    
    try:
        from firebase_sync import get_firebase_sync_manager
        from firebase_upload_manager import get_upload_manager
        
        # Initialize Firebase sync
        db_path = get_db_path()
        print(f"\n📁 Database path: {db_path}")
        print(f"📁 Database exists: {os.path.exists(db_path)}")
        
        if not os.path.exists(db_path):
            print("❌ Database not found. Please run the application first.")
            return False
        
        # Get Firebase sync manager
        try:
            creds_path = os.path.join(os.path.dirname(db_path), 'serviceAccountKey.json')
            fsm = get_firebase_sync_manager(credentials_path=creds_path)
            print(f"✅ Firebase sync manager initialized")
        except Exception as e:
            print(f"❌ Could not initialize Firebase: {e}")
            return False
        
        if not fsm or not getattr(fsm, 'db', None):
            print("❌ Firebase database not connected")
            return False
        
        print(f"✅ Firebase database connected")
        
        # Get upload manager
        upload_mgr = get_upload_manager(fsm)
        print(f"✅ Upload manager initialized")
        
        # Check what data exists in local database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        tables_to_check = ['products', 'invoices', 'customers', 'users', 'stock']
        data_summary = {}
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                data_summary[table] = count
                print(f"  📊 {table}: {count} records")
            except:
                data_summary[table] = 0
        
        conn.close()
        
        # Test upload
        print("\n🚀 Testing UPLOAD to Firebase...")
        store_id = 1
        
        upload_results = upload_mgr.upload_all_data(store_id, db_path)
        
        print(f"\n📤 Upload Results:")
        for data_type, success in upload_results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {data_type}")
        
        # Test download
        print(f"\n📥 Testing DOWNLOAD from Firebase...")
        
        load_results = upload_mgr.load_all_data(store_id, db_path)
        
        print(f"\n📥 Download Results:")
        for data_type, success in load_results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {data_type}")
        
        # Test offline queue
        print(f"\n📋 Checking Offline Queue...")
        queue = fsm.load_offline_queue()
        print(f"  Queue size: {len(queue)} operations")
        if queue:
            print(f"  Queue preview (first 3):")
            for op in queue[:3]:
                print(f"    - {op.get('type')} on {op.get('collection')}/{op.get('doc_id')}")
        
        # Final status
        print("\n" + "=" * 70)
        print("✅ FIREBASE VERIFICATION COMPLETE")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_firebase_upload()
    sys.exit(0 if success else 1)
