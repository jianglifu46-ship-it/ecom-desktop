#!/usr/bin/env python3
"""
电商详情页管理系统 - 桌面客户端
主入口文件
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config import APP_NAME, UIConfig
from services.api_client import api_client
from ui.main_window import MainWindow


def setup_app_style(app: QApplication):
    """设置应用程序样式"""
    # 设置默认字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # 设置全局样式
    theme = UIConfig.THEME
    app.setStyleSheet(f"""
        QWidget {{
            font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
        }}
        QToolTip {{
            background-color: {theme['bg_secondary']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            padding: 5px;
        }}
        QScrollBar:vertical {{
            background-color: {theme['bg_secondary']};
            width: 10px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background-color: {theme['bg_tertiary']};
            border-radius: 5px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {theme['accent']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar:horizontal {{
            background-color: {theme['bg_secondary']};
            height: 10px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {theme['bg_tertiary']};
            border-radius: 5px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {theme['accent']};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
    """)


def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出，最小化到托盘
    
    # 设置样式
    setup_app_style(app)
    
    # 创建主窗口
    window = MainWindow()
    
    # 检查登录状态
    if not api_client.is_logged_in:
        window.show_login()
    
    # 显示主窗口
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
