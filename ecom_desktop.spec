# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件
使用方法: python -m PyInstaller ecom_desktop.spec
"""

import sys
import os

block_cipher = None

# 项目根目录
project_root = os.path.dirname(os.path.abspath(SPEC))

# 收集数据文件
datas = [
    # 添加资源文件夹
    (os.path.join(project_root, 'assets'), 'assets'),
    (os.path.join(project_root, 'templates'), 'templates'),
    (os.path.join(project_root, 'models'), 'models'),
]

# 隐式导入（只包含必需的）
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtWidgets',
    'PyQt6.QtGui',
    'PIL',
    'PIL.Image',
    'PIL.ImageEnhance',
    'PIL.ImageFilter',
    'numpy',
    'requests',
]

# 排除不需要的模块（包括可选的重型依赖）
excludes = [
    'tkinter',
    'matplotlib',
    'scipy',
    'pandas',
    'jupyter',
    'IPython',
    # 排除可选的图像处理库（它们会在运行时按需加载）
    'rembg',
    'onnxruntime',
    'cv2',
    'opencv-python',
]

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EcomDesigner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以设置图标: icon='assets/icons/app.ico'
)
