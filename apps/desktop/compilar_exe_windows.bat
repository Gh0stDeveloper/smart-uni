@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SMART UNI - Compilacion Windows

echo ==========================================
echo SMART UNI - Ejecutable independiente
 echo ==========================================
echo.

where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON=py -3"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo ERROR: Instala Python desde python.org y activa Add to PATH.
        pause
        exit /b 1
    )
    set "PYTHON=python"
)

echo [1/3] Comprobamos las 17 pruebas...
%PYTHON% -m unittest discover -s tests -v
if errorlevel 1 (
    echo ERROR: Las pruebas no pasaron.
    pause
    exit /b 1
)

echo [2/3] Preparamos PyInstaller...
%PYTHON% -m pip install "pyinstaller>=6,<7"
if errorlevel 1 (
    echo ERROR: No pudimos instalar PyInstaller.
    pause
    exit /b 1
)

echo [3/3] Creamos el EXE con el icono original...
%PYTHON% -m PyInstaller --noconfirm --clean --onefile --windowed --name Smart_Uni --icon "design\smart_uni.ico" --add-data "design\previews\00_isotipo_smart_uni.png;design/previews" main.py
if errorlevel 1 (
    echo ERROR: La compilacion fallo.
    pause
    exit /b 1
)

if not exist "dist\Smart_Uni.exe" (
    echo ERROR: No aparece dist\Smart_Uni.exe
    pause
    exit /b 1
)

echo.
echo LISTO: dist\Smart_Uni.exe
 echo Este EXE es independiente de Python.
pause
endlocal
