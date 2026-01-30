"""
智能抠图工具 - 使用 Rembg
延迟加载避免打包问题，添加完善的错误处理防止闪退
"""
import os
import io
import traceback
from typing import Optional, List
from PIL import Image

# 延迟检查 rembg 是否可用
_rembg_checked = False
_has_rembg = False
_remove_func = None
_error_msg = ""


def _check_rembg():
    """延迟检查 rembg 是否可用"""
    global _rembg_checked, _has_rembg, _remove_func, _error_msg
    if _rembg_checked:
        return _has_rembg
    
    _rembg_checked = True
    try:
        from rembg import remove
        _remove_func = remove
        _has_rembg = True
        _error_msg = ""
    except ImportError as e:
        _has_rembg = False
        _error_msg = f"rembg 未安装: {e}"
    except Exception as e:
        _has_rembg = False
        _error_msg = f"rembg 加载失败: {e}"
    
    return _has_rembg


def get_error_message() -> str:
    """获取错误信息"""
    _check_rembg()
    return _error_msg


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
        print(f"抠图功能不可用: {_error_msg}")
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
        traceback.print_exc()
        return None


def remove_background_from_image(image: Image.Image) -> Optional[Image.Image]:
    """
    从 PIL Image 对象移除背景
    
    Args:
        image: PIL Image 对象
    
    Returns:
        处理后的 PIL Image 对象，失败返回 None
    """
    if not _check_rembg():
        print(f"抠图功能不可用: {_error_msg}")
        return None
    
    if image is None:
        print("抠图失败: 图片对象为空")
        return None
    
    try:
        # 确保图片格式正确
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # 转换为字节
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        input_data = buffer.getvalue()
        
        # 调用 rembg
        output_data = _remove_func(input_data)
        
        if output_data is None:
            print("抠图失败: rembg 返回空数据")
            return None
        
        # 解析结果
        result = Image.open(io.BytesIO(output_data))
        result = result.convert('RGBA')
        
        return result
    except Exception as e:
        print(f"抠图失败: {e}")
        traceback.print_exc()
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
