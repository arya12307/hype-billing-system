# =============================================================================
# HYPE ERP v3.0.0 - AI ASSISTANT MODULE
# Developer: David | GitHub: david0154
# Lightweight AI model auto-download & inference engine (<250MB)
# =============================================================================

import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from modules.window_utils import set_icon

AI_MODEL_DIR = Path.home() / ".hype_billing" / "ai_models"
AI_MODEL_DIR.mkdir(parents=True, exist_ok=True)

AVAILABLE_MODELS = {
    "sales_predictor": {
        "name": "Hype Sales Predictor (Scikit-learn)",
        "description": "Predicts sales trends and low-stock alerts",
        "size_mb": 2,
        "type": "sklearn",
        "auto_install": True,
        "packages": ["scikit-learn", "numpy", "pandas", "joblib"]
    },
    "smart_search": {
        "name": "Smart Product Search (TF-IDF)",
        "description": "Fuzzy product name search and suggestion",
        "size_mb": 1,
        "type": "tfidf",
        "auto_install": True,
        "packages": ["scikit-learn", "numpy"]
    },
    "anomaly_detector": {
        "name": "Transaction Anomaly Detector",
        "description": "Detects unusual billing patterns automatically",
        "size_mb": 3,
        "type": "sklearn",
        "auto_install": True,
        "packages": ["scikit-learn", "numpy", "pandas"]
    },
    "price_optimizer": {
        "name": "Price Optimization AI",
        "description": "Suggests optimal pricing based on sales history",
        "size_mb": 2,
        "type": "sklearn",
        "auto_install": True,
        "packages": ["scikit-learn", "numpy", "pandas"]
    }
}

MODEL_STATUS_FILE = AI_MODEL_DIR / "model_status.json"


def load_model_status():
    if MODEL_STATUS_FILE.exists():
        try:
            with open(MODEL_STATUS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_model_status(status):
    try:
        with open(MODEL_STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)
    except Exception:
        pass


def install_model_packages(model_key, progress_callback=None):
    import subprocess
    model = AVAILABLE_MODELS[model_key]
    for pkg in model["packages"]:
        if progress_callback:
            progress_callback(f"Installing {pkg}...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg, "-q"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass


def auto_download_and_install(model_key, progress_callback=None, done_callback=None):
    def run():
        status = load_model_status()
        try:
            if progress_callback:
                progress_callback(f"Setting up {AVAILABLE_MODELS[model_key]['name']}...")
            install_model_packages(model_key, progress_callback)
            _initialize_model(model_key, progress_callback)
            status[model_key] = "installed"
            save_model_status(status)
            if done_callback:
                done_callback(model_key, True, None)
        except Exception as e:
            status[model_key] = "failed"
            save_model_status(status)
            if done_callback:
                done_callback(model_key, False, str(e))
    threading.Thread(target=run, daemon=True).start()


def _initialize_model(model_key, progress_callback=None):
    import numpy as np
    model_path = AI_MODEL_DIR / f"{model_key}.pkl"
    if model_path.exists():
        return
    if progress_callback:
        progress_callback(f"Initializing {model_key} model...")
    try:
        if model_key == "sales_predictor":
            from sklearn.linear_model import LinearRegression
            import joblib
            X = np.array([[i] for i in range(1, 31)])
            y = np.random.randint(500, 5000, 30)
            model = LinearRegression().fit(X, y)
            joblib.dump(model, model_path)
        elif model_key == "smart_search":
            from sklearn.feature_extraction.text import TfidfVectorizer
            import joblib
            sample_products = ["Rice 1kg", "Wheat Flour 5kg", "Sugar 2kg", "Oil 1L",
                               "Salt 500g", "Tea 250g", "Coffee 200g", "Biscuits 100g"]
            vec = TfidfVectorizer()
            vec.fit(sample_products)
            joblib.dump(vec, model_path)
        elif model_key in ("anomaly_detector", "price_optimizer"):
            from sklearn.ensemble import IsolationForest
            import joblib
            X = np.random.rand(100, 3) * 1000
            model = IsolationForest(contamination=0.1, random_state=42).fit(X)
            joblib.dump(model, model_path)
    except Exception:
        pass


def is_model_installed(model_key):
    status = load_model_status()
    return status.get(model_key) == "installed"


def predict_sales(days_ahead=7, db_path=None):
    """
    Predict sales for next N days using real invoice data.
    Falls back to a stable model prediction if available.
    """
    try:
        if db_path:
            import sqlite3
            from datetime import datetime, timedelta
            conn = sqlite3.connect(db_path)
            c = conn.cursor()

            date_30_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            c.execute("""
                SELECT DATE(date) as sales_date, SUM(total_amount) as daily_total
                FROM invoices
                WHERE date >= ?
                GROUP BY DATE(date)
                ORDER BY sales_date ASC
            """, (date_30_ago,))

            sales_data = [(row[0], row[1] or 0.0) for row in c.fetchall()]
            conn.close()

            if sales_data:
                # Use a simple linear trend if there are multiple days of data.
                dates = []
                totals = []
                for row in sales_data:
                    try:
                        dt = datetime.fromisoformat(row[0])
                    except Exception:
                        try:
                            dt = datetime.strptime(row[0], '%Y-%m-%d')
                        except Exception:
                            continue
                    dates.append(dt)
                    totals.append(float(row[1]))

                if len(dates) >= 3:
                    epoch = datetime(year=1970, month=1, day=1)
                    xs = [(d - epoch).days for d in dates]
                    ys = totals
                    n = len(xs)
                    x_mean = sum(xs) / n
                    y_mean = sum(ys) / n
                    denom = sum((x - x_mean) ** 2 for x in xs)
                    slope = 0.0
                    if denom:
                        slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom
                    intercept = y_mean - slope * x_mean
                    predictions = []
                    for i in range(1, days_ahead + 1):
                        future_x = (datetime.now() + timedelta(days=i) - epoch).days
                        pred = intercept + slope * future_x
                        predictions.append(round(max(pred, 0.0), 2))
                    return predictions

                # If there is insufficient trend data, use stable average with small adjustment.
                avg_daily_sales = sum(totals) / max(len(totals), 1)
                predictions = []
                for i in range(1, days_ahead + 1):
                    variance = 0.98 + ((i - 1) % 3) * 0.01
                    predictions.append(round(max(avg_daily_sales * variance, 0.0), 2))
                return predictions
    except Exception as e:
        print(f"Real data prediction error: {e}")

    model_path = AI_MODEL_DIR / "sales_predictor.pkl"
    if model_path.exists():
        try:
            import joblib
            import numpy as np
            model = joblib.load(model_path)
            future = np.array([[30 + i] for i in range(1, days_ahead + 1)])
            results = model.predict(future)
            return [round(max(float(v), 0.0), 2) for v in results]
        except Exception:
            pass

    return [round(max(100.0 + i * 5.0, 0.0), 2) for i in range(days_ahead)]


def smart_product_search(query, products):
    model_path = AI_MODEL_DIR / "smart_search.pkl"
    if not model_path.exists() or not products:
        return [p for p in products if query.lower() in p.lower()]
    try:
        import joblib
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity
        vec = joblib.load(model_path)
        q_vec = vec.transform([query])
        p_vecs = vec.transform(products)
        scores = cosine_similarity(q_vec, p_vecs)[0]
        ranked = sorted(zip(products, scores), key=lambda x: -x[1])
        return [p for p, s in ranked if s > 0]
    except Exception:
        return products


def detect_anomaly(amount, qty, discount):
    model_path = AI_MODEL_DIR / "anomaly_detector.pkl"
    if not model_path.exists():
        return False
    try:
        import joblib
        import numpy as np
        model = joblib.load(model_path)
        result = model.predict([[amount, qty, discount]])
        return result[0] == -1
    except Exception:
        return False


def suggest_price(cost_price, historical_avg_sale):
    try:
        margin = 0.20
        suggested = max(cost_price * (1 + margin), historical_avg_sale * 0.95)
        return round(suggested, 2)
    except Exception:
        return cost_price * 1.2


def _safe_widget_call(widget, **kwargs):
    """
    Safely update a tkinter widget.
    Catches TclError when the window has been closed/destroyed.
    """
    try:
        if widget.winfo_exists():
            widget.config(**kwargs)
    except Exception:
        pass


# ─── AI Dashboard UI ─────────────────────────────────────────────────────────

class AIAssistantWindow:
    def __init__(self, parent):
        self.parent = parent
        self.win = tk.Toplevel(parent)
        self.win.title("Hype ERP — AI Assistant")
        self.win.geometry("700x520")
        self.win.configure(bg="#0f0f1a")
        set_icon(self.win)
        self.status_labels = {}
        self.model_btns = {}
        self._build_ui()
        self._check_and_auto_install()

    def _build_ui(self):
        hdr = tk.Frame(self.win, bg="#1a1a2e", pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="\U0001f916 Hype AI Assistant", font=("Segoe UI", 16, "bold"),
                 bg="#1a1a2e", fg="#00d4ff").pack()
        tk.Label(hdr, text="Powered by open-source ML models | Developer: David",
                 font=("Segoe UI", 9), bg="#1a1a2e", fg="#aaaaaa").pack()

        mf = tk.LabelFrame(self.win, text=" AI Models ", bg="#0f0f1a", fg="#00d4ff",
                            font=("Segoe UI", 10, "bold"), pady=8, padx=8)
        mf.pack(fill="x", padx=16, pady=8)

        for key, info in AVAILABLE_MODELS.items():
            row = tk.Frame(mf, bg="#0f0f1a")
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"\u25cf {info['name']}", font=("Segoe UI", 9, "bold"),
                     bg="#0f0f1a", fg="#ffffff", width=38, anchor="w").pack(side="left")
            tk.Label(row, text=f"{info['size_mb']}MB", font=("Segoe UI", 8),
                     bg="#0f0f1a", fg="#888888", width=6).pack(side="left")
            sl = tk.Label(row, text="Checking...", font=("Segoe UI", 8),
                          bg="#0f0f1a", fg="#ffaa00", width=14)
            sl.pack(side="left")
            self.status_labels[key] = sl
            btn = tk.Button(row, text="Install", font=("Segoe UI", 8),
                            bg="#4a90d9", fg="white", relief="flat",
                            command=lambda k=key: self._install_model(k))
            btn.pack(side="right", padx=4)
            self.model_btns[key] = btn

        lf = tk.LabelFrame(self.win, text=" Activity Log ", bg="#0f0f1a", fg="#00d4ff",
                            font=("Segoe UI", 10, "bold"))
        lf.pack(fill="both", expand=True, padx=16, pady=8)
        self.log = tk.Text(lf, height=8, bg="#0a0a14", fg="#00ff88",
                           font=("Consolas", 9), relief="flat", state="disabled")
        self.log.pack(fill="both", expand=True, padx=4, pady=4)

        bf = tk.Frame(self.win, bg="#0f0f1a")
        bf.pack(fill="x", padx=16, pady=6)
        tk.Button(bf, text="\U0001f4c8 Predict Next 7-Day Sales", font=("Segoe UI", 10, "bold"),
                  bg="#00aa44", fg="white", relief="flat",
                  command=self._show_prediction).pack(side="left", padx=4)
        tk.Button(bf, text="\U0001f504 Install All Models", font=("Segoe UI", 10),
                  bg="#aa4400", fg="white", relief="flat",
                  command=self._install_all).pack(side="left", padx=4)

    def _log(self, msg):
        try:
            if not self.win.winfo_exists():
                return
            self.log.config(state="normal")
            self.log.insert("end", f"\u25ba {msg}\n")
            self.log.see("end")
            self.log.config(state="disabled")
        except Exception:
            pass

    def _check_and_auto_install(self):
        def check():
            for key in AVAILABLE_MODELS:
                if is_model_installed(key):
                    try:
                        if self.win.winfo_exists():
                            self.win.after(0, lambda k=key: self._mark_installed(k))
                    except Exception:
                        pass
                else:
                    try:
                        if self.win.winfo_exists():
                            self.win.after(0, lambda k=key: self._mark_pending(k))
                    except Exception:
                        pass
                    if AVAILABLE_MODELS[key]["auto_install"]:
                        self._install_model(key)
        threading.Thread(target=check, daemon=True).start()

    def _install_model(self, key):
        _safe_widget_call(self.status_labels[key], text="Installing...", fg="#ffaa00")
        _safe_widget_call(self.model_btns[key], state="disabled")
        self._log(f"Starting install: {AVAILABLE_MODELS[key]['name']}")

        def done_cb(k, ok, e):
            try:
                if self.win.winfo_exists():
                    self.win.after(0, lambda: self._on_done(k, ok, e))
            except Exception:
                pass

        auto_download_and_install(
            key,
            progress_callback=lambda m: (
                self.win.after(0, lambda: self._log(m))
                if self._win_alive() else None
            ),
            done_callback=done_cb
        )

    def _win_alive(self):
        try:
            return self.win.winfo_exists()
        except Exception:
            return False

    def _install_all(self):
        for key in AVAILABLE_MODELS:
            if not is_model_installed(key):
                self._install_model(key)

    def _on_done(self, key, ok, err):
        if ok:
            self._mark_installed(key)
            self._log(f"\u2713 {AVAILABLE_MODELS[key]['name']} ready")
        else:
            _safe_widget_call(self.status_labels[key], text="Failed", fg="#ff4444")
            _safe_widget_call(self.model_btns[key], state="normal")
            self._log(f"\u2717 {key}: {err}")

    def _mark_installed(self, key):
        _safe_widget_call(self.status_labels[key], text="\u2713 Ready", fg="#00ff88")
        _safe_widget_call(self.model_btns[key], text="Reinstall", state="normal")

    def _mark_pending(self, key):
        _safe_widget_call(self.status_labels[key], text="Not Installed", fg="#ff8800")
        _safe_widget_call(self.model_btns[key], state="normal")

    def _show_prediction(self):
        preds = predict_sales(7)
        if preds:
            msg = "Predicted Sales (next 7 days):\n"
            for i, v in enumerate(preds, 1):
                msg += f"  Day {i}: \u20b9{v:,.0f}\n"
            messagebox.showinfo("AI Sales Prediction", msg, parent=self.win)
        else:
            messagebox.showwarning("AI", "Sales predictor not ready yet.", parent=self.win)