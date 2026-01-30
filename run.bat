@echo off
REM 电商详情页管理系统 - 运行脚本
REM 使用方法: 双击运行

REM 激活虚拟环境（如果存在）
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM 运行程序
python main.py

pause
