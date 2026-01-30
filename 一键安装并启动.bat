@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║          电商详情页管理系统 - 一键安装程序                    ║
echo ║                                                              ║
echo ║  本程序将自动完成以下操作：                                   ║
echo ║  1. 检测并安装 Python（如需要）                               ║
echo ║  2. 安装程序依赖                                             ║
echo ║  3. 创建桌面快捷方式                                         ║
echo ║  4. 启动程序                                                 ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM 获取当前目录
set "INSTALL_DIR=%~dp0"
cd /d "%INSTALL_DIR%"

REM ========== 步骤1: 检测 Python ==========
echo [1/4] 检测 Python 环境...

where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
    echo       已检测到 Python !PYVER!
    set "PYTHON_CMD=python"
    goto :check_pip
)

where python3 >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python3 --version 2^>^&1') do set PYVER=%%i
    echo       已检测到 Python !PYVER!
    set "PYTHON_CMD=python3"
    goto :check_pip
)

REM Python 未安装，下载并安装
echo       未检测到 Python，正在下载安装...
echo.

REM 下载 Python 安装程序
set "PYTHON_URL=https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe"
set "PYTHON_INSTALLER=%TEMP%\python-installer.exe"

echo       正在下载 Python 安装程序...
powershell -Command "(New-Object Net.WebClient).DownloadFile('%PYTHON_URL%', '%PYTHON_INSTALLER%')"

if not exist "%PYTHON_INSTALLER%" (
    echo.
    echo [错误] 下载 Python 失败，请检查网络连接
    echo        或手动下载安装: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo       正在安装 Python（可能需要管理员权限）...
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

REM 等待安装完成
timeout /t 30 /nobreak >nul

REM 刷新环境变量
set "PATH=%LOCALAPPDATA%\Programs\Python\Python310;%LOCALAPPDATA%\Programs\Python\Python310\Scripts;%PATH%"

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [错误] Python 安装可能未完成，请重启电脑后再次运行此程序
    pause
    exit /b 1
)

set "PYTHON_CMD=python"
echo       Python 安装完成！

:check_pip
REM ========== 步骤2: 安装依赖 ==========
echo.
echo [2/4] 安装程序依赖...

REM 升级 pip
%PYTHON_CMD% -m pip install --upgrade pip -q 2>nul

REM 安装依赖
echo       正在安装 PyQt6、Pillow、Requests 等依赖...
%PYTHON_CMD% -m pip install PyQt6 Pillow requests numpy opencv-python -q

if %errorlevel% neq 0 (
    echo.
    echo [警告] 部分依赖安装失败，尝试继续...
)

echo       依赖安装完成！

REM ========== 步骤3: 创建桌面快捷方式 ==========
echo.
echo [3/4] 创建桌面快捷方式...

set "SHORTCUT_PATH=%USERPROFILE%\Desktop\电商详情页管理系统.lnk"
set "TARGET_PATH=%INSTALL_DIR%启动程序.bat"

REM 创建启动脚本
echo @echo off > "%INSTALL_DIR%启动程序.bat"
echo cd /d "%INSTALL_DIR%" >> "%INSTALL_DIR%启动程序.bat"
echo %PYTHON_CMD% main.py >> "%INSTALL_DIR%启动程序.bat"

REM 使用 PowerShell 创建快捷方式
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%TARGET_PATH%'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Description = '电商详情页管理系统'; $s.Save()"

if exist "%SHORTCUT_PATH%" (
    echo       桌面快捷方式创建成功！
) else (
    echo       快捷方式创建失败，您可以手动运行 启动程序.bat
)

REM ========== 步骤4: 启动程序 ==========
echo.
echo [4/4] 启动程序...
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                     安装完成！                               ║
echo ║                                                              ║
echo ║  程序即将启动，首次启动可能需要几秒钟...                      ║
echo ║                                                              ║
echo ║  以后可以通过桌面快捷方式启动程序                             ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

timeout /t 3 /nobreak >nul

%PYTHON_CMD% main.py

if %errorlevel% neq 0 (
    echo.
    echo [提示] 如果程序未能正常启动，请尝试：
    echo        1. 重启电脑后再次运行
    echo        2. 右键以管理员身份运行
    pause
)
