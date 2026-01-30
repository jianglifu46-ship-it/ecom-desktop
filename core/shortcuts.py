"""
快捷键管理器
"""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QWidget
from typing import Dict, Callable, List, Tuple


class ShortcutManager:
    """快捷键管理器"""
    
    # 默认快捷键配置
    DEFAULT_SHORTCUTS = {
        # 文件操作
        "new": ("Ctrl+N", "新建项目"),
        "open": ("Ctrl+O", "打开项目"),
        "save": ("Ctrl+S", "保存项目"),
        "save_as": ("Ctrl+Shift+S", "另存为"),
        "export": ("Ctrl+E", "导出"),
        
        # 编辑操作
        "undo": ("Ctrl+Z", "撤销"),
        "redo": ("Ctrl+Shift+Z", "重做"),
        "cut": ("Ctrl+X", "剪切"),
        "copy": ("Ctrl+C", "复制"),
        "paste": ("Ctrl+V", "粘贴"),
        "delete": ("Delete", "删除"),
        "select_all": ("Ctrl+A", "全选"),
        
        # 视图操作
        "zoom_in": ("Ctrl+=", "放大"),
        "zoom_out": ("Ctrl+-", "缩小"),
        "zoom_fit": ("Ctrl+0", "适应窗口"),
        "zoom_100": ("Ctrl+1", "100% 缩放"),
        
        # 图层操作
        "layer_up": ("Ctrl+]", "图层上移"),
        "layer_down": ("Ctrl+[", "图层下移"),
        "layer_top": ("Ctrl+Shift+]", "图层置顶"),
        "layer_bottom": ("Ctrl+Shift+[", "图层置底"),
        "duplicate": ("Ctrl+D", "复制图层"),
        "group": ("Ctrl+G", "编组"),
        "ungroup": ("Ctrl+Shift+G", "取消编组"),
        
        # 工具切换
        "tool_select": ("V", "选择工具"),
        "tool_move": ("M", "移动工具"),
        "tool_text": ("T", "文字工具"),
        "tool_rectangle": ("R", "矩形工具"),
        "tool_ellipse": ("E", "椭圆工具"),
        
        # 对齐操作
        "align_left": ("Ctrl+Shift+L", "左对齐"),
        "align_center": ("Ctrl+Shift+C", "水平居中"),
        "align_right": ("Ctrl+Shift+R", "右对齐"),
        "align_top": ("Ctrl+Shift+T", "顶部对齐"),
        "align_middle": ("Ctrl+Shift+M", "垂直居中"),
        "align_bottom": ("Ctrl+Shift+B", "底部对齐"),
        
        # 移动操作
        "move_up": ("Up", "上移 1px"),
        "move_down": ("Down", "下移 1px"),
        "move_left": ("Left", "左移 1px"),
        "move_right": ("Right", "右移 1px"),
        "move_up_fast": ("Shift+Up", "上移 10px"),
        "move_down_fast": ("Shift+Down", "下移 10px"),
        "move_left_fast": ("Shift+Left", "左移 10px"),
        "move_right_fast": ("Shift+Right", "右移 10px"),
        
        # 其他
        "toggle_guides": ("Ctrl+;", "显示/隐藏辅助线"),
        "toggle_grid": ("Ctrl+'", "显示/隐藏网格"),
        "preferences": ("Ctrl+,", "偏好设置"),
    }
    
    def __init__(self, parent: QWidget = None):
        self.parent = parent
        self.shortcuts: Dict[str, QShortcut] = {}
        self.callbacks: Dict[str, Callable] = {}
        self.custom_shortcuts: Dict[str, str] = {}
    
    def register(self, action_id: str, callback: Callable, 
                 custom_key: str = None) -> QShortcut:
        """
        注册快捷键
        
        Args:
            action_id: 动作 ID（对应 DEFAULT_SHORTCUTS 中的键）
            callback: 回调函数
            custom_key: 自定义快捷键（可选）
        
        Returns:
            QShortcut 对象
        """
        if action_id not in self.DEFAULT_SHORTCUTS and custom_key is None:
            raise ValueError(f"未知的动作 ID: {action_id}")
        
        # 获取快捷键
        if custom_key:
            key = custom_key
        elif action_id in self.custom_shortcuts:
            key = self.custom_shortcuts[action_id]
        else:
            key = self.DEFAULT_SHORTCUTS[action_id][0]
        
        # 创建快捷键
        shortcut = QShortcut(QKeySequence(key), self.parent)
        shortcut.activated.connect(callback)
        
        self.shortcuts[action_id] = shortcut
        self.callbacks[action_id] = callback
        
        return shortcut
    
    def unregister(self, action_id: str):
        """取消注册快捷键"""
        if action_id in self.shortcuts:
            self.shortcuts[action_id].deleteLater()
            del self.shortcuts[action_id]
            del self.callbacks[action_id]
    
    def set_custom_shortcut(self, action_id: str, key: str):
        """设置自定义快捷键"""
        self.custom_shortcuts[action_id] = key
        
        # 如果已注册，更新快捷键
        if action_id in self.shortcuts:
            callback = self.callbacks[action_id]
            self.unregister(action_id)
            self.register(action_id, callback, key)
    
    def get_shortcut_key(self, action_id: str) -> str:
        """获取快捷键"""
        if action_id in self.custom_shortcuts:
            return self.custom_shortcuts[action_id]
        if action_id in self.DEFAULT_SHORTCUTS:
            return self.DEFAULT_SHORTCUTS[action_id][0]
        return ""
    
    def get_shortcut_description(self, action_id: str) -> str:
        """获取快捷键描述"""
        if action_id in self.DEFAULT_SHORTCUTS:
            return self.DEFAULT_SHORTCUTS[action_id][1]
        return ""
    
    def get_all_shortcuts(self) -> List[Tuple[str, str, str]]:
        """获取所有快捷键列表 [(action_id, key, description), ...]"""
        result = []
        for action_id, (key, desc) in self.DEFAULT_SHORTCUTS.items():
            actual_key = self.custom_shortcuts.get(action_id, key)
            result.append((action_id, actual_key, desc))
        return result
    
    def reset_to_default(self, action_id: str = None):
        """重置为默认快捷键"""
        if action_id:
            if action_id in self.custom_shortcuts:
                del self.custom_shortcuts[action_id]
                # 重新注册
                if action_id in self.callbacks:
                    callback = self.callbacks[action_id]
                    self.unregister(action_id)
                    self.register(action_id, callback)
        else:
            # 重置所有
            self.custom_shortcuts.clear()
            for action_id in list(self.shortcuts.keys()):
                if action_id in self.callbacks:
                    callback = self.callbacks[action_id]
                    self.unregister(action_id)
                    self.register(action_id, callback)
    
    def save_config(self, filepath: str):
        """保存快捷键配置"""
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.custom_shortcuts, f, ensure_ascii=False, indent=2)
    
    def load_config(self, filepath: str):
        """加载快捷键配置"""
        import json
        import os
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                self.custom_shortcuts = json.load(f)


# 全局快捷键管理器
shortcut_manager: ShortcutManager = None


def init_shortcuts(parent: QWidget) -> ShortcutManager:
    """初始化快捷键管理器"""
    global shortcut_manager
    shortcut_manager = ShortcutManager(parent)
    return shortcut_manager
