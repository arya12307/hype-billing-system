import hashlib
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

import firebase_sync


class FirebaseSyncRestoreTests(unittest.TestCase):
    def test_normalize_password_preserves_existing_hash(self):
        password_hash = 'a' * 64
        self.assertEqual(firebase_sync._normalize_password_for_restore(password_hash), password_hash)

    def test_normalize_password_hashes_plaintext(self):
        plain_password = 'emp123'
        expected_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        self.assertEqual(firebase_sync._normalize_password_for_restore(plain_password), expected_hash)

    def test_get_db_path_uses_hypeerp_when_frozen(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {'LOCALAPPDATA': temp_dir, 'APPDATA': temp_dir}, clear=False):
                with patch.object(sys, 'frozen', True, create=True):
                    db_path = firebase_sync.get_db_path()
                    self.assertTrue(db_path.startswith(os.path.join(temp_dir, 'HypeERP')))
                    self.assertTrue(db_path.endswith('hype_billing_system.db'))
                    self.assertTrue(os.path.exists(os.path.dirname(db_path)))

    def test_get_firebase_sync_manager_uses_explicit_credentials_path(self):
        class FakeFirebaseSync:
            def __init__(self, credentials_path=None):
                self.credentials_path = credentials_path
                self.db = object()

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as handle:
            credentials_path = handle.name

        try:
            with patch.object(firebase_sync, 'firebase_sync_manager', None):
                with patch.object(firebase_sync, 'FirebaseSync', FakeFirebaseSync):
                    manager = firebase_sync.get_firebase_sync_manager(credentials_path=credentials_path)

            self.assertIsNotNone(manager)
            self.assertEqual(manager.credentials_path, credentials_path)
        finally:
            os.remove(credentials_path)


if __name__ == '__main__':
    unittest.main()
