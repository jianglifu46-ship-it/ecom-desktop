"""
图片增强工具 - 使用 OpenCV 和 Pillow
延迟加载避免打包问题
"""
from typing import Optional
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

# 延迟检查 OpenCV
_opencv_checked = False
_has_opencv = False
_cv2 = None


def _check_opencv():
    """延迟检查 OpenCV 是否可用"""
    global _opencv_checked, _has_opencv, _cv2
    if _opencv_checked:
        return _has_opencv
    
    _opencv_checked = True
    try:
        import cv2
        _cv2 = cv2
        _has_opencv = True
    except ImportError:
        _has_opencv = False
    except Exception:
        _has_opencv = False
    
    return _has_opencv


def enhance_image(image: Image.Image, mode: str = "auto") -> Image.Image:
    """
    增强图片质量
    
    Args:
        image: PIL Image 对象
        mode: "auto" | "sharpen" | "denoise" | "contrast" | "brightness"
    
    Returns:
        处理后的 PIL Image 对象
    """
    if _check_opencv():
        return _enhance_opencv(image, mode)
    else:
        return _enhance_pillow(image, mode)


def _enhance_opencv(image: Image.Image, mode: str) -> Image.Image:
    """使用 OpenCV 增强"""
    cv2 = _cv2
    # PIL 转 OpenCV
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    if mode == "sharpen":
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        result = cv2.filter2D(img, -1, kernel)
    
    elif mode == "denoise":
        result = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
    
    elif mode == "contrast":
        # 自适应直方图均衡
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    elif mode == "brightness":
        # 增加亮度
        result = cv2.convertScaleAbs(img, alpha=1.2, beta=20)
    
    else:  # auto - 综合优化
        # 1. 轻微降噪
        img = cv2.fastNlMeansDenoisingColored(img, None, 5, 5, 7, 21)
        # 2. 对比度增强
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        # 3. 轻微锐化
        kernel = np.array([[0, -0.5, 0], [-0.5, 3, -0.5], [0, -0.5, 0]])
        result = cv2.filter2D(img, -1, kernel)
    
    # OpenCV 转 PIL
    result = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    return Image.fromarray(result)


def _enhance_pillow(image: Image.Image, mode: str) -> Image.Image:
    """使用 Pillow 增强（备用方案）"""
    if mode == "sharpen":
        return image.filter(ImageFilter.SHARPEN)
    
    elif mode == "denoise":
        # Pillow 没有专门的降噪，使用轻微模糊
        return image.filter(ImageFilter.SMOOTH)
    
    elif mode == "contrast":
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(1.3)
    
    elif mode == "brightness":
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(1.2)
    
    else:  # auto
        # 综合增强
        img = image.filter(ImageFilter.SMOOTH_MORE)
        img = ImageEnhance.Contrast(img).enhance(1.2)
        img = ImageEnhance.Sharpness(img).enhance(1.3)
        return img


def adjust_color(image: Image.Image, saturation: float = 1.0, 
                 brightness: float = 1.0, contrast: float = 1.0) -> Image.Image:
    """
    调整颜色
    
    Args:
        image: PIL Image 对象
        saturation: 饱和度 (0.0-2.0, 1.0 为原始)
        brightness: 亮度 (0.0-2.0, 1.0 为原始)
        contrast: 对比度 (0.0-2.0, 1.0 为原始)
    
    Returns:
        处理后的图片
    """
    result = image
    
    if saturation != 1.0:
        enhancer = ImageEnhance.Color(result)
        result = enhancer.enhance(saturation)
    
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(result)
        result = enhancer.enhance(brightness)
    
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(result)
        result = enhancer.enhance(contrast)
    
    return result


def apply_filter(image: Image.Image, filter_name: str) -> Image.Image:
    """
    应用滤镜
    
    Args:
        image: PIL Image 对象
        filter_name: 滤镜名称
    
    Returns:
        处理后的图片
    """
    filters = {
        "blur": ImageFilter.BLUR,
        "contour": ImageFilter.CONTOUR,
        "detail": ImageFilter.DETAIL,
        "edge_enhance": ImageFilter.EDGE_ENHANCE,
        "emboss": ImageFilter.EMBOSS,
        "sharpen": ImageFilter.SHARPEN,
        "smooth": ImageFilter.SMOOTH,
    }
    
    if filter_name in filters:
        return image.filter(filters[filter_name])
    
    return image


def batch_enhance(input_paths: list, output_dir: str, mode: str = "auto",
                  callback=None) -> list:
    """
    批量增强图片
    
    Args:
        input_paths: 输入图片路径列表
        output_dir: 输出目录
        mode: 增强模式
        callback: 进度回调函数
    
    Returns:
        输出文件路径列表
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    results = []
    total = len(input_paths)
    
    for i, path in enumerate(input_paths):
        try:
            filename = os.path.basename(path)
            name, ext = os.path.splitext(filename)
            output_path = os.path.join(output_dir, f"{name}_enhanced{ext}")
            
            img = Image.open(path)
            result = enhance_image(img, mode)
            result.save(output_path)
            results.append(output_path)
            
            if callback:
                callback(i + 1, total, filename)
                
        except Exception as e:
            print(f"处理 {path} 失败: {e}")
    
    return results


def is_opencv_available() -> bool:
    """检查 OpenCV 是否可用"""
    return _check_opencv()
