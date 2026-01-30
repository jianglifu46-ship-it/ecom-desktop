"""
导出对话框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QGroupBox,
    QFileDialog, QProgressBar, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

import os

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from config import UIConfig, ExportConfig
from core.canvas import Canvas
from core.export import Exporter


class ExportWorkerThread(QThread):
    """导出工作线程"""
    
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str, list)
    
    def __init__(self, exporter: Exporter, output_dir: str, platform: str, 
                 quality: int, export_full: bool, parent=None):
        super().__init__(parent)
        self.exporter = exporter
        self.output_dir = output_dir
        self.platform = platform
        self.quality = quality
        self.export_full = export_full
    
    def run(self):
        """执行导出"""
        try:
            self.progress.emit(10, "准备导出...")
            
            if self.export_full:
                self.progress.emit(50, "导出完整画布...")
                output_path = os.path.join(self.output_dir, "full_detail")
                result = self.exporter.export_full(output_path, self.platform, self.quality)
            else:
                self.progress.emit(30, "按分屏导出...")
                result = self.exporter.export_screens(self.output_dir, self.platform, self.quality)
            
            self.progress.emit(100, "完成")
            self.finished.emit(result.success, result.message, result.files)
            
        except Exception as e:
            self.finished.emit(False, f"导出失败: {str(e)}", [])


class ExportDialog(QDialog):
    """导出对话框"""
    
    export_completed = pyqtSignal(list)  # 导出完成信号，传递文件列表
    
    def __init__(self, canvas: Canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.exporter = Exporter(canvas)
        self._worker: ExportWorkerThread = None
        
        self.setWindowTitle("导出详情页")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("导出详情页")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 输出目录
        dir_group = QGroupBox("输出目录")
        dir_layout = QHBoxLayout(dir_group)
        
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("选择输出目录...")
        self.dir_input.setText(os.path.expanduser("~/Desktop/export"))
        dir_layout.addWidget(self.dir_input)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._on_browse)
        dir_layout.addWidget(browse_btn)
        
        layout.addWidget(dir_group)
        
        # 导出选项
        options_group = QGroupBox("导出选项")
        options_layout = QVBoxLayout(options_group)
        
        # 平台选择
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel("目标平台:"))
        self.platform_combo = QComboBox()
        for key, config in ExportConfig.PLATFORMS.items():
            self.platform_combo.addItem(config["name"], key)
        platform_layout.addWidget(self.platform_combo)
        platform_layout.addStretch()
        options_layout.addLayout(platform_layout)
        
        # 质量
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("图片质量:"))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(50, 100)
        self.quality_spin.setValue(95)
        self.quality_spin.setSuffix("%")
        quality_layout.addWidget(self.quality_spin)
        quality_layout.addStretch()
        options_layout.addLayout(quality_layout)
        
        # 导出模式
        self.split_check = QCheckBox("按分屏切图导出（推荐）")
        self.split_check.setChecked(True)
        options_layout.addWidget(self.split_check)
        
        self.full_check = QCheckBox("同时导出完整长图")
        options_layout.addWidget(self.full_check)
        
        layout.addWidget(options_group)
        
        # 预览信息
        info_frame = QFrame()
        info_frame.setObjectName("infoFrame")
        info_layout = QVBoxLayout(info_frame)
        
        screen_count = len([s for s in self.canvas.screens if not s.is_blank])
        self.info_label = QLabel(f"将导出 {screen_count} 张分屏图片")
        self.info_label.setObjectName("infoLabel")
        info_layout.addWidget(self.info_label)
        
        platform_info = ExportConfig.PLATFORMS.get("taobao", {})
        self.format_label = QLabel(f"格式: {platform_info.get('format', 'jpg').upper()} | 最大宽度: {platform_info.get('max_width', 750)}px")
        self.format_label.setObjectName("formatLabel")
        info_layout.addWidget(self.format_label)
        
        layout.addWidget(info_frame)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        self.export_btn = QPushButton("开始导出")
        self.export_btn.setObjectName("exportBtn")
        self.export_btn.clicked.connect(self._on_export)
        btn_layout.addWidget(self.export_btn)
        
        layout.addLayout(btn_layout)
        
        # 连接信号
        self.platform_combo.currentIndexChanged.connect(self._on_platform_changed)
    
    def _apply_style(self):
        """应用样式"""
        theme = UIConfig.THEME
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme['bg_primary']};
            }}
            QLabel {{
                color: {theme['text_primary']};
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
            QLineEdit {{
                background-color: {theme['bg_secondary']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
                padding: 8px;
            }}
            QComboBox, QSpinBox {{
                background-color: {theme['bg_secondary']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
                padding: 5px;
            }}
            QCheckBox {{
                color: {theme['text_primary']};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            QFrame#infoFrame {{
                background-color: {theme['bg_secondary']};
                border-radius: 5px;
                padding: 10px;
            }}
            QLabel#infoLabel {{
                color: {theme['accent']};
                font-size: 13px;
            }}
            QLabel#formatLabel {{
                color: {theme['text_secondary']};
                font-size: 11px;
            }}
            QPushButton {{
                background-color: {theme['bg_tertiary']};
                color: {theme['text_primary']};
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background-color: {theme['accent']};
            }}
            QPushButton#exportBtn {{
                background-color: {theme['accent']};
                font-weight: bold;
            }}
            QPushButton#exportBtn:hover {{
                background-color: {theme['accent_hover']};
            }}
            QProgressBar {{
                background-color: {theme['bg_tertiary']};
                border: none;
                border-radius: 3px;
                text-align: center;
                color: {theme['text_primary']};
            }}
            QProgressBar::chunk {{
                background-color: {theme['accent']};
                border-radius: 3px;
            }}
        """)
    
    def _on_browse(self):
        """浏览目录"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择输出目录",
            self.dir_input.text() or os.path.expanduser("~")
        )
        if folder:
            self.dir_input.setText(folder)
    
    def _on_platform_changed(self, index):
        """平台选择变化"""
        platform = self.platform_combo.currentData()
        config = ExportConfig.PLATFORMS.get(platform, {})
        self.format_label.setText(
            f"格式: {config.get('format', 'jpg').upper()} | 最大宽度: {config.get('max_width', 750)}px"
        )
    
    def _on_export(self):
        """开始导出"""
        output_dir = self.dir_input.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "提示", "请选择输出目录")
            return
        
        platform = self.platform_combo.currentData()
        quality = self.quality_spin.value()
        export_full = self.full_check.isChecked()
        
        self.export_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self._worker = ExportWorkerThread(
            self.exporter, output_dir, platform, quality, export_full
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()
    
    def _on_progress(self, value: int, status: str):
        """进度更新"""
        self.progress_bar.setValue(value)
        self.status_label.setText(status)
    
    def _on_finished(self, success: bool, message: str, files: list):
        """导出完成"""
        self.export_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText(f"✅ {message}")
            self.export_completed.emit(files)
            
            # 询问是否打开目录
            reply = QMessageBox.question(
                self, "导出成功",
                f"成功导出 {len(files)} 张图片\n是否打开输出目录？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                import subprocess
                subprocess.Popen(['xdg-open', self.dir_input.text()])
            
            self.accept()
        else:
            self.status_label.setText(f"❌ {message}")
            QMessageBox.critical(self, "导出失败", message)
