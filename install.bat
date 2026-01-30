@echo off
REM 电商详情页管理系统 - 安装依赖脚本
REM 使用方法: 双击运行

echo ========================================
echo 电商详情页管理系统 - 安装依赖
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [信息] Python 已安装
python --version
echo.

REM 创建虚拟环境
if not exist "venv" (
    echo [信息] 创建虚拟环境...
    python -m venv venv
    echo [成功] 虚拟环境创建完成
) else (
    echo [信息] 虚拟环境已存在
)
echo.

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 升级 pip
echo [信息] 升级 pip...
python -m pip install --upgrade pip -q

REM 安装基础依赖
echo [信息] 安装基础依赖...
pip install -r requirements.txt

echo.
echo ========================================
echo [成功] 基础依赖安装完成！
echo ========================================
echo.

REM 询问是否安装可选依赖
set /p install_rembg="是否安装智能抠图功能 (rembg, 约170MB)? [y/N]: "
if /i "%install_rembg%"=="y" (
    echo [信息] 安装 rembg...
    pip install rembg
    echo [成功] rembg 安装完成
)
echo.

echo ========================================
echo 安装完成！
echo.
echo 运行程序: python main.py
echo 打包程序: build.bat
echo ========================================
pause
