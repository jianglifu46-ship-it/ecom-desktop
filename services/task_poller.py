"""
任务轮询服务 - 定时检查新任务和通知
"""
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from typing import List, Set
import time

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from services.api_client import api_client, Task, Notification, APIError
from services.notification import notification_service
from config import PollerConfig


class TaskPollerThread(QThread):
    """任务轮询线程"""
    
    # 信号
    tasks_updated = pyqtSignal(list)  # 任务列表更新
    new_task_received = pyqtSignal(object)  # 收到新任务
    notification_received = pyqtSignal(object)  # 收到通知
    error_occurred = pyqtSignal(str)  # 发生错误
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self._known_task_ids: Set[int] = set()
        self._known_notification_ids: Set[int] = set()
        self._first_run = True
    
    def run(self):
        """运行轮询"""
        while self._running:
            try:
                if api_client.is_logged_in:
                    # 获取任务列表
                    tasks = api_client.get_my_tasks()
                    self.tasks_updated.emit(tasks)
                    
                    # 检查新任务
                    current_task_ids = {t.id for t in tasks}
                    if not self._first_run:
                        new_ids = current_task_ids - self._known_task_ids
                        for task in tasks:
                            if task.id in new_ids:
                                self.new_task_received.emit(task)
                                notification_service.show_new_task(task.title)
                    
                    self._known_task_ids = current_task_ids
                    
                    # 获取通知
                    notifications = api_client.get_notifications()
                    for notif in notifications:
                        if notif.id not in self._known_notification_ids:
                            self._known_notification_ids.add(notif.id)
                            if not self._first_run:
                                self.notification_received.emit(notif)
                                if notif.type == "task_urgent":
                                    notification_service.show_task_urgent(notif.content)
                    
                    self._first_run = False
                    
            except APIError as e:
                self.error_occurred.emit(str(e))
            except Exception as e:
                self.error_occurred.emit(f"轮询错误: {str(e)}")
            
            # 等待下一次轮询
            for _ in range(PollerConfig.INTERVAL_SECONDS):
                if not self._running:
                    break
                time.sleep(1)
    
    def stop(self):
        """停止轮询"""
        self._running = False
        self.wait()


class TaskPoller:
    """任务轮询管理器"""
    
    def __init__(self):
        self._thread: TaskPollerThread = None
    
    def start(self):
        """启动轮询"""
        if self._thread is None or not self._thread.isRunning():
            self._thread = TaskPollerThread()
            self._thread.start()
        return self._thread
    
    def stop(self):
        """停止轮询"""
        if self._thread and self._thread.isRunning():
            self._thread.stop()
            self._thread = None
    
    def get_thread(self) -> TaskPollerThread:
        """获取轮询线程"""
        return self._thread


# 全局轮询管理器
task_poller = TaskPoller()
