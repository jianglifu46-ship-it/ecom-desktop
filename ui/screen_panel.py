"""
分屏管理面板 - 管理详情页分屏结构
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMenu, QSpinBox, QDialog, QDialogButtonBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QAction

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from config import UIConfig
from core.canvas import Screen


class ScreenItem(QFrame):
    """分屏项"""
    
    clicked = pyqtSignal(str)
    insert_above = pyqtSignal(str)
    insert_below = pyqtSignal(str)
    insert_blank_above = pyqtSignal(str)
    insert_blank_below = pyqtSignal(str)
    delete_screen = pyqtSignal(str)
    duplicate_screen = pyqtSignal(str)
    resize_screen = pyqtSignal(str, int)
    rename_screen = pyqtSignal(str, str)
    
    def __init__(self, screen: Screen, parent=None):
        super().__init__(parent)
        self.screen = screen
        self.is_selected = False
        self._setup_ui()
        self._apply_style()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 6, 8, 6)
        
        # 名称
        self.name_label = QLabel(self.screen.name)
        self.name_label.setMinimumWidth(100)
        layout.addWidget(self.name_label, 1)
        
        # 高度
        self.height_label = QLabel(f"{self.screen.height}px")
        self.height_label.setObjectName("height")
        layout.addWidget(self.height_label)
    
    def _apply_style(self):
        """应用样式"""
        theme = UIConfig.THEME
        
        if self.screen.is_blank:
            bg_color = theme['bg_primary']
            text_color = theme['text_secondary']
        elif self.is_selected:
            bg_color = theme['accent']
            text_color = theme['text_primary']
        else:
            bg_color = theme['bg_tertiary']
            text_color = theme['text_primary']
        
        self.setStyleSheet(f"""
            ScreenItem {{
                background-color: {bg_color};
                border-radius: 5px;
            }}
            ScreenItem:hover {{
                border: 1px solid {theme['accent']};
            }}
            QLabel {{
                color: {text_color};
                font-size: 11px;
            }}
            QLabel#height {{
                color: {theme['text_secondary']};
            }}
        """)
    
    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        self._apply_style()
    
    def mousePressEvent(self, event):
        """鼠标点击"""
        self.clicked.emit(self.screen.id)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """双击重命名"""
        self._show_rename_dialog()
        super().mouseDoubleClickEvent(event)
    
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)
        theme = UIConfig.THEME
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {theme['bg_secondary']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border']};
            }}
            QMenu::item:selected {{
                background-color: {theme['accent']};
            }}
        """)
        
        # 上方插入新屏
        insert_above_action = QAction("上方插入新屏", menu)
        insert_above_action.triggered.connect(lambda: self.insert_above.emit(self.screen.id))
        menu.addAction(insert_above_action)
        
        # 下方插入新屏
        insert_below_action = QAction("下方插入新屏", menu)
        insert_below_action.triggered.connect(lambda: self.insert_below.emit(self.screen.id))
        menu.addAction(insert_below_action)
        
        menu.addSeparator()
        
        # 上方添加留白
        blank_above_action = QAction("上方添加留白", menu)
        blank_above_action.triggered.connect(lambda: self.insert_blank_above.emit(self.screen.id))
        menu.addAction(blank_above_action)
        
        # 下方添加留白
        blank_below_action = QAction("下方添加留白", menu)
        blank_below_action.triggered.connect(lambda: self.insert_blank_below.emit(self.screen.id))
        menu.addAction(blank_below_action)
        
        menu.addSeparator()
        
        # 调整高度
        resize_action = QAction("调整高度...", menu)
        resize_action.triggered.connect(self._show_resize_dialog)
        menu.addAction(resize_action)
        
        # 重命名
        rename_action = QAction("重命名...", menu)
        rename_action.triggered.connect(self._show_rename_dialog)
        menu.addAction(rename_action)
        
        # 复制
        dup_action = QAction("复制此屏", menu)
        dup_action.triggered.connect(lambda: self.duplicate_screen.emit(self.screen.id))
        menu.addAction(dup_action)
        
        menu.addSeparator()
        
        # 删除
        del_action = QAction("删除此屏", menu)
        del_action.triggered.connect(lambda: self.delete_screen.emit(self.screen.id))
        menu.addAction(del_action)
        
        menu.exec(self.mapToGlobal(pos))
    
    def _show_resize_dialog(self):
        """显示调整高度对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("调整高度")
        dialog.setFixedSize(250, 100)
        
        layout = QVBoxLayout(dialog)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("高度:"))
        spin = QSpinBox()
        spin.setRange(50, 2000)
        spin.setValue(self.screen.height)
        spin.setSuffix(" px")
        h_layout.addWidget(spin)
        layout.addLayout(h_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.resize_screen.emit(self.screen.id, spin.value())
    
    def _show_rename_dialog(self):
        """显示重命名对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("重命名")
        dialog.setFixedSize(300, 100)
        
        layout = QVBoxLayout(dialog)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("名称:"))
        name_input = QLineEdit(self.screen.name)
        h_layout.addWidget(name_input)
        layout.addLayout(h_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = name_input.text().strip()
            if new_name:
                self.rename_screen.emit(self.screen.id, new_name)


class ScreenPanel(QWidget):
    """分屏管理面板"""
    
    screen_selected = pyqtSignal(str)
    screen_added = pyqtSignal(int, bool)  # index, is_blank
    screen_deleted = pyqtSignal(str)
    screen_duplicated = pyqtSignal(str)
    screen_resized = pyqtSignal(str, int)
    screen_renamed = pyqtSignal(str, str)
    insert_screen = pyqtSignal(str, bool, bool)  # screen_id, above, is_blank
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.screens = []
        self.selected_screen_id = None
        self._screen_items = {}
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题栏
        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 8, 10, 8)
        
        title = QLabel("分屏管理")
        title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # 分屏列表
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(4)
        self.list_layout.setContentsMargins(8, 5, 8, 5)
        self.list_layout.addStretch()
        
        layout.addWidget(self.list_widget, 1)
        
        # 添加按钮
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(8, 5, 8, 8)
        
        add_screen_btn = QPushButton("+ 添加分屏")
        add_screen_btn.setObjectName("addBtn")
        add_screen_btn.clicked.connect(lambda: self.screen_added.emit(-1, False))
        btn_layout.addWidget(add_screen_btn)
        
        add_blank_btn = QPushButton("+ 留白")
        add_blank_btn.setObjectName("addBlankBtn")
        add_blank_btn.clicked.connect(lambda: self.screen_added.emit(-1, True))
        btn_layout.addWidget(add_blank_btn)
        
        layout.addWidget(btn_frame)
    
    def _apply_style(self):
        """应用样式"""
        theme = UIConfig.THEME
        self.setStyleSheet(f"""
            ScreenPanel {{
                background-color: {theme['bg_secondary']};
            }}
            QFrame#header {{
                background-color: {theme['accent']};
            }}
            QLabel {{
                color: {theme['text_primary']};
            }}
            QPushButton#addBtn {{
                background-color: transparent;
                color: {theme['accent']};
                border: 1px solid {theme['accent']};
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton#addBtn:hover {{
                background-color: {theme['accent']};
                color: white;
            }}
            QPushButton#addBlankBtn {{
                background-color: transparent;
                color: {theme['text_secondary']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton#addBlankBtn:hover {{
                border-color: {theme['accent']};
                color: {theme['accent']};
            }}
        """)
    
    def set_screens(self, screens: list):
        """设置分屏列表"""
        self.screens = screens
        self._refresh_list()
    
    def _refresh_list(self):
        """刷新列表"""
        # 清空现有项
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._screen_items.clear()
        
        # 添加分屏项
        for screen in self.screens:
            item = ScreenItem(screen)
            item.clicked.connect(self._on_screen_clicked)
            item.insert_above.connect(lambda sid: self.insert_screen.emit(sid, True, False))
            item.insert_below.connect(lambda sid: self.insert_screen.emit(sid, False, False))
            item.insert_blank_above.connect(lambda sid: self.insert_screen.emit(sid, True, True))
            item.insert_blank_below.connect(lambda sid: self.insert_screen.emit(sid, False, True))
            item.delete_screen.connect(self.screen_deleted.emit)
            item.duplicate_screen.connect(self.screen_duplicated.emit)
            item.resize_screen.connect(self.screen_resized.emit)
            item.rename_screen.connect(self.screen_renamed.emit)
            
            if screen.id == self.selected_screen_id:
                item.set_selected(True)
            
            self._screen_items[screen.id] = item
            self.list_layout.insertWidget(self.list_layout.count() - 1, item)
    
    def select_screen(self, screen_id: str):
        """选择分屏"""
        self.selected_screen_id = screen_id
        
        for sid, item in self._screen_items.items():
            item.set_selected(sid == screen_id)
    
    def _on_screen_clicked(self, screen_id: str):
        """分屏被点击"""
        self.select_screen(screen_id)
        self.screen_selected.emit(screen_id)
