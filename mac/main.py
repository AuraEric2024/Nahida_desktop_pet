# -*- coding: utf-8 -*-
"""
纳西妲 Live2D 桌宠 (Mac 版)
功能：
  1. 看向鼠标指针（全局追踪，鼠标在窗口外也会看过去）
  2. 全局左键点击 → 播放 click 音效 + 随机表情
  3. 全局右键点击 → 播放 barely 音效
  4. 自然眨眼（自动，无需操作）
  5. 滚轮自由缩放大小（0.7 ~ 1.0）
  6. 按住拖拽移动窗口
  7. 系统托盘图标（单击显示/隐藏，右键菜单退出）

依赖：live2d-py、PyQt6、PyOpenGL、pygame、pyobjc-framework-Quartz、pyobjc-framework-Cocoa

注意：全局鼠标点击监听需要"辅助功能"权限。
首次运行时 Mac 会弹窗提示授权，请在
"系统设置 → 隐私与安全性 → 辅助功能"中允许此应用。
"""

import sys
import os

import pygame.mixer
import live2d.v3 as live2d
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QSurfaceFormat
from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu,
)
from PyQt6.QtOpenGLWidgets import QOpenGLWidget

# Mac 专用的全局鼠标 API
from Quartz import CGEventGetLocation
from AppKit import NSEvent


# ---------- 资源路径 ----------
def resource_path(relative_path: str) -> str:
    """获取资源绝对路径，兼容开发环境与 py2app 打包后的环境"""
    if getattr(sys, "frozen", False):
        # py2app 打包后：资源在 .app/Contents/Resources/
        base = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), "Resources")
    else:
        # 开发环境：从 mac/ 目录引用上一级的资源
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base, relative_path)


MODEL_PATH = resource_path(os.path.join("Nahida_model", "Nahida_1080.model3.json"))
ICON_PATH = resource_path(os.path.join("Nahida_model", "icon.jpg"))
AUDIO_CLICK_PATH = resource_path(os.path.join("audio", "click.ogg"))
AUDIO_BARELY_PATH = resource_path(os.path.join("audio", "barely.ogg"))


# Mac 鼠标事件掩码（NSEventMask 常量）
NS_LEFT_MOUSE_DOWN_MASK = 1 << 1   # 左键按下
NS_RIGHT_MOUSE_DOWN_MASK = 1 << 3  # 右键按下


class NahidaPet(QOpenGLWidget):
    """Live2D 渲染控件，本身就是一个无边框透明置顶窗口"""

    def __init__(self):
        super().__init__()
        # 无边框 + 置顶 + 不在 Dock 显示（Tool 窗口）
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        # 透明背景：让窗口没贴图的地方直接透出桌面
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("纳西妲桌宠")
        self.resize(380, 560)

        self.model = None
        self.scale = 1.0        # 模型缩放（滚轮调节）
        self.offset_x = 0.0
        self.offset_y = 0.0

        # 初始化音频播放器（pygame.mixer）
        pygame.mixer.init()
        self._snd_click = pygame.mixer.Sound(AUDIO_CLICK_PATH)
        self._snd_barely = pygame.mixer.Sound(AUDIO_BARELY_PATH)

        # 拖拽窗口用
        self._drag_offset = None
        self._press_moved = False

        # 当前鼠标局部坐标（全局轮询得到，用于眼球追踪）
        self._mouse_local = (self.width() / 2, self.height() / 2)
        # 视线/头部平滑值（用于缓动跟随，避免抖动）
        self._look_x = 0.0
        self._look_y = 0.0

        # 设置全局鼠标点击监听（Mac 需要"辅助功能"权限）
        self._setup_global_mouse_monitor()

        # 主循环定时器：约 60 FPS
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    def _setup_global_mouse_monitor(self):
        """设置全局鼠标点击监听。
        Mac 上使用 NSEvent.addGlobalMonitorForEventsMatchingMask 监听全局事件，
        首次运行需要授权"辅助功能"权限。"""
        def on_left_down(event):
            # 全局左键按下 → click 音效 + 随机表情（切到主线程执行）
            QTimer.singleShot(0, self._on_global_left_click)

        def on_right_down(event):
            # 全局右键按下 → barely 音效（切到主线程执行）
            QTimer.singleShot(0, self._on_global_right_click)

        # addGlobalMonitor 只监听其他应用的事件（不监听本应用窗口的点击）
        # 返回的 monitor 对象必须保持引用，否则会被释放导致监听失效
        self._left_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NS_LEFT_MOUSE_DOWN_MASK, on_left_down
        )
        self._right_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NS_RIGHT_MOUSE_DOWN_MASK, on_right_down
        )

    def _on_global_left_click(self):
        """全局左键点击回调（主线程执行）"""
        if self.model:
            self._snd_click.play()
            self.model.SetRandomExpression()

    def _on_global_right_click(self):
        """全局右键点击回调（主线程执行）"""
        self._snd_barely.play()

    # ---------- OpenGL 生命周期 ----------
    def initializeGL(self):
        live2d.glInit()
        self.model = live2d.LAppModel()
        self.model.LoadModelJson(MODEL_PATH)
        # 开启自动眨眼（自然眨眼）与自动呼吸
        self.model.SetAutoBlinkEnable(True)
        self.model.SetAutoBreathEnable(True)
        self.model.Resize(self.width(), self.height())
        # 中性点（眼睛位置）在首次绘制后才能扫描，先用窗口中心占位
        self._neutral_x = self.width() / 2
        self._neutral_y = self.height() / 2
        self._neutral_detected = False

    def _detect_neutral(self):
        """扫描模型，找到眼睛部件所在位置作为视线中性点。
        必须在至少一次 Draw 之后调用（HitPart 依赖已渲染的顶点数据）。"""
        w, h = self.width(), self.height()
        xs, ys = [], []
        step = 8
        for yy in range(0, h, step):
            for xx in range(0, w, step):
                parts = self.model.HitPart(xx, yy, False)
                if "Part4" in parts or "Part15" in parts:
                    xs.append(xx)
                    ys.append(yy)
        if xs:
            self._neutral_x = sum(xs) / len(xs)
            self._neutral_y = sum(ys) / len(ys)
        self._neutral_detected = True

    def resizeGL(self, w, h):
        if self.model:
            self.model.Resize(w, h)
            # 窗口尺寸变了，中性点需要重新扫描
            self._neutral_detected = False

    def paintGL(self):
        live2d.clearBuffer()  # 透明清屏
        if not self.model:
            return
        # 1. 更新模型（自动眨眼、呼吸、物理演算在此生效）
        self.model.Update()
        # 2. 应用视线参数（头部/眼球/身体朝向追踪鼠标）
        self._apply_look()
        # 3. 缩放与偏移
        self.model.SetScale(self.scale)
        self.model.SetOffset(self.offset_x, self.offset_y)
        # 4. 绘制
        self.model.Draw()
        # 5. 首次绘制完成后，扫描眼睛位置作为中性点
        if not self._neutral_detected:
            self._detect_neutral()
        # 6. 更新视线目标值（供下一帧使用）
        self._update_look_target()

    def _update_look_target(self):
        """根据鼠标位置计算视线目标值（归一化到 -1..1）"""
        nx, ny = self._neutral_x, self._neutral_y
        hw, hh = self.width() / 2, self.height() / 2
        tx = (self._mouse_local[0] - nx) / hw   # 鼠标在右 → 正
        ty = (ny - self._mouse_local[1]) / hh   # 鼠标在上 → 正
        # 缓动跟随（0.2 较灵敏但不抖）
        self._look_x += (tx - self._look_x) * 0.2
        self._look_y += (ty - self._look_y) * 0.2

    def _apply_look(self):
        """把当前视线值写入模型参数（头部/眼球/身体朝向）"""
        lx, ly = self._look_x, self._look_y
        self.model.SetParameterValue("ParamAngleX", max(-30, min(30, lx * 30)))
        self.model.SetParameterValue("ParamAngleY", max(-30, min(30, ly * 30)))
        self.model.SetParameterValue("ParamEyeBallX", max(-1, min(1, lx)))
        self.model.SetParameterValue("ParamEyeBallY", max(-1, min(1, ly)))
        self.model.SetParameterValue("ParamBodyAngleX", max(-10, min(10, lx * 10)))
        self.model.SetParameterValue("ParamBodyAngleY", max(-10, min(10, ly * 10)))

    # ---------- 主循环 ----------
    def _tick(self):
        if not self.model:
            return
        # Mac 上获取全局鼠标位置：CGEventGetLocation 返回 Quartz 坐标（原点在左下角）
        pt = CGEventGetLocation(None)
        # 获取屏幕高度，用于 y 坐标转换（Quartz 坐标 → Qt 坐标）
        # Quartz 原点在左下角，Qt 原点在左上角，需要翻转 y
        screen = QApplication.primaryScreen()
        screen_h = screen.size().height()
        global_x = pt.x
        global_y = screen_h - pt.y

        # 转换为窗口局部坐标
        g = self.geometry()
        lx = global_x - g.x()
        ly = global_y - g.y()
        self._mouse_local = (lx, ly)

        # 触发重绘（paintGL 中会更新视线）
        self.update()

    # ---------- 鼠标交互 ----------
    def mousePressEvent(self, event):
        # 整个窗口区域都可拖拽（不要求精确点在模型贴图上）
        self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        self._press_moved = False

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None:
            gp = event.globalPosition().toPoint()
            # 超过 4 像素才算拖拽，避免点击时手抖误判为移动
            if not self._press_moved:
                start = gp - self._drag_offset - self.frameGeometry().topLeft()
                if abs(start.x()) < 4 and abs(start.y()) < 4:
                    return
            self.move(gp - self._drag_offset)
            self._press_moved = True

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        # 音效和表情已由全局监听器处理，这里只清理拖拽状态

    def wheelEvent(self, event):
        # 滚轮缩放，范围 0.7 ~ 1.0（不会超出窗口）
        delta = event.angleDelta().y() / 1200.0
        self.scale = max(0.7, min(1.0, self.scale + delta))
        self.update()

    # ---------- 关闭 ----------
    def closeEvent(self, event):
        self.timer.stop()
        if self.model:
            del self.model
            self.model = None
        live2d.dispose()
        event.accept()


def main():
    # 设置 OpenGL 默认格式：带 alpha 通道，保证透明背景生效
    fmt = QSurfaceFormat()
    fmt.setAlphaBufferSize(8)
    QSurfaceFormat.setDefaultFormat(fmt)

    live2d.init()
    app = QApplication(sys.argv)

    pet = NahidaPet()
    pet.show()

    # 系统托盘图标
    tray = QSystemTrayIcon(QIcon(ICON_PATH), app)
    tray.setToolTip("纳西妲桌宠\n左键=click音效+表情 / 右键=barely音效 / 滚轮=缩放 / 拖拽=移动")
    menu = QMenu()
    act_show = menu.addAction("显示 / 隐藏")
    menu.addSeparator()
    act_quit = menu.addAction("退出")
    tray.setContextMenu(menu)

    def on_tray_activated(reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            pet.setVisible(not pet.isVisible())

    def on_menu(action):
        if action is act_show:
            pet.setVisible(not pet.isVisible())
        elif action is act_quit:
            pet.close()
            app.quit()

    tray.activated.connect(on_tray_activated)
    menu.triggered.connect(on_menu)
    tray.show()

    code = app.exec()
    sys.exit(code)


if __name__ == "__main__":
    main()
