"""
进度对话框 - 用于显示后台任务进度
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


class WorkerThread(QThread):
    """后台工作线程"""
    finished = pyqtSignal(object)  # 完成信号，携带结果
    error = pyqtSignal(str)  # 错误信号
    progress = pyqtSignal(str)  # 进度信息
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None
    
    def run(self):
        try:
            self.result = self.func(*self.args, **self.kwargs)
            self.finished.emit(self.result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))


class ProgressDialog(QDialog):
    """进度对话框"""
    
    def __init__(self, parent=None, title="处理中", message="正在处理，请稍候..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 180)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        self._setup_ui(message)
        self._worker = None
        self._result = None
        self._error = None
    
    def _setup_ui(self, message):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题标签
        self.title_label = QLabel(message)
        self.title_label.setFont(QFont("Microsoft YaHei", 11))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # 提示标签
        self.hint_label = QLabel("")
        self.hint_label.setStyleSheet("color: #666666; font-size: 10px;")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 无限循环模式
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 5px;
                background-color: #f0f0f0;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("请稍候...")
        self.status_label.setStyleSheet("color: #888888;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def set_hint(self, hint: str):
        """设置提示信息"""
        self.hint_label.setText(hint)
    
    def set_status(self, status: str):
        """设置状态信息"""
        self.status_label.setText(status)
    
    def run_task(self, func, *args, **kwargs):
        """运行后台任务"""
        self._worker = WorkerThread(func, *args, **kwargs)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.progress.connect(self._on_progress)
        self._worker.start()
        
        # 显示对话框（阻塞）
        self.exec()
        
        return self._result, self._error
    
    def _on_finished(self, result):
        """任务完成"""
        self._result = result
        self._error = None
        self.accept()
    
    def _on_error(self, error):
        """任务出错"""
        self._result = None
        self._error = error
        self.reject()
    
    def _on_progress(self, message):
        """进度更新"""
        self.status_label.setText(message)
    
    def closeEvent(self, event):
        """关闭事件 - 防止用户关闭对话框"""
        if self._worker and self._worker.isRunning():
            event.ignore()
        else:
            event.accept()


def run_with_progress(parent, title, message, hint, func, *args, **kwargs):
    """
    使用进度对话框运行后台任务
    
    Args:
        parent: 父窗口
        title: 对话框标题
        message: 主要提示信息
        hint: 额外提示（如首次使用提醒）
        func: 要执行的函数
        *args, **kwargs: 函数参数
    
    Returns:
        (result, error) 元组
    """
    dialog = ProgressDialog(parent, title, message)
    if hint:
        dialog.set_hint(hint)
    
    return dialog.run_task(func, *args, **kwargs)
