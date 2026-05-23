#!/usr/bin/env python3
"""Add bill_number column to purchase_orders if missing"""
import sqlite3

db_path = 'hype_billing_system.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute('ALTER TABLE purchase_orders ADD COLUMN bill_number TEXT')
    print('✓ Added bill_number column')
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print('✓ bill_number column already exists')
    else:
        print(f'Error: {e}')

conn.commit()
conn.close()

# Verify
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute('PRAGMA table_info(purchase_orders)')
cols = [col[1] for col in c.fetchall()]
print(f'✓ bill_number in columns: {"bill_number" in cols}')
print(f'✓ Total columns: {len(cols)}')
conn.close()
