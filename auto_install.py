# =============================================================================
# HYPE ERP - AUTO INSTALLER MODULE
# Developer: David | GitHub: https://github.com/david0154
# Version: 3.0.0
#
# HOW IT WORKS:
#   - When running from SOURCE (python main.py):
#       pip-installs any missing packages at startup, then downloads AI models.
#   - When running as a COMPILED EXE (PyInstaller):
#       pip is NOT available inside the frozen exe. This module detects that
#       and instead downloads AI model FILES to the user's AppData folder.
#       All Python packages must be bundled by PyInstaller at build time.
#
# The SplashAutoInstall class shows a startup splash screen with progress.
# =============================================================================

import sys
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk

# Is this running as a PyInstaller frozen EXE?
IS_FROZEN = getattr(sys, 'frozen', False)

# App data directory (used for AI model storage in EXE mode)
if IS_FROZEN:
    _appdata = os.getenv('LOCALAPPDATA') or os.getenv('APPDATA') or os.path.expanduser('~')
    MODELS_DIR = os.path.join(_appdata, 'HypeERP', 'models')
else:
    MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

# Packages needed when running from source (NOT needed in EXE — bundled by PyInstaller)
REQUIRED_PACKAGES = [
    "firebase-admin",
    "scikit-learn",
    "numpy",
    "pandas",
    "joblib",
    "reportlab",
    "pillow",
    "requests",
    "cryptography",
]


def check_package(pkg):
    """Check if a Python package is importable."""
    try:
        __import__(pkg.replace("-", "_").split("[")[0])
        return True
    except ImportError:
        return False


def install_package(pkg, log_callback=None):
    """
    Install a pip package.
    ONLY works in source mode. In EXE mode this is a no-op.
    """
    if IS_FROZEN:
        # Cannot pip install inside a PyInstaller EXE
        if log_callback:
            log_callback(f"[EXE Mode] Skipping pip install for {pkg}")
        return False
    try:
        if log_callback:
            log_callback(f"Installing {pkg}...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", pkg, "-q",
             "--disable-pip-version-check"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except Exception as e:
        if log_callback:
            log_callback(f"Failed: {pkg} — {e}")
        return False


def _setup_ai_models(log_callback=None):
    """
    Download/set up AI model files into MODELS_DIR.
    Works in both source mode AND EXE mode because it only writes files,
    not Python packages.
    """
    try:
        from ai_assistant import auto_download_and_install, AVAILABLE_MODELS
        for key, info in AVAILABLE_MODELS.items():
            model_file = os.path.join(MODELS_DIR, f"{key}.pkl")
            if os.path.exists(model_file):
                if log_callback:
                    log_callback(f"✓ AI model ready: {info['name']}")
                continue
            if log_callback:
                log_callback(f"Setting up AI: {info['name']}...")
            try:
                auto_download_and_install(key, models_dir=MODELS_DIR)
            except TypeError:
                # Older signature without models_dir
                auto_download_and_install(key)
    except ImportError:
        if log_callback:
            log_callback("AI module not found — skipping model setup.")
    except Exception as e:
        if log_callback:
            log_callback(f"AI setup note: {e}")


def run_auto_install(log_callback=None, done_callback=None):
    """
    Main auto-install entry point. Called from main.py at startup.

    SOURCE MODE: installs missing pip packages + sets up AI model files.
    EXE MODE:    skips pip (already bundled), only sets up AI model files.
    """
    def run():
        if IS_FROZEN:
            if log_callback:
                log_callback("EXE mode: checking AI models...")
            _setup_ai_models(log_callback)
        else:
            missing = [p for p in REQUIRED_PACKAGES if not check_package(p)]
            if missing:
                if log_callback:
                    log_callback(f"Installing {len(missing)} missing packages...")
                for pkg in missing:
                    install_package(pkg, log_callback)
            else:
                if log_callback:
                    log_callback("✓ All dependencies installed.")
            _setup_ai_models(log_callback)

        if done_callback:
            done_callback(True)

    threading.Thread(target=run, daemon=True).start()


class SplashAutoInstall:
    """
    Splash screen shown on first launch.
    Shows logo, progress bar, and live install log.
    After install completes, calls on_complete() to launch the main app.

    USAGE:
        SplashAutoInstall(on_complete=launch_main_app)
    """

    def __init__(self, on_complete):
        self.on_complete = on_complete
        self.root = tk.Tk()
        self.root.title("Hype ERP — Starting Up")
        self.root.geometry("520x340")
        self.root.configure(bg="#1a1a2e")
        self.root.overrideredirect(True)
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"520x340+{(sw-520)//2}+{(sh-340)//2}")
        self._build_ui()
        self._start_install()
        self.root.mainloop()

    def _build_ui(self):
        tk.Label(self.root, text="🏢  Hype ERP",
                 font=("Segoe UI", 22, "bold"), bg="#1a1a2e", fg="#e94560").pack(pady=(28, 2))
        tk.Label(self.root, text="Enterprise Resource Planning System",
                 font=("Segoe UI", 10, "italic"), bg="#1a1a2e", fg="#7a7a9a").pack()
        tk.Label(self.root, text="Developer: David  |  github.com/david0154",
                 font=("Segoe UI", 8), bg="#1a1a2e", fg="#555577").pack(pady=(2, 0))
        tk.Frame(self.root, height=1, bg="#e94560").pack(fill="x", padx=40, pady=10)
        tk.Label(self.root, text="Setting up AI models & dependencies...",
                 font=("Segoe UI", 9), bg="#1a1a2e", fg="#aaaacc").pack()
        self.progress = ttk.Progressbar(self.root, mode="indeterminate", length=420)
        self.progress.pack(pady=8)
        self.progress.start(12)
        self.log_var = tk.StringVar(value="Initializing...")
        tk.Label(self.root, textvariable=self.log_var,
                 font=("Consolas", 8), bg="#1a1a2e", fg="#00ff88",
                 wraplength=480).pack(pady=4)
        tk.Button(self.root, text="Skip & Launch",
                  bg="#333355", fg="#aaaaaa",
                  font=("Segoe UI", 9), relief="flat",
                  command=self._skip).pack(pady=8)
        # Footer
        tk.Label(self.root, text="Powered by Hype ERP v3.0.0",
                 font=("Segoe UI", 7), bg="#1a1a2e", fg="#333355").pack(side="bottom", pady=4)

    def _start_install(self):
        run_auto_install(
            log_callback=lambda m: self.root.after(0, lambda: self.log_var.set(m)),
            done_callback=lambda ok: self.root.after(600, self._finish)
        )

    def _finish(self):
        self.progress.stop()
        self.log_var.set("✓ Ready! Launching Hype ERP...")
        self.root.after(900, self._close)

    def _skip(self):
        self._close()

    def _close(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        self.on_complete()
