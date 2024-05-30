# -*- encoding: utf-8 -*-
"""
@File    :   auto_label.py
@Time    :   2024/04/26 13:28:46
@Author  :   Sicheng Chen 
@Contact :   sichengchen@example.com
功能：自动标注新截图，
用于给审核人员使用YoloLabel修改系统的错误自动标注图像提供参考
"""

import os
import sys
import django
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
DJANGO_DIR = PROJECT_DIR / "mysite"
ADDS_DIR = PROJECT_DIR / "adds"
CONFIG_DIR = ADDS_DIR / "config.json"
RUN_DIR = ADDS_DIR / "run.json"
MEDIA_DIR = PROJECT_DIR / "media"
RESULTS_DIR = PROJECT_DIR / "runs"
LABEL_DIR = RESULTS_DIR / "detect" / "predict" / "labels"

if str(DJANGO_DIR) not in sys.path:
    sys.path.append(str(DJANGO_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

import time
import json
import shutil
import smtplib

from ultralytics import YOLO
from datetime import datetime
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from Relabel_Detection.models import ImageHistory


class AutoLabel:
    def __init__(self):
        # 加载配置文件
        with open(CONFIG_DIR, "r", encoding="utf8") as f:
            self.config = json.load(f)

        # 加载运行文件
        with open(RUN_DIR, "r", encoding="utf8") as f:
            self.run = json.load(f)

        # 扫描新增图像
        self.images = []
        for f in MEDIA_DIR.glob("*.jpg"):
            # 排除已经自动标注过的图像
            if not f.with_suffix(".txt").exists():
                self.images.append(f)

        if self.images != []:
            self.model = YOLO(self.config["onnx_weight_path"], task="detect")

            for image in self.images:

                # 自动标注
                self.model.predict(
                    source=image,
                    conf=self.config["conf"],
                    iou=self.config["iou"],
                    imgsz=self.config["model_input"],
                    save_txt=True,
                )

                # 更新数据库图片状态
                ImageHistory.objects.filter(image_path=image).update(labeled=True)

            # 转移标签到数据集目录
            for label in LABEL_DIR.glob("*"):
                _label = MEDIA_DIR / label.name
                shutil.move(label, _label)

            shutil.rmtree(RESULTS_DIR)

            # 更新要人工标注的图片数量
            self.run["img_to_label"] += len(self.images)

            # 发送邮件提醒人工标注
            if self.config["email"]:
                self.send_email()

            # 更新运行文件
            with open(RUN_DIR, "w") as f:
                json.dump(self.run, f)

    def send_email(self):
        message = MIMEMultipart("related")
        message["From"] = Header(self.config["sender_email"], "utf-8")
        message["To"] = Header(self.config["receiver_email"], "utf-8")
        message["Subject"] = Header(
            "Relabel Detection System Image Label Reminder", "utf-8"
        )
        message_body = f"There are {self.run['img_to_label']} new images to label."
        msgAlternative = MIMEMultipart("alternative")
        message.attach(msgAlternative)
        msgAlternative.attach(MIMEText(message_body, "plain", "utf-8"))
        smtplib.SMTP("relay.sing.example.com").sendmail(
            self.config["sender_email"],
            self.config["receiver_email"],
            message.as_string(),
        )


if __name__ == "__main__":
    print("自动标注开始")
    AutoLabel()
    print("自动标注结束")
