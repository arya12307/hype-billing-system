import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import main as app


class LoginRestoreFlowTests(unittest.TestCase):
    def test_restore_all_data_before_login_when_local_db_is_empty(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, 'hype_billing_system.db')
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute('CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT DEFAULT \"cashier\" )')
            c.execute('CREATE TABLE products (id INTEGER PRIMARY KEY AUTOINCREMENT, store_id INTEGER)')
            c.execute('CREATE TABLE customers (id INTEGER PRIMARY KEY AUTOINCREMENT, store_id INTEGER)')
            c.execute('CREATE TABLE invoices (id INTEGER PRIMARY KEY AUTOINCREMENT, store_id INTEGER)')
            conn.commit()
            conn.close()

            class FakeFirebaseSync:
                def __init__(self):
                    self.db = object()
                    self.auto_restore_calls = 0
                    self.restore_user_calls = 0

                def auto_restore_all_data(self, store_id):
                    self.auto_restore_calls += 1
                    conn = sqlite3.connect(db_path)
                    c = conn.cursor()
                    c.execute(
                        'INSERT OR REPLACE INTO users (username, password, role) VALUES (?, ?, ?)',
                        ('newuser', app._hash_password('secret'), 'admin'),
                    )
                    conn.commit()
                    conn.close()
                    return {'users': True}

                def restore_user_from_firebase(self, username, password_hash=None):
                    self.restore_user_calls += 1
                    return False

            fake_manager = FakeFirebaseSync()

            with patch.object(app, 'DB_PATH', db_path), patch.object(app, 'get_setting', return_value='1'):
                row = app._authenticate_user_and_restore('newuser', app._hash_password('secret'), fake_manager)

            self.assertEqual(row[0], 'newuser')
            self.assertEqual(fake_manager.auto_restore_calls, 1)
            self.assertEqual(fake_manager.restore_user_calls, 0)


if __name__ == '__main__':
    unittest.main()
