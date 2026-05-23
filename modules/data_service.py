# Hype ERP - Unified Data Service
# Connects all modules - single source of truth for shared data
# Developer: David | Nexuzy Lab
import sqlite3
from datetime import datetime

class DataService:
    """Unified data service that all ERP modules use to access shared data"""
    
    def __init__(self, db_path="hype_billing_system.db"):
        self.db_path = db_path
        self._init_shared_schema()
    
    def _init_shared_schema(self):
        """Initialize shared tables across all modules"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.executescript("""
            -- ═══════════════════════════════════════════════════════════════════════════
            -- VENDORS TABLE - Single source of truth for vendor data
            -- ═══════════════════════════════════════════════════════════════════════════
            CREATE TABLE IF NOT EXISTS vendors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                company TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                postal_code TEXT,
                gstin TEXT,
                pan TEXT,
                bank_account TEXT,
                bank_name TEXT,
                ifsc_code TEXT,
                credit_limit REAL DEFAULT 0.0,
                payment_terms INTEGER DEFAULT 30,
                tax_id TEXT,
                contact_person TEXT,
                contact_phone TEXT,
                notes TEXT,
                status TEXT DEFAULT 'Active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- ═══════════════════════════════════════════════════════════════════════════
            -- CUSTOMERS TABLE - Single source of truth for customer data
            -- ═══════════════════════════════════════════════════════════════════════════
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                company TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                postal_code TEXT,
                gstin TEXT,
                pan TEXT,
                credit_limit REAL DEFAULT 0.0,
                credit_days INTEGER DEFAULT 30,
                contact_person TEXT,
                contact_phone TEXT,
                notes TEXT,
                status TEXT DEFAULT 'Active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- ═══════════════════════════════════════════════════════════════════════════
            -- PRODUCTS TABLE - Single source of truth for product master data
            -- ═══════════════════════════════════════════════════════════════════════════
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT,
                unit TEXT,
                hsn_code TEXT,
                gst_rate REAL DEFAULT 18.0,
                cost_price REAL DEFAULT 0,
                selling_price REAL DEFAULT 0,
                quantity INTEGER DEFAULT 0,
                reorder_level INTEGER DEFAULT 10,
                description TEXT,
                status TEXT DEFAULT 'Active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- ═══════════════════════════════════════════════════════════════════════════
            -- MODULES_REGISTRY - Track which modules are connected
            -- ═══════════════════════════════════════════════════════════════════════════
            CREATE TABLE IF NOT EXISTS modules_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_name TEXT UNIQUE NOT NULL,
                module_code TEXT,
                status TEXT DEFAULT 'Active',
                last_sync TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
    
    def get_vendors(self):
        """Get list of all active vendors"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("""SELECT id, name, phone, email, gstin FROM vendors 
                        WHERE status='Active' OR status IS NULL ORDER BY name""")
            vendors = [dict(row) for row in c.fetchall()]
            conn.close()
            return vendors
        except Exception as e:
            print(f"Error fetching vendors: {e}")
            return []
    
    def get_vendor_by_id(self, vendor_id):
        """Get vendor details by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM vendors WHERE id=?", (vendor_id,))
            vendor = c.fetchone()
            conn.close()
            return dict(vendor) if vendor else None
        except Exception as e:
            print(f"Error fetching vendor: {e}")
            return None
    
    def get_vendor_by_name(self, vendor_name):
        """Get vendor by name"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT id FROM vendors WHERE name=?", (vendor_name,))
            vendor = c.fetchone()
            conn.close()
            return dict(vendor) if vendor else None
        except Exception as e:
            print(f"Error fetching vendor by name: {e}")
            return None
    
    def add_vendor(self, vendor_data):
        """Add new vendor (called from Vendor Module)"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                INSERT INTO vendors 
                (name, company, email, phone, address, city, state, postal_code, gstin, pan, 
                 bank_account, bank_name, ifsc_code, credit_limit, payment_terms, contact_person, contact_phone, notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                vendor_data.get('name'),
                vendor_data.get('company'),
                vendor_data.get('email'),
                vendor_data.get('phone'),
                vendor_data.get('address'),
                vendor_data.get('city'),
                vendor_data.get('state'),
                vendor_data.get('postal_code'),
                vendor_data.get('gstin'),
                vendor_data.get('pan'),
                vendor_data.get('bank_account'),
                vendor_data.get('bank_name'),
                vendor_data.get('ifsc_code'),
                vendor_data.get('credit_limit', 0),
                vendor_data.get('payment_terms', 30),
                vendor_data.get('contact_person'),
                vendor_data.get('contact_phone'),
                vendor_data.get('notes')
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding vendor: {e}")
            return False
    
    def get_customer_by_id(self, customer_id):
        """Get customer details by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM customers WHERE id=?", (customer_id,))
            customer = c.fetchone()
            conn.close()
            return dict(customer) if customer else None
        except Exception as e:
            print(f"Error fetching customer: {e}")
            return None
    
    def get_customers(self):
        """Get list of all active customers"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            try:
                c.execute("""SELECT id, name, phone, email, gstin FROM customers 
                            WHERE status='Active' OR status IS NULL ORDER BY name""")
            except:
                # If query fails, table might not have status column - try without it
                c.execute("SELECT id, name, phone, email, gstin FROM customers ORDER BY name")
            customers = [dict(row) for row in c.fetchall()]
            conn.close()
            return customers
        except Exception as e:
            print(f"Error fetching customers: {e}")
            return []
    
    def add_customer(self, customer_data):
        """Add new customer (called from CRM/Sales Module)"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                INSERT INTO customers 
                (name, company, email, phone, address, city, state, postal_code, gstin, pan, credit_limit, credit_days, contact_person, contact_phone, notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                customer_data.get('name'),
                customer_data.get('company'),
                customer_data.get('email'),
                customer_data.get('phone'),
                customer_data.get('address'),
                customer_data.get('city'),
                customer_data.get('state'),
                customer_data.get('postal_code'),
                customer_data.get('gstin'),
                customer_data.get('pan'),
                customer_data.get('credit_limit', 0),
                customer_data.get('credit_days', 30),
                customer_data.get('contact_person'),
                customer_data.get('contact_phone'),
                customer_data.get('notes')
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding customer: {e}")
            return False
    
    def get_products(self):
        """Get list of all active products"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            try:
                c.execute("""SELECT id, sku, name, category, unit, gst_rate, selling_price, quantity FROM products 
                            WHERE status='Active' OR status IS NULL ORDER BY name""")
            except:
                # If query fails, table might not have these columns - try simpler query
                c.execute("SELECT id, name, gst_rate, selling_price FROM products ORDER BY name")
            products = [dict(row) for row in c.fetchall()]
            conn.close()
            return products
        except Exception as e:
            print(f"Error fetching products: {e}")
            return []
    
    def get_product_by_id(self, product_id):
        """Get product details by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM products WHERE id=?", (product_id,))
            product = c.fetchone()
            conn.close()
            return dict(product) if product else None
        except Exception as e:
            print(f"Error fetching product: {e}")
            return None
    
    def add_product(self, product_data):
        """Add new product (called from Inventory Module)"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                INSERT INTO products 
                (sku, name, category, unit, hsn_code, gst_rate, cost_price, selling_price, quantity, reorder_level, description)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                product_data.get('sku'),
                product_data.get('name'),
                product_data.get('category'),
                product_data.get('unit'),
                product_data.get('hsn_code'),
                product_data.get('gst_rate', 18.0),
                product_data.get('cost_price', 0),
                product_data.get('selling_price', 0),
                product_data.get('quantity', 0),
                product_data.get('reorder_level', 10),
                product_data.get('description')
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding product: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # HSN CODE MANAGEMENT - Category-based HSN code mapping
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_hsn_for_category(self, category):
        """Get HSN code for a specific category"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT hsn_code FROM category_hsn_mapping WHERE category=?", (category,))
            result = c.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            print(f"Error fetching HSN for category {category}: {e}")
            return None
    
    def get_all_category_hsn_mapping(self):
        """Get all category-HSN mappings"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT category, hsn_code, gst_rate FROM category_hsn_mapping ORDER BY category")
            mappings = {row['category']: row['hsn_code'] for row in c.fetchall()}
            conn.close()
            return mappings
        except Exception as e:
            print(f"Error fetching category-HSN mappings: {e}")
            return {}
    
    def apply_hsn_to_products(self, category=None):
        """Apply HSN codes to products based on category mapping"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            if category:
                # Apply to specific category
                hsn = self.get_hsn_for_category(category)
                if hsn:
                    c.execute("UPDATE products SET hsn_code=? WHERE category=? AND (hsn_code IS NULL OR hsn_code='')",
                             (hsn, category))
            else:
                # Apply to all products without HSN codes
                c.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL")
                categories = c.fetchall()
                for (cat,) in categories:
                    hsn = self.get_hsn_for_category(cat)
                    if hsn:
                        c.execute("UPDATE products SET hsn_code=? WHERE category=? AND (hsn_code IS NULL OR hsn_code='')",
                                 (hsn, cat))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error applying HSN to products: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MODULE REGISTRY - Track which modules are using this data service
    # ═══════════════════════════════════════════════════════════════════════════
    
    def register_module(self, module_name, module_code):
        """Register a module as using this data service"""
        import time
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("PRAGMA journal_mode=WAL")
                c = conn.cursor()
                c.execute("""
                    INSERT OR REPLACE INTO modules_registry (module_name, module_code, last_sync)
                    VALUES (?, ?, ?)
                """, (module_name, module_code, datetime.now().isoformat()))
                conn.commit()
                conn.close()
                return True
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e):
                    retry_count += 1
                    if retry_count < max_retries:
                        time.sleep(0.5)
                    else:
                        print(f'Error registering module: database is locked after {max_retries} retries')
                        return False
                else:
                    print(f"Error registering module: {e}")
                    return False
            except Exception as e:
                print(f"Error registering module: {e}")
                return False
    
    def get_registered_modules(self):
        """Get list of modules that are connected"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT module_name, module_code, status FROM modules_registry ORDER BY module_name")
            modules = [dict(row) for row in c.fetchall()]
            conn.close()
            return modules
        except Exception as e:
            print(f"Error fetching modules: {e}")
            return []


# ═══════════════════════════════════════════════════════════════════════════
# Global DataService Instance - Use this in all modules
# ═══════════════════════════════════════════════════════════════════════════
_data_service = None

def get_data_service(db_path="hype_billing_system.db"):
    """Get or create the global data service instance"""
    global _data_service
    if _data_service is None:
        _data_service = DataService(db_path)
    return _data_service
