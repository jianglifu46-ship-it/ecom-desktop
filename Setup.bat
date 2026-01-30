@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================================
echo       Ecom Detail Page Manager - Setup
echo ========================================================
echo.
echo This will install Python and dependencies automatically.
echo.

set "INSTALL_DIR=%~dp0"
cd /d "%INSTALL_DIR%"

echo [1/4] Checking Python...

where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
    echo       Found Python !PYVER!
    set "PYTHON_CMD=python"
    goto :install_deps
)

where python3 >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python3 --version 2^>^&1') do set PYVER=%%i
    echo       Found Python !PYVER!
    set "PYTHON_CMD=python3"
    goto :install_deps
)

if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    echo       Found Python 3.10
    set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    goto :install_deps
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    echo       Found Python 3.11
    set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :install_deps
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    echo       Found Python 3.12
    set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :install_deps
)

echo       Python not found. Downloading...
echo.

set "PYTHON_URL=https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe"
set "PYTHON_INSTALLER=%TEMP%\python-installer.exe"

powershell -Command "(New-Object Net.WebClient).DownloadFile('%PYTHON_URL%', '%PYTHON_INSTALLER%')"

if not exist "%PYTHON_INSTALLER%" (
    echo.
    echo [ERROR] Download failed. Please check your network.
    echo         Or download Python manually: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo       Installing Python...
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

echo       Waiting for installation...
timeout /t 30 /nobreak >nul

set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"

if not exist "%PYTHON_CMD%" (
    echo.
    echo [ERROR] Python installation may have failed.
    echo         Please restart your computer and run this again.
    pause
    exit /b 1
)

echo       Python installed successfully!

:install_deps
echo.
echo [2/4] Installing dependencies...

"%PYTHON_CMD%" -m pip install --upgrade pip -q 2>nul

echo       Installing PyQt6, Pillow, Requests...
"%PYTHON_CMD%" -m pip install PyQt6 Pillow requests numpy -q

if %errorlevel% neq 0 (
    echo       Some dependencies may have failed, trying to continue...
)

echo       Dependencies installed!

:create_shortcut
echo.
echo [3/4] Creating desktop shortcut...

set "SHORTCUT=%USERPROFILE%\Desktop\EcomManager.lnk"

echo @echo off > "%INSTALL_DIR%Start.bat"
echo cd /d "%INSTALL_DIR%" >> "%INSTALL_DIR%Start.bat"
echo "%PYTHON_CMD%" main.py >> "%INSTALL_DIR%Start.bat"

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%INSTALL_DIR%Start.bat'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Save()" 2>nul

if exist "%SHORTCUT%" (
    echo       Desktop shortcut created!
) else (
    echo       Shortcut creation failed. You can run Start.bat directly.
)

:launch
echo.
echo [4/4] Launching application...
echo.
echo ========================================================
echo       Setup Complete!
echo       
echo       Starting the application now...
echo       You can use the desktop shortcut next time.
echo ========================================================
echo.

timeout /t 2 /nobreak >nul

"%PYTHON_CMD%" main.py

if %errorlevel% neq 0 (
    echo.
    echo [INFO] If the app did not start:
    echo        1. Restart your computer
    echo        2. Run this setup again
    pause
)
