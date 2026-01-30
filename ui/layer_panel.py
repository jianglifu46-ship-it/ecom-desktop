"""
图层面板 - 显示和管理图层
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QAction

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from config import UIConfig
from core.layer import Layer


class LayerItem(QFrame):
    """图层项"""
    
    clicked = pyqtSignal(str)  # 点击信号，传递图层 ID
    visibility_changed = pyqtSignal(str, bool)  # 可见性变化
    
    def __init__(self, layer: Layer, parent=None):
        super().__init__(parent)
        self.layer = layer
        self.is_selected = False
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 6, 8, 6)
        
        # 可见性按钮
        self.visibility_btn = QPushButton("👁")
        self.visibility_btn.setFixedSize(24, 24)
        self.visibility_btn.setCheckable(True)
        self.visibility_btn.setChecked(self.layer.visible)
        self.visibility_btn.clicked.connect(self._on_visibility_toggle)
        layout.addWidget(self.visibility_btn)
        
        # 图层类型图标
        type_icons = {
            "image": "🖼",
            "text": "T",
            "shape": "◼",
            "base": "□"
        }
        type_label = QLabel(type_icons.get(self.layer.layer_type, "□"))
        type_label.setFixedWidth(20)
        layout.addWidget(type_label)
        
        # 图层名称
        self.name_label = QLabel(self.layer.name)
        self.name_label.setMinimumWidth(100)
        layout.addWidget(self.name_label, 1)
        
        # 锁定状态
        if self.layer.locked:
            lock_label = QLabel("🔒")
            layout.addWidget(lock_label)
    
    def _apply_style(self):
        """应用样式"""
        theme = UIConfig.THEME
        bg_color = theme['accent'] if self.is_selected else theme['bg_tertiary']
        
        self.setStyleSheet(f"""
            LayerItem {{
                background-color: {bg_color};
                border-radius: 5px;
            }}
            LayerItem:hover {{
                background-color: {theme['accent'] if self.is_selected else theme['bg_tertiary']};
                border: 1px solid {theme['accent']};
            }}
            QLabel {{
                color: {theme['text_primary']};
                font-size: 12px;
            }}
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {theme['text_primary']};
            }}
        """)
    
    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        self._apply_style()
    
    def _on_visibility_toggle(self):
        """切换可见性"""
        visible = self.visibility_btn.isChecked()
        self.visibility_changed.emit(self.layer.id, visible)
    
    def mousePressEvent(self, event):
        """鼠标点击"""
        self.clicked.emit(self.layer.id)
        super().mousePressEvent(event)


class LayerPanel(QWidget):
    """图层面板"""
    
    layer_selected = pyqtSignal(str)
    layer_visibility_changed = pyqtSignal(str, bool)
    layer_order_changed = pyqtSignal(str, int)  # layer_id, new_index
    layer_deleted = pyqtSignal(str)
    layer_duplicated = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layers = []
        self.selected_layer_id = None
        self._layer_items = {}
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题栏
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 8, 10, 8)
        
        title = QLabel("图层")
        title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # 图层列表区域
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(4)
        self.list_layout.setContentsMargins(8, 5, 8, 5)
        self.list_layout.addStretch()
        
        layout.addWidget(self.list_widget, 1)
        
        # 操作按钮
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(8, 5, 8, 8)
        btn_layout.setSpacing(5)
        
        self.up_btn = QPushButton("↑")
        self.up_btn.setToolTip("上移图层")
        self.up_btn.setFixedSize(30, 26)
        self.up_btn.clicked.connect(self._on_move_up)
        btn_layout.addWidget(self.up_btn)
        
        self.down_btn = QPushButton("↓")
        self.down_btn.setToolTip("下移图层")
        self.down_btn.setFixedSize(30, 26)
        self.down_btn.clicked.connect(self._on_move_down)
        btn_layout.addWidget(self.down_btn)
        
        btn_layout.addStretch()
        
        self.dup_btn = QPushButton("📋")
        self.dup_btn.setToolTip("复制图层")
        self.dup_btn.setFixedSize(30, 26)
        self.dup_btn.clicked.connect(self._on_duplicate)
        btn_layout.addWidget(self.dup_btn)
        
        self.del_btn = QPushButton("🗑")
        self.del_btn.setToolTip("删除图层")
        self.del_btn.setFixedSize(30, 26)
        self.del_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(self.del_btn)
        
        layout.addWidget(btn_frame)
    
    def _apply_style(self):
        """应用样式"""
        theme = UIConfig.THEME
        self.setStyleSheet(f"""
            LayerPanel {{
                background-color: {theme['bg_secondary']};
            }}
            QLabel {{
                color: {theme['text_primary']};
            }}
            QPushButton {{
                background-color: {theme['bg_tertiary']};
                color: {theme['text_primary']};
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {theme['accent']};
            }}
        """)
    
    def set_layers(self, layers: list):
        """设置图层列表"""
        self.layers = layers
        self._refresh_list()
    
    def _refresh_list(self):
        """刷新列表"""
        # 清空现有项
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._layer_items.clear()
        
        # 从上到下添加图层（倒序，因为上面的图层在列表顶部）
        for layer in reversed(self.layers):
            item = LayerItem(layer)
            item.clicked.connect(self._on_layer_clicked)
            item.visibility_changed.connect(self._on_visibility_changed)
            
            if layer.id == self.selected_layer_id:
                item.set_selected(True)
            
            self._layer_items[layer.id] = item
            self.list_layout.insertWidget(self.list_layout.count() - 1, item)
    
    def select_layer(self, layer_id: str):
        """选择图层"""
        self.selected_layer_id = layer_id
        
        for lid, item in self._layer_items.items():
            item.set_selected(lid == layer_id)
    
    def _on_layer_clicked(self, layer_id: str):
        """图层被点击"""
        self.select_layer(layer_id)
        self.layer_selected.emit(layer_id)
    
    def _on_visibility_changed(self, layer_id: str, visible: bool):
        """可见性变化"""
        self.layer_visibility_changed.emit(layer_id, visible)
    
    def _on_move_up(self):
        """上移图层"""
        if self.selected_layer_id:
            # 找到当前索引
            for i, layer in enumerate(self.layers):
                if layer.id == self.selected_layer_id:
                    if i < len(self.layers) - 1:
                        self.layer_order_changed.emit(self.selected_layer_id, i + 1)
                    break
    
    def _on_move_down(self):
        """下移图层"""
        if self.selected_layer_id:
            for i, layer in enumerate(self.layers):
                if layer.id == self.selected_layer_id:
                    if i > 0:
                        self.layer_order_changed.emit(self.selected_layer_id, i - 1)
                    break
    
    def _on_duplicate(self):
        """复制图层"""
        if self.selected_layer_id:
            self.layer_duplicated.emit(self.selected_layer_id)
    
    def _on_delete(self):
        """删除图层"""
        if self.selected_layer_id:
            self.layer_deleted.emit(self.selected_layer_id)
