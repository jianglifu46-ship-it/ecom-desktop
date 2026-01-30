"""
图层基类和通用图层类型
"""
from dataclasses import dataclass, field
from typing import Optional, Tuple, Any
from PIL import Image, ImageDraw, ImageFont
import uuid
import os


# 图片导入最大尺寸限制
MAX_IMPORT_WIDTH = 600  # 最大宽度（画布宽度750的80%）
MAX_IMPORT_HEIGHT = 800  # 最大高度


@dataclass
class Layer:
    """图层基类"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "图层"
    x: int = 0
    y: int = 0
    width: int = 100
    height: int = 100
    rotation: float = 0.0
    opacity: float = 1.0
    visible: bool = True
    locked: bool = False
    layer_type: str = "base"
    
    def render(self, scale: float = 1.0) -> Optional[Image.Image]:
        """渲染图层，子类实现"""
        return None
    
    def get_bounds(self) -> Tuple[int, int, int, int]:
        """获取边界框 (x, y, x+width, y+height)"""
        return (self.x, self.y, self.x + self.width, self.y + self.height)
    
    def contains_point(self, px: int, py: int) -> bool:
        """检查点是否在图层内"""
        return (self.x <= px <= self.x + self.width and 
                self.y <= py <= self.y + self.height)
    
    def move(self, dx: int, dy: int):
        """移动图层"""
        self.x += dx
        self.y += dy
    
    def resize(self, new_width: int, new_height: int):
        """调整大小"""
        self.width = max(1, new_width)
        self.height = max(1, new_height)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'rotation': self.rotation,
            'opacity': self.opacity,
            'visible': self.visible,
            'locked': self.locked,
            'layer_type': self.layer_type,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Layer':
        """从字典创建"""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', '图层'),
            x=data.get('x', 0),
            y=data.get('y', 0),
            width=data.get('width', 100),
            height=data.get('height', 100),
            rotation=data.get('rotation', 0.0),
            opacity=data.get('opacity', 1.0),
            visible=data.get('visible', True),
            locked=data.get('locked', False),
            layer_type=data.get('layer_type', 'base'),
        )


@dataclass
class ImageLayer(Layer):
    """图片图层"""
    image_path: str = ""
    _image: Optional[Image.Image] = field(default=None, repr=False)
    _render_cache: Optional[Image.Image] = field(default=None, repr=False)
    _cache_key: str = field(default="", repr=False)
    layer_type: str = "image"
    
    def __post_init__(self):
        if self.name == "图层":
            self.name = "图片图层"
    
    def _invalidate_cache(self):
        """清除缓存"""
        self._render_cache = None
        self._cache_key = ""
    
    def _get_cache_key(self) -> str:
        """生成缓存键"""
        return f"{self.width}_{self.height}_{self.rotation}_{self.opacity}"
    
    def load_image(self, auto_resize: bool = True) -> bool:
        """加载图片，可选自动缩放到合适尺寸"""
        if self.image_path and os.path.exists(self.image_path):
            try:
                self._image = Image.open(self.image_path).convert("RGBA")
                orig_w, orig_h = self._image.width, self._image.height
                
                # 自动缩放大图
                if auto_resize and (orig_w > MAX_IMPORT_WIDTH or orig_h > MAX_IMPORT_HEIGHT):
                    ratio_w = MAX_IMPORT_WIDTH / orig_w
                    ratio_h = MAX_IMPORT_HEIGHT / orig_h
                    ratio = min(ratio_w, ratio_h)
                    
                    new_w = int(orig_w * ratio)
                    new_h = int(orig_h * ratio)
                    
                    self._image = self._image.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    self.width = new_w
                    self.height = new_h
                else:
                    self.width = self._image.width
                    self.height = self._image.height
                
                self._invalidate_cache()
                return True
            except Exception as e:
                print(f"加载图片失败: {e}")
        return False
    
    def set_image(self, image: Image.Image, auto_resize: bool = True):
        """直接设置图片，可选自动缩放"""
        self._image = image.convert("RGBA")
        orig_w, orig_h = self._image.width, self._image.height
        
        # 自动缩放大图
        if auto_resize and (orig_w > MAX_IMPORT_WIDTH or orig_h > MAX_IMPORT_HEIGHT):
            ratio_w = MAX_IMPORT_WIDTH / orig_w
            ratio_h = MAX_IMPORT_HEIGHT / orig_h
            ratio = min(ratio_w, ratio_h)
            
            new_w = int(orig_w * ratio)
            new_h = int(orig_h * ratio)
            
            self._image = self._image.resize((new_w, new_h), Image.Resampling.LANCZOS)
            self.width = new_w
            self.height = new_h
        else:
            self.width = self._image.width
            self.height = self._image.height
        
        self._invalidate_cache()
    
    def render(self, scale: float = 1.0) -> Optional[Image.Image]:
        """渲染图片图层（带缓存）"""
        if self._image is None:
            self.load_image()
        
        if self._image is None:
            return None
        
        # 检查缓存
        cache_key = self._get_cache_key()
        if self._render_cache is not None and self._cache_key == cache_key:
            return self._render_cache
        
        # 缩放
        if self.width != self._image.width or self.height != self._image.height:
            img = self._image.resize((self.width, self.height), Image.Resampling.LANCZOS)
        else:
            img = self._image.copy()
        
        # 旋转
        if self.rotation != 0:
            img = img.rotate(-self.rotation, expand=True, resample=Image.Resampling.BICUBIC)
        
        # 透明度
        if self.opacity < 1.0:
            alpha = img.split()[3]
            alpha = alpha.point(lambda x: int(x * self.opacity))
            img.putalpha(alpha)
        
        # 更新缓存
        self._render_cache = img
        self._cache_key = cache_key
        
        return img
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data['image_path'] = self.image_path
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ImageLayer':
        layer = cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', '图片图层'),
            x=data.get('x', 0),
            y=data.get('y', 0),
            width=data.get('width', 100),
            height=data.get('height', 100),
            rotation=data.get('rotation', 0.0),
            opacity=data.get('opacity', 1.0),
            visible=data.get('visible', True),
            locked=data.get('locked', False),
            image_path=data.get('image_path', ''),
        )
        return layer


@dataclass
class TextLayer(Layer):
    """文字图层"""
    text: str = "文本"
    font_family: str = "Arial"
    font_size: int = 24
    font_color: str = "#000000"
    font_weight: str = "normal"  # normal, bold
    text_align: str = "left"  # left, center, right
    line_height: float = 1.5
    layer_type: str = "text"
    _render_cache: Optional[Image.Image] = field(default=None, repr=False)
    _cache_key: str = field(default="", repr=False)
    
    def __post_init__(self):
        if self.name == "图层":
            self.name = f"文字: {self.text[:10]}"
    
    def _get_cache_key(self) -> str:
        """生成缓存键"""
        return f"{self.text}_{self.font_size}_{self.font_color}_{self.width}_{self.height}_{self.rotation}_{self.opacity}"
    
    def render(self, scale: float = 1.0) -> Optional[Image.Image]:
        """渲染文字图层（带缓存）"""
        cache_key = self._get_cache_key()
        if self._render_cache is not None and self._cache_key == cache_key:
            return self._render_cache
        
        # 创建透明背景
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 加载字体
        try:
            font_path = self._get_font_path()
            font = ImageFont.truetype(font_path, self.font_size)
        except:
            font = ImageFont.load_default()
        
        # 解析颜色
        color = self._hex_to_rgba(self.font_color)
        
        # 绘制文字
        draw.text((0, 0), self.text, fill=color, font=font)
        
        # 旋转
        if self.rotation != 0:
            img = img.rotate(-self.rotation, expand=True, resample=Image.Resampling.BICUBIC)
        
        # 透明度
        if self.opacity < 1.0:
            alpha = img.split()[3]
            alpha = alpha.point(lambda x: int(x * self.opacity))
            img.putalpha(alpha)
        
        # 更新缓存
        self._render_cache = img
        self._cache_key = cache_key
        
        return img
    
    def _get_font_path(self) -> str:
        """获取字体路径"""
        # 常用字体映射
        font_map = {
            "Arial": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "微软雅黑": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "宋体": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        }
        return font_map.get(self.font_family, "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    
    def _hex_to_rgba(self, hex_color: str) -> Tuple[int, int, int, int]:
        """十六进制颜色转 RGBA"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return (r, g, b, 255)
        elif len(hex_color) == 8:
            r, g, b, a = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16), int(hex_color[6:8], 16)
            return (r, g, b, a)
        return (0, 0, 0, 255)
    
    def update_size_from_text(self):
        """根据文字内容更新尺寸"""
        try:
            font_path = self._get_font_path()
            font = ImageFont.truetype(font_path, self.font_size)
            bbox = font.getbbox(self.text)
            self.width = bbox[2] - bbox[0] + 10
            self.height = bbox[3] - bbox[1] + 10
        except:
            self.width = len(self.text) * self.font_size
            self.height = int(self.font_size * self.line_height)
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            'text': self.text,
            'font_family': self.font_family,
            'font_size': self.font_size,
            'font_color': self.font_color,
            'font_weight': self.font_weight,
            'text_align': self.text_align,
            'line_height': self.line_height,
        })
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TextLayer':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', '文字图层'),
            x=data.get('x', 0),
            y=data.get('y', 0),
            width=data.get('width', 100),
            height=data.get('height', 50),
            rotation=data.get('rotation', 0.0),
            opacity=data.get('opacity', 1.0),
            visible=data.get('visible', True),
            locked=data.get('locked', False),
            text=data.get('text', '文本'),
            font_family=data.get('font_family', 'Arial'),
            font_size=data.get('font_size', 24),
            font_color=data.get('font_color', '#000000'),
            font_weight=data.get('font_weight', 'normal'),
            text_align=data.get('text_align', 'left'),
            line_height=data.get('line_height', 1.5),
        )


@dataclass
class ShapeLayer(Layer):
    """形状图层"""
    shape_type: str = "rectangle"  # rectangle, ellipse, line
    fill_color: str = "#cccccc"
    stroke_color: str = "#000000"
    stroke_width: int = 1
    layer_type: str = "shape"
    _render_cache: Optional[Image.Image] = field(default=None, repr=False)
    _cache_key: str = field(default="", repr=False)
    
    def __post_init__(self):
        if self.name == "图层":
            shape_names = {"rectangle": "矩形", "ellipse": "椭圆", "line": "线条"}
            self.name = f"形状: {shape_names.get(self.shape_type, '形状')}"
    
    def _get_cache_key(self) -> str:
        """生成缓存键"""
        return f"{self.shape_type}_{self.fill_color}_{self.stroke_color}_{self.stroke_width}_{self.width}_{self.height}_{self.rotation}_{self.opacity}"
    
    def render(self, scale: float = 1.0) -> Optional[Image.Image]:
        """渲染形状图层（带缓存）"""
        cache_key = self._get_cache_key()
        if self._render_cache is not None and self._cache_key == cache_key:
            return self._render_cache
        
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        fill = self._hex_to_rgba(self.fill_color)
        stroke = self._hex_to_rgba(self.stroke_color) if self.stroke_width > 0 else None
        
        if self.shape_type == "rectangle":
            draw.rectangle(
                [0, 0, self.width - 1, self.height - 1],
                fill=fill,
                outline=stroke,
                width=self.stroke_width
            )
        elif self.shape_type == "ellipse":
            draw.ellipse(
                [0, 0, self.width - 1, self.height - 1],
                fill=fill,
                outline=stroke,
                width=self.stroke_width
            )
        elif self.shape_type == "line":
            draw.line(
                [0, self.height // 2, self.width, self.height // 2],
                fill=stroke or fill,
                width=self.stroke_width or 2
            )
        
        # 旋转
        if self.rotation != 0:
            img = img.rotate(-self.rotation, expand=True, resample=Image.Resampling.BICUBIC)
        
        # 透明度
        if self.opacity < 1.0:
            alpha = img.split()[3]
            alpha = alpha.point(lambda x: int(x * self.opacity))
            img.putalpha(alpha)
        
        # 更新缓存
        self._render_cache = img
        self._cache_key = cache_key
        
        return img
    
    def _hex_to_rgba(self, hex_color: str) -> Tuple[int, int, int, int]:
        """十六进制颜色转 RGBA"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return (r, g, b, 255)
        return (0, 0, 0, 255)
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            'shape_type': self.shape_type,
            'fill_color': self.fill_color,
            'stroke_color': self.stroke_color,
            'stroke_width': self.stroke_width,
        })
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ShapeLayer':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', '形状图层'),
            x=data.get('x', 0),
            y=data.get('y', 0),
            width=data.get('width', 100),
            height=data.get('height', 100),
            rotation=data.get('rotation', 0.0),
            opacity=data.get('opacity', 1.0),
            visible=data.get('visible', True),
            locked=data.get('locked', False),
            shape_type=data.get('shape_type', 'rectangle'),
            fill_color=data.get('fill_color', '#cccccc'),
            stroke_color=data.get('stroke_color', '#000000'),
            stroke_width=data.get('stroke_width', 1),
        )


def create_layer_from_dict(data: dict) -> Layer:
    """根据类型创建图层"""
    layer_type = data.get('layer_type', 'base')
    if layer_type == 'image':
        return ImageLayer.from_dict(data)
    elif layer_type == 'text':
        return TextLayer.from_dict(data)
    elif layer_type == 'shape':
        return ShapeLayer.from_dict(data)
    else:
        return Layer.from_dict(data)
