#!/usr/bin/env python3
"""Check if product codes are stored in database and Firebase"""

import sqlite3
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from datetime import datetime

# Setup
script_dir = os.path.dirname(os.path.abspath(__file__))
cred_path = os.path.join(script_dir, 'serviceAccountKey.json')
db_path = os.path.join(script_dir, 'hype_billing_system.db')

print("="*60)
print("PRODUCT CODE VERIFICATION")
print("="*60)

# 1. Check local database
print("\n1. LOCAL DATABASE CHECK")
print("-" * 60)
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table structure
    cursor.execute("PRAGMA table_info(products)")
    columns = cursor.fetchall()
    print("Product table columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Get sample products
    cursor.execute("SELECT product_id, product_code, product_name, price, mrp, unit FROM products LIMIT 5")
    products = cursor.fetchall()
    print("\nSample products in database:")
    for p in products:
        print(f"  ID: {p[0]}, Code: {p[1]}, Name: {p[2]}, Price: {p[3]}, MRP: {p[4]}, Unit: {p[5]}")
    
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")

# 2. Check Firebase backup
print("\n2. FIREBASE BACKUP CHECK")
print("-" * 60)
try:
    # Initialize Firebase if not already done
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    doc = db.collection('stores').document('1').collection('products').document('backup').get()
    
    if doc.exists:
        data = doc.to_dict()
        if 'products' in data:
            products = data['products']
            print(f"Found {len(products)} products in Firebase backup\n")
            print("Sample products in Firebase:")
            for p in products[:3]:
                print(f"  ID: {p.get('product_id')}, Code: {p.get('product_code')}, Name: {p.get('product_name')}")
                print(f"    Price: {p.get('price')}, MRP: {p.get('mrp')}, Unit: {p.get('unit')}")
        else:
            print("No 'products' key in backup document")
    else:
        print("No backup document found in Firebase")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "="*60)
print("SUMMARY:")
print("="*60)
print("""
If product codes show as "None" in local DB:
  1. Old backup data didn't include product codes
  2. Need to update products with codes and sync again
  
SOLUTION:
  1. Run the app
  2. Edit products to add product codes
  3. Auto-sync will backup new data with codes
  4. When restored, codes will be included
""")
print("="*60)
