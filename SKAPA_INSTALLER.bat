@echo off
setlocal EnableDelayedExpansion
title The Isle Server Manager - Skapar Setup.exe
color 0A
cls

echo.
echo  ================================================
echo    THE ISLE SERVER MANAGER - Bygger Setup.exe
echo  ================================================
echo.

set LOGFILE=%~dp0build_log.txt
echo BUILD START %date% %time% > "%LOGFILE%"

:: ── Steg 1: Python ──────────────────────────────────────────────────
echo  [1/4] Kontrollerar Python...
python --version >nul 2>&1
if %errorlevel% == 0 goto :python_ok

echo  [INFO] Installerar Python via winget...
winget install -e --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [FEL] Python saknas. Installera fran https://python.org
    echo  Bocka i "Add Python to PATH" vid installationen!
    pause
    exit /b 1
)

:python_ok
for /f "tokens=*" %%i in ('python --version') do echo  [OK] %%i

:: ── Steg 2: Beroenden ───────────────────────────────────────────────
echo.
echo  [2/4] Installerar beroenden...
python -m pip install --upgrade pip --quiet >> "%LOGFILE%" 2>&1
python -m pip install pyinstaller customtkinter requests psutil Pillow --quiet --upgrade >> "%LOGFILE%" 2>&1
if %errorlevel% neq 0 (
    echo  [FEL] pip misslyckades. Se: %LOGFILE%
    pause & exit /b 1
)
echo  [OK] Klart.

:: ── Steg 3: Bygg huvud-appen ────────────────────────────────────────
echo.
echo  [3/4] Bygger TheIsleServerManager.exe (2-4 min)...

if not exist "assets" mkdir assets
if not exist "Output"  mkdir Output

python -c "import struct,os; os.makedirs('assets',exist_ok=True); open('assets/icon.ico','wb').write(struct.pack('<HHH',0,1,1)+struct.pack('BBBBHHII',16,16,0,0,1,32,40+16*16*4,22)+struct.pack('<IiiHHIIiiII',40,16,32,1,32,0,16*16*4,0,0,0,0)+b'\x00\xC8\x53\xFF'*256+b'\x00'*64) if not os.path.exists('assets/icon.ico') else None" 2>nul

pyinstaller --onefile --windowed --uac-admin --name TheIsleServerManager --icon assets\icon.ico --add-data "ui;ui" --add-data "core;core" --hidden-import customtkinter --hidden-import PIL --hidden-import PIL._imagingtk --hidden-import psutil --hidden-import requests --collect-data customtkinter --noconfirm --clean --log-level WARN main.py >> "%LOGFILE%" 2>&1

if not exist "dist\TheIsleServerManager.exe" (
    echo  [FEL] Byggandet misslyckades. Loggen: %LOGFILE%
    notepad "%LOGFILE%"
    pause & exit /b 1
)
echo  [OK] TheIsleServerManager.exe klar.

:: ── Steg 4: Bygg Setup.exe ──────────────────────────────────────────
echo.
echo  [4/4] Bygger Setup.exe...

pyinstaller --onefile --windowed --uac-admin --name TheIsleServerManager_Setup --icon assets\icon.ico --add-data "dist\TheIsleServerManager.exe;." --hidden-import customtkinter --hidden-import PIL --hidden-import PIL._imagingtk --collect-data customtkinter --noconfirm --log-level WARN installer\setup_app.py >> "%LOGFILE%" 2>&1

if not exist "dist\TheIsleServerManager_Setup.exe" (
    echo  [FEL] Setup.exe byggandet misslyckades. Loggen: %LOGFILE%
    notepad "%LOGFILE%"
    pause & exit /b 1
)

copy /Y "dist\TheIsleServerManager_Setup.exe" "Output\TheIsleServerManager_Setup.exe" >nul

echo.
echo  ================================================
echo   KLART!
echo  ================================================
echo.
echo  Fil: Output\TheIsleServerManager_Setup.exe
echo.
echo  Dubbelklicka pa den filen - normalt
echo  Windows-installationsprogram!
echo.
explorer Output
pause
