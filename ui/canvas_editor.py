"""
画布编辑器 - 核心编辑组件
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QMenu, QApplication, QRubberBand
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect, QSize, QMimeData
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPixmap, QImage, 
    QMouseEvent, QWheelEvent, QKeyEvent, QDragEnterEvent, QDropEvent
)

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from config import UIConfig
from core.canvas import Canvas, Screen
from core.layer import Layer, ImageLayer, TextLayer, ShapeLayer
from core.history import CanvasHistoryManager


class CanvasWidget(QWidget):
    """画布渲染组件"""
    
    # 信号
    layer_selected = pyqtSignal(str)
    layer_moved = pyqtSignal(str, int, int)
    layer_resized = pyqtSignal(str, int, int)
    screen_right_clicked = pyqtSignal(str, object)  # screen_id, QPoint
    canvas_changed = pyqtSignal()
    drop_image = pyqtSignal(str, int, int)  # path, x, y
    
    def __init__(self, canvas: Canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.history = CanvasHistoryManager(canvas)
        
        # 视图状态
        self.scale = 0.5
        self.offset_x = 50
        self.offset_y = 30
        
        # 交互状态
        self.current_tool = "select"  # select, text, rectangle, ellipse
        self.is_dragging = False
        self.is_resizing = False
        self.resize_handle = None
        self.drag_start = QPoint()
        self.drag_layer_start = (0, 0)
        
        # 选择框
        self.rubber_band = None
        self.rubber_band_origin = QPoint()
        
        # 对齐辅助线
        self.show_guides = True
        self.guide_lines = []
        
        # 图层缓存（优化性能）
        self._pixmap_cache = {}  # layer_id -> (cache_key, QPixmap)
        
        self._setup_ui()
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
    
    def _setup_ui(self):
        """设置 UI"""
        self.setMinimumSize(800, 600)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        theme = UIConfig.THEME
        self.setStyleSheet(f"background-color: {theme['bg_primary']};")
    
    def paintEvent(self, event):
        """绑定绑定绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        theme = UIConfig.THEME
        
        # 绘制背景网格
        self._draw_grid(painter)
        
        # 计算画布位置
        canvas_x = self.offset_x
        canvas_y = self.offset_y
        canvas_w = int(self.canvas.width * self.scale)
        canvas_h = int(self.canvas.height * self.scale)
        
        # 绘制画布背景（白色）
        painter.fillRect(canvas_x, canvas_y, canvas_w, canvas_h, QColor(self.canvas.background_color))
        
        # 先渲染图层（图层在分屏标签下面）
        self._draw_layers(painter, canvas_x, canvas_y)
        
        # 再绘制分屏分隔线和标签（在图层上面）
        self._draw_screen_dividers(painter, canvas_x, canvas_y)
        
        # 绘制选中图层的边框和控制点
        self._draw_selection(painter, canvas_x, canvas_y)
        
        # 绘制对齐辅助线
        if self.show_guides and self.guide_lines:
            self._draw_guide_lines(painter, canvas_x, canvas_y)
        
        # 绘制画布边框
        painter.setPen(QPen(QColor(theme['accent']), 2))
        painter.drawRect(canvas_x, canvas_y, canvas_w, canvas_h)
        
        # 绘制尺寸标注
        painter.setPen(QColor(theme['accent']))
        painter.drawText(canvas_x, canvas_y - 5, f"{self.canvas.width}px")
    
    def _draw_grid(self, painter: QPainter):
        """绘制背景网格"""
        theme = UIConfig.THEME
        grid_color = QColor(theme['bg_tertiary'])
        painter.setPen(QPen(grid_color, 1))
        
        grid_size = 50
        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)
    
    def _draw_screen_dividers(self, painter: QPainter, canvas_x: int, canvas_y: int):
        """绘制分屏分隔线"""
        theme = UIConfig.THEME
        y_offset = 0
        
        for i, screen in enumerate(self.canvas.screens):
            screen_y = canvas_y + int(y_offset * self.scale)
            screen_h = int(screen.height * self.scale)
            
            # 分屏标签
            if not screen.is_blank:
                label_rect = QRect(canvas_x + 5, screen_y + 5, 80, 18)
                painter.fillRect(label_rect, QColor(theme['accent']))
                painter.setPen(QColor("white"))
                painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, screen.name[:8])
            else:
                # 留白区域 - 使用半透明填充，不遮挡图层
                blank_rect = QRect(canvas_x, screen_y, int(self.canvas.width * self.scale), screen_h)
                # 绘制半透明背景
                painter.fillRect(blank_rect, QColor(240, 240, 240, 100))
                # 绘制边框
                painter.setPen(QPen(QColor("#cccccc"), 1, Qt.PenStyle.DashLine))
                painter.drawRect(blank_rect)
                # 绘制文字
                painter.setPen(QColor("#999999"))
                painter.drawText(blank_rect, Qt.AlignmentFlag.AlignCenter, "留白")
            
            # 分隔线
            if i < len(self.canvas.screens) - 1:
                divider_y = screen_y + screen_h
                painter.setPen(QPen(QColor(theme['accent']), 2))
                painter.drawLine(canvas_x, divider_y, canvas_x + int(self.canvas.width * self.scale), divider_y)
                
                # 拖拽手柄
                handle_x = canvas_x + int(self.canvas.width * self.scale) // 2
                handle_rect = QRect(handle_x - 20, divider_y - 4, 40, 8)
                painter.fillRect(handle_rect, QColor(theme['accent']))
            
            y_offset += screen.height
    
    def _draw_layers(self, painter: QPainter, canvas_x: int, canvas_y: int):
        """绘制图层（带缓存优化）"""
        for layer in self.canvas.layers:
            if not layer.visible:
                continue
            
            # 计算缩放后的尺寸
            scaled_w = int(layer.width * self.scale)
            scaled_h = int(layer.height * self.scale)
            if scaled_w <= 0 or scaled_h <= 0:
                continue
            
            # 生成缓存键（包含图层属性和缩放比例）
            cache_key = f"{layer.width}_{layer.height}_{layer.rotation}_{layer.opacity}_{self.scale}"
            
            # 检查缓存
            cached = self._pixmap_cache.get(layer.id)
            if cached and cached[0] == cache_key:
                # 使用缓存的 QPixmap
                scaled_pixmap = cached[1]
            else:
                # 需要重新渲染
                layer_img = layer.render()
                if layer_img is None:
                    continue
                
                # PIL Image 转 QPixmap
                try:
                    img_data = layer_img.tobytes("raw", "RGBA")
                    qimg = QImage(img_data, layer_img.width, layer_img.height, QImage.Format.Format_RGBA8888)
                    pixmap = QPixmap.fromImage(qimg)
                    
                    # 缩放
                    scaled_pixmap = pixmap.scaled(
                        scaled_w, scaled_h, 
                        Qt.AspectRatioMode.IgnoreAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    
                    # 更新缓存
                    self._pixmap_cache[layer.id] = (cache_key, scaled_pixmap)
                except Exception as e:
                    print(f"渲染图层 {layer.id} 失败: {e}")
                    continue
            
            # 绘制
            x = canvas_x + int(layer.x * self.scale)
            y = canvas_y + int(layer.y * self.scale)
            painter.drawPixmap(x, y, scaled_pixmap)
    
    def invalidate_layer_cache(self, layer_id: str = None):
        """清除图层缓存"""
        if layer_id:
            self._pixmap_cache.pop(layer_id, None)
        else:
            self._pixmap_cache.clear()
    
    def _draw_selection(self, painter: QPainter, canvas_x: int, canvas_y: int):
        """绘制选中框"""
        layer = self.canvas.get_selected_layer()
        if layer is None:
            return
        
        theme = UIConfig.THEME
        
        # 计算位置
        x = canvas_x + int(layer.x * self.scale)
        y = canvas_y + int(layer.y * self.scale)
        w = int(layer.width * self.scale)
        h = int(layer.height * self.scale)
        
        # 选中框
        painter.setPen(QPen(QColor(theme['accent']), 2, Qt.PenStyle.DashLine))
        painter.drawRect(x, y, w, h)
        
        # 控制点
        handle_size = 8
        handles = [
            (x, y),  # 左上
            (x + w // 2, y),  # 上中
            (x + w, y),  # 右上
            (x, y + h // 2),  # 左中
            (x + w, y + h // 2),  # 右中
            (x, y + h),  # 左下
            (x + w // 2, y + h),  # 下中
            (x + w, y + h),  # 右下
        ]
        
        painter.setBrush(QBrush(QColor(theme['accent'])))
        painter.setPen(QPen(QColor("white"), 1))
        for hx, hy in handles:
            painter.drawRect(hx - handle_size // 2, hy - handle_size // 2, handle_size, handle_size)
        
        # 重置画笔状态，避免影响后续绘制
        painter.setBrush(Qt.BrushStyle.NoBrush)
    
    def _draw_guide_lines(self, painter: QPainter, canvas_x: int, canvas_y: int):
        """绘制对齐辅助线"""
        painter.setPen(QPen(QColor("#ff00ff"), 1, Qt.PenStyle.DashLine))
        for line in self.guide_lines:
            if line['type'] == 'vertical':
                x = canvas_x + int(line['pos'] * self.scale)
                painter.drawLine(x, canvas_y, x, canvas_y + int(self.canvas.height * self.scale))
            else:
                y = canvas_y + int(line['pos'] * self.scale)
                painter.drawLine(canvas_x, y, canvas_x + int(self.canvas.width * self.scale), y)
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下"""
        pos = event.position().toPoint()
        canvas_x = self.offset_x
        canvas_y = self.offset_y
        
        # 转换为画布坐标
        cx = int((pos.x() - canvas_x) / self.scale)
        cy = int((pos.y() - canvas_y) / self.scale)
        
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否点击了控制点
            handle = self._get_resize_handle(pos)
            if handle is not None:
                self.is_resizing = True
                self.resize_handle = handle
                self.drag_start = pos
                layer = self.canvas.get_selected_layer()
                if layer:
                    self.drag_layer_start = (layer.x, layer.y, layer.width, layer.height)
                return
            
            # 检查是否点击了图层
            layer = self.canvas.get_layer_at_point(cx, cy)
            if layer:
                self.canvas.select_layer(layer.id)
                self.layer_selected.emit(layer.id)
                self.is_dragging = True
                self.drag_start = pos
                self.drag_layer_start = (layer.x, layer.y)
            else:
                self.canvas.selected_layer_id = None
                self.layer_selected.emit("")
            
            self.update()
        
        elif event.button() == Qt.MouseButton.RightButton:
            # 检查是否右键点击了分屏
            screen = self.canvas.get_screen_at_y(cy)
            if screen:
                self.screen_right_clicked.emit(screen.id, event.globalPosition().toPoint())
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动"""
        pos = event.position().toPoint()
        
        if self.is_dragging:
            layer = self.canvas.get_selected_layer()
            if layer and not layer.locked:
                dx = int((pos.x() - self.drag_start.x()) / self.scale)
                dy = int((pos.y() - self.drag_start.y()) / self.scale)
                
                layer.x = self.drag_layer_start[0] + dx
                layer.y = self.drag_layer_start[1] + dy
                
                # 计算对齐辅助线
                self._calculate_guides(layer)
                
                self.update()
        
        elif self.is_resizing:
            layer = self.canvas.get_selected_layer()
            if layer and not layer.locked:
                dx = int((pos.x() - self.drag_start.x()) / self.scale)
                dy = int((pos.y() - self.drag_start.y()) / self.scale)
                
                ox, oy, ow, oh = self.drag_layer_start
                aspect_ratio = ow / oh if oh > 0 else 1  # 原始宽高比
                
                # 四个角点保持比例缩放
                if self.resize_handle in [0, 2, 5, 7]:  # 角点
                    # 根据拖动距离较大的方向计算新尺寸
                    if abs(dx) > abs(dy):
                        # 水平方向主导
                        if self.resize_handle in [0, 5]:  # 左侧角点
                            new_w = max(10, ow - dx)
                        else:  # 右侧角点
                            new_w = max(10, ow + dx)
                        new_h = int(new_w / aspect_ratio)
                    else:
                        # 垂直方向主导
                        if self.resize_handle in [0, 2]:  # 上侧角点
                            new_h = max(10, oh - dy)
                        else:  # 下侧角点
                            new_h = max(10, oh + dy)
                        new_w = int(new_h * aspect_ratio)
                    
                    new_w = max(10, new_w)
                    new_h = max(10, new_h)
                    
                    # 调整位置（左上角点需要移动）
                    if self.resize_handle == 0:  # 左上
                        layer.x = ox + (ow - new_w)
                        layer.y = oy + (oh - new_h)
                    elif self.resize_handle == 2:  # 右上
                        layer.y = oy + (oh - new_h)
                    elif self.resize_handle == 5:  # 左下
                        layer.x = ox + (ow - new_w)
                    # 右下角不需要移动位置
                    
                    layer.width = new_w
                    layer.height = new_h
                else:
                    # 边缘控制点：自由缩放
                    if self.resize_handle == 3:  # 左中
                        layer.x = ox + dx
                        layer.width = max(10, ow - dx)
                    elif self.resize_handle == 4:  # 右中
                        layer.width = max(10, ow + dx)
                    elif self.resize_handle == 1:  # 上中
                        layer.y = oy + dy
                        layer.height = max(10, oh - dy)
                    elif self.resize_handle == 6:  # 下中
                        layer.height = max(10, oh + dy)
                
                # 清除该图层的缓存
                self.invalidate_layer_cache(layer.id)
                self.update()
        
        else:
            # 更新鼠标光标
            handle = self._get_resize_handle(pos)
            if handle is not None:
                cursors = [
                    Qt.CursorShape.SizeFDiagCursor,  # 左上
                    Qt.CursorShape.SizeVerCursor,    # 上中
                    Qt.CursorShape.SizeBDiagCursor,  # 右上
                    Qt.CursorShape.SizeHorCursor,    # 左中
                    Qt.CursorShape.SizeHorCursor,    # 右中
                    Qt.CursorShape.SizeBDiagCursor,  # 左下
                    Qt.CursorShape.SizeVerCursor,    # 下中
                    Qt.CursorShape.SizeFDiagCursor,  # 右下
                ]
                self.setCursor(cursors[handle])
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放"""
        if self.is_dragging or self.is_resizing:
            self.history.save_state("移动/调整图层")
            self.canvas_changed.emit()
        
        self.is_dragging = False
        self.is_resizing = False
        self.resize_handle = None
        self.guide_lines = []
        self.update()
    
    def wheelEvent(self, event: QWheelEvent):
        """鼠标滚轮缩放"""
        delta = event.angleDelta().y()
        if delta > 0:
            self.scale = min(2.0, self.scale * 1.1)
        else:
            self.scale = max(0.2, self.scale / 1.1)
        self.update()
    
    def keyPressEvent(self, event: QKeyEvent):
        """键盘事件"""
        layer = self.canvas.get_selected_layer()
        
        if event.key() == Qt.Key.Key_Delete:
            if layer:
                self.canvas.remove_layer(layer.id)
                self.history.save_state("删除图层")
                self.canvas_changed.emit()
                self.update()
        
        elif event.key() == Qt.Key.Key_Z and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.history.redo()
            else:
                self.history.undo()
            self.canvas_changed.emit()
            self.update()
        
        elif event.key() in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right]:
            if layer and not layer.locked:
                step = 10 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1
                if event.key() == Qt.Key.Key_Up:
                    layer.y -= step
                elif event.key() == Qt.Key.Key_Down:
                    layer.y += step
                elif event.key() == Qt.Key.Key_Left:
                    layer.x -= step
                elif event.key() == Qt.Key.Key_Right:
                    layer.x += step
                self.update()
    
    def _get_resize_handle(self, pos: QPoint) -> int:
        """获取鼠标位置的控制点索引"""
        layer = self.canvas.get_selected_layer()
        if layer is None:
            return None
        
        canvas_x = self.offset_x
        canvas_y = self.offset_y
        
        x = canvas_x + int(layer.x * self.scale)
        y = canvas_y + int(layer.y * self.scale)
        w = int(layer.width * self.scale)
        h = int(layer.height * self.scale)
        
        handle_size = 12
        handles = [
            (x, y), (x + w // 2, y), (x + w, y),
            (x, y + h // 2), (x + w, y + h // 2),
            (x, y + h), (x + w // 2, y + h), (x + w, y + h),
        ]
        
        for i, (hx, hy) in enumerate(handles):
            if abs(pos.x() - hx) < handle_size and abs(pos.y() - hy) < handle_size:
                return i
        
        return None
    
    def _calculate_guides(self, layer: Layer):
        """计算对齐辅助线"""
        self.guide_lines = []
        
        # 画布中心线
        center_x = self.canvas.width // 2
        if abs(layer.x + layer.width // 2 - center_x) < 10:
            self.guide_lines.append({'type': 'vertical', 'pos': center_x})
            layer.x = center_x - layer.width // 2
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入"""
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """拖拽放下"""
        pos = event.position().toPoint()
        canvas_x = self.offset_x
        canvas_y = self.offset_y
        
        cx = int((pos.x() - canvas_x) / self.scale)
        cy = int((pos.y() - canvas_y) / self.scale)
        
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    self.drop_image.emit(url.toLocalFile(), cx, cy)
        elif event.mimeData().hasText():
            path = event.mimeData().text()
            self.drop_image.emit(path, cx, cy)
    
    def set_scale(self, scale: float):
        """设置缩放比例"""
        self.scale = max(0.2, min(2.0, scale))
        self.update()
    
    def zoom_in(self):
        """放大"""
        self.set_scale(self.scale * 1.2)
    
    def zoom_out(self):
        """缩小"""
        self.set_scale(self.scale / 1.2)
    
    def zoom_fit(self):
        """适应窗口"""
        w_scale = (self.width() - 100) / self.canvas.width
        h_scale = (self.height() - 100) / self.canvas.height
        self.set_scale(min(w_scale, h_scale))


class CanvasEditor(QWidget):
    """画布编辑器容器"""
    
    layer_selected = pyqtSignal(str)
    canvas_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = Canvas()
        self._setup_ui()
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 画布组件
        self.canvas_widget = CanvasWidget(self.canvas)
        self.canvas_widget.layer_selected.connect(self.layer_selected.emit)
        self.canvas_widget.canvas_changed.connect(self.canvas_changed.emit)
        self.canvas_widget.drop_image.connect(self._on_drop_image)
        
        layout.addWidget(self.canvas_widget)
    
    def _on_drop_image(self, path: str, x: int, y: int):
        """处理拖放图片"""
        layer = self.canvas.add_image_layer(path, x, y)
        self.canvas.select_layer(layer.id)
        self.canvas_widget.history.save_state("添加图片")
        self.canvas_widget.update()
        self.layer_selected.emit(layer.id)
        self.canvas_changed.emit()
    
    def get_canvas(self) -> Canvas:
        """获取画布"""
        return self.canvas
    
    def set_canvas(self, canvas: Canvas):
        """设置画布"""
        self.canvas = canvas
        self.canvas_widget.canvas = canvas
        self.canvas_widget.history = CanvasHistoryManager(canvas)
        self.canvas_widget.invalidate_layer_cache()  # 清除缓存
        self.canvas_widget.update()
    
    def add_text_layer(self, text: str, x: int = 100, y: int = 100):
        """添加文字图层"""
        layer = self.canvas.add_text_layer(text, x, y)
        self.canvas.select_layer(layer.id)
        self.canvas_widget.history.save_state("添加文字")
        self.canvas_widget.update()
        self.layer_selected.emit(layer.id)
        self.canvas_changed.emit()
    
    def add_shape_layer(self, shape_type: str, x: int = 100, y: int = 100):
        """添加形状图层"""
        layer = self.canvas.add_shape_layer(shape_type, x, y)
        self.canvas.select_layer(layer.id)
        self.canvas_widget.history.save_state("添加形状")
        self.canvas_widget.update()
        self.layer_selected.emit(layer.id)
        self.canvas_changed.emit()
    
    def undo(self):
        """撤销"""
        self.canvas_widget.history.undo()
        self.canvas_widget.update()
        self.canvas_changed.emit()
    
    def redo(self):
        """重做"""
        self.canvas_widget.history.redo()
        self.canvas_widget.update()
        self.canvas_changed.emit()
