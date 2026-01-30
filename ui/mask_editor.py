# -*- coding: utf-8 -*-
"""
蓬版编辑器 - 用于交互式抠图和精修
支持：
1. 交互式抠图：用户标记保留/删除区域，AI根据标记抠图
2. 抠图精修：抠图后用画笔/橡皮擦调整
3. AI局部修改：涂抹区域+描述，AI修改内容
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFrame, QWidget, QButtonGroup, QRadioButton,
    QLineEdit, QMessageBox, QApplication, QProgressDialog
)
from PyQt6.QtCore import Qt, QPoint, QRect, QSize, pyqtSignal, QThread
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPixmap, QImage,
    QMouseEvent, QPainterPath, QCursor
)
from PIL import Image
import numpy as np
import io

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from config import UIConfig


class MaskCanvas(QWidget):
    """蒙版绘制画布"""
    
    mask_changed = pyqtSignal()
    
    def __init__(self, image: QImage, mode: str = "interactive", parent=None):
        """
        Args:
            image: 原始图像
            mode: "interactive" 交互式抠图, "refine" 精修模式
        """
        super().__init__(parent)
        self.original_image = image
        self.mode = mode
        self.display_scale = 1.0
        
        # 计算显示缩放比例，使图片适合窗口
        max_size = 600
        w, h = image.width(), image.height()
        if w > max_size or h > max_size:
            self.display_scale = min(max_size / w, max_size / h)
        
        self.display_w = int(w * self.display_scale)
        self.display_h = int(h * self.display_scale)
        
        # 创建蒙版图层
        # 交互式模式：绿色=保留(前景), 红色=删除(背景), 透明=未标记
        # 精修模式：白色=保留, 黑色=删除
        self.mask_image = QImage(w, h, QImage.Format.Format_ARGB32)
        self.mask_image.fill(Qt.GlobalColor.transparent)
        
        # 工具状态
        if mode == "interactive":
            self.tool = "keep"  # keep=标记保留(绿色), remove=标记删除(红色)
        else:
            self.tool = "brush"  # brush=画笔(恢复), eraser=橡皮擦(删除)
        
        self.brush_size = 30
        self.is_drawing = False
        self.last_point = QPoint()
        
        self.setFixedSize(self.display_w, self.display_h)
        self.setMouseTracking(True)
        self.setCursor(self._create_brush_cursor())
    
    def _create_brush_cursor(self) -> QCursor:
        """创建画笔光标"""
        size = max(8, int(self.brush_size * self.display_scale))
        cursor_pixmap = QPixmap(size, size)
        cursor_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(cursor_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 根据工具设置颜色
        if self.mode == "interactive":
            color = QColor(0, 255, 0, 200) if self.tool == "keep" else QColor(255, 0, 0, 200)
        else:
            color = QColor(0, 255, 0, 200) if self.tool == "brush" else QColor(255, 0, 0, 200)
        
        pen = QPen(color, 2)
        painter.setPen(pen)
        painter.drawEllipse(1, 1, size - 2, size - 2)
        painter.end()
        
        return QCursor(cursor_pixmap, size // 2, size // 2)
    
    def set_tool(self, tool: str):
        """设置工具"""
        self.tool = tool
        self.setCursor(self._create_brush_cursor())
    
    def set_brush_size(self, size: int):
        """设置画笔大小"""
        self.brush_size = size
        self.setCursor(self._create_brush_cursor())
    
    def set_initial_mask_from_alpha(self, image: QImage):
        """从图片的 alpha 通道初始化蒙版（用于精修模式）"""
        if image.format() != QImage.Format.Format_ARGB32:
            image = image.convertToFormat(QImage.Format.Format_ARGB32)
        
        w, h = image.width(), image.height()
        self.mask_image = QImage(w, h, QImage.Format.Format_ARGB32)
        
        for y in range(h):
            for x in range(w):
                pixel = image.pixel(x, y)
                alpha = (pixel >> 24) & 0xFF
                # alpha > 0 的区域设为白色（保留），否则设为黑色（删除）
                if alpha > 10:
                    self.mask_image.setPixel(x, y, 0xFFFFFFFF)  # 白色
                else:
                    self.mask_image.setPixel(x, y, 0xFF000000)  # 黑色
        
        self.update()
    
    def paintEvent(self, event):
        """绑定绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 绘制棋盘格背景（表示透明）
        self._draw_checkerboard(painter)
        
        # 绘制原图
        scaled_image = self.original_image.scaled(
            self.display_w, self.display_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        painter.drawImage(0, 0, scaled_image)
        
        # 绘制蒙版预览
        scaled_mask = self.mask_image.scaled(
            self.display_w, self.display_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        if self.mode == "interactive":
            # 交互式模式：直接显示绿色/红色标记
            painter.setOpacity(0.5)
            painter.drawImage(0, 0, scaled_mask)
            painter.setOpacity(1.0)
        else:
            # 精修模式：红色半透明表示将被删除的区域
            overlay = QImage(self.display_w, self.display_h, QImage.Format.Format_ARGB32)
            overlay.fill(Qt.GlobalColor.transparent)
            
            for y in range(scaled_mask.height()):
                for x in range(scaled_mask.width()):
                    pixel = scaled_mask.pixel(x, y)
                    r = (pixel >> 16) & 0xFF
                    g = (pixel >> 8) & 0xFF
                    b = pixel & 0xFF
                    # 黑色区域（将被删除）显示红色
                    if r < 128 and g < 128 and b < 128:
                        overlay.setPixel(x, y, 0x80FF0000)  # 半透明红色
            
            painter.drawImage(0, 0, overlay)
    
    def _draw_checkerboard(self, painter: QPainter):
        """绘制棋盘格背景"""
        cell_size = 10
        colors = [QColor(200, 200, 200), QColor(255, 255, 255)]
        
        for y in range(0, self.display_h, cell_size):
            for x in range(0, self.display_w, cell_size):
                color_idx = ((x // cell_size) + (y // cell_size)) % 2
                painter.fillRect(x, y, cell_size, cell_size, colors[color_idx])
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_drawing = True
            self.last_point = event.position().toPoint()
            self._draw_at(self.last_point)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动"""
        if self.is_drawing:
            current_point = event.position().toPoint()
            self._draw_line(self.last_point, current_point)
            self.last_point = current_point
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_drawing = False
            self.mask_changed.emit()
    
    def _get_draw_color(self) -> QColor:
        """获取绘制颜色"""
        if self.mode == "interactive":
            if self.tool == "keep":
                return QColor(0, 255, 0, 255)  # 绿色=保留
            else:
                return QColor(255, 0, 0, 255)  # 红色=删除
        else:
            if self.tool == "brush":
                return QColor(255, 255, 255, 255)  # 白色=保留
            else:
                return QColor(0, 0, 0, 255)  # 黑色=删除
    
    def _draw_at(self, pos: QPoint):
        """在指定位置绘制"""
        # 转换到原始图像坐标
        x = int(pos.x() / self.display_scale)
        y = int(pos.y() / self.display_scale)
        radius = self.brush_size // 2
        
        painter = QPainter(self.mask_image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        color = self._get_draw_color()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPoint(x, y), radius, radius)
        painter.end()
        
        self.update()
    
    def _draw_line(self, start: QPoint, end: QPoint):
        """绘制线条"""
        # 转换到原始图像坐标
        x1 = int(start.x() / self.display_scale)
        y1 = int(start.y() / self.display_scale)
        x2 = int(end.x() / self.display_scale)
        y2 = int(end.y() / self.display_scale)
        
        painter = QPainter(self.mask_image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        color = self._get_draw_color()
        pen = QPen(color, self.brush_size, Qt.PenStyle.SolidLine, 
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(x1, y1, x2, y2)
        painter.end()
        
        self.update()
    
    def get_mask_image(self) -> QImage:
        """获取蒙版图像"""
        return self.mask_image
    
    def get_foreground_mask(self) -> Image.Image:
        """获取前景蒙版（用于交互式抠图）
        返回 PIL Image，绿色区域为白色，其他为黑色
        """
        w, h = self.mask_image.width(), self.mask_image.height()
        mask = Image.new('L', (w, h), 0)
        
        for y in range(h):
            for x in range(w):
                pixel = self.mask_image.pixel(x, y)
                alpha = (pixel >> 24) & 0xFF
                g = (pixel >> 8) & 0xFF
                r = (pixel >> 16) & 0xFF
                # 绿色区域（保留）设为白色
                if alpha > 0 and g > r:
                    mask.putpixel((x, y), 255)
        
        return mask
    
    def get_background_mask(self) -> Image.Image:
        """获取背景蒙版（用于交互式抠图）
        返回 PIL Image，红色区域为白色，其他为黑色
        """
        w, h = self.mask_image.width(), self.mask_image.height()
        mask = Image.new('L', (w, h), 0)
        
        for y in range(h):
            for x in range(w):
                pixel = self.mask_image.pixel(x, y)
                alpha = (pixel >> 24) & 0xFF
                g = (pixel >> 8) & 0xFF
                r = (pixel >> 16) & 0xFF
                # 红色区域（删除）设为白色
                if alpha > 0 and r > g:
                    mask.putpixel((x, y), 255)
        
        return mask
    
    def has_marks(self) -> bool:
        """检查是否有标记"""
        w, h = self.mask_image.width(), self.mask_image.height()
        for y in range(0, h, 10):  # 采样检查
            for x in range(0, w, 10):
                pixel = self.mask_image.pixel(x, y)
                alpha = (pixel >> 24) & 0xFF
                if alpha > 0:
                    return True
        return False
    
    def apply_mask_to_image(self) -> QImage:
        """将蒙版应用到图像，返回处理后的图像（用于精修模式）"""
        result = self.original_image.convertToFormat(QImage.Format.Format_ARGB32)
        w, h = result.width(), result.height()
        
        for y in range(h):
            for x in range(w):
                mask_pixel = self.mask_image.pixel(x, y)
                r = (mask_pixel >> 16) & 0xFF
                g = (mask_pixel >> 8) & 0xFF
                b = mask_pixel & 0xFF
                # 黑色区域设为透明
                if r < 128 and g < 128 and b < 128:
                    result.setPixel(x, y, 0x00000000)
        
        return result
    
    def reset_mask(self):
        """重置蒙版"""
        self.mask_image.fill(Qt.GlobalColor.transparent)
        self.update()
        self.mask_changed.emit()


class RemoveBgWorker(QThread):
    """抠图工作线程"""
    finished = pyqtSignal(object, str)  # result, error
    
    def __init__(self, image, fg_mask=None, bg_mask=None, parent=None):
        super().__init__(parent)
        self.image = image
        self.fg_mask = fg_mask
        self.bg_mask = bg_mask
    
    def run(self):
        try:
            from tools.remove_bg import remove_background_from_image
            result = remove_background_from_image(self.image)
            if result:
                self.finished.emit(result, "")
            else:
                self.finished.emit(None, "抠图处理失败")
        except Exception as e:
            self.finished.emit(None, str(e))


class InteractiveRemoveBgDialog(QDialog):
    """交互式抠图对话框"""
    
    def __init__(self, image: QImage, parent=None):
        super().__init__(parent)
        self.original_qimage = image
        self.result_image = None
        self._worker = None
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """设置 UI"""
        self.setWindowTitle("智能抠图")
        self.setModal(True)
        self.setMinimumWidth(700)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 提示文字
        tip = QLabel(
            "\u4f7f\u7528\u8bf4\u660e:\n"
            "1. \u7528\u7eff\u8272\u753b\u7b14\u6d82\u62b9\u8981\u4fdd\u7559\u7684\u4e3b\u4f53\u533a\u57df(\u4ea7\u54c1)\n"
            "2. \u7528\u7ea2\u8272\u753b\u7b14\u6d82\u62b9\u8981\u5220\u9664\u7684\u80cc\u666f\u533a\u57df(\u53ef\u9009)\n"
            "3. \u70b9\u51fb[\u5f00\u59cb\u62a0\u56fe], AI \u4f1a\u6839\u636e\u60a8\u7684\u6807\u8bb0\u8fdb\u884c\u62a0\u56fe\n"
            "4. \u4e0d\u6807\u8bb0\u4e5f\u53ef\u4ee5\u76f4\u63a5\u62a0\u56fe, AI \u4f1a\u81ea\u52a8\u8bc6\u522b"
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("padding: 10px; background-color: rgba(0,150,255,0.1); border-radius: 5px;")
        layout.addWidget(tip)
        
        # 工具栏
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # 工具选择
        self.keep_btn = QPushButton("🟢 标记保留")
        self.keep_btn.setCheckable(True)
        self.keep_btn.setChecked(True)
        self.keep_btn.clicked.connect(lambda: self._set_tool("keep"))
        toolbar_layout.addWidget(self.keep_btn)
        
        self.remove_btn = QPushButton("🔴 标记删除")
        self.remove_btn.setCheckable(True)
        self.remove_btn.clicked.connect(lambda: self._set_tool("remove"))
        toolbar_layout.addWidget(self.remove_btn)
        
        toolbar_layout.addWidget(QLabel("  画笔大小:"))
        
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(10, 100)
        self.size_slider.setValue(30)
        self.size_slider.setFixedWidth(100)
        self.size_slider.valueChanged.connect(self._on_size_changed)
        toolbar_layout.addWidget(self.size_slider)
        
        self.size_label = QLabel("30")
        self.size_label.setFixedWidth(30)
        toolbar_layout.addWidget(self.size_label)
        
        toolbar_layout.addStretch()
        
        self.reset_btn = QPushButton("清除标记")
        self.reset_btn.clicked.connect(self._on_reset)
        toolbar_layout.addWidget(self.reset_btn)
        
        layout.addWidget(toolbar)
        
        # 画布
        self.canvas = MaskCanvas(self.original_qimage, mode="interactive")
        layout.addWidget(self.canvas, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.start_btn = QPushButton("🚀 开始抠图")
        self.start_btn.setStyleSheet("background-color: #0096FF; font-weight: bold;")
        self.start_btn.clicked.connect(self._on_start_remove_bg)
        btn_layout.addWidget(self.start_btn)
        
        layout.addLayout(btn_layout)
    
    def _apply_style(self):
        """应用样式"""
        theme = UIConfig.THEME
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme['bg_primary']};
            }}
            QLabel {{
                color: {theme['text_primary']};
            }}
            QPushButton {{
                background-color: {theme['bg_tertiary']};
                color: {theme['text_primary']};
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {theme['accent']};
            }}
            QPushButton:checked {{
                background-color: {theme['accent']};
            }}
            QSlider::groove:horizontal {{
                background: {theme['bg_tertiary']};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {theme['accent']};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
        """)
    
    def _set_tool(self, tool: str):
        """设置工具"""
        self.canvas.set_tool(tool)
        self.keep_btn.setChecked(tool == "keep")
        self.remove_btn.setChecked(tool == "remove")
    
    def _on_size_changed(self, value: int):
        """画笔大小改变"""
        self.size_label.setText(str(value))
        self.canvas.set_brush_size(value)
    
    def _on_reset(self):
        """重置标记"""
        self.canvas.reset_mask()
    
    def _on_start_remove_bg(self):
        """开始抠图"""
        # 转换原图为 PIL Image
        original_pil = qimage_to_pil(self.original_qimage)
        
        # 获取标记蒙版（如果有）
        fg_mask = None
        bg_mask = None
        if self.canvas.has_marks():
            fg_mask = self.canvas.get_foreground_mask()
            bg_mask = self.canvas.get_background_mask()
        
        # 禁用按钮
        self.start_btn.setEnabled(False)
        self.start_btn.setText("正在处理...")
        
        # 启动工作线程
        self._worker = RemoveBgWorker(original_pil, fg_mask, bg_mask)
        self._worker.finished.connect(self._on_remove_bg_finished)
        self._worker.start()
    
    def _on_remove_bg_finished(self, result, error):
        """抠图完成"""
        self.start_btn.setEnabled(True)
        self.start_btn.setText("🚀 开始抠图")
        
        if error:
            QMessageBox.critical(self, "错误", f"抠图失败:\n{error}")
            return
        
        if result is None:
            QMessageBox.warning(self, "失败", "抠图处理失败")
            return
        
        # 询问是否需要精修
        reply = QMessageBox.question(
            self, "\u62a0\u56fe\u5b8c\u6210",
            "\u62a0\u56fe\u5b8c\u6210!\n\n\u662f\u5426\u9700\u8981\u7cbe\u4fee?\n- \u70b9\u51fb[\u662f]\u6253\u5f00\u7cbe\u4fee\u7f16\u8f91\u5668\n- \u70b9\u51fb[\u5426]\u76f4\u63a5\u4f7f\u7528\u7ed3\u679c",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 打开精修编辑器
            result_qimage = pil_to_qimage(result)
            editor = MaskEditorDialog(result_qimage, mode="refine", parent=self)
            if editor.exec() == MaskEditorDialog.DialogCode.Accepted:
                refined_qimage = editor.get_result()
                if refined_qimage:
                    self.result_image = qimage_to_pil(refined_qimage)
                else:
                    self.result_image = result
            else:
                self.result_image = result
        else:
            self.result_image = result
        
        self.accept()
    
    def get_result(self) -> Image.Image:
        """获取结果"""
        return self.result_image


class MaskEditorDialog(QDialog):
    """蒙版编辑器对话框（用于精修）"""
    
    def __init__(self, image: QImage, mode: str = "refine", parent=None):
        """
        Args:
            image: 要编辑的图像
            mode: "refine" 抠图精修, "inpaint" AI局部修改
        """
        super().__init__(parent)
        self.mode = mode
        self.result_image = None
        self.inpaint_prompt = ""
        
        self._setup_ui(image)
        self._apply_style()
    
    def _setup_ui(self, image: QImage):
        """设置 UI"""
        if self.mode == "refine":
            self.setWindowTitle("抠图精修 - 蒙版编辑")
        else:
            self.setWindowTitle("AI 局部修改")
        
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 提示文字
        if self.mode == "refine":
            tip = QLabel("🖌️ 画笔：恢复被误删的区域  |  🧹 橡皮擦：删除多余的区域  |  红色区域将被删除")
        else:
            tip = QLabel("🖌️ 用画笔涂抹要修改的区域，然后输入想要修改成什么")
        tip.setWordWrap(True)
        layout.addWidget(tip)
        
        # 工具栏
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # 工具选择
        self.brush_btn = QPushButton("🖌️ 画笔(恢复)")
        self.brush_btn.setCheckable(True)
        self.brush_btn.setChecked(True)
        self.brush_btn.clicked.connect(lambda: self._set_tool("brush"))
        toolbar_layout.addWidget(self.brush_btn)
        
        self.eraser_btn = QPushButton("🧹 橡皮擦(删除)")
        self.eraser_btn.setCheckable(True)
        self.eraser_btn.clicked.connect(lambda: self._set_tool("eraser"))
        toolbar_layout.addWidget(self.eraser_btn)
        
        toolbar_layout.addWidget(QLabel("  画笔大小:"))
        
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(5, 100)
        self.size_slider.setValue(20)
        self.size_slider.setFixedWidth(100)
        self.size_slider.valueChanged.connect(self._on_size_changed)
        toolbar_layout.addWidget(self.size_slider)
        
        self.size_label = QLabel("20")
        self.size_label.setFixedWidth(30)
        toolbar_layout.addWidget(self.size_label)
        
        toolbar_layout.addStretch()
        
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self._on_reset)
        toolbar_layout.addWidget(self.reset_btn)
        
        layout.addWidget(toolbar)
        
        # 画布
        self.canvas = MaskCanvas(image, mode="refine")
        # 从 alpha 通道初始化蒙版
        self.canvas.set_initial_mask_from_alpha(image)
        layout.addWidget(self.canvas, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # AI 局部修改模式：添加提示词输入
        if self.mode == "inpaint":
            prompt_layout = QHBoxLayout()
            prompt_layout.addWidget(QLabel("修改为:"))
            self.prompt_input = QLineEdit()
            self.prompt_input.setPlaceholderText("输入想要修改成什么，例如：新品上市、红色背景...")
            prompt_layout.addWidget(self.prompt_input)
            layout.addLayout(prompt_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.apply_btn = QPushButton("应用")
        self.apply_btn.clicked.connect(self._on_apply)
        btn_layout.addWidget(self.apply_btn)
        
        layout.addLayout(btn_layout)
    
    def _apply_style(self):
        """应用样式"""
        theme = UIConfig.THEME
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme['bg_primary']};
            }}
            QLabel {{
                color: {theme['text_primary']};
            }}
            QPushButton {{
                background-color: {theme['bg_tertiary']};
                color: {theme['text_primary']};
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {theme['accent']};
            }}
            QPushButton:checked {{
                background-color: {theme['accent']};
            }}
            QLineEdit {{
                background-color: {theme['bg_tertiary']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border']};
                border-radius: 5px;
                padding: 8px;
            }}
            QSlider::groove:horizontal {{
                background: {theme['bg_tertiary']};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {theme['accent']};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
        """)
    
    def _set_tool(self, tool: str):
        """设置工具"""
        self.canvas.set_tool(tool)
        self.brush_btn.setChecked(tool == "brush")
        self.eraser_btn.setChecked(tool == "eraser")
    
    def _on_size_changed(self, value: int):
        """画笔大小改变"""
        self.size_label.setText(str(value))
        self.canvas.set_brush_size(value)
    
    def _on_reset(self):
        """重置蒙版"""
        # 重新从原图 alpha 初始化
        self.canvas.set_initial_mask_from_alpha(self.canvas.original_image)
    
    def _on_apply(self):
        """应用修改"""
        if self.mode == "refine":
            # 抠图精修：应用蒙版
            self.result_image = self.canvas.apply_mask_to_image()
            self.accept()
        else:
            # AI 局部修改
            if hasattr(self, 'prompt_input'):
                self.inpaint_prompt = self.prompt_input.text().strip()
                if not self.inpaint_prompt:
                    QMessageBox.warning(self, "提示", "请输入要修改成什么")
                    return
            self.result_image = self.canvas.get_mask_image()
            self.accept()
    
    def get_result(self):
        """获取结果"""
        return self.result_image
    
    def get_prompt(self):
        """获取提示词（仅 inpaint 模式）"""
        return self.inpaint_prompt


def qimage_to_pil(qimage: QImage) -> Image.Image:
    """QImage 转 PIL Image"""
    qimage = qimage.convertToFormat(QImage.Format.Format_RGBA8888)
    width = qimage.width()
    height = qimage.height()
    
    ptr = qimage.bits()
    ptr.setsize(height * width * 4)
    arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))
    
    return Image.fromarray(arr, 'RGBA')


def pil_to_qimage(pil_image: Image.Image) -> QImage:
    """PIL Image 转 QImage"""
    if pil_image.mode != 'RGBA':
        pil_image = pil_image.convert('RGBA')
    
    data = pil_image.tobytes('raw', 'RGBA')
    qimage = QImage(data, pil_image.width, pil_image.height, QImage.Format.Format_RGBA8888)
    return qimage.copy()  # 返回副本，避免数据被释放
