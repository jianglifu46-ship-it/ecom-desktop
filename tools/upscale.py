"""
图片放大工具 - 使用 Real-ESRGAN
"""
import os
import subprocess
import platform
from typing import Optional
from PIL import Image

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from config import MODELS_DIR


def get_realesrgan_path() -> str:
    """获取 Real-ESRGAN 可执行文件路径"""
    if platform.system() == "Windows":
        return os.path.join(MODELS_DIR, "realesrgan-ncnn-vulkan.exe")
    else:
        return os.path.join(MODELS_DIR, "realesrgan-ncnn-vulkan")


def is_available() -> bool:
    """检查放大功能是否可用"""
    return os.path.exists(get_realesrgan_path())


def upscale_image(input_path: str, output_path: str, scale: int = 2) -> bool:
    """
    使用 Real-ESRGAN 放大图片
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        scale: 放大倍数 (2 或 4)
    
    Returns:
        是否成功
    """
    realesrgan_path = get_realesrgan_path()
    
    if not os.path.exists(realesrgan_path):
        print(f"Real-ESRGAN 未找到: {realesrgan_path}")
        print("请从 https://github.com/xinntao/Real-ESRGAN/releases 下载")
        return False
    
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        result = subprocess.run([
            realesrgan_path,
            "-i", input_path,
            "-o", output_path,
            "-s", str(scale),
            "-n", "realesrgan-x4plus"
        ], check=True, capture_output=True, timeout=300)
        
        return os.path.exists(output_path)
    except subprocess.CalledProcessError as e:
        print(f"放大失败: {e.stderr.decode() if e.stderr else str(e)}")
        return False
    except subprocess.TimeoutExpired:
        print("放大超时")
        return False
    except Exception as e:
        print(f"放大失败: {e}")
        return False


def upscale_image_pillow(image: Image.Image, scale: int = 2) -> Image.Image:
    """
    使用 Pillow 放大图片（备用方案，质量较低）
    
    Args:
        image: PIL Image 对象
        scale: 放大倍数
    
    Returns:
        放大后的图片
    """
    new_width = image.width * scale
    new_height = image.height * scale
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def batch_upscale(input_paths: list, output_dir: str, scale: int = 2,
                  callback=None) -> list:
    """
    批量放大图片
    
    Args:
        input_paths: 输入图片路径列表
        output_dir: 输出目录
        scale: 放大倍数
        callback: 进度回调函数
    
    Returns:
        输出文件路径列表
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []
    total = len(input_paths)
    use_realesrgan = is_available()
    
    for i, path in enumerate(input_paths):
        try:
            filename = os.path.basename(path)
            name, ext = os.path.splitext(filename)
            output_path = os.path.join(output_dir, f"{name}_{scale}x{ext}")
            
            if use_realesrgan:
                success = upscale_image(path, output_path, scale)
            else:
                # 使用 Pillow 备用方案
                img = Image.open(path)
                result = upscale_image_pillow(img, scale)
                result.save(output_path)
                success = True
            
            if success:
                results.append(output_path)
            
            if callback:
                callback(i + 1, total, filename)
                
        except Exception as e:
            print(f"处理 {path} 失败: {e}")
    
    return results
