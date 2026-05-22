# ===========================================================================
# Hype ERP v3.0.0 - PyInstaller Build Script (PowerShell)
# Developer: David | Nexuzy Lab
# Run: .\build_pyinstaller.ps1
# ===========================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Hype ERP v3.0.0 - PyInstaller Build" -ForegroundColor Cyan
Write-Host "  Developer: David | Nexuzy Lab" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Clean old build
Write-Host "[1/4] Cleaning old build files..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "HypeERP.spec") { Remove-Item -Force "HypeERP.spec" }
Write-Host "      Done." -ForegroundColor Green

# Step 2: Encrypt Firebase key
Write-Host "[2/4] Encrypting serviceAccountKey.json..." -ForegroundColor Yellow
if (Test-Path "serviceAccountKey.json") {
    python encrypt_key.py
    Write-Host "      Encrypted -> serviceAccountKey.enc" -ForegroundColor Green
} else {
    Write-Host "      WARNING: serviceAccountKey.json not found - skipping encryption." -ForegroundColor Red
    Write-Host "      EXE will run without Firebase cloud sync." -ForegroundColor Red
}

# Step 3: PyInstaller build
Write-Host "[3/4] Running PyInstaller..." -ForegroundColor Yellow
Write-Host ""

pyinstaller `
    --onefile `
    --windowed `
    --icon=icon.ico `
    --name="HypeERP" `
    --add-data "icon.ico;." `
    --add-data "logo.png;." `
    --add-data "modules;modules" `
    --hidden-import "modules.account" `
    --hidden-import "modules.account_invoice" `
    --hidden-import "modules.account_asset" `
    --hidden-import "modules.account_tax" `
    --hidden-import "modules.account_statement" `
    --hidden-import "modules.sale" `
    --hidden-import "modules.purchase" `
    --hidden-import "modules.stock" `
    --hidden-import "modules.production" `
    --hidden-import "modules.hr_module" `
    --hidden-import "modules.payroll_module" `
    --hidden-import "modules.crm_module" `
    --hidden-import "modules.projects_module" `
    --hidden-import "modules.timesheet" `
    --hidden-import "modules.pos_module" `
    --hidden-import "modules.stock_package" `
    --hidden-import "modules.quality_control" `
    --hidden-import "modules.marketing" `
    --hidden-import "modules.reporting_module" `
    --hidden-import "modules.erp_main_menu" `
    --hidden-import "modules.mode_selector" `
    --hidden-import "modules.scrollable_frame" `
    --hidden-import "modules.erp_branding" `
    --hidden-import "modules.inventory_analysis" `
    --hidden-import "sklearn.utils._cython_blas" `
    --hidden-import "sklearn.utils._typedefs" `
    --hidden-import "sklearn.utils._heap" `
    --hidden-import "sklearn.utils._sorting" `
    --hidden-import "sklearn.utils._vector_sentinel" `
    --hidden-import "sklearn.neighbors.typedefs" `
    --hidden-import "sklearn.neighbors._partition_nodes" `
    --hidden-import "sklearn.tree._utils" `
    --hidden-import "sklearn.tree._criterion" `
    --hidden-import "sklearn.tree._splitter" `
    --hidden-import "sklearn.ensemble._forest" `
    --hidden-import "sklearn.linear_model._base" `
    --hidden-import "firebase_admin" `
    --hidden-import "firebase_admin.credentials" `
    --hidden-import "firebase_admin.firestore" `
    --hidden-import "firebase_admin.auth" `
    --hidden-import "firebase_admin.storage" `
    --hidden-import "google.cloud.firestore" `
    --hidden-import "google.cloud.firestore_v1" `
    --hidden-import "google.auth" `
    --hidden-import "google.auth.credentials" `
    --hidden-import "google.oauth2" `
    --hidden-import "google.oauth2.credentials" `
    --hidden-import "google.oauth2.service_account" `
    --hidden-import "reportlab.pdfgen" `
    --hidden-import "reportlab.pdfgen.canvas" `
    --hidden-import "reportlab.lib.pagesizes" `
    --hidden-import "reportlab.lib.styles" `
    --hidden-import "reportlab.lib.units" `
    --hidden-import "reportlab.platypus" `
    --hidden-import "PIL._tkinter_finder" `
    --hidden-import "PIL.Image" `
    --hidden-import "PIL.ImageTk" `
    --hidden-import "cryptography.fernet" `
    --hidden-import "cryptography.hazmat.primitives" `
    --hidden-import "joblib" `
    --hidden-import "numpy" `
    --hidden-import "pandas" `
    --hidden-import "pandas._libs.tslibs.np_datetime" `
    --hidden-import "pandas._libs.tslibs.nattype" `
    --hidden-import "pandas._libs.tslibs.timedeltas" `
    --hidden-import "pandas._libs.skiplist" `
    --hidden-import "sqlite3" `
    --hidden-import "json" `
    --hidden-import "tkinter" `
    --hidden-import "tkinter.ttk" `
    --hidden-import "tkinter.messagebox" `
    --hidden-import "tkinter.filedialog" `
    --hidden-import "tkinter.simpledialog" `
    --collect-all "firebase_admin" `
    --collect-all "google.cloud.firestore" `
    --collect-all "google.auth" `
    --collect-all "reportlab" `
    --collect-all "sklearn" `
    main.py

# Step 4: Result
Write-Host ""
if (Test-Path "dist\HypeERP.exe") {
    $size = [math]::Round((Get-Item "dist\HypeERP.exe").Length / 1MB, 1)
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  BUILD SUCCESSFUL!" -ForegroundColor Green
    Write-Host "  Output: dist\HypeERP.exe ($size MB)" -ForegroundColor Green
    Write-Host "  Next: Run Inno Setup with hype_billing_installer.iss" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  BUILD FAILED - check errors above" -ForegroundColor Red
    Write-Host "  Tip: Run 'dist\HypeERP.exe' in CMD to see crash log" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}
