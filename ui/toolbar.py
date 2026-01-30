"""
工具栏组件
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QFrame, QLabel, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from config import UIConfig


class ToolButton(QPushButton):
    """工具按钮"""
    
    def __init__(self, text: str, icon: str = "", checkable: bool = False, parent=None):
        super().__init__(parent)
        self.setText(f"{icon} {text}" if icon else text)
        self.setCheckable(checkable)
        self._apply_style()
    
    def _apply_style(self):
        theme = UIConfig.THEME
        self.setStyleSheet(f"""
            ToolButton {{
                background-color: {theme['bg_secondary']};
                color: {theme['text_primary']};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            ToolButton:hover {{
                background-color: {theme['accent']};
            }}
            ToolButton:checked {{
                background-color: {theme['accent']};
            }}
            ToolButton:pressed {{
                background-color: {theme['accent_hover']};
            }}
        """)


class ToolSeparator(QFrame):
    """工具栏分隔线"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.VLine)
        self.setFixedWidth(2)
        theme = UIConfig.THEME
        self.setStyleSheet(f"background-color: {theme['border']};")


class Toolbar(QWidget):
    """工具栏"""
    
    # 工具选择信号
    tool_selected = pyqtSignal(str)
    
    # 操作信号
    undo_clicked = pyqtSignal()
    redo_clicked = pyqtSignal()
    add_screen_clicked = pyqtSignal()
    add_blank_clicked = pyqtSignal()
    remove_bg_clicked = pyqtSignal()
    upscale_clicked = pyqtSignal()
    enhance_clicked = pyqtSignal()
    ai_generate_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tool_buttons = {}
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QHBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 选择工具组
        self._add_tool_button(layout, "select", "选择", "🔲", True)
        self._add_tool_button(layout, "move", "移动", "✥", True)
        self._add_tool_button(layout, "text", "文字", "T", True)
        self._add_tool_button(layout, "rectangle", "矩形", "▢", True)
        
        layout.addWidget(ToolSeparator())
        
        # 图像处理工具
        rembg_btn = ToolButton("抠图", "✂️")
        rembg_btn.clicked.connect(self.remove_bg_clicked.emit)
        layout.addWidget(rembg_btn)
        
        upscale_btn = ToolButton("放大", "🔍")
        upscale_btn.clicked.connect(self.upscale_clicked.emit)
        layout.addWidget(upscale_btn)
        
        enhance_btn = ToolButton("增强", "✨")
        enhance_btn.clicked.connect(self.enhance_clicked.emit)
        layout.addWidget(enhance_btn)
        
        layout.addWidget(ToolSeparator())
        
        # 撤销/重做
        undo_btn = ToolButton("撤销", "↩")
        undo_btn.clicked.connect(self.undo_clicked.emit)
        layout.addWidget(undo_btn)
        
        redo_btn = ToolButton("重做", "↪")
        redo_btn.clicked.connect(self.redo_clicked.emit)
        layout.addWidget(redo_btn)
        
        layout.addWidget(ToolSeparator())
        
        # 分屏操作
        add_screen_btn = ToolButton("添加屏", "➕")
        add_screen_btn.setStyleSheet(add_screen_btn.styleSheet() + f"""
            ToolButton {{
                border: 1px solid {UIConfig.THEME['accent']};
                color: {UIConfig.THEME['accent']};
                background-color: transparent;
            }}
            ToolButton:hover {{
                background-color: {UIConfig.THEME['accent']};
                color: white;
            }}
        """)
        add_screen_btn.clicked.connect(self.add_screen_clicked.emit)
        layout.addWidget(add_screen_btn)
        
        add_blank_btn = ToolButton("插入留白", "⬜")
        add_blank_btn.clicked.connect(self.add_blank_clicked.emit)
        layout.addWidget(add_blank_btn)
        
        layout.addWidget(ToolSeparator())
        
        # AI 生成
        ai_btn = ToolButton("AI生成", "🤖")
        ai_btn.setStyleSheet(f"""
            ToolButton {{
                background-color: {UIConfig.THEME['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: bold;
            }}
            ToolButton:hover {{
                background-color: {UIConfig.THEME['accent_hover']};
            }}
        """)
        ai_btn.clicked.connect(self.ai_generate_clicked.emit)
        layout.addWidget(ai_btn)
        
        layout.addStretch()
        
        # 缩放控制
        zoom_label = QLabel("缩放:")
        zoom_label.setStyleSheet(f"color: {UIConfig.THEME['text_secondary']};")
        layout.addWidget(zoom_label)
        
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["25%", "50%", "75%", "100%", "150%", "200%"])
        self.zoom_combo.setCurrentText("50%")
        self.zoom_combo.setFixedWidth(80)
        layout.addWidget(self.zoom_combo)
    
    def _add_tool_button(self, layout, tool_id: str, text: str, icon: str, checkable: bool):
        """添加工具按钮"""
        btn = ToolButton(text, icon, checkable)
        btn.clicked.connect(lambda: self._on_tool_clicked(tool_id))
        self._tool_buttons[tool_id] = btn
        layout.addWidget(btn)
        
        if tool_id == "select":
            btn.setChecked(True)
    
    def _on_tool_clicked(self, tool_id: str):
        """工具被点击"""
        # 取消其他工具的选中状态
        for tid, btn in self._tool_buttons.items():
            btn.setChecked(tid == tool_id)
        
        self.tool_selected.emit(tool_id)
    
    def _apply_style(self):
        """应用样式"""
        theme = UIConfig.THEME
        self.setStyleSheet(f"""
            Toolbar {{
                background-color: {theme['bg_tertiary']};
            }}
            QComboBox {{
                background-color: {theme['bg_secondary']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme['bg_secondary']};
                color: {theme['text_primary']};
                selection-background-color: {theme['accent']};
            }}
        """)
    
    def get_current_tool(self) -> str:
        """获取当前工具"""
        for tid, btn in self._tool_buttons.items():
            if btn.isChecked():
                return tid
        return "select"
    
    def set_zoom(self, scale: float):
        """设置缩放显示"""
        percent = int(scale * 100)
        self.zoom_combo.setCurrentText(f"{percent}%")
