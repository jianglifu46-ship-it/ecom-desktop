"""
中台面板 - 集成web界面
"""
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    print("PyQt6 WebEngine组件未安装，请运行: pip install PyQt6-WebEngine")
    # 创建一个替代的提示组件
    from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
    class QWebEngineView(QLabel):
        def __init__(self):
            super().__init__("WebEngine未安装\n请运行: pip install PyQt6-WebEngine")
            self.setStyleSheet("color: red; font-size: 16px; padding: 50px;")
        
        def load(self, url):
            pass
        
        def reload(self):
            pass
        
        def page(self):
            class MockPage:
                def setWebChannel(self, channel):
                    pass
                def runJavaScript(self, script):
                    pass
                class MockLoadFinished:
                    def connect(self, func):
                        pass
                loadFinished = MockLoadFinished()
            return MockPage()

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QObject
from PyQt6.QtWebChannel import QWebChannel
import json
import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])


class WebChannelBridge(QObject):
    """Web与Qt通信的桥接对象"""
    
    # 定义信号
    data_received = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
    
    def send_to_web(self, data):
        """发送数据到web页面"""
        return json.dumps(data)
    
    def receive_from_web(self, data_json):
        """接收来自web页面的数据"""
        try:
            data = json.loads(data_json)
            self.data_received.emit(data)
        except json.JSONDecodeError:
            print("Web数据解析错误:", data_json)


class MiddlewarePanel(QWidget):
    """中台面板"""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._setup_web_channel()
        self._load_web_content()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建Web视图
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
    
    def _setup_web_channel(self):
        """设置Web通道"""
        # 创建通信桥接对象
        self.bridge = WebChannelBridge()
        
        # 创建Web通道并注册桥接对象
        self.channel = QWebChannel()
        self.channel.registerObject("qtBridge", self.bridge)
        
        # 设置Web视图的通道
        self.web_view.page().setWebChannel(self.channel)
        
        # 连接信号
        self.bridge.data_received.connect(self._on_web_data_received)
    
    def _load_web_content(self):
        """加载网页内容"""
        # 加载中台页面
        self.web_view.load(QUrl("https://ecom-admin.manus.space/"))
        
        # 页面加载完成后注入WebChannel支持代码
        self.web_view.page().loadFinished.connect(self._inject_webchannel_script)
    
    def _inject_webchannel_script(self, success):
        """注入WebChannel支持脚本"""
        if not success:
            print("页面加载失败")
            return
        
        # 注入WebChannel支持代码
        script = """
        // 注入Qt WebChannel支持
        var script = document.createElement('script');
        script.src = 'qrc:///qtwebchannel/qwebchannel.js';
        document.head.appendChild(script);
        
        script.onload = function() {
            new QWebChannel(qt.webChannelTransport, function(channel) {
                // 获取Qt桥接对象
                window.qtBridge = channel.objects.qtBridge;
                
                // 定义接收Qt数据的函数
                window.receiveFromQt = function(data) {
                    console.log('收到Qt数据:', data);
                    // 可以在这里处理来自Qt的数据
                    // 例如更新页面内容或触发特定操作
                };
                
                // 页面加载完成，向Qt发送初始化消息
                if (window.qtBridge) {
                    window.qtBridge.receive_from_web(JSON.stringify({
                        type: 'page_loaded',
                        message: '页面加载完成'
                    }));
                }
                
                console.log('WebChannel连接成功');
            });
        };
        """
        
        self.web_view.page().runJavaScript(script)
    
    def _on_web_data_received(self, data):
        """处理来自web的数据"""
        print("收到web数据:", data)
        # 这里可以根据需要处理来自web页面的数据
        # 例如更新其他面板的状态等
    
    def send_to_web(self, data):
        """发送数据到web页面"""
        """通过WebChannel向网页发送数据"""
        if hasattr(self, 'web_view') and self.web_view:
            # 通过JavaScript调用
            script = f"if(window.receiveFromQt) {{ window.receiveFromQt({json.dumps(data)}); }}"
            self.web_view.page().runJavaScript(script)
    
    def reload_page(self):
        """重新加载页面"""
        self.web_view.reload()
    
    def get_web_view(self):
        """获取Web视图对象"""
        return self.web_view