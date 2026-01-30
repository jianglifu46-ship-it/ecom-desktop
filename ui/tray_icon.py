"""
系统托盘图标
"""
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor
from PyQt6.QtCore import pyqtSignal, QObject

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from config import APP_NAME


class TrayIcon(QSystemTrayIcon):
    """系统托盘图标"""
    
    show_window_signal = pyqtSignal()
    quit_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_icon()
        self._setup_menu()
        self._setup_signals()
    
    def _setup_icon(self):
        """设置图标"""
        # 创建一个简单的图标
        icon = self._create_default_icon()
        self.setIcon(icon)
        self.setToolTip(APP_NAME)
    
    def _create_default_icon(self) -> QIcon:
        """创建默认图标"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 122, 204))  # 蓝色背景
        
        painter = QPainter(pixmap)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(painter.font())
        font = painter.font()
        font.setPointSize(24)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), 0x0084, "E")  # AlignCenter
        painter.end()
        
        return QIcon(pixmap)
    
    def _setup_menu(self):
        """设置右键菜单"""
        menu = QMenu()
        
        # 显示主窗口
        show_action = QAction("显示主窗口", menu)
        show_action.triggered.connect(self.show_window_signal.emit)
        menu.addAction(show_action)
        
        menu.addSeparator()
        
        # 退出
        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self.quit_signal.emit)
        menu.addAction(quit_action)
        
        self.setContextMenu(menu)
    
    def _setup_signals(self):
        """设置信号"""
        self.activated.connect(self._on_activated)
    
    def _on_activated(self, reason):
        """托盘图标被激活"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_signal.emit()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window_signal.emit()
    
    def show_message(self, title: str, message: str, 
                     icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
                     duration: int = 3000):
        """显示托盘通知"""
        self.showMessage(title, message, icon, duration)
    
    def show_new_task_notification(self, task_title: str):
        """显示新任务通知"""
        self.show_message(
            "新任务",
            f"您有新的任务: {task_title}",
            QSystemTrayIcon.MessageIcon.Information
        )
    
    def show_urgent_notification(self, message: str):
        """显示紧急通知"""
        self.show_message(
            "紧急提醒",
            message,
            QSystemTrayIcon.MessageIcon.Warning
        )
