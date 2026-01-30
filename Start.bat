@echo off
cd /d "%~dp0"

where python >nul 2>&1
if %errorlevel% equ 0 (
    python main.py
    goto :end
)

where python3 >nul 2>&1
if %errorlevel% equ 0 (
    python3 main.py
    goto :end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" main.py
    goto :end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" main.py
    goto :end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" main.py
    goto :end
)

echo.
echo [ERROR] Python not found. Please run Setup.bat first.
pause

:end
