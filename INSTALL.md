# Installation & Setup

This document shows how to create a Python virtual environment, install dependencies, configure Firebase credentials, and run the Hype Retail Billing System.

## 1) Prerequisites

- Python 3.8+ installed and on PATH
- Git (optional)
- Internet access for installing packages

## 2) Quick install (Windows PowerShell)

Open PowerShell in the project root and run:

```powershell
.\install_dependencies.ps1
```

Then activate the venv and run the app:

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

## 3) Quick install (Linux / macOS)

Open a terminal in the project root and run:

```bash
./install.sh
source .venv/bin/activate
python main.py
```

## 4) Firebase credentials

1. Go to Firebase Console → Project → Settings → Service Accounts.
2. Click "Generate new private key" and download the JSON file.
3. Save it as `serviceAccountKey.json` in the project root (same folder as `main.py`).

## 5) Verify sync

1. Run `python main.py`, log in with the admin user (default: username `admin`, password `admin123`).
2. After login the app initializes Firebase and starts background sync. Watch `firebase_sync.log` for activity.

## 6) Optional: Running on a VM or behind VPN

- For remote deployments (multiple stores), consider running the app on a VM (Windows/Linux) or using a VPN (WireGuard/OpenVPN) to secure traffic between sites. The Firebase Admin SDK communicates with Firestore over HTTPS; VPN is optional but recommended for added network security.

## 7) Troubleshooting

- If `firebase_admin` import fails: `pip install firebase-admin`
- If credentials not found: ensure `serviceAccountKey.json` exists and is valid JSON.
- If sync is queuing operations: check internet connectivity (DNS and outbound HTTPS allowed).

## 8) Additional scripts

- `install_dependencies.ps1` — Windows installer script
- `install.sh` — Unix installer script

## 10) Build Windows executable and installer (PyInstaller + Inno Setup)

1) Build executable with PyInstaller (Windows PowerShell):

```powershell
# activate venv first
.\.venv\Scripts\Activate.ps1
.\build_pyinstaller.ps1
```

This produces `dist\HypeBilling.exe`.

2) Create Inno Setup installer

- Install Inno Setup (https://jrsoftware.org/isinfo.php) on a Windows machine.
- Open `hype_billing_installer.iss` in Inno Setup and compile — it expects `dist\HypeBilling.exe` and application files in the project root.

Notes:
- `serviceAccountKey.json` is not bundled by default (sensitive). After installation, copy `serviceAccountKey.json` into the install folder (e.g., `C:\Program Files\HypeRetailBilling`).
- Test the installed app on a clean Windows VM before distributing.


## 9) Security

- Never commit `serviceAccountKey.json` to source control. Treat it as a secret.
