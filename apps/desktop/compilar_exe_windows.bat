@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SMART UNI - Compilacion Windows
echo ==========================================
echo SMART UNI - Ejecutable Windows independiente
echo ==========================================
where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON=py -3"
) else (
    set "PYTHON=python"
)
%PYTHON% -m unittest discover -s tests -v
if errorlevel 1 goto fail
%PYTHON% -m pip install "pyinstaller>=6,<7" "pillow>=10,<13"
if errorlevel 1 goto fail
%PYTHON% design\build_icon.py
if errorlevel 1 goto fail
%PYTHON% -m PyInstaller --noconfirm --clean --onefile --windowed --name Smart_Uni --icon "design\smart_uni.ico" --add-data "design\previews\00_isotipo_smart_uni.png;design/previews" --add-data "design\tokens.json;design" main.py
if errorlevel 1 goto fail
echo Listo: dist\Smart_Uni.exe
pause
exit /b 0
:fail
echo ERROR: no se pudo completar la compilacion.
pause
exit /b 1
