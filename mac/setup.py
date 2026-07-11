# -*- coding: utf-8 -*-
"""
py2app 打包配置（Mac 专用）
用法：在 mac/ 目录下执行
    python setup.py py2app
生成 dist/NahidaPet.app
"""

from setuptools import setup

APP = ["main.py"]

OPTIONS = {
    "argv_emulation": False,
    "packages": [],
    "includes": [
        "live2d", "live2d.v3",
        "pygame", "pygame.mixer",
        "PyQt6", "PyQt6.QtCore", "PyQt6.QtGui",
        "PyQt6.QtWidgets", "PyQt6.QtOpenGLWidgets",
        "Quartz", "AppKit",
    ],
    # 把整个 Nahida_model 和 audio 文件夹打包进 .app/Contents/Resources/
    "resources": ["../Nahida_model", "../audio"],
    "plist": {
        "LSUIElement": True,  # 不在 Dock 显示，不显示菜单栏（桌宠必备）
        "CFBundleName": "NahidaPet",
        "CFBundleDisplayName": "纳西妲桌宠",
        "NSAccessibilityUsageDescription": "需要辅助功能权限来监听全局鼠标点击。",
    },
}

setup(
    app=APP,
    data_files=[],
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
