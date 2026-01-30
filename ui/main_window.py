"""
主窗口
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QStatusBar, QLabel, QMessageBox, QFileDialog,
    QInputDialog, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QCloseEvent

import os

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from config import APP_NAME, UIConfig
from services.api_client import api_client
from services.task_poller import task_poller
from services.notification import notification_service

from .tray_icon import TrayIcon
from .login_dialog import LoginDialog
from .toolbar import Toolbar
from .task_panel import TaskPanel, TaskDetailPanel
from .canvas_editor import CanvasEditor
from .layer_panel import LayerPanel
from .property_panel import PropertyPanel
from .screen_panel import ScreenPanel
from .assets_panel import AssetsPanel
from .ai_panel import AIPanel
from .middleware_panel import MiddlewarePanel
from .tab_manager import TabManager
from .export_dialog import ExportDialog


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1400, 900)
        
        self._setup_tray()
        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._setup_shortcuts()
        self._apply_style()
        self._connect_signals()
        
        # 启动任务轮询
        self._start_polling()
    
    def _setup_tray(self):
        """设置系统托盘"""
        self.tray = TrayIcon(self)
        self.tray.show_window_signal.connect(self._show_window)
        self.tray.quit_signal.connect(self._quit_app)
        self.tray.show()
    
    def _setup_ui(self):
        """设置 UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 工具栏
        self.toolbar = Toolbar()
        main_layout.addWidget(self.toolbar)
        
        # 创建标签页管理器
        self.tab_manager = TabManager()
        main_layout.addWidget(self.tab_manager, 1)
        
        # 创建编辑器页面内容
        editor_widget = self._create_editor_widget()
        self.tab_manager.add_editor_tab(editor_widget, "编辑器")
        
        # 创建中台页面内容
        self.middleware_panel = MiddlewarePanel()
        self.tab_manager.add_middleware_tab(self.middleware_panel, "中台")
        
        # 连接标签页切换信号
        self.tab_manager.tab_changed.connect(self._on_tab_changed)
    
    def _create_editor_widget(self):
        """创建编辑器页面内容"""
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧面板
        left_widget = QWidget()
        left_widget.setFixedWidth(260)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(5)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # 任务面板
        self.task_panel = TaskPanel()
        left_layout.addWidget(self.task_panel, 2)
        
        # 素材面板
        self.assets_panel = AssetsPanel()
        left_layout.addWidget(self.assets_panel, 2)
        
        # 分屏管理面板
        self.screen_panel = ScreenPanel()
        left_layout.addWidget(self.screen_panel, 3)
        
        content_splitter.addWidget(left_widget)
        
        # 中间画布区域
        self.canvas_editor = CanvasEditor()
        content_splitter.addWidget(self.canvas_editor)
        
        # 右侧面板
        right_widget = QWidget()
        right_widget.setFixedWidth(270)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(5)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # 图层面板
        self.layer_panel = LayerPanel()
        right_layout.addWidget(self.layer_panel, 2)
        
        # 属性面板
        self.property_panel = PropertyPanel()
        right_layout.addWidget(self.property_panel, 2)
        
        # AI 助手面板
        self.ai_panel = AIPanel()
        right_layout.addWidget(self.ai_panel, 3)
        
        content_splitter.addWidget(right_widget)
        
        # 设置分割比例
        content_splitter.setStretchFactor(0, 0)
        content_splitter.setStretchFactor(1, 1)
        content_splitter.setStretchFactor(2, 0)
        
        return content_splitter
    
    def _on_tab_changed(self, index):
        """标签页切换处理"""
        if index == 0:  # 编辑器标签页
            # 可以在这里添加切换到编辑器时的逻辑
            pass
        elif index == 1:  # 中台标签页
            # 可以在这里添加切换到中台时的逻辑
            pass
    
    def _setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        new_action = QAction("新建", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._on_new)
        file_menu.addAction(new_action)
        
        open_action = QAction("打开...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)
        
        save_action = QAction("保存", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("另存为...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self._on_save_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("导出...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self._on_export)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("退出", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self._quit_app)
        file_menu.addAction(quit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        undo_action = QAction("撤销", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.canvas_editor.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("重做", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.canvas_editor.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        delete_action = QAction("删除", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(self._on_delete_layer)
        edit_menu.addAction(delete_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        zoom_in_action = QAction("放大", self)
        zoom_in_action.setShortcut(QKeySequence("Ctrl+="))
        zoom_in_action.triggered.connect(self.canvas_editor.canvas_widget.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("缩小", self)
        zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_action.triggered.connect(self.canvas_editor.canvas_widget.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        zoom_fit_action = QAction("适应窗口", self)
        zoom_fit_action.setShortcut(QKeySequence("Ctrl+0"))
        zoom_fit_action.triggered.connect(self.canvas_editor.canvas_widget.zoom_fit)
        view_menu.addAction(zoom_fit_action)
        
        # 图层菜单
        layer_menu = menubar.addMenu("图层")
        
        add_text_action = QAction("添加文字", self)
        add_text_action.setShortcut(QKeySequence("T"))
        add_text_action.triggered.connect(self._on_add_text)
        layer_menu.addAction(add_text_action)
        
        add_rect_action = QAction("添加矩形", self)
        add_rect_action.setShortcut(QKeySequence("R"))
        add_rect_action.triggered.connect(lambda: self.canvas_editor.add_shape_layer("rectangle"))
        layer_menu.addAction(add_rect_action)
        
        layer_menu.addSeparator()
        
        layer_up_action = QAction("上移图层", self)
        layer_up_action.setShortcut(QKeySequence("Ctrl+]"))
        layer_up_action.triggered.connect(self._on_layer_up)
        layer_menu.addAction(layer_up_action)
        
        layer_down_action = QAction("下移图层", self)
        layer_down_action.setShortcut(QKeySequence("Ctrl+["))
        layer_down_action.triggered.connect(self._on_layer_down)
        layer_menu.addAction(layer_down_action)
        
        # 分屏菜单
        screen_menu = menubar.addMenu("分屏")
        
        add_screen_action = QAction("添加分屏", self)
        add_screen_action.triggered.connect(lambda: self._on_add_screen(False))
        screen_menu.addAction(add_screen_action)
        
        add_blank_action = QAction("添加留白", self)
        add_blank_action.triggered.connect(lambda: self._on_add_screen(True))
        screen_menu.addAction(add_blank_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        
        rembg_action = QAction("智能抠图", self)
        rembg_action.triggered.connect(self._on_remove_bg)
        tools_menu.addAction(rembg_action)
        
        upscale_action = QAction("图片放大", self)
        upscale_action.triggered.connect(self._on_upscale)
        tools_menu.addAction(upscale_action)
        
        enhance_action = QAction("图片增强", self)
        enhance_action.triggered.connect(self._on_enhance)
        tools_menu.addAction(enhance_action)
        
        # AI 助手菜单
        ai_menu = menubar.addMenu("AI助手")
        
        ai_copy_action = QAction("智能文案生成", self)
        ai_copy_action.triggered.connect(self.ai_panel._on_generate_copy)
        ai_menu.addAction(ai_copy_action)
        
        ai_layout_action = QAction("一键排版优化", self)
        ai_layout_action.triggered.connect(self.ai_panel._on_optimize_layout)
        ai_menu.addAction(ai_layout_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _setup_statusbar(self):
        """设置状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # 缩放信息
        self.zoom_label = QLabel("缩放: 50%")
        self.statusbar.addWidget(self.zoom_label)
        
        # 画布信息
        self.canvas_label = QLabel("画布: 750×1000px")
        self.statusbar.addWidget(self.canvas_label)
        
        # 分屏信息
        self.screen_label = QLabel("分屏: 3")
        self.statusbar.addWidget(self.screen_label)
        
        # 图层信息
        self.layer_label = QLabel("图层: 0")
        self.statusbar.addWidget(self.layer_label)
        
        # 弹性空间
        self.statusbar.addWidget(QLabel(), 1)
        
        # 任务信息
        self.task_label = QLabel("未选择任务")
        self.statusbar.addWidget(self.task_label)
        
        # 连接状态
        self.connection_label = QLabel("● 已连接")
        self.connection_label.setStyleSheet(f"color: {UIConfig.THEME['success']};")
        self.statusbar.addWidget(self.connection_label)
    
    def _setup_shortcuts(self):
        """设置快捷键"""
        # 快捷键在菜单中已设置
        pass
    
    def _apply_style(self):
        """应用样式"""
        theme = UIConfig.THEME
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme['bg_primary']};
            }}
            QMenuBar {{
                background-color: {theme['bg_secondary']};
                color: {theme['text_primary']};
                padding: 5px;
            }}
            QMenuBar::item:selected {{
                background-color: {theme['accent']};
            }}
            QMenu {{
                background-color: {theme['bg_secondary']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border']};
            }}
            QMenu::item:selected {{
                background-color: {theme['accent']};
            }}
            QStatusBar {{
                background-color: {theme['bg_tertiary']};
                color: {theme['text_secondary']};
            }}
            QStatusBar QLabel {{
                padding: 0 10px;
            }}
            QSplitter::handle {{
                background-color: {theme['border']};
            }}
        """)
    
    def _connect_signals(self):
        """连接信号"""
        # 工具栏信号
        self.toolbar.tool_selected.connect(self._on_tool_selected)
        self.toolbar.undo_clicked.connect(self.canvas_editor.undo)
        self.toolbar.redo_clicked.connect(self.canvas_editor.redo)
        self.toolbar.add_screen_clicked.connect(lambda: self._on_add_screen(False))
        self.toolbar.add_blank_clicked.connect(lambda: self._on_add_screen(True))
        self.toolbar.remove_bg_clicked.connect(self._on_remove_bg)
        self.toolbar.upscale_clicked.connect(self._on_upscale)
        self.toolbar.enhance_clicked.connect(self._on_enhance)
        self.toolbar.ai_generate_clicked.connect(self.ai_panel._on_generate_copy)
        
        # 画布信号
        self.canvas_editor.layer_selected.connect(self._on_layer_selected)
        self.canvas_editor.canvas_changed.connect(self._update_status)
        
        # 图层面板信号
        self.layer_panel.layer_selected.connect(self._on_layer_panel_select)
        self.layer_panel.layer_visibility_changed.connect(self._on_layer_visibility)
        self.layer_panel.layer_order_changed.connect(self._on_layer_order)
        self.layer_panel.layer_deleted.connect(self._on_layer_delete)
        self.layer_panel.layer_duplicated.connect(self._on_layer_duplicate)
        
        # 属性面板信号
        self.property_panel.property_changed.connect(self._on_property_changed)
        
        # 分屏面板信号
        self.screen_panel.screen_added.connect(self._on_screen_added)
        self.screen_panel.screen_deleted.connect(self._on_screen_deleted)
        self.screen_panel.screen_resized.connect(self._on_screen_resized)
        self.screen_panel.screen_renamed.connect(self._on_screen_renamed)
        self.screen_panel.insert_screen.connect(self._on_insert_screen)
        
        # 素材面板信号
        self.assets_panel.asset_add_to_canvas.connect(self._on_asset_add)
        
        # AI 面板信号
        self.ai_panel.remove_bg_requested.connect(self._on_remove_bg)
        self.ai_panel.upscale_requested.connect(self._on_upscale)
        self.ai_panel.enhance_requested.connect(self._on_enhance)
        self.ai_panel.copy_generated.connect(self._on_copy_generated)
        
        # 任务面板信号
        self.task_panel.task_selected.connect(self._on_task_selected)
        
        # 中台面板信号
        if hasattr(self.middleware_panel, 'bridge'):
            self.middleware_panel.bridge.data_received.connect(self._on_middleware_data_received)
    
    def _start_polling(self):
        """启动任务轮询"""
        if api_client.is_logged_in:
            thread = task_poller.start()
            thread.tasks_updated.connect(self._on_tasks_updated)
            thread.new_task_received.connect(self._on_new_task)
    
    def _update_status(self):
        """更新状态栏"""
        canvas = self.canvas_editor.get_canvas()
        
        self.zoom_label.setText(f"缩放: {int(self.canvas_editor.canvas_widget.scale * 100)}%")
        self.canvas_label.setText(f"画布: {canvas.width}×{canvas.height}px")
        self.screen_label.setText(f"分屏: {len(canvas.screens)}")
        self.layer_label.setText(f"图层: {len(canvas.layers)}")
        
        # 更新面板
        self.layer_panel.set_layers(canvas.layers)
        self.screen_panel.set_screens(canvas.screens)
    
    def _on_layer_selected(self, layer_id: str):
        """图层被选中"""
        canvas = self.canvas_editor.get_canvas()
        layer = canvas.get_layer(layer_id) if layer_id else None
        
        self.layer_panel.select_layer(layer_id)
        self.property_panel.set_layer(layer)
    
    def _on_layer_panel_select(self, layer_id: str):
        """图层面板选择"""
        canvas = self.canvas_editor.get_canvas()
        canvas.select_layer(layer_id)
        
        layer = canvas.get_layer(layer_id)
        self.property_panel.set_layer(layer)
        self.canvas_editor.canvas_widget.update()
    
    def _on_layer_visibility(self, layer_id: str, visible: bool):
        """图层可见性变化"""
        canvas = self.canvas_editor.get_canvas()
        layer = canvas.get_layer(layer_id)
        if layer:
            layer.visible = visible
            self.canvas_editor.canvas_widget.update()
    
    def _on_layer_order(self, layer_id: str, new_index: int):
        """图层顺序变化"""
        canvas = self.canvas_editor.get_canvas()
        canvas.move_layer(layer_id, new_index)
        self.canvas_editor.canvas_widget.history.save_state("调整图层顺序")
        self._update_status()
        self.canvas_editor.canvas_widget.update()
    
    def _on_layer_delete(self, layer_id: str):
        """删除图层"""
        canvas = self.canvas_editor.get_canvas()
        canvas.remove_layer(layer_id)
        self.canvas_editor.canvas_widget.history.save_state("删除图层")
        self._update_status()
        self.canvas_editor.canvas_widget.update()
    
    def _on_layer_duplicate(self, layer_id: str):
        """复制图层"""
        canvas = self.canvas_editor.get_canvas()
        new_layer = canvas.duplicate_layer(layer_id)
        if new_layer:
            canvas.select_layer(new_layer.id)
            self.canvas_editor.canvas_widget.history.save_state("复制图层")
            self._update_status()
            self.canvas_editor.canvas_widget.update()
    
    def _on_property_changed(self, layer_id: str, prop: str, value):
        """属性变化"""
        canvas = self.canvas_editor.get_canvas()
        layer = canvas.get_layer(layer_id)
        if layer and hasattr(layer, prop):
            setattr(layer, prop, value)
            self.canvas_editor.canvas_widget.update()
    
    def _on_screen_added(self, index: int, is_blank: bool):
        """添加分屏"""
        canvas = self.canvas_editor.get_canvas()
        canvas.add_screen(is_blank=is_blank)
        self.canvas_editor.canvas_widget.history.save_state("添加分屏")
        self._update_status()
        self.canvas_editor.canvas_widget.update()
    
    def _on_screen_deleted(self, screen_id: str):
        """删除分屏"""
        canvas = self.canvas_editor.get_canvas()
        canvas.remove_screen(screen_id)
        self.canvas_editor.canvas_widget.history.save_state("删除分屏")
        self._update_status()
        self.canvas_editor.canvas_widget.update()
    
    def _on_screen_resized(self, screen_id: str, height: int):
        """调整分屏高度"""
        canvas = self.canvas_editor.get_canvas()
        canvas.resize_screen(screen_id, height)
        self.canvas_editor.canvas_widget.history.save_state("调整分屏高度")
        self._update_status()
        self.canvas_editor.canvas_widget.update()
    
    def _on_screen_renamed(self, screen_id: str, name: str):
        """重命名分屏"""
        canvas = self.canvas_editor.get_canvas()
        screen = canvas.get_screen(screen_id)
        if screen:
            screen.name = name
            self._update_status()
    
    def _on_insert_screen(self, screen_id: str, above: bool, is_blank: bool):
        """插入分屏"""
        canvas = self.canvas_editor.get_canvas()
        if above:
            canvas.insert_screen_above(screen_id, is_blank)
        else:
            canvas.insert_screen_below(screen_id, is_blank)
        self.canvas_editor.canvas_widget.history.save_state("插入分屏")
        self._update_status()
        self.canvas_editor.canvas_widget.update()
    
    def _on_asset_add(self, path: str):
        """添加素材到画布"""
        canvas = self.canvas_editor.get_canvas()
        layer = canvas.add_image_layer(path, 100, 100)
        canvas.select_layer(layer.id)
        self.canvas_editor.canvas_widget.history.save_state("添加图片")
        self._update_status()
        self.canvas_editor.canvas_widget.update()
        self._on_layer_selected(layer.id)
    
    def _on_copy_generated(self, text: str):
        """文案生成完成"""
        self.canvas_editor.add_text_layer(text, 100, 100)
    
    def _on_tool_selected(self, tool: str):
        """工具选择"""
        self.canvas_editor.canvas_widget.current_tool = tool
    
    def _on_add_screen(self, is_blank: bool):
        """添加分屏"""
        canvas = self.canvas_editor.get_canvas()
        canvas.add_screen(is_blank=is_blank)
        self.canvas_editor.canvas_widget.history.save_state("添加分屏")
        self._update_status()
        self.canvas_editor.canvas_widget.update()
    
    def _on_add_text(self):
        """添加文字"""
        text, ok = QInputDialog.getText(self, "添加文字", "输入文字内容:")
        if ok and text:
            self.canvas_editor.add_text_layer(text)
    
    def _on_layer_up(self):
        """图层上移"""
        canvas = self.canvas_editor.get_canvas()
        if canvas.selected_layer_id:
            canvas.move_layer_up(canvas.selected_layer_id)
            self._update_status()
            self.canvas_editor.canvas_widget.update()
    
    def _on_layer_down(self):
        """图层下移"""
        canvas = self.canvas_editor.get_canvas()
        if canvas.selected_layer_id:
            canvas.move_layer_down(canvas.selected_layer_id)
            self._update_status()
            self.canvas_editor.canvas_widget.update()
    
    def _on_delete_layer(self):
        """删除图层"""
        canvas = self.canvas_editor.get_canvas()
        if canvas.selected_layer_id:
            canvas.remove_layer(canvas.selected_layer_id)
            self.canvas_editor.canvas_widget.history.save_state("删除图层")
            self._update_status()
            self.canvas_editor.canvas_widget.update()
    
    def _on_remove_bg(self):
        """抠图"""
        try:
            canvas = self.canvas_editor.get_canvas()
            layer = canvas.get_selected_layer()
            
            if layer is None:
                QMessageBox.information(self, "提示", "请先选择一个图片图层")
                return
            
            from core.layer import ImageLayer
            if not isinstance(layer, ImageLayer):
                QMessageBox.information(self, "提示", "请选择图片图层")
                return
            
            from tools.remove_bg import remove_background_from_image, is_available, get_error_message
            if not is_available():
                err_msg = get_error_message()
                QMessageBox.warning(self, "提示", f"抠图功能不可用\n{err_msg}\n\n请安装: pip install rembg")
                return
            
            if layer._image is None:
                QMessageBox.warning(self, "提示", "图层图片未加载")
                return
            
            result = remove_background_from_image(layer._image)
            if result:
                layer.set_image(result)
                self.canvas_editor.canvas_widget.history.save_state("智能抠图")
                self.canvas_editor.canvas_widget.update()
                QMessageBox.information(self, "成功", "抠图完成")
            else:
                QMessageBox.warning(self, "失败", "抠图处理失败，请查看控制台日志")
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"抠图时发生错误:\n{str(e)}")
    
    def _on_upscale(self):
        """放大"""
        QMessageBox.information(self, "提示", "图片放大功能需要 Real-ESRGAN 模型，请参考文档下载")
    
    def _on_enhance(self):
        """增强"""
        try:
            canvas = self.canvas_editor.get_canvas()
            layer = canvas.get_selected_layer()
            
            if layer is None:
                QMessageBox.information(self, "提示", "请先选择一个图片图层")
                return
            
            from core.layer import ImageLayer
            if not isinstance(layer, ImageLayer):
                QMessageBox.information(self, "提示", "请选择图片图层")
                return
            
            if layer._image is None:
                QMessageBox.warning(self, "提示", "图层图片未加载")
                return
            
            from tools.enhance import enhance_image
            result = enhance_image(layer._image, "auto")
            if result:
                layer.set_image(result)
                self.canvas_editor.canvas_widget.history.save_state("图片增强")
                self.canvas_editor.canvas_widget.update()
                QMessageBox.information(self, "成功", "增强完成")
            else:
                QMessageBox.warning(self, "失败", "图片增强失败")
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"增强时发生错误:\n{str(e)}")
    
    def _on_new(self):
        """新建"""
        from core.canvas import Canvas
        self.canvas_editor.set_canvas(Canvas())
        self._update_status()
    
    def _on_open(self):
        """打开"""
        path, _ = QFileDialog.getOpenFileName(
            self, "打开项目",
            os.path.expanduser("~"),
            "项目文件 (*.ecom);;所有文件 (*)"
        )
        if path:
            try:
                from core.canvas import Canvas
                canvas = Canvas.load(path)
                self.canvas_editor.set_canvas(canvas)
                self._update_status()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"打开失败: {e}")
    
    def _on_save(self):
        """保存"""
        self._on_save_as()
    
    def _on_save_as(self):
        """另存为"""
        path, _ = QFileDialog.getSaveFileName(
            self, "保存项目",
            os.path.expanduser("~/untitled.ecom"),
            "项目文件 (*.ecom);;所有文件 (*)"
        )
        if path:
            try:
                self.canvas_editor.get_canvas().save(path)
                QMessageBox.information(self, "成功", "保存成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def _on_export(self):
        """导出"""
        dialog = ExportDialog(self.canvas_editor.get_canvas(), self)
        dialog.exec()
    
    def _on_about(self):
        """关于"""
        QMessageBox.about(
            self, f"关于 {APP_NAME}",
            f"{APP_NAME}\n\n"
            "专业电商美工工作台\n"
            "版本 1.0.0\n\n"
            "帮助电商美工快速完成详情页落地"
        )
    
    def _on_tasks_updated(self, tasks):
        """任务列表更新"""
        self.task_panel.set_tasks(tasks)
    
    def _on_new_task(self, task):
        """收到新任务"""
        self.tray.show_new_task_notification(task.title)
    
    def _on_task_selected(self, task):
        """任务被选中"""
        self.task_label.setText(f"任务: {task.title[:20]}")
    
    def _show_window(self):
        """显示窗口"""
        self.showNormal()
        self.activateWindow()
    
    def _quit_app(self):
        """退出应用"""
        task_poller.stop()
        QApplication.quit()
    
    def closeEvent(self, event: QCloseEvent):
        """关闭事件 - 最小化到托盘"""
        event.ignore()
        self.hide()
        self.tray.show_message("提示", f"{APP_NAME} 已最小化到系统托盘")
    
    def show_login(self):
        """显示登录对话框"""
        dialog = LoginDialog(self)
        dialog.login_success.connect(self._on_login_success)
        if dialog.exec() != LoginDialog.DialogCode.Accepted:
            # 登录取消，退出应用
            self._quit_app()
    
    def _on_login_success(self, user):
        """登录成功"""
        self.connection_label.setText(f"● {user.name}")
        self._start_polling()
    
    def _on_middleware_data_received(self, data):
        """处理来自中台的数据"""
        print(f"收到中台数据: {data}")
        # 这里可以根据中台传来的数据进行相应处理
        # 例如更新画布、切换任务等
        
        if data.get('type') == 'update_canvas':
            # 如果中台发送了画布更新数据
            pass
        elif data.get('type') == 'switch_task':
            # 如果中台请求切换任务
            pass
        # 可以根据需要添加更多处理逻辑
    
    def send_to_middleware(self, data):
        """向中台发送数据"""
        if hasattr(self, 'middleware_panel'):
            self.middleware_panel.send_to_web(data)
