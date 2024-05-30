# -*- encoding: utf-8 -*-
"""
@File    :   put_frame.py
@Time    :   2024/05/07 09:45:52
@Author  :   Sicheng Chen 
@Contact :   sichengchen@example.com
功能：读取摄像头画面并通过WebSockets发送给其他进程
"""

import cv2
import json
import asyncio
import functools
import websockets
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_DIR / "adds" / "config.json"


class PutFrame:
    def __init__(self):
        # 加载配置文件
        with open(CONFIG_DIR, "r", encoding="utf8") as f:
            self.config = json.load(f)

        # 初始化视频采集
        self.cap = cv2.VideoCapture(self.config["camera_index"], cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config["video_width"])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config["video_height"])
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

        print("视频帧写入开始")

    async def put_frame(self, websocket):

        while True:
            # 读取帧
            ret, frame = self.cap.read()

            # 嵌入当前时间
            now = datetime.now()
            cv2.putText(
                frame,
                now.strftime("%Y_%m_%d_%H_%M_%S"),
                (
                    int(0.03 * self.config["video_width"]),
                    int(0.1 * self.config["video_height"]),
                ),  # 左下角坐标
                cv2.FONT_HERSHEY_SIMPLEX,  # 字体
                1,  # 大小
                (255, 255, 255),  # 颜色
                2,  # 粗细
            )

            # 将帧转换为字节流
            ret, frame = cv2.imencode(".jpg", frame)

            # 发送帧到客户端
            await websocket.send(frame.tobytes())

        # 关闭视频采集
        cap.release()

    async def run(self):
        # 启动服务器
        async with websockets.serve(
            self.put_frame, "localhost", 5900, ping_interval=None
        ):
            await asyncio.Future()  # 保持运行


if __name__ == "__main__":
    asyncio.run(PutFrame().run())
