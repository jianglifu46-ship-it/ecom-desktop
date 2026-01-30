"""
素材面板 - 本地素材库管理
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea, QFileDialog, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QMimeData, QUrl
from PyQt6.QtGui import QFont, QPixmap, QDrag, QImage

import os
from pathlib import Path

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from config import UIConfig, save_asset_folders, load_asset_folders
from services.file_watcher import asset_manager, SUPPORTED_FORMATS


class AssetThumbnail(QLabel):
    """素材缩略图"""
    
    double_clicked = pyqtSignal(str)  # 双击信号，传递文件路径
    
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._setup_ui()
    
    def _setup_ui(self):
        """设置 UI"""
        self.setFixedSize(60, 60)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip(os.path.basename(self.file_path))
        
        # 加载缩略图
        self._load_thumbnail()
        
        # 样式
        theme = UIConfig.THEME
        self.setStyleSheet(f"""
            AssetThumbnail {{
                background-color: {theme['bg_tertiary']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
            }}
            AssetThumbnail:hover {{
                border: 1px solid {theme['accent']};
            }}
        """)
    
    def _load_thumbnail(self):
        """加载缩略图"""
        try:
            pixmap = QPixmap(self.file_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    56, 56,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.setPixmap(scaled)
            else:
                self.setText("IMG")
        except Exception as e:
            self.setText("ERR")
    
    def mousePressEvent(self, event):
        """鼠标按下 - 开始拖拽"""
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setUrls([QUrl.fromLocalFile(self.file_path)])
            mime_data.setText(self.file_path)
            drag.setMimeData(mime_data)
            
            # 设置拖拽图标
            if self.pixmap():
                drag.setPixmap(self.pixmap().scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio))
            
            drag.exec(Qt.DropAction.CopyAction)
    
    def mouseDoubleClickEvent(self, event):
        """双击添加到画布"""
        self.double_clicked.emit(self.file_path)


class AssetsPanel(QWidget):
    """素材面板"""
    
    asset_selected = pyqtSignal(str)  # 素材被选中
    asset_add_to_canvas = pyqtSignal(str)  # 添加素材到画布
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._thumbnails = []
        self._setup_ui()
        self._apply_style()
        self._setup_asset_manager()
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题栏
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 8, 10, 8)
        
        title = QLabel("本地素材库")
        title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # 添加文件夹按钮
        add_folder_btn = QPushButton("+")
        add_folder_btn.setFixedSize(24, 24)
        add_folder_btn.setToolTip("添加素材文件夹")
        add_folder_btn.clicked.connect(self._on_add_folder)
        header_layout.addWidget(add_folder_btn)
        
        layout.addWidget(header)
        
        # 素材网格区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(6)
        self.grid_layout.setContentsMargins(8, 8, 8, 8)
        
        self.scroll_area.setWidget(self.grid_widget)
        layout.addWidget(self.scroll_area, 1)
        
        # 提示文字
        self.empty_label = QLabel("拖拽素材到画布\n或点击 + 添加文件夹")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setObjectName("emptyLabel")
        layout.addWidget(self.empty_label)
    
    def _apply_style(self):
        """应用样式"""
        theme = UIConfig.THEME
        self.setStyleSheet(f"""
            AssetsPanel {{
                background-color: {theme['bg_secondary']};
            }}
            QLabel {{
                color: {theme['text_primary']};
            }}
            QLabel#emptyLabel {{
                color: {theme['text_secondary']};
                font-size: 11px;
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
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)
    
    def _setup_asset_manager(self):
        """设置素材管理器"""
        asset_manager.add_callback(self._on_asset_change)
        
        # 加载保存的素材文件夹路径
        saved_folders = load_asset_folders()
        if saved_folders:
            # 使用保存的文件夹
            for folder in saved_folders:
                if os.path.isdir(folder):
                    asset_manager.add_watch_path(folder)
        else:
            # 首次运行，添加默认素材目录
            default_dirs = [
                os.path.expanduser("~/Pictures"),
                os.path.expanduser("~/Desktop"),
            ]
            for d in default_dirs:
                if os.path.isdir(d):
                    asset_manager.add_watch_path(d)
        
        # 刷新素材列表
        self._refresh_assets()
    
    def _on_asset_change(self, action: str, path: str):
        """素材变化回调"""
        self._refresh_assets()
    
    def _refresh_assets(self):
        """刷新素材列表"""
        # 清空现有缩略图
        for thumb in self._thumbnails:
            thumb.deleteLater()
        self._thumbnails.clear()
        
        # 清空网格
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 获取素材列表
        assets = asset_manager.get_assets()
        
        if not assets:
            self.empty_label.show()
            self.scroll_area.hide()
            return
        
        self.empty_label.hide()
        self.scroll_area.show()
        
        # 添加缩略图
        cols = 3
        for i, path in enumerate(assets[:50]):  # 限制显示数量
            thumb = AssetThumbnail(path)
            thumb.double_clicked.connect(self.asset_add_to_canvas.emit)
            self._thumbnails.append(thumb)
            
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(thumb, row, col)
    
    def _on_add_folder(self):
        """添加素材文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择素材文件夹",
            os.path.expanduser("~")
        )
        if folder:
            asset_manager.add_watch_path(folder)
            # 保存文件夹路径
            save_asset_folders(asset_manager.watch_paths)
            self._refresh_assets()
    
    def add_files(self, file_paths: list):
        """添加文件到素材库"""
        for path in file_paths:
            if os.path.isfile(path):
                ext = Path(path).suffix.lower()
                if ext in SUPPORTED_FORMATS:
                    # 复制到素材目录或直接添加
                    pass
        self._refresh_assets()
