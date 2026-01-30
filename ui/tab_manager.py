"""
标签页管理器
"""
from PyQt6.QtWidgets import QTabWidget, QWidget
from PyQt6.QtCore import pyqtSignal
from typing import Any
import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])


class TabManager(QTabWidget):
    """标签页管理器"""
    
    # 定义信号
    tab_changed: pyqtSignal = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.setTabsClosable(False)  # 不允许关闭标签页
        self.setMovable(False)  # 不允许拖动标签页
        
        # 设置标签页样式
        self._setup_style()
        
        # 连接信号
        self.currentChanged.connect(self._on_tab_changed)
    
    def _setup_style(self):
        """设置样式"""
        theme = {"bg_primary": "#2b2b2b", "bg_secondary": "#3c3c3c", "text_primary": "#ffffff", 
                "accent": "#007acc", "border": "#555555"}
        
        self.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {theme['border']};
                background-color: {theme['bg_primary']};
            }}
            
            QTabBar::tab {{
                background-color: {theme['bg_secondary']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border']};
                border-bottom: none;
                padding: 8px 16px;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {theme['accent']};
                border-bottom: 1px solid {theme['accent']};
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {theme['bg_secondary']};
                border-bottom: 1px solid {theme['accent']};
            }}
        """)
    
    def _on_tab_changed(self, index: int) -> None:
        """标签页变化"""
        self.tab_changed.emit(index)
    
    def add_editor_tab(self, widget: Any, title: str = "编辑器") -> None:
        """添加编辑器标签页"""
        _ = self.addTab(widget, title)
    
    def add_middleware_tab(self, widget: Any, title: str = "中台") -> None:
        """添加中台标签页"""
        _ = self.addTab(widget, title)
    
    def set_current_editor(self) -> None:
        """切换到编辑器标签页"""
        self.setCurrentIndex(0)
    
    def set_current_middleware(self) -> None:
        """切换到中台标签页"""
        self.setCurrentIndex(1)