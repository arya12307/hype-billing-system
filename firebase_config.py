# ===========================================================================
# Hype ERP v3.0.0 - Central Firebase Configuration
# Developer: David | Nexuzy Lab
# ===========================================================================
#
#  HOW TO CONFIGURE FIREBASE (only edit this file - nowhere else):
#
#  OPTION A  — Paste your Firebase project details below manually
#  OPTION B  — Run:  python firebase_config.py  (interactive setup wizard)
#  OPTION C  — Inside the app: Settings → Firebase Setup
#
#  After saving here, firebase_sync.py and firebase_deep.py
#  read config automatically. No manual edits in any other file.
#
#  NOTE: shop_id is AUTO-GENERATED from your shop name in app settings.
#        You do NOT need to set it manually here.
# ===========================================================================

import os
import json
import sqlite3
import re
import uuid

# ---------------------------------------------------------------------------
# 🔧 PASTE YOUR FIREBASE DETAILS HERE (shop_id is auto-generated)
# ---------------------------------------------------------------------------

FIREBASE_CONFIG = {
    # Firebase Project ID
    # From: Firebase Console → ⚙️ Project Settings → General → Project ID
    "project_id": "hype-retail-billing-softwaer",

    # Realtime Database URL
    # From: Firebase Console → Build → Realtime Database → top of Data tab
    "database_url": "https://hype-retail-billing-softwaer-default-rtdb.asia-southeast1.firebasedatabase.app",

    # Firebase Storage Bucket
    # Format: <project-id>.appspot.com
    "storage_bucket": "hype-retail-billing-softwaer.appspot.com",

    # Path to your service account key file
    # Place serviceAccountKey.json in project root (beside main.py)
    "service_account_key_path": "serviceAccountKey.json",

    # shop_id is AUTO-GENERATED — do not set manually
    # It is derived from your shop name in app settings (Store → Settings)
    # e.g. shop_name "My Shop Kolkata" → shop_id "my_shop_kolkata_a1b2"
    "shop_id": "",

    # Enable / disable Firebase sync globally
    "enabled": True,
}

# ---------------------------------------------------------------------------
# ⚠️  DO NOT EDIT BELOW THIS LINE
# ---------------------------------------------------------------------------

_CONFIG_JSON_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "firebase_runtime_config.json"
)

_EXE_CONFIG_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "HypeERP", "firebase_runtime_config.json"
)


def _is_frozen():
    import sys
    return getattr(sys, 'frozen', False)


def _runtime_config_path():
    """Return the correct config path for source or EXE mode."""
    if _is_frozen():
        os.makedirs(os.path.dirname(_EXE_CONFIG_PATH), exist_ok=True)
        return _EXE_CONFIG_PATH
    return _CONFIG_JSON_PATH


def generate_shop_id(shop_name: str = "") -> str:
    """
    Auto-generate a unique shop_id from the shop name.
    Example: "My Shop Kolkata" -> "my_shop_kolkata_a1b2"
    If shop_name is empty, uses a random UUID suffix.
    """
    if shop_name:
        # Lowercase, replace spaces/special chars with underscore
        base = re.sub(r'[^a-z0-9]+', '_', shop_name.lower()).strip('_')
        # Add 4-char unique suffix to avoid collisions
        suffix = uuid.uuid4().hex[:4]
        return f"{base}_{suffix}"
    else:
        return f"shop_{uuid.uuid4().hex[:8]}"


def get_or_create_shop_id(shop_name: str = "") -> str:
    """
    Returns existing shop_id from config, or auto-generates and saves one.
    Call this once on first run — shop_id is then persisted.
    """
    cfg = load_config()
    if cfg.get('shop_id'):
        return cfg['shop_id']
    # Auto-generate from shop name
    new_id = generate_shop_id(shop_name)
    cfg['shop_id'] = new_id
    save_config(cfg)
    return new_id


def save_config(cfg: dict):
    """Save Firebase config to JSON file (persists across restarts)."""
    path = _runtime_config_path()
    with open(path, 'w') as f:
        json.dump(cfg, f, indent=2)


def load_config() -> dict:
    """
    Load Firebase config with priority order:
      1. Runtime JSON file (set via in-app wizard / auto-saved)
      2. FIREBASE_CONFIG dict above (manually filled)
      3. SQLite settings table (legacy fallback)
      4. Returns disabled config if none found
    """
    # Priority 1: Runtime JSON
    path = _runtime_config_path()
    if os.path.exists(path):
        try:
            with open(path) as f:
                cfg = json.load(f)
            if cfg.get('project_id'):
                return cfg
        except Exception:
            pass

    # Priority 2: Hardcoded config above
    if FIREBASE_CONFIG.get('project_id'):
        return FIREBASE_CONFIG.copy()

    # Priority 3: SQLite settings table
    db_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     'hype_billing_system.db'),
        os.path.join(os.environ.get("LOCALAPPDATA", ""),
                     'HypeERP', 'hype_billing_system.db'),
    ]
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("SELECT key, value FROM settings WHERE key IN "
                            "('firebase_project_id','firebase_database_url',"
                            "'firebase_storage_bucket','firebase_shop_id',"
                            "'firebase_enabled','firebase_key_path','shop_name')")
                rows = dict(cur.fetchall())
                conn.close()
                if rows.get('firebase_project_id'):
                    shop_id = rows.get('firebase_shop_id', '')
                    # Auto-generate shop_id from shop_name if missing
                    if not shop_id and rows.get('shop_name'):
                        shop_id = generate_shop_id(rows['shop_name'])
                    return {
                        'project_id':    rows.get('firebase_project_id', ''),
                        'database_url':  rows.get('firebase_database_url', ''),
                        'storage_bucket':rows.get('firebase_storage_bucket', ''),
                        'service_account_key_path': rows.get('firebase_key_path',
                                                             'serviceAccountKey.json'),
                        'shop_id':       shop_id,
                        'enabled':       rows.get('firebase_enabled', 'true').lower() == 'true',
                    }
            except Exception:
                pass

    # Priority 4: Disabled
    return {**FIREBASE_CONFIG, 'enabled': False}


def get(key: str, default=None):
    """Quick single-key getter. e.g. get('project_id')"""
    return load_config().get(key, default)


def is_enabled() -> bool:
    """Returns True if Firebase is configured and enabled."""
    cfg = load_config()
    return bool(cfg.get('enabled', False) and cfg.get('project_id', ''))


def get_service_account_path() -> str:
    """
    Returns correct absolute path to serviceAccountKey.json.
    Checks: config path → project root → EXE folder.
    """
    import sys
    configured = get('service_account_key_path', 'serviceAccountKey.json')
    candidates = [
        configured,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'serviceAccountKey.json'),
    ]
    if _is_frozen():
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, 'serviceAccountKey.json'))
        candidates.append(os.path.join(exe_dir, 'serviceAccountKey.enc'))
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return configured


# ---------------------------------------------------------------------------
# Interactive Setup Wizard (run: python firebase_config.py)
# ---------------------------------------------------------------------------

def _setup_wizard():
    print()
    print("="*60)
    print("  Hype ERP v3.0.0 - Firebase Setup Wizard")
    print("  Developer: David | Nexuzy Lab")
    print("="*60)
    print()
    print("Open Firebase Console → Project Settings to get these values.")
    print("shop_id is AUTO-GENERATED — no need to enter it manually.")
    print()

    cfg = load_config()

    def ask(prompt, current):
        hint = f" [{current}]" if current else ""
        val = input(f"{prompt}{hint}: ").strip()
        return val if val else current

    cfg['project_id']     = ask("Firebase Project ID", cfg.get('project_id', ''))
    cfg['database_url']   = ask("Realtime DB URL",     cfg.get('database_url', ''))
    cfg['storage_bucket'] = ask("Storage Bucket",      cfg.get('storage_bucket', ''))
    cfg['service_account_key_path'] = ask(
        "Path to serviceAccountKey.json",
        cfg.get('service_account_key_path', 'serviceAccountKey.json')
    )

    # shop_id: auto-generate if not already set
    if not cfg.get('shop_id'):
        shop_name = input("Your shop name (for auto-generating shop_id) [leave blank for random]: ").strip()
        cfg['shop_id'] = generate_shop_id(shop_name)
        print(f"  → shop_id auto-generated: {cfg['shop_id']}")
    else:
        print(f"  → shop_id already set: {cfg['shop_id']} (keeping as is)")

    enable = input("Enable Firebase sync? (y/n) [y]: ").strip().lower()
    cfg['enabled'] = enable != 'n'

    save_config(cfg)
    print()
    print("✅  Config saved to:", _runtime_config_path())
    print(f"   Project : {cfg.get('project_id')}")
    print(f"   Shop ID : {cfg.get('shop_id')}  (auto-generated)")
    print(f"   DB URL  : {cfg.get('database_url')}")
    print(f"   Key     : {cfg.get('service_account_key_path')}")
    print()
    print("Restart Hype ERP for changes to take effect.")
    print()


if __name__ == '__main__':
    _setup_wizard()