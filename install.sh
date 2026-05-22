#!/usr/bin/env bash
# Unix install script for Hype Retail Billing System
set -e
echo "Creating virtual environment .venv..."
python3 -m venv .venv
echo "Activating venv and installing requirements..."
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo "Installation complete. Activate with: source .venv/bin/activate and run: python main.py"
