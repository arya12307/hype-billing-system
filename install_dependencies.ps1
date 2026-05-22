<#
PowerShell install script for Hype Retail Billing System
Usage (PowerShell):
  Open PowerShell, navigate to project root, then:
    .\install_dependencies.ps1

This will create a virtual environment, activate it, upgrade pip, and install requirements.
#>
Write-Host "Creating virtual environment .venv..."
python -m venv .venv

Write-Host "Activating virtual environment and installing dependencies..."
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host "Installation complete. Activate the venv with:` .\.venv\Scripts\Activate.ps1` and run `python main.py`"
