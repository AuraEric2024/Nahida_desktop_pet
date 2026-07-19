# 纳西妲桌宠 / Nahida Desktop Pet

一个基于 Live2D 的桌面宠物应用，让《原神》角色纳西妲陪伴你的桌面时光。支持鼠标追踪和摄像头动作捕捉，纳西妲会跟着你的头部动作一起动。

A Live2D-based desktop pet featuring Nahida from Genshin Impact. Supports mouse tracking and webcam motion capture — Nahida mirrors your head movements in real time.

## 功能特性 / Features

### 鼠标模式（默认）/ Mouse Mode (Default)

- **目光追踪** — 纳西妲的眼睛、头部和身体会跟随鼠标指针移动，无论鼠标在哪里
  **Gaze Tracking** — Nahida's eyes, head and body follow your cursor anywhere on screen
- **自然眨眼** — 自动眨眼与呼吸动作，栩栩如生
  **Natural Blinking** — Automatic blinking and breathing animations
- **点击互动** — 全局左键点击触发随机表情 + 音效，右键点击播放专属音效
  **Click Interaction** — Global left-click triggers random expressions with sound; right-click plays a unique sound
- **点击音效开关** — 托盘菜单可一键关闭全局点击音效，保留表情互动
  **Sound Toggle** — Mute global click sounds from the tray menu while keeping expressions
- **自由缩放** — 鼠标滚轮调节大小（0.7x ~ 1.0x）
  **Free Scaling** — Adjust size with mouse wheel (0.7x ~ 1.0x)
- **拖拽移动** — 按住纳西妲即可拖动到桌面任意位置
  **Drag & Drop** — Drag Nahida anywhere on your desktop
- **系统托盘** — 托盘图标可快速显示/隐藏、开关摄像头追踪、开关音效或退出
  **System Tray** — Quick show/hide, toggle camera tracking, toggle sounds, or quit

### 摄像头模式（可开关）/ Camera Mode (Toggleable)

完全本地运行的人脸动作捕捉，不依赖任何云端服务，不上传任何画面。

Fully on-device face motion capture — no cloud, no video upload.

- **身体探头** — 左右转头时纳西妲的身体会跟着探出去，动作幅度更大
  **Body Lean** — Body leans side-to-side as you turn your head
- **头部跟随** — 点头、转头、歪头都会被识别并同步到纳西妲的头部
  **Head Tracking** — Nodding, turning, and tilting your head are mirrored
- **歪头侧倾** — 头部向肩膀倾斜时，纳西妲也会歪头（ParamAngleZ）
  **Head Tilt** — Tilting toward your shoulder makes Nahida tilt too
- **嘴巴张合** — 你张嘴纳西妲也张嘴，说话/唱歌都会跟随
  **Mouth Sync** — Open your mouth and Nahida opens hers; follows speech and singing
- **呼吸感晃动** — 静止时身体会有轻微的呼吸感摇摆，不死板
  **Idle Sway** — Subtle breathing-like sway when you hold still

## 技术栈 / Tech Stack

- **渲染引擎 / Rendering**: Live2D Cubism SDK（通过 live2d-py 绑定）
- **图形框架 / GUI Framework**: PyQt6 + QOpenGLWidget
- **音频播放 / Audio**: pygame.mixer
- **全局鼠标监听 / Global Mouse**: Win32 API (win32gui / win32api)
- **人脸捕捉 / Face Capture**: MediaPipe Tasks Vision（Face Landmarker，本地推理）
- **摄像头采集 / Camera Capture**: OpenCV (cv2)
- **打包 / Packaging**: PyInstaller

## 目录结构 / Project Structure

```
纳西妲桌宠/
├── main.py                    # 主程序 / Main program
├── camera_tracker.py          # 摄像头人脸追踪模块 / Webcam face tracking module
├── face_landmarker.task       # MediaPipe 人脸模型 / MediaPipe face model
├── Nahida_model/              # Live2D 模型资源 / Live2D model assets
│   ├── Nahida_1080.model3.json
│   ├── Nahida_1080.moc3
│   ├── *.exp3.json            # 表情文件 / Expression files
│   └── ...
├── audio/                     # 音效文件 / Sound files
│   ├── click.ogg              # 左键音效 / Left-click sound
│   └── barely.ogg             # 右键音效 / Right-click sound
└── dist/                      # 构建产物 / Build output
    └── NahidaPet.exe
```

## 快速开始 / Quick Start

### 直接使用 / Just Use It

从 GitHub Release 下载 `NahidaPet.exe`，双击运行即可，无需安装 Python 环境。

Download `NahidaPet.exe` from the GitHub Release and double-click to run — no Python installation required.

> 摄像头人脸模型 `face_landmarker.task` 已内置在 EXE 中，无需额外下载。
> The face model is bundled inside the EXE — no separate download needed.

### 开发运行 / Development

```bash
pip install live2d-py PyQt6 PyOpenGL pygame pywin32 mediapipe opencv-python
python main.py
```

> 首次运行若项目根目录没有 `face_landmarker.task`，程序会自动从 Google 下载到系统临时目录。
> If `face_landmarker.task` is missing, it will be auto-downloaded to the system temp directory on first run.

## 操作说明 / Controls

| 操作 / Action | 效果 / Effect |
|------|--------|
| 鼠标移动 / Move mouse | 纳西妲看向鼠标 / Nahida looks at cursor |
| 全局左键 / Global left-click | click 音效 + 随机表情 / click sound + random expression |
| 全局右键 / Global right-click | barely 音效 / barely sound |
| 滚轮 / Mouse wheel | 缩放大小 / Scale size |
| 按住拖拽 / Drag | 移动窗口 / Move window |
| 托盘右键 → 摄像头头部追踪 / Tray → Camera Tracking | 开关摄像头模式 / Toggle camera mode |
| 托盘右键 → 点击音效 / Tray → Click Sound | 开关点击音效 / Toggle click sounds |

## 打包 / Build

```bash
python -m PyInstaller --noconfirm --onefile --windowed ^
  --name NahidaPet ^
  --add-data "Nahida_model;Nahida_model" ^
  --add-data "audio;audio" ^
  --add-data "face_landmarker.task;." ^
  --hidden-import win32gui --hidden-import win32api --hidden-import win32con ^
  --collect-all live2d --collect-submodules mediapipe ^
  main.py
```

## 致谢 / Acknowledgments

- Live2D Cubism SDK by Live2D Inc.
- [live2d-py](https://github.com/Arkueid/live2d-py) by Arkueid
- [MediaPipe](https://developers.google.com/mediapipe) by Google
- 纳西妲角色版权归 miHoYo / HoYoverse 所有，本项目仅供学习交流
  Nahida character © miHoYo / HoYoverse. This project is for educational purposes only.
