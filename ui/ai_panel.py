"""
AI 助手面板 - 云端 AI 功能调用
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTextEdit, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from config import UIConfig
from services.api_client import api_client


class AIWorkerThread(QThread):
    """AI 处理工作线程"""
    
    finished = pyqtSignal(bool, str, object)  # success, message, result
    progress = pyqtSignal(int, str)  # progress, status
    
    def __init__(self, task_type: str, params: dict, parent=None):
        super().__init__(parent)
        self.task_type = task_type
        self.params = params
    
    def run(self):
        """执行 AI 任务"""
        try:
            self.progress.emit(10, "正在连接服务器...")
            
            if self.task_type == "generate_copy":
                # 智能文案生成
                self.progress.emit(30, "AI 正在生成文案...")
                result = api_client.ai_generate_copy(
                    self.params.get("product_name", ""),
                    self.params.get("keywords", []),
                    self.params.get("style", "促销")
                )
                self.progress.emit(100, "完成")
                self.finished.emit(True, "文案生成成功", result)
            
            elif self.task_type == "generate_background":
                # 背景生成
                self.progress.emit(30, "AI 正在生成背景...")
                result = api_client.generate_background(
                    self.params.get("image_path", ""),
                    self.params.get("style", "简约")
                )
                self.progress.emit(100, "完成")
                self.finished.emit(True, "背景生成成功", result)
            
            elif self.task_type == "optimize_layout":
                # 排版优化
                self.progress.emit(30, "AI 正在分析排版...")
                # 模拟 AI 处理
                import time
                time.sleep(1)
                self.progress.emit(100, "完成")
                self.finished.emit(True, "排版优化建议已生成", {"suggestions": ["建议1", "建议2"]})
            
            else:
                self.finished.emit(False, f"未知的任务类型: {self.task_type}", None)
                
        except Exception as e:
            self.finished.emit(False, f"处理失败: {str(e)}", None)


class AIFeatureButton(QPushButton):
    """AI 功能按钮"""
    
    def __init__(self, text: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.setText(f"{icon} {text}" if icon else text)
        self._apply_style()
    
    def _apply_style(self):
        theme = UIConfig.THEME
        self.setStyleSheet(f"""
            AIFeatureButton {{
                background-color: {theme['bg_tertiary']};
                color: {theme['text_primary']};
                border: none;
                border-radius: 5px;
                padding: 10px;
                text-align: left;
                font-size: 12px;
            }}
            AIFeatureButton:hover {{
                background-color: {theme['accent']};
            }}
            AIFeatureButton:pressed {{
                background-color: {theme['accent_hover']};
            }}
        """)


class AIPanel(QWidget):
    """AI 助手面板"""
    
    # 信号
    copy_generated = pyqtSignal(str)  # 文案生成完成
    background_generated = pyqtSignal(str)  # 背景生成完成
    layout_optimized = pyqtSignal(list)  # 排版优化完成
    remove_bg_requested = pyqtSignal()  # 请求抠图
    upscale_requested = pyqtSignal()  # 请求放大
    enhance_requested = pyqtSignal()  # 请求增强
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: AIWorkerThread = None
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题栏
        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 8, 10, 8)
        
        title = QLabel("AI 助手")
        title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # 功能按钮区域
        btn_container = QWidget()
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setSpacing(6)
        btn_layout.setContentsMargins(8, 5, 8, 5)
        
        # 云端 AI 功能
        self.copy_btn = AIFeatureButton("智能文案生成", "✍️")
        self.copy_btn.clicked.connect(self._on_generate_copy)
        btn_layout.addWidget(self.copy_btn)
        
        self.layout_btn = AIFeatureButton("一键排版优化", "📐")
        self.layout_btn.clicked.connect(self._on_optimize_layout)
        btn_layout.addWidget(self.layout_btn)
        
        self.style_btn = AIFeatureButton("风格迁移", "🎨")
        self.style_btn.clicked.connect(self._on_style_transfer)
        btn_layout.addWidget(self.style_btn)
        
        self.bg_btn = AIFeatureButton("背景生成", "🖼️")
        self.bg_btn.clicked.connect(self._on_generate_background)
        btn_layout.addWidget(self.bg_btn)
        
        # 本地图像处理
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        btn_layout.addWidget(separator)
        
        local_label = QLabel("本地处理")
        local_label.setObjectName("sectionLabel")
        btn_layout.addWidget(local_label)
        
        self.rembg_btn = AIFeatureButton("智能抠图", "✂️")
        self.rembg_btn.clicked.connect(self.remove_bg_requested.emit)
        btn_layout.addWidget(self.rembg_btn)
        
        self.upscale_btn = AIFeatureButton("图片放大", "🔍")
        self.upscale_btn.clicked.connect(self.upscale_requested.emit)
        btn_layout.addWidget(self.upscale_btn)
        
        self.enhance_btn = AIFeatureButton("图片增强", "✨")
        self.enhance_btn.clicked.connect(self.enhance_requested.emit)
        btn_layout.addWidget(self.enhance_btn)
        
        layout.addWidget(btn_container)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def _apply_style(self):
        """应用样式"""
        theme = UIConfig.THEME
        self.setStyleSheet(f"""
            AIPanel {{
                background-color: {theme['bg_secondary']};
            }}
            QFrame#header {{
                background-color: {theme['accent']};
            }}
            QLabel {{
                color: {theme['text_primary']};
            }}
            QLabel#sectionLabel {{
                color: {theme['text_secondary']};
                font-size: 11px;
            }}
            QLabel#statusLabel {{
                color: {theme['text_secondary']};
                font-size: 11px;
            }}
            QFrame#separator {{
                color: {theme['border']};
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
    
    def _on_generate_copy(self):
        """生成文案"""
        # TODO: 弹出对话框输入产品信息
        self._run_ai_task("generate_copy", {
            "product_name": "春季新品",
            "keywords": ["时尚", "舒适", "新款"],
            "style": "促销"
        })
    
    def _on_optimize_layout(self):
        """优化排版"""
        self._run_ai_task("optimize_layout", {})
    
    def _on_style_transfer(self):
        """风格迁移"""
        QMessageBox.information(self, "提示", "风格迁移功能开发中...")
    
    def _on_generate_background(self):
        """生成背景"""
        self._run_ai_task("generate_background", {
            "style": "简约"
        })
    
    def _run_ai_task(self, task_type: str, params: dict):
        """运行 AI 任务"""
        if self._worker and self._worker.isRunning():
            QMessageBox.warning(self, "提示", "有任务正在执行中，请稍候...")
            return
        
        self._set_buttons_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self._worker = AIWorkerThread(task_type, params)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_task_finished)
        self._worker.start()
    
    def _on_progress(self, value: int, status: str):
        """进度更新"""
        self.progress_bar.setValue(value)
        self.status_label.setText(status)
    
    def _on_task_finished(self, success: bool, message: str, result):
        """任务完成"""
        self._set_buttons_enabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(message if success else f"❌ {message}")
        
        if success:
            if isinstance(result, str):
                self.copy_generated.emit(result)
            elif isinstance(result, dict):
                if "suggestions" in result:
                    self.layout_optimized.emit(result["suggestions"])
    
    def _set_buttons_enabled(self, enabled: bool):
        """设置按钮可用状态"""
        self.copy_btn.setEnabled(enabled)
        self.layout_btn.setEnabled(enabled)
        self.style_btn.setEnabled(enabled)
        self.bg_btn.setEnabled(enabled)
