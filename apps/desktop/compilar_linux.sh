#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo '[1/3] Comprobamos las 17 pruebas...'
python3 -m unittest discover -s tests -v

echo '[2/3] Creamos un entorno de compilación e instalamos PyInstaller...'
python3 -m venv .venv-build
.venv-build/bin/python -m pip install 'pyinstaller>=6,<7'

echo '[3/3] Generamos la versión independiente para Linux...'
.venv-build/bin/python -m PyInstaller --noconfirm --clean --onefile --windowed \
  --name Smart_Uni \
  --add-data 'design/previews/00_isotipo_smart_uni.png:design/previews' \
  main.py

echo 'LISTO: dist/Smart_Uni (ejecutable Linux, no Windows)'
