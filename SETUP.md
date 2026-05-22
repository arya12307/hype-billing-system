# 🛠️ Hype ERP — Complete Step-by-Step Setup Guide

> Version **3.0.0** | Developer: [David](https://github.com/david0154) | Org: [Nexuzy Lab](https://github.com/nexuzy-lab)

---

## 📋 Table of Contents

1. [Prerequisites — Install Everything First](#1-prerequisites--install-everything-first)
2. [VS Code Setup](#2-vs-code-setup)
3. [Clone & Open Project](#3-clone--open-project)
4. [Python Virtual Environment](#4-python-virtual-environment)
5. [Install Dependencies](#5-install-dependencies)
6. [Run the App (First Time)](#6-run-the-app-first-time)
7. [Firebase — Create Project (Step by Step)](#7-firebase--create-project-step-by-step)
8. [Firebase — Enable Firestore Database](#8-firebase--enable-firestore-database)
9. [Firebase — Enable Realtime Database](#9-firebase--enable-realtime-database)
10. [Firebase — Get Service Account Key](#10-firebase--get-service-account-key)
11. [Firebase — Security Rules](#11-firebase--security-rules)
12. [Firebase — Configure in Hype ERP](#12-firebase--configure-in-hype-erp)
13. [App Settings — Shop Info, GST, Invoice](#13-app-settings--shop-info-gst-invoice)
14. [Role-Based Access — Users & Permissions](#14-role-based-access--users--permissions)
15. [App Flow After Login](#15-app-flow-after-login)
16. [ERP Modules — All 19](#16-erp-modules--all-19)
17. [Scroll & Keyboard Support](#17-scroll--keyboard-support)
18. [AI Models Setup](#18-ai-models-setup)
19. [Build EXE — PyInstaller](#19-build-exe--pyinstaller)
20. [Build Installer — Inno Setup](#20-build-installer--inno-setup)
21. [First Run Checklist](#21-first-run-checklist)
22. [Troubleshooting](#22-troubleshooting)
23. [Full Build Pipeline Summary](#23-full-build-pipeline-summary)

---

## 1. Prerequisites — Install Everything First

Install all of these **before** doing anything else.

### ▶️ Python 3.10 or 3.11 (recommended)

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Click **Download Python 3.11.x** (latest 3.11)
3. Run the installer
4. ✅ **CHECK “Add Python to PATH”** at the bottom of the installer before clicking Install
5. Click **Install Now**
6. Verify install — open **Command Prompt** and type:
   ```cmd
   python --version
   ```
   Should show: `Python 3.11.x`

### ▶️ Git

1. Go to [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Download and run the installer — click **Next** through all defaults
3. Verify:
   ```cmd
   git --version
   ```

### ▶️ VS Code (Visual Studio Code)

1. Go to [https://code.visualstudio.com/](https://code.visualstudio.com/)
2. Click **Download for Windows** — run the installer
3. ✅ Check **“Add to PATH”** and **“Open with Code”** options during install

### ▶️ Inno Setup 6 (for building Windows installer)

1. Go to [https://jrsoftware.org/isinfo.php](https://jrsoftware.org/isinfo.php)
2. Click **Download Inno Setup** — run the installer, click Next through all defaults

---

## 2. VS Code Setup

### Step 1 — Install Python Extension
1. Open **VS Code**
2. Press `Ctrl+Shift+X` (Extensions panel)
3. Search: `Python`
4. Click **Install** on the one by **Microsoft** (first result)

### Step 2 — Install Useful Extensions

In the Extensions panel (`Ctrl+Shift+X`), search and install each:

| Extension | By | Why |
|-----------|----|---------|
| `Python` | Microsoft | Python IntelliSense, linting |
| `Pylance` | Microsoft | Better autocomplete |
| `GitLens` | GitKraken | Git history in editor |
| `SQLite Viewer` | Florian Klampfer | View `.db` database files |
| `Better Comments` | Aaron Bond | Coloured comments |
| `Indent Rainbow` | oderwat | Visual indentation |

### Step 3 — Open Integrated Terminal in VS Code

- Press `` Ctrl+` `` (backtick key) **OR**
- Menu → **Terminal → New Terminal**

All commands in this guide are run in this terminal.

---

## 3. Clone & Open Project

### Step 1 — Open Terminal

Open **Command Prompt** or **PowerShell** (search in Start menu).

### Step 2 — Navigate to where you want the project

```cmd
cd C:\Users\YourName\Documents
```

> Replace `YourName` with your actual Windows username.

### Step 3 — Clone the repository

```cmd
git clone https://github.com/david0154/hype-billing-system.git
```

This creates a folder: `C:\Users\YourName\Documents\hype-billing-system`

### Step 4 — Open in VS Code

```cmd
cd hype-billing-system
code .
```

VS Code opens with the entire project. You will see all files in the left **Explorer** panel.

### Project Folder Structure

```
hype-billing-system/
├── main.py                        ← Run this to start the app
├── firebase_config.py             ← Firebase settings (edit once)
├── firebase_sync.py               ← Cloud sync logic
├── firebase_deep.py               ← Deep sync features
├── auto_install.py                ← Auto dependency installer
├── ai_assistant.py                ← AI features
├── encrypt_key.py                 ← Encrypts Firebase key for EXE
├── requirements.txt               ← All Python packages needed
├── build_pyinstaller.ps1          ← One-click EXE builder
├── hype_billing_installer.iss     ← Inno Setup installer script
├── serviceAccountKey.json         ← Your Firebase key (YOU add this)
├── icon.ico                       ← App icon
├── logo.png                       ← App logo
└── modules/
       ├── mode_selector.py           ← Role-based login router
       ├── scrollable_frame.py        ← Scroll + keyboard helper
       ├── erp_main_menu.py           ← 19-module ERP grid
       ├── firebase_settings_ui.py    ← In-app Firebase setup GUI
       ├── account.py                 ← Accounting module
       ├── sale.py                    ← Sales module
       └── ... (all 19 ERP modules)
```

---

## 4. Python Virtual Environment

A virtual environment keeps project packages separate from system Python.

### Step 1 — Create virtual environment

In VS Code terminal (or Command Prompt inside the project folder):

```cmd
python -m venv venv
```

This creates a `venv/` folder.

### Step 2 — Activate it

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

> If PowerShell blocks it, run once:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

**Linux / Mac:**
```bash
source venv/bin/activate
```

You'll see `(venv)` at the start of your terminal prompt — this means it's active.

### Step 3 — Select Python interpreter in VS Code

1. Press `Ctrl+Shift+P`
2. Type: `Python: Select Interpreter`
3. Press **Enter**
4. Select the one that shows `venv` in the path:
   ```
   .\venv\Scripts\python.exe
   ```

---

## 5. Install Dependencies

With your virtual environment **active** (`(venv)` shown in terminal):

```cmd
pip install -r requirements.txt
```

This installs everything: tkinter support, Firebase, ReportLab PDF, scikit-learn AI, Pillow, cryptography, pandas, etc.

> ⏱ This takes 2–5 minutes on first install.

### Verify key packages installed

```cmd
pip list
```

You should see packages like:
- `firebase-admin`
- `google-cloud-firestore`
- `reportlab`
- `scikit-learn`
- `Pillow`
- `cryptography`
- `pandas`
- `pyinstaller`

---

## 6. Run the App (First Time)

```cmd
python main.py
```

The app launches. Login with:
- **Username:** `admin`
- **Password:** `admin123`

> ⚠️ Firebase will NOT be connected yet — that's fine. The app works fully offline with SQLite. Follow Section 7–12 to connect Firebase.

---

## 7. Firebase — Create Project (Step by Step)

> Firebase is **optional**. Skip to Section 13 if you want offline-only mode.

### Step 1 — Open Firebase Console

1. Open your browser
2. Go to: [https://console.firebase.google.com](https://console.firebase.google.com)
3. Sign in with your **Google account**

### Step 2 — Create a new project

1. Click the big **“Add project”** card (or **“Create a project”**)
2. **Project name:** type something like `hype-erp-myshop`
   > The project ID is shown below the name — note it down (e.g. `hype-erp-myshop-a1b2c`)
3. Click **Continue**
4. **Google Analytics:** you can toggle it OFF — not needed
5. Click **Create project**
6. Wait 10–20 seconds — click **Continue** when ready

You are now inside your Firebase project dashboard.

### Step 3 — Note your Project ID

1. Click the **gear icon** (⚙️) next to “Project Overview” in the left sidebar
2. Click **Project settings**
3. Under **General** tab, find **Project ID**
4. Copy it — example: `hype-erp-myshop-a1b2c`

> You will use this as `project_id` in `firebase_config.py`.

---

## 8. Firebase — Enable Firestore Database

### Step 1 — Open Firestore

1. In Firebase Console left sidebar, click **Build** to expand it
2. Click **Firestore Database**
3. Click **Create database**

### Step 2 — Choose security mode

1. Select **Start in production mode**
2. Click **Next**

### Step 3 — Choose location

1. Click the **location dropdown**
2. Select **asia-south1** (Mumbai — best for India)
3. Click **Enable**
4. Wait 30–60 seconds while Firestore is created

✅ Firestore is now enabled. You'll see an empty database.

---

## 9. Firebase — Enable Realtime Database

### Step 1 — Open Realtime Database

1. In Firebase Console left sidebar, under **Build**
2. Click **Realtime Database**
3. Click **Create database**

### Step 2 — Choose location and mode

1. Location: select **United States (us-central1)** or keep default
2. Click **Next**
3. Select **Start in locked mode**
4. Click **Enable**

### Step 3 — Copy your Database URL

1. At the top of the Realtime Database page you'll see:
   ```
   https://your-project-id-default-rtdb.firebaseio.com/
   ```
2. Copy this URL — you need it for `database_url` in config

> Example: `https://hype-erp-myshop-a1b2c-default-rtdb.firebaseio.com`

---

## 10. Firebase — Get Service Account Key

This JSON file is your app’s password to access Firebase. Keep it secret.

### Step 1 — Open Project Settings

1. Click the **gear icon** (⚙️) next to “Project Overview”
2. Click **Project settings**

### Step 2 — Go to Service Accounts

1. Click the **Service accounts** tab (top of settings page)
2. You'll see **Firebase Admin SDK** section
3. Make sure **Python** is selected in the language dropdown

### Step 3 — Generate the key

1. Click the blue button: **Generate new private key**
2. A popup appears — click **Generate key**
3. A JSON file downloads automatically to your `Downloads` folder
   > Filename like: `hype-erp-myshop-a1b2c-firebase-adminsdk-xxxxx.json`

### Step 4 — Rename and place the file

1. Go to your `Downloads` folder
2. Rename the file to exactly: `serviceAccountKey.json`
3. Move it to your project folder:
   ```
   C:\Users\YourName\Documents\hype-billing-system\serviceAccountKey.json
   ```
   In VS Code Explorer panel, it should appear in the root alongside `main.py`.

### Step 5 — Verify the file contents

Open `serviceAccountKey.json` in VS Code. It should look like:
```json
{
  "type": "service_account",
  "project_id": "hype-erp-myshop-a1b2c",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN RSA PRIVATE KEY-----\n...",
  "client_email": "firebase-adminsdk-xxx@hype-erp-myshop.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  ...
}
```

> ⚠️ **NEVER push this file to GitHub.** It is already in `.gitignore` — double-check:
> ```cmd
> type .gitignore
> ```
> You should see `serviceAccountKey.json` listed there.

### Step 6 — Note your Storage Bucket

1. In Firebase Console → **Project settings** → **General** tab
2. Scroll to **Your apps** section (or look at the project ID)
3. Storage bucket format: `your-project-id.appspot.com`
   > Example: `hype-erp-myshop-a1b2c.appspot.com`

---

## 11. Firebase — Security Rules

### Firestore Rules

1. In Firebase Console left sidebar → **Firestore Database**
2. Click the **Rules** tab (next to Data, Indexes, Usage)
3. Delete everything in the editor
4. Paste this:

```javascript
rules_version = '2';
service cloud.firestore {
   match /databases/{database}/documents {
      // Default: allow reads only for authenticated users
      match /{document=**} {
         allow read: if request.auth != null;
      }

      // Shops collection: fine-grained rules per shop
      match /shops/{shopId} {
         // Allow listing/reading shop-level doc for authenticated users
         allow read: if request.auth != null;

         // Only shop owner may update or delete the shop document
         allow update, delete: if request.auth != null && get(/databases/$(database)/documents/shops/$(shopId)).data.owner_uid == request.auth.uid;

         // Subcollections within a shop (invoices, products, customers, etc.)
         match /invoices/{invoiceId} {
            allow read: if request.auth != null;
            allow create: if request.auth != null && request.resource.data.shop_id == shopId;
            allow update, delete: if request.auth != null && get(/databases/$(database)/documents/shops/$(shopId)).data.owner_uid == request.auth.uid;
         }

         match /products/{productId} {
            allow read: if request.auth != null;
            allow create: if request.auth != null && request.resource.data.shop_id == shopId;
            allow update, delete: if request.auth != null && get(/databases/$(database)/documents/shops/$(shopId)).data.owner_uid == request.auth.uid;
         }

         match /customers/{customerId} {
            allow read: if request.auth != null;
            allow create: if request.auth != null && request.resource.data.shop_id == shopId;
            allow update, delete: if request.auth != null && get(/databases/$(database)/documents/shops/$(shopId)).data.owner_uid == request.auth.uid;
         }

         match /users/{userId} {
            // Users can read their own profile; owners can manage shop users
            allow read: if request.auth != null && (request.auth.uid == userId || get(/databases/$(database)/documents/shops/$(shopId)).data.owner_uid == request.auth.uid);
            allow create: if request.auth != null && get(/databases/$(database)/documents/shops/$(shopId)).data.owner_uid == request.auth.uid;
            allow update, delete: if request.auth != null && (request.auth.uid == userId || get(/databases/$(database)/documents/shops/$(shopId)).data.owner_uid == request.auth.uid);
         }
      }
   }
}
```

5. Click **Publish**

### Realtime Database Rules

1. In Firebase Console → **Realtime Database**
2. Click the **Rules** tab
3. Replace with:

```json
{
   "rules": {
      // Default: authenticated users can read; writes are restricted to owners
      ".read": "auth != null",
      ".write": "auth != null && auth.token.admin == true",

      "shops": {
         "$shopId": {
            ".read": "auth != null",
            ".write": "auth != null && (data.child('owner_uid').val() === auth.uid || newData.child('owner_uid').val() === auth.uid)",

            "invoices": {
               "$invoiceId": {
                  ".read": "auth != null",
                  ".write": "auth != null && (data.parent().child('owner_uid').val() === auth.uid || newData.parent().child('owner_uid').val() === auth.uid)"
               }
            },

            "products": {
               "$productId": {
                  ".read": "auth != null",
                  ".write": "auth != null && data.parent().child('owner_uid').val() === auth.uid"
               }
            }
         }
      },

      "users": {
         "$uid": {
            ".read": "auth != null && auth.uid === $uid",
            ".write": "auth != null && auth.uid === $uid"
         }
      }
   }
}
```

4. Click **Publish**

> ⚠️ For **development / testing only**, you can temporarily use `".read": true, ".write": true`. Never use this in production.

---

## 12. Firebase — Configure in Hype ERP

You have **3 ways** to enter your Firebase details. Choose one.

### ⭐ Option A — Edit `firebase_config.py` in VS Code (simplest)

1. In VS Code **Explorer** panel, click on **`firebase_config.py`**
2. Find the `FIREBASE_CONFIG` dictionary at the top of the file
3. Fill in your values:

```python
FIREBASE_CONFIG = {
    # From Firebase Console → Project Settings → General → Project ID
    "project_id": "hype-erp-myshop-a1b2c",

    # From Firebase Console → Realtime Database → top of page
    "database_url": "https://hype-erp-myshop-a1b2c-default-rtdb.firebaseio.com",

    # Your project ID + .appspot.com
    "storage_bucket": "hype-erp-myshop-a1b2c.appspot.com",

    # Unique ID for this shop (your choice, no spaces)
    "shop_id": "my_shop_kolkata",

    # Leave as is if key is in project root folder
    "service_account_key_path": "serviceAccountKey.json",

    # Set True to enable Firebase sync
    "enabled": True,
}
```

4. Press `Ctrl+S` to save

Done — `firebase_sync.py` and `firebase_deep.py` read this automatically. No other file needs editing.

---

### Option B — CLI Wizard (terminal)

1. Make sure `(venv)` is active in terminal
2. Run:
   ```cmd
   python firebase_config.py
   ```
3. It asks each value one by one — paste your values and press Enter
4. Config is saved to `firebase_runtime_config.json` automatically

---

### Option C — In-App GUI

1. Run `python main.py` and log in as `admin`
2. Inside the app, go to: **Settings → Firebase Setup**
3. A window opens with all fields:

   | Field | What to enter |
   |-------|---------------|
   | Firebase Project ID | `hype-erp-myshop-a1b2c` |
   | Realtime Database URL | `https://hype-erp-myshop-a1b2c-default-rtdb.firebaseio.com` |
   | Storage Bucket | `hype-erp-myshop-a1b2c.appspot.com` |
   | Shop ID | `my_shop_kolkata` |
   | Path to serviceAccountKey.json | Click 📂 to browse for the file |

4. Click **🔌 Test Connection** — it should say “Firebase connection successful!”
5. Click **💾 Save Config**
6. Restart the app

---

### Where to find each Firebase value:

| Config Field | Where in Firebase Console |
|---|---|
| `project_id` | ⚙️ Project Settings → General tab → **Project ID** |
| `database_url` | Build → Realtime Database → **top of Data tab** |
| `storage_bucket` | ⚙️ Project Settings → General → scroll to **Default GCS bucket** |
| `service_account_key_path` | The JSON file you downloaded in Section 10 |

### Config Priority (how the app decides which config to use)

```
Priority 1 → firebase_runtime_config.json   (saved by GUI or wizard)
Priority 2 → FIREBASE_CONFIG dict            (edited in firebase_config.py)
Priority 3 → SQLite settings table           (legacy)
Priority 4 → Firebase DISABLED               (offline mode)
```

### Encrypt Key for EXE Distribution

Before building the EXE, encrypt your key:
```cmd
python encrypt_key.py
```
This creates `serviceAccountKey.enc`. The installer bundles this encrypted file — never the raw `.json`.

---

## 13. App Settings — Shop Info, GST, Invoice

After logging in as `admin`:

1. Go to **Store → Settings** inside the app
2. Fill in:

| Setting | What to enter | Example |
|---------|---------------|---------|
| Shop Name | Your business name | `Raj Electronics` |
| Owner Name | Owner’s name | `Rajesh Kumar` |
| Shop Address | Full address | `12 Park Street, Kolkata 700016` |
| Phone | Contact number | `+91 98765 43210` |
| GSTIN | Your GST number | `19ABCDE1234F1Z5` |
| Invoice Prefix | Invoice number start | `INV` or `RAJ` |
| State Code | Your state’s GST code | `19` (West Bengal) |
| Shop ID | Firebase identifier | `raj_electronics_kolkata` |

3. Click **Save Settings**

### GST State Codes Reference

| State | Code | State | Code |
|-------|------|-------|------|
| West Bengal | 19 | Maharashtra | 27 |
| Delhi | 07 | Karnataka | 29 |
| Tamil Nadu | 33 | Gujarat | 24 |
| Uttar Pradesh | 09 | Rajasthan | 08 |
| Kerala | 32 | Punjab | 03 |

---

## 14. Role-Based Access — Users & Permissions

Hype ERP has 4 user roles. The role is set when creating a user account.

### Role Permissions

| Role | Mode Selector Shown | Billing | ERP (19 modules) | Badge |
|------|:---:|:---:|:---:|------|
| `admin` | ✅ Yes | ✅ Yes | ✅ Full Access | 👑 Red |
| `owner` | ✅ Yes | ✅ Yes | ✅ Full Access | 💎 Orange |
| `manager` | ✅ Yes | ✅ Yes | ✅ Full Access | 🏢 Blue |
| `cashier` | ❌ No | ✅ Yes | ❌ No Access | 🧾 Green |
| other | ❌ No | ✅ Yes | ❌ No Access | — |

### Create a New User

1. Log in as `admin`
2. Go to **Users → Manage Users**
3. Click **Add User**
4. Fill in: Username, Password, Role (select from dropdown: `admin` / `owner` / `manager` / `cashier`)
5. Click **Save**

### How Role Routing Works (`main.py`)

```python
from modules.mode_selector import launch_after_login

# Called right after login button is clicked and credentials verified:
launch_after_login(
    parent          = root,
    db_path         = DB_PATH,
    username        = logged_in_user,    # e.g. "rajesh"
    role            = logged_in_role,    # e.g. "manager"
    open_billing_cb = lambda: open_billing(root),
    open_erp_cb     = lambda: open_erp_menu(root)
)
# That’s it — one line handles all role logic automatically
```

---

## 15. App Flow After Login

```
python main.py
     ↓
  ┌─────────────────────────────┐
  │     Login Screen              │
  │   Username: admin             │
  │   Password: admin123          │
  └─────────────────────────────┘
     ↓ Login OK
  launch_after_login()  [mode_selector.py]
     ↓
  Is role admin / owner / manager?
  ┌──── YES ────────────────────────────────────┐
  │  Mode Selector Window                    │
  │  ┌───────────────┐  ┌───────────────┐  │
  │  │ 🧾 BILLING   │  │  🏢 ERP MODE  │  │
  │  │ Key: 1/F1  │  │  Key: 2/F2  │  │
  │  └───────────────┘  └───────────────┘  │
  └──────────────────────────────────────────┘
  Role = cashier
  └─ Billing opens directly (no mode screen)
```

### Mode Selector Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1` or `F1` | Open Billing Mode |
| `2` or `F2` | Open ERP Mode |
| `Enter` | Open Billing (default) |
| `Esc` | Close |

---

## 16. ERP Modules — All 19

Visible only for `admin` / `owner` / `manager` roles via **ERP Mode**:

| # | Module | File | Description |
|---|--------|------|-------------|
| 1 | Accounting | `modules/account.py` | General ledger, journals |
| 2 | Invoice | `modules/account_invoice.py` | GST invoice management |
| 3 | Asset | `modules/account_asset.py` | Fixed asset tracking |
| 4 | Tax / GST | `modules/account_tax.py` | GST config and reports |
| 5 | Banking | `modules/account_statement.py` | Bank reconciliation |
| 6 | Sales | `modules/sale.py` | Sales orders and quotes |
| 7 | Purchase | `modules/purchase.py` | Purchase orders |
| 8 | Inventory | `modules/stock.py` | Stock management |
| 9 | Manufacturing | `modules/production.py` | Production orders |
| 10 | HR | `modules/hr_module.py` | Employee management |
| 11 | Payroll | `modules/payroll_module.py` | Salary processing |
| 12 | CRM | `modules/crm_module.py` | Customer relationship |
| 13 | Projects | `modules/projects_module.py` | Project tracking |
| 14 | Timesheet | `modules/timesheet.py` | Time logging |
| 15 | POS | `modules/pos_module.py` | Point of sale |
| 16 | Shipping | `modules/stock_package.py` | Delivery management |
| 17 | Quality Control | `modules/quality_control.py` | QC checks |
| 18 | Marketing | `modules/marketing.py` | Campaigns |
| 19 | Reporting | `modules/reporting_module.py` | Analytics & reports |

### ERP Grid Features
- 🔍 **Live search** — type module name to filter instantly (`Ctrl+F` to focus)
- 📜 **Scrollable** — mouse wheel + arrow keys work
- ⌨️ **Keyboard navigation** — arrows, Tab, Enter to open, number keys `1–9`
- 🔢 **Keyboard shortcut** — press `1` through `9` to open that module directly

---

## 17. Scroll & Keyboard Support

Every window uses `modules/scrollable_frame.py` for full scroll + keyboard support.

### Add Scroll to Any Window

```python
from modules.scrollable_frame import ScrollableFrame

# Replace a regular Frame with ScrollableFrame:
sf = ScrollableFrame(win, bg='#1a1a2e')
sf.pack(fill='both', expand=True)
container = sf.scrollable_frame   # ← put all your widgets inside this
```

### Add Scroll to Any Treeview

```python
from modules.scrollable_frame import add_treeview_scroll

vsb, hsb = add_treeview_scroll(parent_frame, my_treeview)
vsb.pack(side='right', fill='y')
hsb.pack(side='bottom', fill='x')
```

### All Supported Controls

| Control | Action |
|---------|--------|
| Mouse wheel | Scroll up / down |
| `↑ ↓` | Scroll by line |
| `← →` | Scroll horizontally |
| `Page Up` | Scroll up fast |
| `Page Down` | Scroll down fast |
| `Home` | Jump to top |
| `End` | Jump to bottom |
| `↑ ↓` on Treeview | Move selected row |
| `Home / End` on Treeview | First / last row |

---

## 18. AI Models Setup

### Automatic (recommended)

AI models auto-download on first launch via `auto_install.py`.

| Mode | Models stored at |
|------|-----------------|
| Source (`python main.py`) | `./models/` |
| EXE (`HypeERP.exe`) | `%LOCALAPPDATA%\HypeERP\models\` |

### Manual Download

If auto-download fails, run in terminal:
```cmd
python -c "from ai_assistant import auto_download_and_install, AVAILABLE_MODELS; [auto_download_and_install(k) for k in AVAILABLE_MODELS]"
```

### AI Models Available

| Model | Purpose | Used In |
|-------|---------|--------|
| `sales_predictor` | 7-day sales forecast | Dashboard, Reports |
| `price_suggester` | Smart price suggestions | Products |
| `anomaly_detector` | Unusual transaction alerts | Billing, Accounting |

> 💡 `.pkl` model files are **never bundled in the EXE** (too large). Downloaded once on first launch, then work fully offline.

---

## 19. Build EXE — PyInstaller

### Step 1 — Install PyInstaller

```cmd
pip install pyinstaller
```

### Step 2 — Encrypt Firebase key first

```cmd
python encrypt_key.py
```

This creates `serviceAccountKey.enc` in the project root.

### Step 3 — Build the EXE

**Option A — PowerShell script (recommended, one click):**

In VS Code terminal, switch to PowerShell:
```powershell
powershell
.\build_pyinstaller.ps1
```

The script automatically:
1. 🗑️ Cleans old `dist/` and `build/` folders
2. 🔐 Runs `encrypt_key.py`
3. 🔨 Runs PyInstaller with all correct flags for all 19 modules
4. ✅ Reports success + file size

**Option B — Manual command (CMD):**

```cmd
pyinstaller --onefile --windowed --icon=icon.ico ^
  --name="HypeERP" ^
  --add-data "icon.ico;." ^
  --add-data "logo.png;." ^
  --add-data "modules;modules" ^
  --hidden-import "modules.account" ^
  --hidden-import "modules.account_invoice" ^
  --hidden-import "modules.account_asset" ^
  --hidden-import "modules.account_tax" ^
  --hidden-import "modules.account_statement" ^
  --hidden-import "modules.sale" ^
  --hidden-import "modules.purchase" ^
  --hidden-import "modules.stock" ^
  --hidden-import "modules.production" ^
  --hidden-import "modules.hr_module" ^
  --hidden-import "modules.payroll_module" ^
  --hidden-import "modules.crm_module" ^
  --hidden-import "modules.projects_module" ^
  --hidden-import "modules.timesheet" ^
  --hidden-import "modules.pos_module" ^
  --hidden-import "modules.stock_package" ^
  --hidden-import "modules.quality_control" ^
  --hidden-import "modules.marketing" ^
  --hidden-import "modules.reporting_module" ^
  --hidden-import "modules.erp_main_menu" ^
  --hidden-import "modules.mode_selector" ^
  --hidden-import "modules.scrollable_frame" ^
  --hidden-import "modules.firebase_settings_ui" ^
  --hidden-import "firebase_config" ^
  --hidden-import "firebase_admin" ^
  --hidden-import "firebase_admin.credentials" ^
  --hidden-import "firebase_admin.firestore" ^
  --hidden-import "google.cloud.firestore" ^
  --hidden-import "google.auth" ^
  --hidden-import "google.oauth2.service_account" ^
  --hidden-import "reportlab.pdfgen" ^
  --hidden-import "reportlab.lib.pagesizes" ^
  --hidden-import "reportlab.platypus" ^
  --hidden-import "PIL._tkinter_finder" ^
  --hidden-import "cryptography.fernet" ^
  --hidden-import "sklearn.utils._cython_blas" ^
  --hidden-import "sklearn.neighbors._partition_nodes" ^
  --hidden-import "sklearn.tree._utils" ^
  --hidden-import "joblib" ^
  --hidden-import "numpy" ^
  --hidden-import "pandas" ^
  --collect-all "firebase_admin" ^
  --collect-all "google.cloud.firestore" ^
  --collect-all "google.auth" ^
  --collect-all "reportlab" ^
  --collect-all "sklearn" ^
  main.py
```

### Step 4 — Find your EXE

After build completes (3–7 minutes):
```
dist\HypeERP.exe   ← your distributable EXE
```

### Important Rules

| Rule | Detail |
|------|--------|
| ✅ Include `modules;modules` | All 19 ERP modules + helpers |
| ✅ Place beside EXE | `serviceAccountKey.enc` |
| ❌ Never distribute | `serviceAccountKey.json` (raw key) |
| ❌ Don’t bundle | AI `.pkl` files (auto-downloaded) |
| 🖥️ DB path in EXE mode | `%LOCALAPPDATA%\HypeERP\hype_billing_system.db` |
| 🔥 Firebase config EXE path | `%LOCALAPPDATA%\HypeERP\firebase_runtime_config.json` |

---

## 20. Build Installer — Inno Setup

### Step 1 — Open Inno Setup Compiler

Search **Inno Setup Compiler** in Windows Start menu and open it.

### Step 2 — Open the script

1. Click **File → Open**
2. Navigate to your project folder
3. Select `hype_billing_installer.iss`
4. Click **Open**

### Step 3 — Compile

1. Press `F9` **OR** click **Build → Compile** in menu
2. Watch the output log — should end with: `Successful`
3. Output file:
   ```
   installer_output\HypeERP_Setup_v3.0.0.exe
   ```

### What the Installer Does for End Users

| Action | Detail |
|--------|--------|
| Installs EXE | `C:\Program Files\HypeERP\HypeERP.exe` |
| Creates data folders | `%LOCALAPPDATA%\HypeERP\{models, backups, exports, logs}` |
| Desktop shortcut | Optional (user chooses during install) |
| Start Menu entry | `Hype ERP` group |
| Bundles | `serviceAccountKey.enc`, `icon.ico`, `logo.png`, docs |
| Welcome screen | Shows default login: `admin` / `admin123` |
| No admin required | `PrivilegesRequired=lowest` |
| Uninstaller | In Windows Add/Remove Programs |
| Auto-launch | Runs app after install finishes |

---

## 21. First Run Checklist

After installing and launching for the first time:

- [ ] **Login** with `admin` / `admin123`
- [ ] **Change admin password** → Users → My Account
- [ ] **Set shop info** → Store → Settings (name, GSTIN, address, phone)
- [ ] **Set invoice prefix** (default: `INV`) → Store → Settings
- [ ] **Add products** → Store → Manage Products
- [ ] **Configure Firebase** (if cloud sync needed) → Settings → Firebase Setup
- [ ] **Create staff accounts** → Users → Manage Users (cashiers, managers)
- [ ] **Test a GST invoice** with PDF export
- [ ] **Test ERP module** (login as admin → Mode Selector → ERP Mode → open any module)

---

## 22. Troubleshooting

### App doesn’t start / Python not found
```cmd
python --version
```
If not found: reinstall Python and check **“Add to PATH”** during install.

### `ModuleNotFoundError` on `python main.py`
```cmd
pip install -r requirements.txt
```

### EXE crashes with no error window
```cmd
cd dist
HypeERP.exe
```
Run from Command Prompt to see the full traceback error.

### `ModuleNotFoundError` inside EXE
Add missing module to `--hidden-import` in `build_pyinstaller.ps1` and rebuild:
```powershell
.\build_pyinstaller.ps1
```

### Firebase: `serviceAccountKey.json` not found
- Make sure the file is in the **project root** (same folder as `main.py`)
- Check the exact filename — must be: `serviceAccountKey.json` (case-sensitive on Linux)

### Firebase: Connection error / timeout
1. Open app → **Settings → Firebase Setup** → click **Test Connection**
2. Check your `project_id` matches exactly what’s in Firebase Console
3. Check internet connection
4. Check Firestore is **enabled** in Firebase Console

### Firebase: `is_enabled()` returns False
- Run `python firebase_config.py` (wizard)
- Or open app → Settings → Firebase Setup → check `enabled` is ticked → Save

### `firebase_runtime_config.json` location

| Mode | Path |
|------|------|
| Source | `./firebase_runtime_config.json` |
| EXE | `%LOCALAPPDATA%\HypeERP\firebase_runtime_config.json` |

### Mode Selector not showing after login
- Check `main.py` calls `launch_after_login()`
- Verify user has role `admin`, `owner`, or `manager` in DB:
  ```cmd
  sqlite3 hype_billing_system.db "SELECT username, role FROM users;"
  ```

### ERP module fails to open
- Check `modules/xxx.py` file exists
- Check class name in `erp_main_menu.py` matches exactly
- Run `python main.py` in source mode to see full error

### Scroll not working in a window
```python
from modules.scrollable_frame import ScrollableFrame
sf = ScrollableFrame(win)
sf.pack(fill='both', expand=True)
# put all widgets in sf.scrollable_frame
```

### AI models not loading
```cmd
python -c "from ai_assistant import auto_download_and_install, AVAILABLE_MODELS; [auto_download_and_install(k) for k in AVAILABLE_MODELS]"
```

### `tkinter` not found (Linux only)
```bash
sudo apt install python3-tk
```

### Database reset (fresh start)
```
Source: delete  hype_billing_system.db         (in project root)
EXE:    delete  %LOCALAPPDATA%\HypeERP\hype_billing_system.db
```

### PowerShell says script can’t run
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 23. Full Build Pipeline Summary

```
┌───────────────────────────────────────────────────────┐
│  COMPLETE BUILD PIPELINE — Hype ERP v3.0.0    │
└───────────────────────────────────────────────────────┘

Step 1  git clone + cd + code .          (VS Code)
Step 2  python -m venv venv              (create env)
Step 3  venv\Scripts\activate            (activate env)
Step 4  pip install -r requirements.txt  (install packages)
Step 5  [Firebase Console] Setup project, Firestore, Realtime DB
Step 6  [Download] serviceAccountKey.json → rename → project root
Step 7  [firebase_config.py] Fill in project_id, database_url, etc.
Step 8  python main.py                   (test everything)
Step 9  python encrypt_key.py            (create .enc key)
Step 10 .\build_pyinstaller.ps1          (builds dist\HypeERP.exe)
Step 11 [Inno Setup] Open .iss → F9     (builds installer EXE)
Step 12 Distribute HypeERP_Setup_v3.0.0.exe
```

### New Files Added in v3.0.0

| File | Purpose |
|------|---------|
| `firebase_config.py` | Central Firebase config — edit once, read everywhere |
| `modules/firebase_settings_ui.py` | In-app Firebase setup GUI window |
| `modules/mode_selector.py` | Role-based post-login router (Billing / ERP) |
| `modules/scrollable_frame.py` | Reusable scroll + keyboard support for all windows |
| `modules/erp_main_menu.py` | 19-module ERP grid — searchable, scrollable |
| `build_pyinstaller.ps1` | One-click PowerShell EXE builder |
| `hype_billing_installer.iss` | Inno Setup 6 Windows installer script |

---

## 📞 Support

- **GitHub Issues:** [https://github.com/david0154/hype-billing-system/issues](https://github.com/david0154/hype-billing-system/issues)
- **Developer:** [https://github.com/david0154](https://github.com/david0154)
- **Org:** [https://github.com/nexuzy-lab](https://github.com/nexuzy-lab)

---

<p align="center">
  <i>Powered by <b>Hype ERP</b> v3.0.0 — Developed by <b>Nexuzy Lab</b> &amp; Lead Developer <b>David (DevilOne)</b></i>
</p>
