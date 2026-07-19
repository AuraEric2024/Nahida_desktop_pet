# -*- coding: utf-8 -*-
"""
摄像头头部追踪模块
使用 MediaPipe Tasks Vision API 在本地检测面部关键点，
计算头部 yaw/pitch + 嘴巴张合，提供给 Live2D 模型使用。

完全本地运行，不依赖任何云端服务。
依赖：mediapipe>=0.10.30, opencv-python

模型文件 face_landmarker.task 首次运行自动下载到系统临时目录。
"""

import os
import shutil
import tempfile
import threading
import urllib.request
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision


# 模型文件名与下载地址
MODEL_FILENAME = "face_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"


def _get_model_path():
    """获取模型文件路径。优先用临时目录（纯英文，避免 MediaPipe 无法处理中文路径）。
    不存在则从项目目录复制或从网络下载。"""
    tmp_dir = tempfile.gettempdir()
    tmp_path = os.path.join(tmp_dir, MODEL_FILENAME)
    if os.path.exists(tmp_path):
        return tmp_path

    # 从项目目录复制
    base = getattr(__import__("sys"), "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    sources = [
        os.path.join(base, MODEL_FILENAME),
        os.path.join(os.path.dirname(__file__), MODEL_FILENAME),
        os.path.join(os.path.dirname(__file__), "..", MODEL_FILENAME),
    ]
    for src in sources:
        if os.path.exists(src):
            print(f"[摄像头] 复制模型 {src} → {tmp_path}")
            shutil.copy2(src, tmp_path)
            return tmp_path

    # 下载
    print(f"[摄像头] 下载 MediaPipe 模型到 {tmp_path} ...")
    urllib.request.urlretrieve(MODEL_URL, tmp_path)
    print(f"[摄像头] 模型下载完成")
    return tmp_path


class CameraTracker:
    """后台摄像头追踪器，线程安全。

    检测内容：
      - 头部 yaw/pitch/roll（左右转头/上下点头/歪头）
      - 嘴巴张合程度 mouth_open（0=闭嘴, 1=张大）

    主线程通过 get_pose() 读取最新结果。
    """

    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self._thread = None
        self._running = False
        self._cap = None
        self._landmarker = None
        # 最新的姿态数据
        self._yaw = 0.0
        self._pitch = 0.0
        self._roll = 0.0
        self._mouth_open = 0.0
        self._lock = threading.Lock()
        self._detected = False  # 是否检测到人脸
        self._error = None

    @property
    def enabled(self):
        return self._running

    @property
    def error(self):
        return self._error

    def start(self):
        if self._running:
            return
        self._error = None
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=3)
            self._thread = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None
        with self._lock:
            self._yaw = 0.0
            self._pitch = 0.0
            self._roll = 0.0
            self._mouth_open = 0.0
            self._detected = False

    def get_pose(self):
        """返回 (yaw, pitch, roll, mouth_open, detected)
        yaw:       左右转头（-1..1，正=向右）
        pitch:     上下点头（-1..1，正=向上）
        roll:      歪头侧倾（-1..1，正=向右歪）
        mouth_open:嘴巴张合（0..1，0=闭嘴, 1=张大）
        detected:  是否检测到人脸"""
        with self._lock:
            return self._yaw, self._pitch, self._roll, self._mouth_open, self._detected

    def _loop(self):
        """后台线程主循环"""
        import time
        try:
            # 1. 加载模型
            model_path = _get_model_path()
            options = mp_vision.FaceLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=model_path),
                running_mode=mp_vision.RunningMode.VIDEO,
                num_faces=1,
                min_face_detection_confidence=0.5,
                min_face_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._landmarker = mp_vision.FaceLandmarker.create_from_options(options)

            # 2. 打开摄像头
            self._cap = cv2.VideoCapture(self.camera_index)
            if not self._cap.isOpened():
                self._error = "无法打开摄像头，请检查设备连接或被其他程序占用"
                print(f"[摄像头] {self._error}")
                self._running = False
                return

            print("[摄像头] 追踪已启动")

            while self._running:
                ret, frame = self._cap.read()
                if not ret:
                    continue
                # 水平翻转（镜像），让用户动作和画面方向一致
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                timestamp_ms = int(time.time() * 1000)
                result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

                if result.face_landmarks:
                    lm = result.face_landmarks[0]
                    yaw, pitch, roll = self._calc_head_pose(lm)
                    mouth = self._calc_mouth_open(lm)
                    with self._lock:
                        self._yaw = yaw
                        self._pitch = pitch
                        self._roll = roll
                        self._mouth_open = mouth
                        self._detected = True
                else:
                    with self._lock:
                        self._detected = False
                        self._mouth_open *= 0.8
                        self._yaw *= 0.8
                        self._pitch *= 0.8
                        self._roll *= 0.8

        except Exception as e:
            self._error = f"摄像头追踪启动失败: {e}"
            print(f"[摄像头] {self._error}")
            import traceback
            traceback.print_exc()
        finally:
            if self._cap is not None:
                self._cap.release()
                self._cap = None
            if self._landmarker is not None:
                self._landmarker.close()
                self._landmarker = None
            self._running = False
            print("[摄像头] 追踪已停止")

    def _calc_head_pose(self, lm):
        """根据面部关键点计算 yaw/pitch/roll，归一化到 -1..1"""
        import math
        left_eye = lm[33]
        right_eye = lm[263]
        nose_tip = lm[1]
        chin = lm[152]

        # yaw：鼻尖相对双眼中点的水平偏移
        eye_mid_x = (left_eye.x + right_eye.x) / 2
        eye_dist = abs(right_eye.x - left_eye.x)
        yaw = (nose_tip.x - eye_mid_x) / (eye_dist * 0.5 + 1e-6)
        yaw = max(-1, min(1, yaw * 2))

        # pitch：鼻尖相对眼-下巴的比例
        eye_y = (left_eye.y + right_eye.y) / 2
        nose_to_eye = nose_tip.y - eye_y
        eye_to_chin = chin.y - eye_y
        pitch_ratio = nose_to_eye / (eye_to_chin + 1e-6)
        pitch = (pitch_ratio - 0.45) * 3
        pitch = max(-1, min(1, -pitch))

        # roll：左右眼睛连线的倾斜角度（歪头）
        # 正常头正时两眼连线水平 → angle=0
        # 头向右歪（右耳靠近右肩）→ 右眼升高 → 连线从左下到右上 → angle 为正
        dx = right_eye.x - left_eye.x
        dy = right_eye.y - left_eye.y
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        # 归一化：±30° 映射到 ±1
        roll = max(-1, min(1, angle_deg / 30.0))

        return yaw, pitch, roll

    def _calc_mouth_open(self, lm):
        """计算嘴巴张合程度，归一化到 0..1。
        用上下嘴唇距离除以嘴宽做归一化，消除距离摄像头远近的影响。"""
        upper_lip = lm[13]   # 上嘴唇内沿中点
        lower_lip = lm[14]   # 下嘴唇内沿中点
        left_mouth = lm[61]  # 嘴左角
        right_mouth = lm[291]# 嘴右角

        vert_dist = lower_lip.y - upper_lip.y
        mouth_width = abs(right_mouth.x - left_mouth.x) + 1e-6
        ratio = vert_dist / mouth_width
        # 闭嘴时约 0.05，张大嘴时约 0.35
        mouth_open = (ratio - 0.05) / 0.30
        return max(0, min(1, mouth_open))
