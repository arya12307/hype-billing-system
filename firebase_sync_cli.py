"""Simple CLI for selective Firebase sync operations.

Usage examples:
    python firebase_sync_cli.py --all
    python firebase_sync_cli.py --table settings
    python firebase_sync_cli.py --billing --shop myshop
"""
import argparse
import sys
from firebase_helper import (
    sync_all_erp_data,
    save_settings,
    save_billing_tables,
    initialize_firestore_client,
)
from firebase_sync import initialize_firebase_sync


def main(argv=None):
    parser = argparse.ArgumentParser(description='Firebase sync CLI for Hype ERP')
    parser.add_argument('--creds', default='serviceAccountKey.json', help='Path to Firebase credentials JSON')
    parser.add_argument('--db', default='hype_billing_system.db', help='Path to local SQLite DB')
    parser.add_argument('--shop', default='default', help='Shop ID for shop-scoped collections')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true', help='Sync all ERP data')
    group.add_argument('--table', help='Sync a specific table by name (e.g., products, settings)')
    group.add_argument('--settings', action='store_true', help='Sync settings and GST config')
    group.add_argument('--billing', action='store_true', help='Sync invoices/billing tables')
    group.add_argument('--backup-creds', action='store_true', help='Backup service account key (or .enc) to Firebase Storage')

    args = parser.parse_args(argv)

    if args.all:
        print('Starting full sync...')
        ok = sync_all_erp_data(args.db, args.creds, shop_id=args.shop)
        sys.exit(0 if ok else 2)

    if args.table:
        # fall back to generic table sync using helper
        app, db = initialize_firestore_client(args.creds)
        if db is None:
            print('Failed to initialize Firebase')
            sys.exit(2)
        import sqlite3
        conn = sqlite3.connect(args.db)
        conn.row_factory = sqlite3.Row
        from firebase_helper import save_table_from_sqlite
        saved = save_table_from_sqlite(db, conn, args.table, f'system/{args.table}' if args.table in ('settings', 'gst_config') else f'shops/{args.shop}/{args.table}')
        conn.close()
        sys.exit(0 if saved >= 0 else 2)

    if args.settings:
        ok = save_settings(args.creds, args.db, shop_id=args.shop)
        sys.exit(0 if ok else 2)

    if args.billing:
        saved = save_billing_tables(args.creds, args.db, shop_id=args.shop)
        sys.exit(0 if saved >= 0 else 2)

    if args.backup_creds:
        print('Backing up credentials...')
        fs = initialize_firebase_sync(args.creds, args.shop)
        if not fs:
            print('Failed to initialize Firebase')
            sys.exit(2)
        ok = fs.backup_credentials(args.creds)
        sys.exit(0 if ok else 2)


if __name__ == '__main__':
    main()
