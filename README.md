# 电商详情页管理系统 - 桌面客户端

专业电商美工工作台，帮助美工快速完成详情页设计落地工作。

## 功能特性

### 核心功能
- **任务管理**：接收 Web 端分配的设计任务，实时提醒
- **画布编辑器**：750px 专业画布，支持图层管理、拖拽缩放
- **分屏结构**：灵活的分屏管理，支持插入新屏、添加留白
- **导出功能**：按分屏切图导出，自动符合平台规范

### 图像处理
- **智能抠图**：基于 Rembg 的一键抠图
- **图片放大**：基于 Real-ESRGAN 的超分辨率放大
- **图片增强**：锐化、降噪、对比度调整

### AI 助手
- **智能文案生成**：AI 生成产品卖点文案
- **一键排版优化**：AI 分析并优化排版
- **背景生成**：AI 生成商品背景

## 安装

### 环境要求
- Python 3.10+
- Windows 10/11（推荐）或 macOS/Linux

### 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装可选依赖（智能抠图）
pip install rembg
```

### 运行

```bash
python main.py
```

## 打包为 EXE

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包
pyinstaller ecom_desktop.spec

# 输出在 dist/ 目录
```

## 项目结构

```
ecom-desktop/
├── main.py              # 入口文件
├── config.py            # 配置文件
├── requirements.txt     # 依赖
├── ecom_desktop.spec    # 打包配置
├── core/                # 核心模块
│   ├── layer.py         # 图层系统
│   ├── canvas.py        # 画布管理
│   ├── history.py       # 历史记录
│   └── export.py        # 导出逻辑
├── services/            # 服务模块
│   ├── api_client.py    # API 客户端
│   ├── notification.py  # 通知服务
│   ├── task_poller.py   # 任务轮询
│   └── file_watcher.py  # 文件监控
├── tools/               # 图像处理工具
│   ├── remove_bg.py     # 抠图
│   ├── upscale.py       # 放大
│   └── enhance.py       # 增强
└── ui/                  # UI 组件
    ├── main_window.py   # 主窗口
    ├── canvas_editor.py # 画布编辑器
    ├── toolbar.py       # 工具栏
    ├── task_panel.py    # 任务面板
    ├── layer_panel.py   # 图层面板
    ├── property_panel.py# 属性面板
    ├── screen_panel.py  # 分屏面板
    ├── assets_panel.py  # 素材面板
    ├── ai_panel.py      # AI 助手面板
    └── export_dialog.py # 导出对话框
```

## 配置

编辑 `config.py` 修改配置：

```python
# API 地址
API_BASE_URL = "https://ecom-admin.manus.space"

# 主题颜色
UIConfig.THEME = {
    'accent': '#3B82F6',
    # ...
}
```

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+N | 新建 |
| Ctrl+O | 打开 |
| Ctrl+S | 保存 |
| Ctrl+E | 导出 |
| Ctrl+Z | 撤销 |
| Ctrl+Shift+Z | 重做 |
| Delete | 删除图层 |
| T | 添加文字 |
| R | 添加矩形 |
| Ctrl+] | 图层上移 |
| Ctrl+[ | 图层下移 |
| Ctrl+= | 放大 |
| Ctrl+- | 缩小 |
| Ctrl+0 | 适应窗口 |
| 方向键 | 移动图层 |
| Shift+方向键 | 快速移动 |

## API 接口

客户端与 Web 端通过 tRPC 风格 API 通信：

- `POST /api/trpc/auth.login` - 登录
- `GET /api/trpc/task.myTasks` - 获取任务列表
- `GET /api/trpc/task.detail` - 获取任务详情
- `POST /api/trpc/task.accept` - 接受任务
- `POST /api/trpc/task.submitDesign` - 提交设计稿

## 许可证

MIT License
