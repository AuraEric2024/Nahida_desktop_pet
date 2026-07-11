# 纳西妲桌宠 / Nahida Desktop Pet

一个基于 Live2D 的桌面宠物应用，让《原神》角色纳西妲陪伴你的桌面时光。

A Live2D-based desktop pet application featuring Nahida from Genshin Impact.

## 功能特性 / Features

- **目光追踪** — 纳西妲的眼睛和头部会跟随鼠标指针移动，无论鼠标在哪里
  **Gaze Tracking** — Nahida's eyes and head follow your mouse cursor anywhere on screen
- **自然眨眼** — 自动眨眼与呼吸动作，栩栩如生
  **Natural Blinking** — Automatic blinking and breathing animations
- **点击互动** — 全局左键点击触发随机表情 + 音效，右键点击播放专属音效
  **Click Interaction** — Global left-click triggers random expressions with sound effects; right-click plays a unique sound
- **自由缩放** — 鼠标滚轮调节大小（0.7x ~ 1.0x）
  **Free Scaling** — Adjust size with mouse wheel (0.7x ~ 1.0x)
- **拖拽移动** — 按住纳西妲即可拖动到桌面任意位置
  **Drag & Drop** — Drag Nahida anywhere on your desktop
- **系统托盘** — 托盘图标可快速显示/隐藏或退出
  **System Tray** — Quick show/hide or quit from the tray icon

## 平台支持 / Platform Support

| 平台 / Platform | 状态 / Status | 文件 / File |
|------|--------|---------|
| Windows | ✅ 已支持 / Supported | `NahidaPet.exe` |
| macOS | ✅ 已支持 / Supported | `NahidaPet.app` |

## 技术栈 / Tech Stack

- **渲染引擎 / Rendering**: Live2D Cubism SDK（通过 live2d-py 绑定）
- **图形框架 / GUI Framework**: PyQt6 + QOpenGLWidget
- **音频播放 / Audio**: pygame.mixer
- **全局鼠标监听 / Global Mouse**: Win32 API (Windows) / Quartz + AppKit (macOS)
- **打包 / Packaging**: PyInstaller (Windows) / py2app (macOS)

## 目录结构 / Project Structure

```
纳西妲桌宠/
├── main.py                    # Windows 版主程序 / Windows main program
├── Nahida_model/              # Live2D 模型资源 / Live2D model assets
│   ├── Nahida_1080.model3.json
│   ├── Nahida_1080.moc3
│   ├── *.exp3.json            # 表情文件 / Expression files
│   └── ...
├── audio/                     # 音效文件 / Sound files
│   ├── click.ogg
│   └── barely.ogg
├── mac/                       # Mac 版源码 / macOS source
│   ├── main.py
│   ├── setup.py
│   └── requirements.txt
├── .github/workflows/
│   └── build-mac.yml          # Mac 自动构建工作流 / macOS build workflow
└── dist/                      # 构建产物 / Build output
    └── NahidaPet.exe
```

## 快速开始 / Quick Start

### Windows

直接双击 `dist/NahidaPet.exe` 运行，无需安装 Python 环境。
Simply double-click `dist/NahidaPet.exe` to run — no Python installation required.

### macOS

从 GitHub Actions 下载 `NahidaPet.app`，首次运行需：
Download `NahidaPet.app` from GitHub Actions. On first launch:

1. 右键点击 .app → 打开 / Right-click the .app → Open
2. 在"系统设置 → 隐私与安全性 → 辅助功能"中授权 / Grant Accessibility permission in System Settings → Privacy & Security → Accessibility

## 操作说明 / Controls

| 操作 / Action | 效果 / Effect |
|------|--------|
| 鼠标移动 / Move mouse | 纳西妲看向鼠标 / Nahida looks at cursor |
| 全局左键 / Global left-click | click 音效 + 随机表情 / click sound + random expression |
| 全局右键 / Global right-click | barely 音效 / barely sound |
| 滚轮 / Mouse wheel | 缩放大小 / Scale size |
| 按住拖拽 / Drag | 移动窗口 / Move window |

## 开发运行 / Development

```bash
# Windows
pip install live2d-py PyQt6 PyOpenGL pygame pywin32
python main.py

# macOS
cd mac
pip install -r requirements.txt
python main.py
```

## 致谢 / Acknowledgments

- Live2D Cubism SDK by Live2D Inc.
- [live2d-py](https://github.com/Arkueid/live2d-py) by Arkueid
- 纳西妲角色版权归 miHoYo / HoYoverse 所有，本项目仅供学习交流
  Nahida character © miHoYo / HoYoverse. This project is for educational purposes only.
