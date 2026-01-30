"""
图像处理工具模块
使用延迟导入避免依赖问题
"""

# 延迟导入函数
def remove_background(*args, **kwargs):
    from .remove_bg import remove_background as _func
    return _func(*args, **kwargs)

def remove_background_from_image(*args, **kwargs):
    from .remove_bg import remove_background_from_image as _func
    return _func(*args, **kwargs)

def batch_remove_background(*args, **kwargs):
    from .remove_bg import batch_remove_background as _func
    return _func(*args, **kwargs)

def is_rembg_available():
    from .remove_bg import is_available
    return is_available()

def upscale_image(*args, **kwargs):
    from .upscale import upscale_image as _func
    return _func(*args, **kwargs)

def upscale_image_pillow(*args, **kwargs):
    from .upscale import upscale_image_pillow as _func
    return _func(*args, **kwargs)

def batch_upscale(*args, **kwargs):
    from .upscale import batch_upscale as _func
    return _func(*args, **kwargs)

def is_realesrgan_available():
    from .upscale import is_available
    return is_available()

def enhance_image(*args, **kwargs):
    from .enhance import enhance_image as _func
    return _func(*args, **kwargs)

def adjust_color(*args, **kwargs):
    from .enhance import adjust_color as _func
    return _func(*args, **kwargs)

def apply_filter(*args, **kwargs):
    from .enhance import apply_filter as _func
    return _func(*args, **kwargs)

def batch_enhance(*args, **kwargs):
    from .enhance import batch_enhance as _func
    return _func(*args, **kwargs)

def is_opencv_available():
    from .enhance import is_opencv_available as _func
    return _func()

__all__ = [
    'remove_background', 'remove_background_from_image', 'batch_remove_background', 'is_rembg_available',
    'upscale_image', 'upscale_image_pillow', 'batch_upscale', 'is_realesrgan_available',
    'enhance_image', 'adjust_color', 'apply_filter', 'batch_enhance', 'is_opencv_available',
]
