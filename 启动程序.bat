@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM 检测 Python
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

REM 尝试常见安装路径
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" main.py
    goto :end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" main.py
    goto :end
)

echo.
echo [错误] 未找到 Python，请先运行"一键安装并启动.bat"
pause

:end
