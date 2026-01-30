"""
文件夹监控服务 - 监控本地素材文件夹
"""
import os
from pathlib import Path
from typing import List, Callable, Optional
from PyQt6.QtCore import QThread, pyqtSignal, QFileSystemWatcher

# 支持的图片格式
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.psd'}


class FileWatcherThread(QThread):
    """文件监控线程"""
    
    file_added = pyqtSignal(str)  # 新文件添加
    file_removed = pyqtSignal(str)  # 文件删除
    file_modified = pyqtSignal(str)  # 文件修改
    
    def __init__(self, watch_paths: List[str], parent=None):
        super().__init__(parent)
        self.watch_paths = watch_paths
        self._watcher: Optional[QFileSystemWatcher] = None
        self._known_files: set = set()
    
    def run(self):
        """运行监控"""
        # 初始化已知文件列表
        for path in self.watch_paths:
            if os.path.isdir(path):
                for file in self._scan_directory(path):
                    self._known_files.add(file)
        
        # 使用 Qt 的文件系统监控
        self._watcher = QFileSystemWatcher()
        for path in self.watch_paths:
            if os.path.exists(path):
                self._watcher.addPath(path)
        
        self._watcher.directoryChanged.connect(self._on_directory_changed)
        self._watcher.fileChanged.connect(self._on_file_changed)
        
        self.exec()
    
    def _scan_directory(self, directory: str) -> List[str]:
        """扫描目录中的图片文件"""
        files = []
        try:
            for entry in os.scandir(directory):
                if entry.is_file():
                    ext = Path(entry.path).suffix.lower()
                    if ext in SUPPORTED_FORMATS:
                        files.append(entry.path)
        except Exception as e:
            print(f"扫描目录失败: {e}")
        return files
    
    def _on_directory_changed(self, path: str):
        """目录变化处理"""
        current_files = set(self._scan_directory(path))
        
        # 检查新增文件
        added = current_files - self._known_files
        for file in added:
            self.file_added.emit(file)
        
        # 检查删除文件
        removed = self._known_files - current_files
        for file in removed:
            self.file_removed.emit(file)
        
        self._known_files = current_files
    
    def _on_file_changed(self, path: str):
        """文件变化处理"""
        self.file_modified.emit(path)
    
    def add_watch_path(self, path: str):
        """添加监控路径"""
        if self._watcher and os.path.exists(path):
            self._watcher.addPath(path)
            self.watch_paths.append(path)
    
    def remove_watch_path(self, path: str):
        """移除监控路径"""
        if self._watcher and path in self.watch_paths:
            self._watcher.removePath(path)
            self.watch_paths.remove(path)


class AssetManager:
    """素材管理器"""
    
    def __init__(self):
        self.watch_paths: List[str] = []
        self._watcher_thread: Optional[FileWatcherThread] = None
        self._assets: List[str] = []
        self._callbacks: List[Callable] = []
    
    def add_watch_path(self, path: str):
        """添加监控路径"""
        if path not in self.watch_paths and os.path.isdir(path):
            self.watch_paths.append(path)
            self._scan_path(path)
            if self._watcher_thread:
                self._watcher_thread.add_watch_path(path)
    
    def remove_watch_path(self, path: str):
        """移除监控路径"""
        if path in self.watch_paths:
            self.watch_paths.remove(path)
            # 移除该路径下的素材
            self._assets = [a for a in self._assets if not a.startswith(path)]
            if self._watcher_thread:
                self._watcher_thread.remove_watch_path(path)
    
    def _scan_path(self, path: str):
        """扫描路径下的素材"""
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    ext = Path(entry.path).suffix.lower()
                    if ext in SUPPORTED_FORMATS:
                        if entry.path not in self._assets:
                            self._assets.append(entry.path)
        except Exception as e:
            print(f"扫描素材失败: {e}")
    
    def get_assets(self) -> List[str]:
        """获取所有素材"""
        return self._assets.copy()
    
    def start_watching(self):
        """开始监控"""
        if self._watcher_thread is None and self.watch_paths:
            self._watcher_thread = FileWatcherThread(self.watch_paths)
            self._watcher_thread.file_added.connect(self._on_file_added)
            self._watcher_thread.file_removed.connect(self._on_file_removed)
            self._watcher_thread.start()
    
    def stop_watching(self):
        """停止监控"""
        if self._watcher_thread:
            self._watcher_thread.quit()
            self._watcher_thread.wait()
            self._watcher_thread = None
    
    def _on_file_added(self, path: str):
        """文件添加回调"""
        if path not in self._assets:
            self._assets.append(path)
            for callback in self._callbacks:
                callback('added', path)
    
    def _on_file_removed(self, path: str):
        """文件删除回调"""
        if path in self._assets:
            self._assets.remove(path)
            for callback in self._callbacks:
                callback('removed', path)
    
    def add_callback(self, callback: Callable):
        """添加变化回调"""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """移除变化回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)


# 全局素材管理器
asset_manager = AssetManager()
