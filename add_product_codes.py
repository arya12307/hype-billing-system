#!/usr/bin/env python3
"""Add product codes to existing products"""

import sqlite3
from datetime import datetime

db_path = 'hype_billing_system.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Adding product codes to existing products...")
print("-" * 60)

# Get all products without codes
cursor.execute('SELECT product_id, product_name FROM products WHERE product_code IS NULL OR product_code = ""')
products = cursor.fetchall()

print(f"Found {len(products)} products without codes\n")

# Generate codes and update
for i, (product_id, product_name) in enumerate(products, 1):
    # Generate code from product name (first 3 letters + product_id)
    code = f"{product_name[:3].upper()}{product_id:04d}"
    cursor.execute('UPDATE products SET product_code = ? WHERE product_id = ?', (code, product_id))
    print(f"  {i}. {product_name} -> Code: {code}")

conn.commit()

# Verify
print("\nVerifying updated products:")
cursor.execute('SELECT product_id, product_code, product_name FROM products LIMIT 5')
for row in cursor.fetchall():
    print(f"  ID: {row[0]}, Code: {row[1]}, Name: {row[2]}")

conn.close()

print("\n✅ Product codes added successfully!")
print("\nNext step: Run the app - it will backup these products with codes to Firebase")
