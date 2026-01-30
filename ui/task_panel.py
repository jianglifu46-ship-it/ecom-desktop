"""
任务面板 - 显示任务列表和详情
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QScrollArea, QSplitter,
    QTextEdit, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from config import UIConfig
from services.api_client import Task


class TaskCard(QFrame):
    """任务卡片"""
    
    clicked = pyqtSignal(object)  # 点击信号，传递任务对象
    
    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self._setup_ui()
        self._apply_style()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title_label = QLabel(self.task.title)
        title_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # 截止日期
        if self.task.deadline:
            deadline_label = QLabel(f"截止: {self.task.deadline}")
            deadline_label.setObjectName("deadline")
            layout.addWidget(deadline_label)
        
        # 状态标签
        status_layout = QHBoxLayout()
        status_label = QLabel(self.task.status_display)
        status_label.setObjectName(f"status_{self.task.status}")
        status_label.setFixedHeight(22)
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        
        # 优先级
        if self.task.priority:
            priority_label = QLabel(self.task.priority)
            priority_label.setObjectName("priority")
            status_layout.addWidget(priority_label)
        
        layout.addLayout(status_layout)
    
    def _apply_style(self):
        """应用样式"""
        theme = UIConfig.THEME
        
        status_colors = {
            "pending": theme['warning'],
            "in_progress": theme['accent'],
            "submitted": theme['success'],
            "revision": theme['error'],
        }
        status_color = status_colors.get(self.task.status, theme['text_secondary'])
        
        self.setStyleSheet(f"""
            TaskCard {{
                background-color: {theme['bg_tertiary']};
                border-radius: 8px;
                border: 1px solid transparent;
            }}
            TaskCard:hover {{
                border: 1px solid {theme['accent']};
            }}
            QLabel {{
                color: {theme['text_primary']};
            }}
            QLabel#deadline {{
                color: {theme['text_secondary']};
                font-size: 11px;
            }}
            QLabel[objectName^="status_"] {{
                background-color: {status_color};
                color: white;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 11px;
            }}
            QLabel#priority {{
                color: {theme['warning']};
                font-size: 11px;
            }}
        """)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        self.clicked.emit(self.task)
        super().mousePressEvent(event)


class TaskDetailPanel(QFrame):
    """任务详情面板"""
    
    accept_task = pyqtSignal(object)  # 接单信号
    open_editor = pyqtSignal(object)  # 打开编辑器信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_task: Task = None
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题
        self.title_label = QLabel("选择任务查看详情")
        self.title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        
        # 状态和截止日期
        info_layout = QHBoxLayout()
        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        info_layout.addWidget(self.status_label)
        
        self.deadline_label = QLabel("")
        self.deadline_label.setObjectName("deadline")
        info_layout.addWidget(self.deadline_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # 需求描述
        desc_group = QGroupBox("需求描述")
        desc_layout = QVBoxLayout(desc_group)
        self.desc_text = QTextEdit()
        self.desc_text.setReadOnly(True)
        self.desc_text.setMaximumHeight(150)
        desc_layout.addWidget(self.desc_text)
        layout.addWidget(desc_group)
        
        # 参考素材
        assets_group = QGroupBox("参考素材")
        assets_layout = QVBoxLayout(assets_group)
        self.assets_label = QLabel("暂无素材")
        self.assets_label.setWordWrap(True)
        assets_layout.addWidget(self.assets_label)
        layout.addWidget(assets_group)
        
        layout.addStretch()
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.accept_btn = QPushButton("接受任务")
        self.accept_btn.setObjectName("acceptBtn")
        self.accept_btn.clicked.connect(self._on_accept)
        self.accept_btn.hide()
        btn_layout.addWidget(self.accept_btn)
        
        self.edit_btn = QPushButton("开始编辑")
        self.edit_btn.setObjectName("editBtn")
        self.edit_btn.clicked.connect(self._on_edit)
        self.edit_btn.hide()
        btn_layout.addWidget(self.edit_btn)
        
        layout.addLayout(btn_layout)
    
    def _apply_style(self):
        """应用样式"""
        theme = UIConfig.THEME
        self.setStyleSheet(f"""
            TaskDetailPanel {{
                background-color: {theme['bg_secondary']};
                border-radius: 8px;
            }}
            QLabel {{
                color: {theme['text_primary']};
            }}
            QLabel#status {{
                color: {theme['accent']};
                font-size: 12px;
            }}
            QLabel#deadline {{
                color: {theme['text_secondary']};
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
            QTextEdit {{
                background-color: {theme['bg_tertiary']};
                color: {theme['text_primary']};
                border: none;
                border-radius: 5px;
            }}
            QPushButton#acceptBtn {{
                background-color: {theme['warning']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
            }}
            QPushButton#acceptBtn:hover {{
                background-color: #e68a00;
            }}
            QPushButton#editBtn {{
                background-color: {theme['accent']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
            }}
            QPushButton#editBtn:hover {{
                background-color: {theme['accent_hover']};
            }}
        """)
    
    def set_task(self, task: Task):
        """设置任务"""
        self.current_task = task
        
        self.title_label.setText(task.title)
        self.status_label.setText(task.status_display)
        self.deadline_label.setText(f"截止: {task.deadline}" if task.deadline else "")
        self.desc_text.setText(task.description or "暂无描述")
        
        # 显示素材
        if task.assets:
            assets_text = "\n".join([f"• {a}" for a in task.assets])
            self.assets_label.setText(assets_text)
        else:
            self.assets_label.setText("暂无素材")
        
        # 根据状态显示按钮
        self.accept_btn.hide()
        self.edit_btn.hide()
        
        if task.status == "pending":
            self.accept_btn.show()
        elif task.status in ["in_progress", "revision"]:
            self.edit_btn.show()
    
    def _on_accept(self):
        """接受任务"""
        if self.current_task:
            self.accept_task.emit(self.current_task)
    
    def _on_edit(self):
        """开始编辑"""
        if self.current_task:
            self.open_editor.emit(self.current_task)


class TaskPanel(QWidget):
    """任务面板"""
    
    task_selected = pyqtSignal(object)
    open_editor = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = []
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题栏
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("任务列表")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.setObjectName("refreshBtn")
        refresh_btn.clicked.connect(self._on_refresh)
        header_layout.addWidget(refresh_btn)
        
        layout.addWidget(header)
        
        # 任务列表区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(8)
        self.list_layout.setContentsMargins(10, 5, 10, 10)
        self.list_layout.addStretch()
        
        self.scroll_area.setWidget(self.list_widget)
        layout.addWidget(self.scroll_area)
    
    def _apply_style(self):
        """应用样式"""
        theme = UIConfig.THEME
        self.setStyleSheet(f"""
            TaskPanel {{
                background-color: {theme['bg_secondary']};
            }}
            QLabel {{
                color: {theme['text_primary']};
            }}
            QPushButton#refreshBtn {{
                background-color: {theme['bg_tertiary']};
                color: {theme['text_primary']};
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
            }}
            QPushButton#refreshBtn:hover {{
                background-color: {theme['accent']};
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)
    
    def set_tasks(self, tasks: list):
        """设置任务列表"""
        self.tasks = tasks
        
        # 清空现有卡片
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 添加任务卡片
        for task in tasks:
            card = TaskCard(task)
            card.clicked.connect(self._on_task_clicked)
            self.list_layout.insertWidget(self.list_layout.count() - 1, card)
    
    def _on_task_clicked(self, task: Task):
        """任务被点击"""
        self.task_selected.emit(task)
    
    def _on_refresh(self):
        """刷新任务列表"""
        from services.api_client import api_client
        try:
            tasks = api_client.get_my_tasks()
            self.set_tasks(tasks)
        except Exception as e:
            print(f"刷新任务失败: {e}")
