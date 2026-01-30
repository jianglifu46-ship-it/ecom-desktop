"""
智能抠图工具 - 使用 Rembg
延迟加载避免打包问题
"""
import os
import io
from typing import Optional, List
from PIL import Image

# 延迟检查 rembg 是否可用
_rembg_checked = False
_has_rembg = False
_remove_func = None


def _check_rembg():
    """延迟检查 rembg 是否可用"""
    global _rembg_checked, _has_rembg, _remove_func
    if _rembg_checked:
        return _has_rembg
    
    _rembg_checked = True
    try:
        from rembg import remove
        _remove_func = remove
        _has_rembg = True
    except ImportError:
        _has_rembg = False
    except Exception:
        _has_rembg = False
    
    return _has_rembg


def remove_background(input_path: str, output_path: str = None) -> Optional[Image.Image]:
    """
    移除图片背景
    
    Args:
        input_path: 输入图片路径
        output_path: 输出路径（可选）
    
    Returns:
        处理后的 PIL Image 对象，失败返回 None
    """
    if not _check_rembg():
        print("抠图功能不可用，请安装 rembg: pip install rembg[gpu] 或 pip install rembg")
        return None
    
    try:
        with open(input_path, 'rb') as f:
            input_data = f.read()
        
        output_data = _remove_func(input_data)
        result = Image.open(io.BytesIO(output_data))
        
        if output_path:
            result.save(output_path, "PNG")
        
        return result
    except Exception as e:
        print(f"抠图失败: {e}")
        return None


def remove_background_from_image(image: Image.Image) -> Optional[Image.Image]:
    """
    从 PIL Image 对象移除背景
    
    Args:
        image: PIL Image 对象
    
    Returns:
        处理后的 PIL Image 对象
    """
    if not _check_rembg():
        return None
    
    try:
        # 转换为字节
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        input_data = buffer.getvalue()
        
        output_data = _remove_func(input_data)
        result = Image.open(io.BytesIO(output_data))
        
        return result
    except Exception as e:
        print(f"抠图失败: {e}")
        return None


def batch_remove_background(input_paths: List[str], output_dir: str, 
                            callback=None) -> List[str]:
    """
    批量抠图
    
    Args:
        input_paths: 输入图片路径列表
        output_dir: 输出目录
        callback: 进度回调函数 callback(current, total, filename)
    
    Returns:
        输出文件路径列表
    """
    if not _check_rembg():
        return []
    
    os.makedirs(output_dir, exist_ok=True)
    results = []
    total = len(input_paths)
    
    for i, path in enumerate(input_paths):
        try:
            filename = os.path.basename(path)
            name, _ = os.path.splitext(filename)
            output_path = os.path.join(output_dir, f"{name}_nobg.png")
            
            result = remove_background(path, output_path)
            if result:
                results.append(output_path)
            
            if callback:
                callback(i + 1, total, filename)
                
        except Exception as e:
            print(f"处理 {path} 失败: {e}")
    
    return results


def is_available() -> bool:
    """检查抠图功能是否可用"""
    return _check_rembg()
