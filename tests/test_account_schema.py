import os
import sqlite3
import tempfile
import unittest

from modules.account import AccountingModule


class AccountingSchemaTests(unittest.TestCase):
    def test_journal_entries_schema_is_migrated_for_old_databases(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, 'hype_billing_system.db')
            conn = sqlite3.connect(db_path)
            try:
                conn.execute('CREATE TABLE journal_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, description TEXT, debit_account TEXT, credit_account TEXT, amount REAL NOT NULL)')
                conn.commit()
            finally:
                conn.close()

            module = AccountingModule(None, db_path=db_path)

            conn = sqlite3.connect(db_path)
            try:
                columns = [row[1] for row in conn.execute('PRAGMA table_info(journal_entries)')]
            finally:
                conn.close()

            self.assertIn('date', columns)


if __name__ == '__main__':
    unittest.main()
