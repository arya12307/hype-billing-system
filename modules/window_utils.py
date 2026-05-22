import os
import sys


def get_runtime_path(filename):
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
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
