"""
智能抠图工具 - 使用 Rembg
延迟加载避免打包问题，添加完善的错误处理防止闪退

注意：rembg 依赖 onnxruntime，在某些环境下可能导致崩溃
"""
import os
import io
import sys
import traceback
from typing import Optional, List
from PIL import Image

# 延迟检查 rembg 是否可用
_rembg_checked = False
_has_rembg = False
_remove_func = None
_error_msg = ""


def _safe_import_rembg():
    """安全导入 rembg，捕获所有可能的异常"""
    global _remove_func, _error_msg
    
    try:
        # 尝试导入 rembg
        from rembg import remove
        _remove_func = remove
        return True, ""
    except ImportError as e:
        return False, f"rembg 未安装: {e}\n请运行: pip install rembg"
    except OSError as e:
        return False, f"rembg 依赖库加载失败: {e}\n可能需要安装 Visual C++ Redistributable"
    except RuntimeError as e:
        return False, f"rembg 运行时错误: {e}"
    except Exception as e:
        return False, f"rembg 加载失败: {type(e).__name__}: {e}"


def _check_rembg():
    """延迟检查 rembg 是否可用"""
    global _rembg_checked, _has_rembg, _remove_func, _error_msg
    
    if _rembg_checked:
        return _has_rembg
    
    _rembg_checked = True
    _has_rembg, _error_msg = _safe_import_rembg()
    
    if _has_rembg:
        print("[抠图] rembg 加载成功")
    else:
        print(f"[抠图] rembg 不可用: {_error_msg}")
    
    return _has_rembg


def get_error_message() -> str:
    """获取错误信息"""
    _check_rembg()
    return _error_msg


def is_available() -> bool:
    """检查抠图功能是否可用"""
    return _check_rembg()


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
        print(f"[抠图] 功能不可用: {_error_msg}")
        return None
    
    try:
        with open(input_path, 'rb') as f:
            input_data = f.read()
        
        print(f"[抠图] 正在处理文件: {input_path}")
        output_data = _remove_func(input_data)
        result = Image.open(io.BytesIO(output_data))
        
        if output_path:
            result.save(output_path, "PNG")
            print(f"[抠图] 已保存到: {output_path}")
        
        return result
    except Exception as e:
        print(f"[抠图] 处理失败: {e}")
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
        print(f"[抠图] 功能不可用: {_error_msg}")
        return None
    
    if image is None:
        print("[抠图] 失败: 图片对象为空")
        return None
    
    try:
        print(f"[抠图] 开始处理图片，尺寸: {image.size}, 模式: {image.mode}")
        
        # 确保图片格式正确
        work_image = image
        if work_image.mode != 'RGBA':
            work_image = work_image.convert('RGBA')
            print(f"[抠图] 已转换为 RGBA 模式")
        
        # 转换为字节
        buffer = io.BytesIO()
        work_image.save(buffer, format='PNG')
        input_data = buffer.getvalue()
        print(f"[抠图] 图片数据大小: {len(input_data)} 字节")
        
        # 调用 rembg
        print("[抠图] 正在调用 rembg 处理...")
        output_data = _remove_func(input_data)
        
        if output_data is None:
            print("[抠图] 失败: rembg 返回空数据")
            return None
        
        print(f"[抠图] rembg 返回数据大小: {len(output_data)} 字节")
        
        # 解析结果
        result = Image.open(io.BytesIO(output_data))
        result = result.convert('RGBA')
        
        print(f"[抠图] 处理完成，结果尺寸: {result.size}")
        return result
        
    except MemoryError as e:
        print(f"[抠图] 内存不足: {e}")
        return None
    except Exception as e:
        print(f"[抠图] 处理失败: {type(e).__name__}: {e}")
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
            print(f"[抠图] 处理 {path} 失败: {e}")
    
    return results
