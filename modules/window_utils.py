import os
import sys


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
