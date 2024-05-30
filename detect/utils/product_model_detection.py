# -*- encoding: utf-8 -*-
"""
@File    :   model_detection.py
@Time    :   2024/04/26 09:57:37
@Author  :   Sicheng Chen 
@Contact :   sichengchen@example.com
功能：使用YOLOv8进行产品型号检测，并在检测到产品型号时切换为工人操作检测。
一段时间内未检测到产品型号则返回非静止画面检测。
"""

import cv2
import sys
import json
import time
import websocket
import subprocess
import numpy as np

from pathlib import Path
from ultralytics import YOLO

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
ADDS_DIR = PROJECT_DIR / "adds"
CONFIG_DIR = ADDS_DIR / "config.json"
RUN_DIR = ADDS_DIR / "run.json"
SCRIPT_DIR = PROJECT_DIR / "detect" / "utils"

# 产品型号字典
PM = {4: "DP", 5: "TR"}


class DetectProductModel:
    def __init__(self):
        # 加载配置文件
        with open(CONFIG_DIR, "r", encoding="utf8") as f:
            self.config = json.load(f)

        # 得到配置文件时间戳
        self.timestamp = CONFIG_DIR.stat().st_mtime

        # 初始化模型
        self.model = YOLO(self.config["onnx_weight_path"], task="detect")

        # 初始化次数
        self.fail = 0

        # 开启客户端
        self.ws = websocket.create_connection("ws://localhost:5900", ping_interval=None)

        # 初始化时间
        self.last = time.time()

        # 初始化退出判定
        self.quit = False

        for self.buffer in self.ws:

            # 若前端修改配置文件则刷新配置文件
            if CONFIG_DIR.stat().st_mtime != self.timestamp:
                with open(CONFIG_DIR, "r", encoding="utf8") as f:
                    self.config = json.load(f)
                self.timestamp = CONFIG_DIR.stat().st_mtime

            # 间隔检测
            self.now = time.time()
            if self.now - self.last >= self.config["inference_interval"]:
                self.last = self.now
                self.detect_logic()

                if self.quit:
                    return

    def detect_logic(self):
        # 将字节流解码为图像帧
        self.frame = cv2.imdecode(
            np.frombuffer(self.buffer, np.uint8), cv2.IMREAD_COLOR
        )

        # 检测产品型号
        results = self.model.predict(
            source=self.frame,
            classes=[4, 5],
            conf=self.config["conf"],
            iou=self.config["iou"],
            imgsz=self.config["model_input"],
        )

        for self.result in results:
            # 检测到产品
            if self.result.boxes:
                self.success_logic()
            # 未检测到产品
            else:
                self.fail_logic()

            if self.quit:
                return

    def success_logic(self):
        for box in self.result.boxes:
            pm = int(box.cls[0])

        self.pm = PM[pm]

        # 关闭客户端
        self.ws.close()

        # 写入产品型号
        with open(RUN_DIR, "r", encoding="utf8") as f:
            self.run = json.load(f)

        self.run["pm"] = self.pm

        with open(RUN_DIR, "w") as f:
            json.dump(self.run, f)

        self.quit = True
        return subprocess.Popen(["python", SCRIPT_DIR / "operation_detection.py"])

    def fail_logic(self):
        self.fail += 1

        if self.fail >= self.config["failed_time"]:
            print("未检测到产品")

            # 关闭客户端
            self.ws.close()

            self.quit = True
            return subprocess.Popen(["python", SCRIPT_DIR / "non_still_detection.py"])


if __name__ == "__main__":
    print("产品型号检测开始")
    DetectProductModel()
    print("产品型号检测结束")
