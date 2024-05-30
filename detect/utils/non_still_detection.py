# -*- encoding: utf-8 -*-
"""
@File    :   non_still_detection.py
@Time    :   2024/04/26 09:17:36
@Author  :   Sicheng Chen 
@Contact :   sichengchen@example.com
功能：使用灰度差进行非静止画面检测，
并在检测到非静止画面时切换为YOLOv8进行产品型号检测
"""

import cv2
import time
import json
import websocket
import subprocess
import numpy as np

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPT_DIR = PROJECT_DIR / "detect" / "utils" / "product_model_detection.py"
CONFIG_DIR = PROJECT_DIR / "adds" / "config.json"


class DetectNonStill:
    def __init__(self):
        # 加载配置文件
        with open(CONFIG_DIR, "r", encoding="utf8") as f:
            self.config = json.load(f)

        # 得到配置文件时间戳
        self.timestamp = CONFIG_DIR.stat().st_mtime

        # 开启客户端
        self.ws = websocket.create_connection("ws://localhost:5900")

        # 读取第一帧作为背景
        self.last_frame = cv2.cvtColor(
            cv2.imdecode(np.frombuffer(self.ws.recv(), np.uint8), cv2.IMREAD_COLOR),
            cv2.COLOR_BGR2GRAY,
        )

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
        self.frame = cv2.cvtColor(
            cv2.imdecode(np.frombuffer(self.buffer, np.uint8), cv2.IMREAD_COLOR),
            cv2.COLOR_BGR2GRAY,
        )

        # 计算两幅图的像素差
        similarity = np.average(cv2.absdiff(self.frame, self.last_frame))
        self.last_frame = self.frame

        # 若前后图像差异较大，则开始进行产品类型检测
        if similarity > self.config["difference"]:
            print("检测到非静止画面，开始进行产品型号检测")
            self.ws.close()

            self.quit = True
            return subprocess.Popen(["python", SCRIPT_DIR])


if __name__ == "__main__":
    print("非静止画面检测开始")
    DetectNonStill()
    print("非静止画面检测结束")
