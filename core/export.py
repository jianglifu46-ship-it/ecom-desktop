"""
导出逻辑 - 分屏切图、平台规范适配
"""
import os
from typing import List, Dict, Tuple
from PIL import Image
from dataclasses import dataclass

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from config import ExportConfig


@dataclass
class ExportResult:
    """导出结果"""
    success: bool
    files: List[str]
    message: str = ""


class Exporter:
    """导出器"""
    
    def __init__(self, canvas):
        self.canvas = canvas
    
    def export_screens(self, output_dir: str, platform: str = "taobao", 
                       quality: int = 95) -> ExportResult:
        """按分屏导出"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            platform_config = ExportConfig.PLATFORMS.get(platform, ExportConfig.PLATFORMS["taobao"])
            format_ext = platform_config["format"]
            max_width = platform_config["max_width"]
            
            files = []
            screen_num = 0
            
            for i, screen in enumerate(self.canvas.screens):
                if screen.is_blank:
                    continue
                
                screen_num += 1
                screen_img = self.canvas.render_screen(screen.id)
                
                if screen_img is None:
                    continue
                
                # 调整宽度以符合平台规范
                if screen_img.width > max_width:
                    ratio = max_width / screen_img.width
                    new_height = int(screen_img.height * ratio)
                    screen_img = screen_img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # 转换格式
                if format_ext == "jpg":
                    screen_img = screen_img.convert("RGB")
                
                # 生成文件名
                safe_name = screen.name.replace(" ", "_").replace("/", "_").replace("-", "_")
                filename = f"{screen_num:02d}_{safe_name}.{format_ext}"
                output_path = os.path.join(output_dir, filename)
                
                # 保存
                if format_ext == "jpg":
                    screen_img.save(output_path, "JPEG", quality=quality)
                else:
                    screen_img.save(output_path, format_ext.upper())
                
                files.append(output_path)
            
            return ExportResult(
                success=True,
                files=files,
                message=f"成功导出 {len(files)} 张图片"
            )
            
        except Exception as e:
            return ExportResult(
                success=False,
                files=[],
                message=f"导出失败: {str(e)}"
            )
    
    def export_full(self, output_path: str, platform: str = "taobao",
                    quality: int = 95) -> ExportResult:
        """导出完整画布"""
        try:
            platform_config = ExportConfig.PLATFORMS.get(platform, ExportConfig.PLATFORMS["taobao"])
            format_ext = platform_config["format"]
            max_width = platform_config["max_width"]
            
            canvas_img = self.canvas.render()
            
            # 调整宽度
            if canvas_img.width > max_width:
                ratio = max_width / canvas_img.width
                new_height = int(canvas_img.height * ratio)
                canvas_img = canvas_img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换格式
            if format_ext == "jpg":
                canvas_img = canvas_img.convert("RGB")
            
            # 确保输出路径有正确扩展名
            if not output_path.lower().endswith(f".{format_ext}"):
                output_path = f"{output_path}.{format_ext}"
            
            # 保存
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            if format_ext == "jpg":
                canvas_img.save(output_path, "JPEG", quality=quality)
            else:
                canvas_img.save(output_path, format_ext.upper())
            
            return ExportResult(
                success=True,
                files=[output_path],
                message="导出成功"
            )
            
        except Exception as e:
            return ExportResult(
                success=False,
                files=[],
                message=f"导出失败: {str(e)}"
            )
    
    def export_for_platforms(self, output_dir: str, platforms: List[str] = None,
                             quality: int = 95) -> Dict[str, ExportResult]:
        """为多个平台导出"""
        if platforms is None:
            platforms = list(ExportConfig.PLATFORMS.keys())
        
        results = {}
        for platform in platforms:
            platform_dir = os.path.join(output_dir, platform)
            result = self.export_screens(platform_dir, platform, quality)
            results[platform] = result
        
        return results
    
    @staticmethod
    def get_platform_info(platform: str) -> Dict:
        """获取平台信息"""
        return ExportConfig.PLATFORMS.get(platform, {})
    
    @staticmethod
    def get_available_platforms() -> List[Tuple[str, str]]:
        """获取可用平台列表"""
        return [(key, config["name"]) for key, config in ExportConfig.PLATFORMS.items()]
