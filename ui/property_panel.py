"""
属性面板 - 显示和编辑选中图层的属性
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QFrame, QColorDialog, QPushButton,
    QComboBox, QGroupBox, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from config import UIConfig
from core.layer import Layer, TextLayer, ShapeLayer, ImageLayer


class PropertyPanel(QWidget):
    """属性面板"""
    
    property_changed = pyqtSignal(str, str, object)  # layer_id, property_name, value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_layer: Layer = None
        self._updating = False
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title = QLabel("属性")
        title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 基础属性组
        basic_group = QGroupBox("位置和大小")
        basic_layout = QVBoxLayout(basic_group)
        
        # X, Y
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("X:"))
        self.x_spin = QSpinBox()
        self.x_spin.setRange(-9999, 9999)
        self.x_spin.valueChanged.connect(lambda v: self._on_property_change('x', v))
        pos_layout.addWidget(self.x_spin)
        
        pos_layout.addWidget(QLabel("Y:"))
        self.y_spin = QSpinBox()
        self.y_spin.setRange(-9999, 9999)
        self.y_spin.valueChanged.connect(lambda v: self._on_property_change('y', v))
        pos_layout.addWidget(self.y_spin)
        basic_layout.addLayout(pos_layout)
        
        # 宽, 高
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("宽:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 9999)
        self.width_spin.valueChanged.connect(lambda v: self._on_property_change('width', v))
        size_layout.addWidget(self.width_spin)
        
        size_layout.addWidget(QLabel("高:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 9999)
        self.height_spin.valueChanged.connect(lambda v: self._on_property_change('height', v))
        size_layout.addWidget(self.height_spin)
        basic_layout.addLayout(size_layout)
        
        layout.addWidget(basic_group)
        
        # 变换属性组
        transform_group = QGroupBox("变换")
        transform_layout = QVBoxLayout(transform_group)
        
        # 透明度
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("透明度:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(lambda v: self._on_property_change('opacity', v / 100))
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_label = QLabel("100%")
        self.opacity_label.setFixedWidth(40)
        opacity_layout.addWidget(self.opacity_label)
        transform_layout.addLayout(opacity_layout)
        
        # 旋转
        rotation_layout = QHBoxLayout()
        rotation_layout.addWidget(QLabel("旋转:"))
        self.rotation_spin = QDoubleSpinBox()
        self.rotation_spin.setRange(-360, 360)
        self.rotation_spin.setSuffix("°")
        self.rotation_spin.valueChanged.connect(lambda v: self._on_property_change('rotation', v))
        rotation_layout.addWidget(self.rotation_spin)
        transform_layout.addLayout(rotation_layout)
        
        layout.addWidget(transform_group)
        
        # 文字属性组（仅文字图层显示）
        self.text_group = QGroupBox("文字属性")
        text_layout = QVBoxLayout(self.text_group)
        
        # 字体大小
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("字号:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 200)
        self.font_size_spin.valueChanged.connect(lambda v: self._on_property_change('font_size', v))
        font_size_layout.addWidget(self.font_size_spin)
        text_layout.addLayout(font_size_layout)
        
        # 字体颜色
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("颜色:"))
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(60, 25)
        self.color_btn.clicked.connect(self._on_color_pick)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        text_layout.addLayout(color_layout)
        
        self.text_group.hide()
        layout.addWidget(self.text_group)
        
        # 形状属性组（仅形状图层显示）
        self.shape_group = QGroupBox("形状属性")
        shape_layout = QVBoxLayout(self.shape_group)
        
        # 填充颜色
        fill_layout = QHBoxLayout()
        fill_layout.addWidget(QLabel("填充:"))
        self.fill_btn = QPushButton()
        self.fill_btn.setFixedSize(60, 25)
        self.fill_btn.clicked.connect(self._on_fill_color_pick)
        fill_layout.addWidget(self.fill_btn)
        fill_layout.addStretch()
        shape_layout.addLayout(fill_layout)
        
        # 边框颜色
        stroke_layout = QHBoxLayout()
        stroke_layout.addWidget(QLabel("边框:"))
        self.stroke_btn = QPushButton()
        self.stroke_btn.setFixedSize(60, 25)
        self.stroke_btn.clicked.connect(self._on_stroke_color_pick)
        stroke_layout.addWidget(self.stroke_btn)
        
        self.stroke_width_spin = QSpinBox()
        self.stroke_width_spin.setRange(0, 20)
        self.stroke_width_spin.valueChanged.connect(lambda v: self._on_property_change('stroke_width', v))
        stroke_layout.addWidget(self.stroke_width_spin)
        stroke_layout.addStretch()
        shape_layout.addLayout(stroke_layout)
        
        self.shape_group.hide()
        layout.addWidget(self.shape_group)
        
        layout.addStretch()
    
    def _apply_style(self):
        """应用样式"""
        theme = UIConfig.THEME
        self.setStyleSheet(f"""
            PropertyPanel {{
                background-color: {theme['bg_secondary']};
            }}
            QLabel {{
                color: {theme['text_primary']};
                font-size: 12px;
            }}
            QGroupBox {{
                color: {theme['text_primary']};
                border: 1px solid {theme['border']};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QSpinBox, QDoubleSpinBox {{
                background-color: {theme['bg_tertiary']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border']};
                border-radius: 3px;
                padding: 3px;
            }}
            QSlider::groove:horizontal {{
                background: {theme['bg_tertiary']};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {theme['accent']};
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }}
            QPushButton {{
                border: 1px solid {theme['border']};
                border-radius: 3px;
            }}
        """)
    
    def set_layer(self, layer: Layer):
        """设置当前图层"""
        self._updating = True
        self.current_layer = layer
        
        if layer is None:
            self._updating = False
            return
        
        # 更新基础属性
        self.x_spin.setValue(layer.x)
        self.y_spin.setValue(layer.y)
        self.width_spin.setValue(layer.width)
        self.height_spin.setValue(layer.height)
        self.opacity_slider.setValue(int(layer.opacity * 100))
        self.opacity_label.setText(f"{int(layer.opacity * 100)}%")
        self.rotation_spin.setValue(layer.rotation)
        
        # 根据图层类型显示/隐藏属性组
        self.text_group.hide()
        self.shape_group.hide()
        
        if isinstance(layer, TextLayer):
            self.text_group.show()
            self.font_size_spin.setValue(layer.font_size)
            self._set_color_button(self.color_btn, layer.font_color)
        
        elif isinstance(layer, ShapeLayer):
            self.shape_group.show()
            self._set_color_button(self.fill_btn, layer.fill_color)
            self._set_color_button(self.stroke_btn, layer.stroke_color)
            self.stroke_width_spin.setValue(layer.stroke_width)
        
        self._updating = False
    
    def _set_color_button(self, btn: QPushButton, color: str):
        """设置颜色按钮"""
        btn.setStyleSheet(f"background-color: {color}; border: 1px solid #555;")
        btn.setProperty("color", color)
    
    def _on_property_change(self, prop: str, value):
        """属性变化"""
        if self._updating or self.current_layer is None:
            return
        
        if prop == 'opacity':
            self.opacity_label.setText(f"{int(value * 100)}%")
        
        self.property_changed.emit(self.current_layer.id, prop, value)
    
    def _on_color_pick(self):
        """选择文字颜色"""
        if self.current_layer is None:
            return
        
        current_color = self.color_btn.property("color") or "#000000"
        color = QColorDialog.getColor(QColor(current_color), self, "选择颜色")
        if color.isValid():
            hex_color = color.name()
            self._set_color_button(self.color_btn, hex_color)
            self.property_changed.emit(self.current_layer.id, 'font_color', hex_color)
    
    def _on_fill_color_pick(self):
        """选择填充颜色"""
        if self.current_layer is None:
            return
        
        current_color = self.fill_btn.property("color") or "#cccccc"
        color = QColorDialog.getColor(QColor(current_color), self, "选择填充颜色")
        if color.isValid():
            hex_color = color.name()
            self._set_color_button(self.fill_btn, hex_color)
            self.property_changed.emit(self.current_layer.id, 'fill_color', hex_color)
    
    def _on_stroke_color_pick(self):
        """选择边框颜色"""
        if self.current_layer is None:
            return
        
        current_color = self.stroke_btn.property("color") or "#000000"
        color = QColorDialog.getColor(QColor(current_color), self, "选择边框颜色")
        if color.isValid():
            hex_color = color.name()
            self._set_color_button(self.stroke_btn, hex_color)
            self.property_changed.emit(self.current_layer.id, 'stroke_color', hex_color)
