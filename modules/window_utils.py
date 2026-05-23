import os
import sys
import shutil


def _ensure_bundled_credentials():
    """
    On a fresh PyInstaller EXE run, copy serviceAccountKey.enc (and
    firebase_runtime_config.json) from _MEIPASS bundle into the persistent
    LOCALAPPDATA\HypeERP directory so firebase_configured() can find them.
    Called once at import time when frozen.
    """
    if not getattr(sys, 'frozen', False):
        return
    meipass = getattr(sys, '_MEIPASS', None)
    if not meipass:
        return
    persistent_dir = os.path.join(
        os.getenv('LOCALAPPDATA') or os.getenv('APPDATA') or os.path.expanduser('~'),
        'HypeERP'
    )
    os.makedirs(persistent_dir, exist_ok=True)
    for fname in ('serviceAccountKey.enc', 'serviceAccountKey.json', 'firebase_runtime_config.json'):
        src = os.path.join(meipass, fname)
        dst = os.path.join(persistent_dir, fname)
        # Only copy if destination doesn't exist (don't overwrite user config)
        if os.path.exists(src) and not os.path.exists(dst):
            try:
                shutil.copy2(src, dst)
            except Exception:
                pass


# Run once at import
_ensure_bundled_credentials()


def get_runtime_path(filename):
    """
    Get the path for a file at runtime.

    Special handling for PyInstaller:
    - For credentials files (serviceAccountKey.json/.enc), use persistent LOCALAPPDATA location
    - For other files, use _MEIPASS (extracted bundle) in frozen mode

    This ensures credentials persist between app runs in PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        # In PyInstaller executable mode
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))

        # Credentials files should be in persistent LOCALAPPDATA location
        if filename in ('serviceAccountKey.json', 'serviceAccountKey.enc', 'firebase_config.json'):
            persistent_dir = os.path.join(
                os.getenv('LOCALAPPDATA') or os.getenv('APPDATA') or os.path.expanduser('~'),
                'HypeERP'
            )
            os.makedirs(persistent_dir, exist_ok=True)
            return os.path.join(persistent_dir, filename)
        else:
            # Other files come from the frozen bundle
            return os.path.join(base, filename)
    else:
        # In development mode (not frozen)
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        return os.path.join(base, filename)


def get_icon_path():
    ico = get_runtime_path('icon.ico')
    return ico if os.path.exists(ico) else None


def set_icon(win):
    ico = get_icon_path()
    if ico:
        try:
            win.iconbitmap(ico)
        except Exception:
            pass


def style_button(btn, bg='#e94560', fg='white'):
    btn.configure(relief='flat', bg=bg, fg=fg,
                  activebackground='#ff6b81', activeforeground='white')
