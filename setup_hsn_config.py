#!/usr/bin/env python3
"""
HSN Code Configuration Setup for Hype ERP
Automatically creates and populates HSN code mappings for all product categories
"""

import sqlite3
import sys
import os

# HSN codes for standard Indian product categories (as per GST classification)
DEFAULT_HSN_MAPPING = {
    'Cosmetics': '3304',
    'Grocery': '0901',
    'Drinks': '2202',
    'Electronics': '8471',
    'Clothing': '6201',
    'Food & Beverage': '1905',
    'Dairy': '0401',
    'Pharmaceuticals': '3004',
    'Automotive': '8704',
    'Furniture': '9403',
    'Books': '4901',
    'Education Services': '9209',
    'Healthcare': '6211',
    'Agriculture': '1001',
    'Construction': '6810',
    'Metals': '7208',
    'Chemicals': '2817',
    'Tobacco': '2402',
    'Services': '9999',
    'Petroleum Products': '2710',
}

def setup_hsn_config(db_path='hype_billing_system.db'):
    """Setup HSN configuration in database"""
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Create table if not exists
        c.execute("""
            CREATE TABLE IF NOT EXISTS category_hsn_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT UNIQUE NOT NULL,
                hsn_code TEXT NOT NULL,
                description TEXT,
                gst_rate REAL DEFAULT 18.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default mappings
        for category, hsn in DEFAULT_HSN_MAPPING.items():
            try:
                c.execute("""
                    INSERT OR REPLACE INTO category_hsn_mapping 
                    (category, hsn_code)
                    VALUES (?, ?)
                """, (category, hsn))
                print(f'✓ {category}: {hsn}')
            except Exception as e:
                print(f'✗ Error inserting {category}: {e}')
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f'ERROR: Failed to setup HSN configuration: {e}')
        return False

def apply_hsn_to_products(db_path='hype_billing_system.db'):
    """Apply HSN codes to existing products based on category"""
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Get all categories
        c.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL")
        categories = c.fetchall()
        
        applied = 0
        for (category,) in categories:
            # Get HSN for this category
            c.execute("SELECT hsn_code FROM category_hsn_mapping WHERE category=?", (category,))
            result = c.fetchone()
            
            if result:
                hsn = result[0]
                # Update products without HSN code
                c.execute("UPDATE products SET hsn_code=? WHERE category=? AND (hsn_code IS NULL OR hsn_code='')",
                         (hsn, category))
                updated = c.rowcount
                if updated > 0:
                    print(f'✓ Applied HSN {hsn} to {updated} products in category "{category}"')
                    applied += updated
        
        conn.commit()
        conn.close()
        print(f'\nTotal: Applied HSN codes to {applied} products')
        return True
        
    except Exception as e:
        print(f'ERROR: Failed to apply HSN codes: {e}')
        return False

if __name__ == '__main__':
    db = 'hype_billing_system.db'
    if len(sys.argv) > 1:
        db = sys.argv[1]
    
    print('='*60)
    print('HSN Code Configuration Setup for Hype ERP')
    print('='*60)
    
    print('\n1. Setting up HSN code mappings...')
    print('-'*60)
    if setup_hsn_config(db):
        print(f'✓ HSN mapping table created/updated')
    else:
        sys.exit(1)
    
    print('\n2. Applying HSN codes to existing products...')
    print('-'*60)
    if apply_hsn_to_products(db):
        print('✓ HSN codes applied to products')
    else:
        sys.exit(1)
    
    print('\n'+'='*60)
    print('✓ HSN Configuration Setup Complete!')
    print('='*60)
    print('\nNext steps:')
    print('1. Run the app: python main.py')
    print('2. Go to Billing → HSN Code Configuration')
    print('3. Manage and customize HSN codes for your categories')
    print('4. Use "Apply to Products" button to update all products')
    print('='*60)
