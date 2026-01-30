# 电商详情页管理系统 - 安装与使用指南

## 一、环境要求

- **操作系统**：Windows 10/11（推荐）、macOS、Linux
- **Python**：3.10 或更高版本
- **内存**：建议 8GB 以上
- **硬盘**：至少 500MB 可用空间

## 二、安装步骤

### 方式一：使用安装脚本（推荐）

1. 下载并解压项目文件
2. 双击运行 `install.bat`
3. 按提示完成安装

### 方式二：手动安装

```bash
# 1. 进入项目目录
cd ecom-desktop

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 安装可选依赖（智能抠图）
pip install rembg
```

## 三、运行程序

### 方式一：使用运行脚本

双击 `run.bat`

### 方式二：命令行运行

```bash
# 激活虚拟环境后
python main.py
```

## 四、打包为 EXE

### 方式一：使用打包脚本

双击 `build.bat`，打包完成后在 `dist` 目录找到 exe 文件。

### 方式二：手动打包

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包
pyinstaller ecom_desktop.spec

# 输出在 dist/电商详情页管理系统.exe
```

## 五、配置说明

### API 地址配置

编辑 `config.py` 文件：

```python
class APIConfig:
    # 开发环境
    DEV_BASE_URL = "https://3000-xxx.manus.computer"
    # 生产环境
    PROD_BASE_URL = "https://ecom-admin.manus.space"
    
    # 切换环境
    USE_PRODUCTION = True  # True 使用生产环境，False 使用开发环境
```

### 主题配置

编辑 `config.py` 中的 `UIConfig.THEME` 修改颜色主题。

## 六、可选功能安装

### 智能抠图（Rembg）

```bash
pip install rembg
```

首次使用时会自动下载模型（约 170MB）。

### 图片放大（Real-ESRGAN）

1. 从 [GitHub Releases](https://github.com/xinntao/Real-ESRGAN/releases) 下载 `realesrgan-ncnn-vulkan`
2. 解压到项目的 `models` 目录
3. 确保 `realesrgan-ncnn-vulkan.exe` 在 `models` 目录下

## 七、常见问题

### Q: 启动时提示"找不到 PyQt6"

A: 确保已激活虚拟环境并安装依赖：
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### Q: 抠图功能不可用

A: 安装 rembg：
```bash
pip install rembg
```

### Q: 打包后 exe 无法运行

A: 检查是否缺少依赖，尝试在命令行运行查看错误信息：
```bash
dist\电商详情页管理系统.exe
```

### Q: 登录失败

A: 检查 `config.py` 中的 API 地址是否正确，确保网络连接正常。

## 八、快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+N | 新建 |
| Ctrl+O | 打开 |
| Ctrl+S | 保存 |
| Ctrl+E | 导出 |
| Ctrl+Z | 撤销 |
| Ctrl+Shift+Z | 重做 |
| Delete | 删除图层 |
| T | 文字工具 |
| R | 矩形工具 |
| V | 选择工具 |
| Ctrl+] | 图层上移 |
| Ctrl+[ | 图层下移 |
| Ctrl+= | 放大 |
| Ctrl+- | 缩小 |
| Ctrl+0 | 适应窗口 |
| 方向键 | 移动图层 1px |
| Shift+方向键 | 移动图层 10px |

## 九、技术支持

如有问题，请联系开发团队。
