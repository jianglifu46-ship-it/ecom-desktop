@echo off
REM 电商详情页管理系统 - Windows 打包脚本
REM 使用方法: 双击运行或在命令行执行 build.bat

echo ========================================
echo 电商详情页管理系统 - 打包工具
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo [信息] 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
echo [信息] 安装依赖...
pip install -r requirements.txt -q

REM 检查 PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [信息] 安装 PyInstaller...
    pip install pyinstaller -q
)

REM 清理旧的构建文件
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM 打包
echo [信息] 开始打包...
echo.
pyinstaller ecom_desktop.spec

if errorlevel 1 (
    echo.
    echo [错误] 打包失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo ========================================
echo [成功] 打包完成！
echo 输出文件: dist\电商详情页管理系统.exe
echo ========================================
echo.

REM 打开输出目录
explorer dist

pause
