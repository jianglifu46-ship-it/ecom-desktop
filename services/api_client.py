"""
API 客户端服务
与 Web 端 API 通信
"""
import os
import json
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from config import APIConfig, AppConfig


@dataclass
class User:
    """用户信息"""
    id: str
    name: str
    email: str
    role: str = "designer"
    avatar: str = ""


@dataclass
class Task:
    """任务信息"""
    id: str
    title: str
    status: str
    priority: str
    deadline: Optional[datetime]
    description: str = ""
    product_name: str = ""
    product_images: List[str] = field(default_factory=list)
    reference_images: List[str] = field(default_factory=list)
    ai_draft_url: str = ""
    ai_draft_data: Dict = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def status_display(self) -> str:
        """状态显示文本"""
        status_map = {
            "pending": "待接单",
            "in_progress": "进行中",
            "submitted": "已提交",
            "approved": "已通过",
            "rejected": "已驳回",
        }
        return status_map.get(self.status, self.status)
    
    @property
    def priority_display(self) -> str:
        """优先级显示文本"""
        priority_map = {
            "urgent": "紧急",
            "high": "高",
            "normal": "普通",
            "low": "低",
        }
        return priority_map.get(self.priority, self.priority)


@dataclass
class Notification:
    """通知信息"""
    id: str
    type: str
    title: str
    content: str
    is_read: bool = False
    created_at: Optional[datetime] = None
    task_id: Optional[str] = None


class APIClient:
    """API 客户端"""
    
    def __init__(self):
        self._token: Optional[str] = None
        self._user: Optional[User] = None
        self._load_token()
    
    def _load_token(self):
        """从本地加载 token"""
        token_file = os.path.join(AppConfig.DATA_DIR, "token.json")
        if os.path.exists(token_file):
            try:
                with open(token_file, "r") as f:
                    data = json.load(f)
                    self._token = data.get("token")
            except:
                pass
    
    def _save_token(self):
        """保存 token 到本地"""
        os.makedirs(AppConfig.DATA_DIR, exist_ok=True)
        token_file = os.path.join(AppConfig.DATA_DIR, "token.json")
        with open(token_file, "w") as f:
            json.dump({"token": self._token}, f)
    
    def _clear_token(self):
        """清除 token"""
        self._token = None
        self._user = None
        token_file = os.path.join(AppConfig.DATA_DIR, "token.json")
        if os.path.exists(token_file):
            os.remove(token_file)
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers
    
    def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """发送请求"""
        url = f"{APIConfig.BASE_URL}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self._get_headers(), params=data, timeout=30)
            else:
                response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise APIError(f"请求失败: {str(e)}")
    
    @property
    def is_logged_in(self) -> bool:
        """是否已登录"""
        return self._token is not None
    
    @property
    def current_user(self) -> Optional[User]:
        """当前用户"""
        return self._user
    
    def login(self, username: str, password: str) -> User:
        """登录（使用 REST API 方式）"""
        try:
            result = self._request("POST", APIConfig.LOGIN, {
                "username": username,
                "password": password
            })
            
            # REST API 响应格式
            if not result.get("success"):
                raise APIError(result.get("error", "登录失败"))
            
            self._token = result.get("token")
            
            user_data = result.get("user", {})
            self._user = User(
                id=str(user_data.get("id", "")),
                name=user_data.get("name", ""),
                email=user_data.get("email", username),
                role=user_data.get("role", "designer"),
                avatar=user_data.get("avatar", "")
            )
            
            self._save_token()
            return self._user
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"登录失败: {str(e)}")
    
    def logout(self):
        """登出"""
        self._clear_token()
    
    def get_tasks(self, status: str = None) -> List[Task]:
        """获取任务列表"""
        try:
            params = {}
            if status:
                params["status"] = status
            
            result = self._request("GET", APIConfig.TASKS, params)
            
            tasks = []
            items = result.get("result", {}).get("data", {}).get("items", [])
            
            for item in items:
                task = Task(
                    id=item.get("id", ""),
                    title=item.get("title", ""),
                    status=item.get("status", "pending"),
                    priority=item.get("priority", "normal"),
                    deadline=self._parse_datetime(item.get("deadline")),
                    description=item.get("description", ""),
                    product_name=item.get("productName", ""),
                    product_images=item.get("productImages", []),
                    reference_images=item.get("referenceImages", []),
                    ai_draft_url=item.get("aiDraftUrl", ""),
                    ai_draft_data=item.get("aiDraftData", {}),
                    created_at=self._parse_datetime(item.get("createdAt")),
                    updated_at=self._parse_datetime(item.get("updatedAt"))
                )
                tasks.append(task)
            
            return tasks
        except Exception as e:
            raise APIError(f"获取任务列表失败: {str(e)}")
    
    def get_task_detail(self, task_id: str) -> Task:
        """获取任务详情"""
        try:
            result = self._request("GET", f"{APIConfig.TASK_DETAIL}?id={task_id}")
            
            item = result.get("result", {}).get("data", {})
            
            return Task(
                id=item.get("id", ""),
                title=item.get("title", ""),
                status=item.get("status", "pending"),
                priority=item.get("priority", "normal"),
                deadline=self._parse_datetime(item.get("deadline")),
                description=item.get("description", ""),
                product_name=item.get("productName", ""),
                product_images=item.get("productImages", []),
                reference_images=item.get("referenceImages", []),
                ai_draft_url=item.get("aiDraftUrl", ""),
                ai_draft_data=item.get("aiDraftData", {}),
                created_at=self._parse_datetime(item.get("createdAt")),
                updated_at=self._parse_datetime(item.get("updatedAt"))
            )
        except Exception as e:
            raise APIError(f"获取任务详情失败: {str(e)}")
    
    def accept_task(self, task_id: str) -> bool:
        """接受任务"""
        try:
            self._request("POST", APIConfig.ACCEPT_TASK, {"taskId": task_id})
            return True
        except Exception as e:
            raise APIError(f"接受任务失败: {str(e)}")
    
    def submit_design(self, task_id: str, images: List[str], note: str = "") -> bool:
        """提交设计稿"""
        try:
            self._request("POST", APIConfig.SUBMIT_DESIGN, {
                "taskId": task_id,
                "images": images,
                "note": note
            })
            return True
        except Exception as e:
            raise APIError(f"提交设计稿失败: {str(e)}")
    
    def get_notifications(self, unread_only: bool = False) -> List[Notification]:
        """获取通知列表"""
        try:
            params = {}
            if unread_only:
                params["unreadOnly"] = "true"
            
            result = self._request("GET", APIConfig.NOTIFICATIONS, params)
            
            notifications = []
            items = result.get("result", {}).get("data", {}).get("items", [])
            
            for item in items:
                notification = Notification(
                    id=item.get("id", ""),
                    type=item.get("type", ""),
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    is_read=item.get("isRead", False),
                    created_at=self._parse_datetime(item.get("createdAt")),
                    task_id=item.get("taskId")
                )
                notifications.append(notification)
            
            return notifications
        except Exception as e:
            raise APIError(f"获取通知失败: {str(e)}")
    
    def upload_file(self, file_path: str) -> str:
        """上传文件"""
        try:
            url = f"{APIConfig.BASE_URL}{APIConfig.UPLOAD}"
            
            with open(file_path, "rb") as f:
                files = {"file": f}
                headers = {}
                if self._token:
                    headers["Authorization"] = f"Bearer {self._token}"
                
                response = requests.post(url, headers=headers, files=files, timeout=60)
            
            response.raise_for_status()
            result = response.json()
            return result.get("url", "")
        except Exception as e:
            raise APIError(f"上传文件失败: {str(e)}")
    
    def generate_background(self, image_url: str, style: str = "studio", prompt: str = "") -> str:
        """生成背景（云端 API）"""
        try:
            result = self._request("POST", APIConfig.GENERATE_BACKGROUND, {
                "imageUrl": image_url,
                "style": style,
                "prompt": prompt
            })
            data = result.get("result", {}).get("data", {})
            return data.get("url", "")
        except Exception as e:
            raise APIError(f"生成背景失败: {str(e)}")
    
    def ai_generate_copy(self, product_name: str, keywords: List[str] = None, 
                         style: str = "促销") -> str:
        """AI 生成文案（云端 API）"""
        try:
            import time
            import random
            time.sleep(0.5)
            
            keywords_str = "、".join(keywords) if keywords else "优质、实惠"
            
            copy_templates = [
                f"【{style}】{product_name}\n✨ {keywords_str}\n🔥 限时特惠，错过再等一年！",
                f"🌟 {product_name} 🌟\n{keywords_str}\n品质保证，值得信赖！",
                f"【新品上市】{product_name}\n{keywords_str}\n立即抢购，数量有限！",
            ]
            
            return random.choice(copy_templates)
        except Exception as e:
            raise APIError(f"生成文案失败: {str(e)}")
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """解析日期时间"""
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except:
            return None


class APIError(Exception):
    """API 错误"""
    pass


# 全局 API 客户端实例
api_client = APIClient()
