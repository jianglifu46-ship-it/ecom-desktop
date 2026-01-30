"""
电商详情页管理系统 - 桌面客户端配置文件
"""
import os
from pathlib import Path

# 应用信息
APP_NAME = "电商详情页管理系统"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Manus"

# 目录配置
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
ICONS_DIR = ASSETS_DIR / "icons"
TEMPLATES_DIR = BASE_DIR / "templates"
MODELS_DIR = BASE_DIR / "models"

# 用户数据目录
USER_DATA_DIR = Path.home() / ".ecom-desktop"
USER_DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR = USER_DATA_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# API 配置
class APIConfig:
    # 开发环境
    DEV_BASE_URL = "https://3000-ih87qxxdv7t27cb878dhg-fe96ae91.sg1.manus.computer"
    # 生产环境
    PROD_BASE_URL = "https://ecom-admin.manus.space"
    
    # 当前使用的环境（可通过设置切换）
    USE_PRODUCTION = True
    
    @classmethod
    def get_base_url(cls):
        return cls.PROD_BASE_URL if cls.USE_PRODUCTION else cls.DEV_BASE_URL
    
    # BASE_URL 属性（供直接访问）
    BASE_URL = PROD_BASE_URL
    
    # API 端点
    LOGIN = "/api/auth/login"
    GET_MY_TASKS = "/api/trpc/tasks.getMyTasks"
    TASKS = "/api/trpc/tasks.getMyTasks"  # 别名
    GET_TASK_DETAIL = "/api/trpc/tasks.getTaskDetail"
    TASK_DETAIL = "/api/trpc/tasks.getTaskDetail"  # 别名
    ACCEPT_TASK = "/api/trpc/tasks.acceptTask"
    SUBMIT_DESIGN = "/api/trpc/tasks.submitDesign"
    GET_NOTIFICATIONS = "/api/trpc/notifications.getUnread"
    NOTIFICATIONS = "/api/trpc/notifications.getUnread"  # 别名
    UPLOAD_FILE = "/api/upload"
    UPLOAD = "/api/upload"  # 别名
    GENERATE_BACKGROUND = "/api/trpc/imageTools.generateBackground"

# 画布配置
class CanvasConfig:
    DEFAULT_WIDTH = 750  # 电商详情页标准宽度
    DEFAULT_HEIGHT = 1000
    MIN_ZOOM = 0.1
    MAX_ZOOM = 5.0
    DEFAULT_ZOOM = 1.0
    GRID_SIZE = 10
    SNAP_THRESHOLD = 5

# 导出配置
class ExportConfig:
    # 平台规范
    PLATFORMS = {
        "taobao": {
            "name": "淘宝/天猫",
            "max_width": 790,
            "max_height": 10000,
            "format": "jpg",
            "quality": 95
        },
        "jd": {
            "name": "京东",
            "max_width": 750,
            "max_height": 9999,
            "format": "jpg",
            "quality": 95
        },
        "pdd": {
            "name": "拼多多",
            "max_width": 750,
            "max_height": 10000,
            "format": "jpg",
            "quality": 90
        }
    }
    DEFAULT_PLATFORM = "taobao"

# 应用配置
class AppConfig:
    DATA_DIR = str(USER_DATA_DIR)
    CACHE_DIR = str(CACHE_DIR)
    ASSETS_DIR = str(ASSETS_DIR)
    MODELS_DIR = str(MODELS_DIR)

# 任务轮询配置
class PollerConfig:
    INTERVAL_SECONDS = 30  # 轮询间隔
    NOTIFICATION_INTERVAL = 60  # 通知检查间隔

# UI 配置
class UIConfig:
    # 深色主题配色
    THEME = {
        "bg_primary": "#1e1e1e",
        "bg_secondary": "#252526",
        "bg_tertiary": "#333333",
        "text_primary": "#ffffff",
        "text_secondary": "#a0a0a0",
        "accent": "#007acc",
        "accent_hover": "#1e90ff",
        "border": "rgba(255, 255, 255, 0.1)",
        "success": "#4caf50",
        "warning": "#ff9800",
        "error": "#f44336"
    }
    
    # 窗口尺寸
    MAIN_WINDOW_WIDTH = 1400
    MAIN_WINDOW_HEIGHT = 900
    MIN_WINDOW_WIDTH = 1200
    MIN_WINDOW_HEIGHT = 700
    
    # 面板尺寸
    LEFT_PANEL_WIDTH = 280
    RIGHT_PANEL_WIDTH = 280
    TOOLBAR_HEIGHT = 40
    STATUSBAR_HEIGHT = 25

# Token 存储路径
TOKEN_FILE = USER_DATA_DIR / "token.json"

def save_token(token: str, user: dict):
    """保存登录 token"""
    import json
    data = {"token": token, "user": user}
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def load_token() -> tuple:
    """加载登录 token"""
    import json
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("token"), data.get("user")
        except:
            pass
    return None, None

def clear_token():
    """清除登录 token"""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
