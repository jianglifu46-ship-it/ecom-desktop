"""
登录对话框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from config import APP_NAME, UIConfig
from services.api_client import api_client, APIError


class LoginDialog(QDialog):
    """登录对话框"""
    
    login_success = pyqtSignal(object)  # 登录成功信号，传递用户信息
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} - 登录")
        self.setFixedSize(400, 300)
        self.setModal(True)
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # 标题
        title_label = QLabel(APP_NAME)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("美工工作台")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setObjectName("subtitle")
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(20)
        
        # 用户名
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名")
        self.username_input.setMinimumHeight(40)
        layout.addWidget(self.username_input)
        
        # 密码
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.returnPressed.connect(self._on_login)
        layout.addWidget(self.password_input)
        
        layout.addSpacing(10)
        
        # 登录按钮
        self.login_btn = QPushButton("登 录")
        self.login_btn.setMinimumHeight(45)
        self.login_btn.setObjectName("loginBtn")
        self.login_btn.clicked.connect(self._on_login)
        layout.addWidget(self.login_btn)
        
        # 错误信息
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setObjectName("errorLabel")
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        layout.addStretch()
    
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
            QLabel#subtitle {{
                color: {theme['text_secondary']};
                font-size: 14px;
            }}
            QLabel#errorLabel {{
                color: {theme['error']};
                font-size: 12px;
            }}
            QLineEdit {{
                background-color: {theme['bg_secondary']};
                border: 1px solid {theme['border']};
                border-radius: 5px;
                padding: 10px;
                color: {theme['text_primary']};
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {theme['accent']};
            }}
            QPushButton#loginBtn {{
                background-color: {theme['accent']};
                color: {theme['text_primary']};
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton#loginBtn:hover {{
                background-color: {theme['accent_hover']};
            }}
            QPushButton#loginBtn:pressed {{
                background-color: {theme['accent']};
            }}
            QPushButton#loginBtn:disabled {{
                background-color: {theme['bg_tertiary']};
                color: {theme['text_secondary']};
            }}
        """)
    
    def _on_login(self):
        """登录处理"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username:
            self._show_error("请输入用户名")
            return
        
        if not password:
            self._show_error("请输入密码")
            return
        
        self.login_btn.setEnabled(False)
        self.login_btn.setText("登录中...")
        self.error_label.hide()
        
        try:
            user = api_client.login(username, password)
            self.login_success.emit(user)
            self.accept()
        except APIError as e:
            self._show_error(str(e))
        except Exception as e:
            self._show_error(f"登录失败: {str(e)}")
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("登 录")
    
    def _show_error(self, message: str):
        """显示错误信息"""
        self.error_label.setText(message)
        self.error_label.show()
