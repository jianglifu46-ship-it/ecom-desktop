"""
画布核心类 - 管理图层和分屏
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from PIL import Image
import uuid
import json
import os

from .layer import Layer, ImageLayer, TextLayer, ShapeLayer, create_layer_from_dict


@dataclass
class Screen:
    """分屏"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "分屏"
    height: int = 300
    is_blank: bool = False  # 是否为留白
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'height': self.height,
            'is_blank': self.is_blank,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Screen':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', '分屏'),
            height=data.get('height', 300),
            is_blank=data.get('is_blank', False),
        )


class Canvas:
    """画布类"""
    
    def __init__(self, width: int = 750, height: int = 1000):
        self.width = width
        self.height = height
        self.background_color = "#FFFFFF"
        self.layers: List[Layer] = []
        self.screens: List[Screen] = []
        self.selected_layer_id: Optional[str] = None
        self.selected_screen_id: Optional[str] = None
        
        # 初始化默认分屏
        self._init_default_screens()
    
    def _init_default_screens(self):
        """初始化默认分屏"""
        self.screens = [
            Screen(name="第1屏 - 首屏", height=400),
            Screen(name="第2屏 - 产品展示", height=350),
            Screen(name="第3屏 - 卖点介绍", height=350),
        ]
        self._update_canvas_height()
    
    def _update_canvas_height(self):
        """根据分屏更新画布高度"""
        self.height = sum(s.height for s in self.screens)
    
    # ========== 图层操作 ==========
    
    def add_layer(self, layer: Layer, index: int = None) -> Layer:
        """添加图层"""
        if index is None:
            self.layers.append(layer)
        else:
            self.layers.insert(index, layer)
        return layer
    
    def remove_layer(self, layer_id: str) -> bool:
        """删除图层"""
        for i, layer in enumerate(self.layers):
            if layer.id == layer_id:
                self.layers.pop(i)
                if self.selected_layer_id == layer_id:
                    self.selected_layer_id = None
                return True
        return False
    
    def get_layer(self, layer_id: str) -> Optional[Layer]:
        """获取图层"""
        for layer in self.layers:
            if layer.id == layer_id:
                return layer
        return None
    
    def get_layer_index(self, layer_id: str) -> int:
        """获取图层索引"""
        for i, layer in enumerate(self.layers):
            if layer.id == layer_id:
                return i
        return -1
    
    def move_layer(self, layer_id: str, new_index: int) -> bool:
        """移动图层顺序"""
        layer = self.get_layer(layer_id)
        if layer:
            self.layers.remove(layer)
            self.layers.insert(max(0, min(new_index, len(self.layers))), layer)
            return True
        return False
    
    def move_layer_up(self, layer_id: str) -> bool:
        """图层上移"""
        index = self.get_layer_index(layer_id)
        if index < len(self.layers) - 1:
            return self.move_layer(layer_id, index + 1)
        return False
    
    def move_layer_down(self, layer_id: str) -> bool:
        """图层下移"""
        index = self.get_layer_index(layer_id)
        if index > 0:
            return self.move_layer(layer_id, index - 1)
        return False
    
    def move_layer_to_top(self, layer_id: str) -> bool:
        """图层置顶"""
        return self.move_layer(layer_id, len(self.layers))
    
    def move_layer_to_bottom(self, layer_id: str) -> bool:
        """图层置底"""
        return self.move_layer(layer_id, 0)
    
    def duplicate_layer(self, layer_id: str) -> Optional[Layer]:
        """复制图层"""
        layer = self.get_layer(layer_id)
        if layer:
            data = layer.to_dict()
            data['id'] = str(uuid.uuid4())
            data['name'] = f"{layer.name} 副本"
            data['x'] += 20
            data['y'] += 20
            new_layer = create_layer_from_dict(data)
            index = self.get_layer_index(layer_id)
            self.add_layer(new_layer, index + 1)
            return new_layer
        return None
    
    def select_layer(self, layer_id: str):
        """选择图层"""
        self.selected_layer_id = layer_id
    
    def get_selected_layer(self) -> Optional[Layer]:
        """获取选中的图层"""
        if self.selected_layer_id:
            return self.get_layer(self.selected_layer_id)
        return None
    
    def get_layer_at_point(self, x: int, y: int) -> Optional[Layer]:
        """获取指定位置的图层（从上到下）"""
        for layer in reversed(self.layers):
            if layer.visible and not layer.locked and layer.contains_point(x, y):
                return layer
        return None
    
    # ========== 分屏操作 ==========
    
    def add_screen(self, name: str = None, height: int = 300, index: int = None, is_blank: bool = False) -> Screen:
        """添加分屏"""
        screen_num = len([s for s in self.screens if not s.is_blank]) + 1
        if name is None:
            name = "留白" if is_blank else f"第{screen_num}屏"
        
        screen = Screen(name=name, height=height, is_blank=is_blank)
        
        if index is None:
            self.screens.append(screen)
        else:
            self.screens.insert(index, screen)
        
        self._update_canvas_height()
        self._renumber_screens()
        return screen
    
    def remove_screen(self, screen_id: str) -> bool:
        """删除分屏"""
        if len(self.screens) <= 1:
            return False  # 至少保留一个分屏
        
        for i, screen in enumerate(self.screens):
            if screen.id == screen_id:
                self.screens.pop(i)
                self._update_canvas_height()
                self._renumber_screens()
                return True
        return False
    
    def get_screen(self, screen_id: str) -> Optional[Screen]:
        """获取分屏"""
        for screen in self.screens:
            if screen.id == screen_id:
                return screen
        return None
    
    def get_screen_index(self, screen_id: str) -> int:
        """获取分屏索引"""
        for i, screen in enumerate(self.screens):
            if screen.id == screen_id:
                return i
        return -1
    
    def resize_screen(self, screen_id: str, new_height: int) -> bool:
        """调整分屏高度"""
        screen = self.get_screen(screen_id)
        if screen:
            screen.height = max(50, new_height)  # 最小高度 50px
            self._update_canvas_height()
            return True
        return False
    
    def insert_screen_above(self, screen_id: str, is_blank: bool = False) -> Optional[Screen]:
        """在指定分屏上方插入新屏"""
        index = self.get_screen_index(screen_id)
        if index >= 0:
            return self.add_screen(index=index, is_blank=is_blank)
        return None
    
    def insert_screen_below(self, screen_id: str, is_blank: bool = False) -> Optional[Screen]:
        """在指定分屏下方插入新屏"""
        index = self.get_screen_index(screen_id)
        if index >= 0:
            return self.add_screen(index=index + 1, is_blank=is_blank)
        return None
    
    def duplicate_screen(self, screen_id: str) -> Optional[Screen]:
        """复制分屏"""
        screen = self.get_screen(screen_id)
        if screen:
            index = self.get_screen_index(screen_id)
            new_screen = Screen(
                name=f"{screen.name} 副本",
                height=screen.height,
                is_blank=screen.is_blank
            )
            self.screens.insert(index + 1, new_screen)
            self._update_canvas_height()
            self._renumber_screens()
            return new_screen
        return None
    
    def _renumber_screens(self):
        """重新编号分屏"""
        num = 1
        for screen in self.screens:
            if not screen.is_blank:
                if not screen.name.startswith("第") or "副本" in screen.name:
                    continue
                # 保持用户自定义名称的后缀
                parts = screen.name.split(" - ", 1)
                suffix = parts[1] if len(parts) > 1 else ""
                screen.name = f"第{num}屏" + (f" - {suffix}" if suffix else "")
                num += 1
    
    def get_screen_y_offset(self, screen_id: str) -> int:
        """获取分屏的 Y 偏移量"""
        offset = 0
        for screen in self.screens:
            if screen.id == screen_id:
                return offset
            offset += screen.height
        return offset
    
    def get_screen_at_y(self, y: int) -> Optional[Screen]:
        """获取指定 Y 坐标所在的分屏"""
        offset = 0
        for screen in self.screens:
            if offset <= y < offset + screen.height:
                return screen
            offset += screen.height
        return None
    
    # ========== 渲染 ==========
    
    def render(self, scale: float = 1.0) -> Image.Image:
        """渲染整个画布"""
        # 创建画布
        canvas_width = int(self.width * scale)
        canvas_height = int(self.height * scale)
        canvas = Image.new("RGBA", (canvas_width, canvas_height), self.background_color)
        
        # 渲染每个图层
        for layer in self.layers:
            if not layer.visible:
                continue
            
            layer_img = layer.render(scale)
            if layer_img:
                # 计算位置
                x = int(layer.x * scale)
                y = int(layer.y * scale)
                
                # 调整图层大小
                if scale != 1.0:
                    new_w = int(layer_img.width * scale)
                    new_h = int(layer_img.height * scale)
                    if new_w > 0 and new_h > 0:
                        layer_img = layer_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # 粘贴图层
                try:
                    canvas.paste(layer_img, (x, y), layer_img)
                except Exception as e:
                    print(f"渲染图层失败: {e}")
        
        return canvas
    
    def render_screen(self, screen_id: str, scale: float = 1.0) -> Optional[Image.Image]:
        """渲染单个分屏"""
        screen = self.get_screen(screen_id)
        if not screen:
            return None
        
        y_offset = self.get_screen_y_offset(screen_id)
        
        # 渲染完整画布
        full_canvas = self.render(scale)
        
        # 裁剪分屏区域
        top = int(y_offset * scale)
        bottom = int((y_offset + screen.height) * scale)
        screen_img = full_canvas.crop((0, top, int(self.width * scale), bottom))
        
        return screen_img
    
    # ========== 导出 ==========
    
    def export_screens(self, output_dir: str, format: str = "jpg", quality: int = 95) -> List[str]:
        """按分屏导出"""
        output_files = []
        
        for i, screen in enumerate(self.screens):
            if screen.is_blank:
                continue  # 跳过留白
            
            screen_img = self.render_screen(screen.id)
            if screen_img:
                # 转换格式
                if format.lower() == "jpg":
                    screen_img = screen_img.convert("RGB")
                
                # 生成文件名
                safe_name = screen.name.replace(" ", "_").replace("/", "_")
                filename = f"screen_{i+1:02d}_{safe_name}.{format}"
                output_path = os.path.join(output_dir, filename)
                
                # 保存
                if format.lower() == "jpg":
                    screen_img.save(output_path, "JPEG", quality=quality)
                else:
                    screen_img.save(output_path, format.upper())
                
                output_files.append(output_path)
        
        return output_files
    
    def export_full(self, output_path: str, format: str = "jpg", quality: int = 95) -> str:
        """导出完整画布"""
        canvas = self.render()
        
        if format.lower() == "jpg":
            canvas = canvas.convert("RGB")
            canvas.save(output_path, "JPEG", quality=quality)
        else:
            canvas.save(output_path, format.upper())
        
        return output_path
    
    # ========== 序列化 ==========
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'width': self.width,
            'height': self.height,
            'background_color': self.background_color,
            'layers': [layer.to_dict() for layer in self.layers],
            'screens': [screen.to_dict() for screen in self.screens],
            'selected_layer_id': self.selected_layer_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Canvas':
        """从字典创建"""
        canvas = cls(
            width=data.get('width', 750),
            height=data.get('height', 1000)
        )
        canvas.background_color = data.get('background_color', '#FFFFFF')
        canvas.selected_layer_id = data.get('selected_layer_id')
        
        # 加载图层
        canvas.layers = []
        for layer_data in data.get('layers', []):
            layer = create_layer_from_dict(layer_data)
            canvas.layers.append(layer)
        
        # 加载分屏
        canvas.screens = []
        for screen_data in data.get('screens', []):
            screen = Screen.from_dict(screen_data)
            canvas.screens.append(screen)
        
        if not canvas.screens:
            canvas._init_default_screens()
        
        return canvas
    
    def save(self, filepath: str):
        """保存到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'Canvas':
        """从文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    # ========== 辅助方法 ==========
    
    def add_image_layer(self, image_path: str, x: int = 0, y: int = 0) -> ImageLayer:
        """添加图片图层"""
        layer = ImageLayer(image_path=image_path, x=x, y=y)
        layer.load_image()
        layer.name = f"图片: {os.path.basename(image_path)}"
        self.add_layer(layer)
        return layer
    
    def add_text_layer(self, text: str, x: int = 0, y: int = 0, font_size: int = 24, color: str = "#000000") -> TextLayer:
        """添加文字图层"""
        layer = TextLayer(text=text, x=x, y=y, font_size=font_size, font_color=color)
        layer.update_size_from_text()
        layer.name = f"文字: {text[:10]}"
        self.add_layer(layer)
        return layer
    
    def add_shape_layer(self, shape_type: str, x: int = 0, y: int = 0, width: int = 100, height: int = 100) -> ShapeLayer:
        """添加形状图层"""
        layer = ShapeLayer(shape_type=shape_type, x=x, y=y, width=width, height=height)
        self.add_layer(layer)
        return layer
