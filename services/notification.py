"""
通知服务 - 系统桌面通知
"""
import platform
from typing import Callable, Optional

# 尝试导入通知库
try:
    from plyer import notification as plyer_notification
    HAS_PLYER = True
except ImportError:
    HAS_PLYER = False


class NotificationService:
    """通知服务"""
    
    def __init__(self):
        self.app_name = "电商详情页管理系统"
        self._callback: Optional[Callable] = None
    
    def set_callback(self, callback: Callable):
        """设置通知点击回调"""
        self._callback = callback
    
    def show(self, title: str, message: str, timeout: int = 10):
        """显示桌面通知"""
        if HAS_PLYER:
            try:
                plyer_notification.notify(
                    title=title,
                    message=message,
                    app_name=self.app_name,
                    timeout=timeout
                )
            except Exception as e:
                print(f"通知显示失败: {e}")
        else:
            # 降级处理：打印到控制台
            print(f"[通知] {title}: {message}")
    
    def show_new_task(self, task_title: str):
        """显示新任务通知"""
        self.show(
            title="新任务分配",
            message=f"您有一个新任务：{task_title}",
            timeout=15
        )
    
    def show_task_urgent(self, task_title: str):
        """显示任务催促通知"""
        self.show(
            title="任务催促",
            message=f"任务「{task_title}」即将到期，请尽快完成",
            timeout=15
        )
    
    def show_review_result(self, task_title: str, approved: bool):
        """显示审核结果通知"""
        if approved:
            self.show(
                title="审核通过",
                message=f"任务「{task_title}」已通过审核",
                timeout=10
            )
        else:
            self.show(
                title="审核未通过",
                message=f"任务「{task_title}」需要修改，请查看审核意见",
                timeout=15
            )


# 全局通知服务实例
notification_service = NotificationService()
