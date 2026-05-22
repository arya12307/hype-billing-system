#!/usr/bin/env bash
# Unix helper to run PyInstaller (useful if building on Linux for Windows via wine or for testing)
set -e
python3 -m pip install --user --upgrade pyinstaller
ENTRY=main.py
NAME=HypeBilling
rm -rf build dist ${NAME}.spec || true
python3 -m PyInstaller --noconfirm --clean --onefile --name ${NAME} --add-data "logo.png:." --add-data "LICENSE:." --add-data "README.md:." ${ENTRY}
echo "Build complete: dist/${NAME}"
