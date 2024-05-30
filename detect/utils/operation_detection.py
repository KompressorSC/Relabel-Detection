# -*- encoding: utf-8 -*-
"""
@File    :   operation_detection.py
@Time    :   2024/04/26 11:36:20
@Author  :   Sicheng Chen 
@Contact :   sichengchen@example.com
功能：使用YOLOv8进行工人操作检测，并在检测完毕后切换为非静止画面检测
"""

import os
import sys
import django
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DIR = PROJECT_DIR / "media"
DETECT_DIR = PROJECT_DIR / "detect"
DJANGO_DIR = PROJECT_DIR / "mysite"
WEIGHT_DIR = DETECT_DIR / "weights"
SCRIPT_DIR = DETECT_DIR / "utils" / "non_still_detection.py"
ADDS_DIR = PROJECT_DIR / "adds"
RUN_DIR = ADDS_DIR / "run.json"
CONFIG_DIR = ADDS_DIR / "config.json"

if str(DJANGO_DIR) not in sys.path:
    sys.path.append(str(DJANGO_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

if str(DETECT_DIR) not in sys.path:
    sys.path.append(str(DETECT_DIR))

import cv2
import time
import json
import glob
import copy
import psutil
import websocket
import subprocess
import webbrowser
import numpy as np

from ultralytics import YOLO
from datetime import datetime
from django.utils import timezone

from utils.buzzer import *
from Relabel_Detection.models import VideoHistory, DetectionHistory

# 检测动作阶段
STAGES = {
    "PUT_DESICCANT": [0, 1, 3],  # 加入3是为了DP的第二种情况
    "CHECK_MBB": [2],
    "PASTE_TAPE": [3],
}


class DetectOperation:
    def __init__(self):
        # 加载配置文件
        with open(CONFIG_DIR, "r", encoding="utf8") as f:
            self.config = json.load(f)

        # 加载运行文件
        with open(RUN_DIR, "r", encoding="utf8") as f:
            self.run = json.load(f)

        # 初始化检测开始时间
        self.start_time = timezone.now()

        # 初始化中途退出
        self.exit = False

        # 在数据库中创建记录
        DetectionHistory.objects.create(
            start_date=self.start_time,
            product_model=self.run["pm"],
        )

        # 初始化模型
        self.model = YOLO(self.config["onnx_weight_path"], task="detect")

        # 得到需要推理的阶段
        self.identify_stages()

        for self.stage in self.stages:
            print(f"{self.stage}检测开始")
            self.stage_operation_detection()
            print(f"{self.stage}检测结束")
            if self.exit:
                break

        subprocess.Popen(["python", SCRIPT_DIR])

    def identify_stages(self):
        # 根据得到的产品型号决定推理几次
        if self.run["pm"] == "DP":
            self.stages = ["PUT_DESICCANT", "CHECK_MBB", "PASTE_TAPE"]

        else:  # TR
            self.stages = ["PASTE_TAPE"]

    def init_video(self):
        # 视频保存位置
        self.strnow = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.video_save_path = MEDIA_DIR / f"{self.stage}_{self.strnow}.mp4"

        # 初始化视频保存器
        self.out = cv2.VideoWriter(
            str(self.video_save_path),  # 保存路径
            cv2.VideoWriter_fourcc(*"avc1"),  # 编码
            30.0,  # 帧率
            (self.config["video_width"], self.config["video_height"]),  # 分辨率
        )  # 视频设置

    def inference(self):
        # 模型预测结果
        results = self.model.predict(
            source=self.frame,
            classes=STAGES[self.stage],
            conf=self.config["conf"],
            iou=self.config["iou"],
            imgsz=self.config["model_input"],
        )

        for result in results:
            # 如果检测到目标结果，计数+1
            if result.boxes:
                self.count += 1

                # DP的第二种情况
                for box in result.boxes:
                    if int(box.cls[0]) == 3 and self.run["pm"] == "DP":
                        self.stage = "PASTE_TAPE"
                        self.exit = True

            #  如果需要实时展示，则把预测结果可视化
            if self.config["show_inference"]:
                self.frame = result.plot()

    def add_annotations(self):
        height, width, _ = self.frame.shape

        # 添加检测阶段
        cv2.putText(
            self.frame,
            self.stage,
            (int(0.03 * width), int(0.2 * height)),  # 左下角坐标
            cv2.FONT_HERSHEY_SIMPLEX,  # 字体
            2,  # 大小
            (0, 165, 255),  # 颜色
            2,  # 粗细
        )

        # 添加产品型号
        cv2.putText(
            self.frame,
            self.run["pm"],
            (int(0.03 * width), int(0.3 * height)),  # 左下角坐标
            cv2.FONT_HERSHEY_SIMPLEX,  # 字体
            2,  # 大小
            (255, 0, 255),  # 颜色
            2,  # 粗细
        )

    def check_browser(self):
        for proc in psutil.process_iter(["pid", "name"]):
            if proc.info["name"] == "chrome.exe":
                return True
        return False

    def browser_logic(self):
        # 打开浏览器
        webbrowser.open("http://127.0.0.1:8888/Relabel_Detection/main/")

        # 等待浏览器关闭
        while True:
            time.sleep(1)
            alive = self.check_browser()
            if not alive:
                break

        # 若不保留视频，则此处删除视频
        if not self.config["save_video"]:
            self.video_save_path.unlink()

        # 否则生成视频记录
        else:
            VideoHistory.objects.create(
                video_date=timezone.now(),
                video_path=self.video_save_path,
            )

    def judge_logic(self):
        # 检测是否有在交互后生成的图片
        for file in MEDIA_DIR.glob("*.jpg"):

            # 如果有新截图则说明系统有误，系统进入下一阶段
            if file.stat().st_mtime > self.unmodified_time:

                # 删除保存的视频
                if self.config["save_video"]:
                    self.video_save_path.unlink()

                    # 数据库中删除记录
                    VideoHistory.objects.filter(
                        video_path=str(self.video_save_path)
                    ).delete()

                # 若为最后一个阶段则报警灯关闭
                if (self.stage == "PASTE_TAPE") & self.config["alarm"]:
                    turn_off()

                # 更新数据库
                if self.stage == "PUT_DESICCANT":
                    DetectionHistory.objects.filter(start_date=self.start_time).update(
                        place=True
                    )

                elif self.stage == "CHECK_MBB":
                    DetectionHistory.objects.filter(start_date=self.start_time).update(
                        check_MBB=True
                    )

                else:  # 粘贴胶带
                    DetectionHistory.objects.filter(start_date=self.start_time).update(
                        tape=True
                    )

                return

        # 如果没有新截图则说明工人有误，系统重新进行本阶段
        return self.stage_operation_detection()

    def pass_logic(self):
        # 删除保存的视频
        self.video_save_path.unlink()

        # 若为最后一个阶段则报警灯关闭
        if (self.stage == "PASTE_TAPE") & self.config["alarm"]:
            turn_off()

        # 更新数据库
        if self.stage == "PUT_DESICCANT":
            DetectionHistory.objects.filter(start_date=self.start_time).update(
                place=True
            )

        elif self.stage == "CHECK_MBB":
            DetectionHistory.objects.filter(start_date=self.start_time).update(
                check_MBB=True
            )

        else:  # 粘贴胶带
            DetectionHistory.objects.filter(start_date=self.start_time).update(
                tape=True
            )

    def unpass_logic(self):
        # 报警灯变红并播放对应语音
        if self.config["alarm"]:

            if self.stage == "PUT_DESICCANT":
                put_desiccant()

            elif self.stage == "CHECK_MBB":
                check_MBB()

            else:
                tape_ESD()

        # 初始化时间戳
        self.unmodified_time = datetime.now().timestamp()
        self.browser_logic()

        # 关闭报警灯
        if self.config["alarm"]:
            turn_off()

        self.judge_logic()

    def stage_operation_detection(self):
        self.count = 0  # 初始化计数
        self.check_pass = True  # 初始化状态
        self.begin, self.last = time.time(), time.time()  # 初始化开始时间和上次推理时间
        self.init_video()
        # 报警灯变绿
        if self.config["alarm"]:
            green_light()

        # 开启客户端
        self.ws = websocket.create_connection("ws://localhost:5900", ping_interval=None)

        for self.buffer in self.ws:
            self.now = time.time()

            # 将字节流解码为图像帧
            self.frame = cv2.imdecode(
                np.frombuffer(self.buffer, np.uint8), cv2.IMREAD_COLOR
            )

            # 若模型在时间内没有检测到指定次数规定动作则判定为失败
            if self.now - self.begin >= self.config["failed_time"]:
                self.check_pass = False
                break

            # 若模型在时间内共计检测到指定次数规定动作则判定为成功
            elif self.count >= self.config["chances"]:
                break

            # 可视化推理结果则连续推理
            if self.config["show_inference"]:
                self.inference()

            # 不可视化推理结果则间隔推理
            elif self.now - self.last >= self.config["inference_interval"]:
                self.last = self.now
                self.inference()

            # 添加注释
            self.add_annotations()

            # 写入视频
            self.out.write(self.frame)

        # 结束视频写入
        self.out.release()

        # 关闭客户端
        self.ws.close()

        # 通过检测
        if self.check_pass:
            self.pass_logic()

        # 未通过检测
        else:
            self.unpass_logic()


if __name__ == "__main__":
    print("动作检测开始")
    DetectOperation()
    print("动作检测结束")
