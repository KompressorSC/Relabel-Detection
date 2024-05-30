# -*- encoding: utf-8 -*-
"""
@File    :   manual_label.py
@Time    :   2024/04/26 15:02:06
@Author  :   Sicheng Chen 
@Contact :   sichengchen@example.com
功能：自动打开YoloLabel并打开需标注图像
"""

import sys
import os
import django
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
DJANGO_DIR = PROJECT_DIR / "mysite"
ADDS_DIR = PROJECT_DIR / "adds"
RUN_DIR = ADDS_DIR / "run.json"
YOLO_LABEL_DIR = ADDS_DIR / "YoloLabel" / "YoloLabel.exe"

if str(DJANGO_DIR) not in sys.path:
    sys.path.append(str(DJANGO_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

import time
import json
import pyautogui
import subprocess

from django.utils import timezone

from Relabel_Detection.models import LabelHistory


class ManualLabel:
    def __init__(self):

        # 自动化打开YoloLabel并进入操作页面
        YoloLabel = subprocess.Popen(YOLO_LABEL_DIR)
        time.sleep(0.5)
        pyautogui.getWindowsWithTitle("YoloLabel")
        time.sleep(0.1)
        pyautogui.press("o")
        time.sleep(0.1)
        pyautogui.press("enter")
        time.sleep(0.1)
        pyautogui.press("shift")
        pyautogui.typewrite("media")
        time.sleep(0.1)
        pyautogui.press("enter")
        time.sleep(0.1)
        pyautogui.press("enter")
        time.sleep(0.1)
        pyautogui.press("enter")
        time.sleep(0.1)
        pyautogui.typewrite("labels.txt")
        time.sleep(0.1)
        pyautogui.press("enter")
        YoloLabel.wait()

        # 加载运行文件
        with open(RUN_DIR, "r") as f:
            run = json.load(f)

        # 写入数据库
        LabelHistory.objects.create(
            label_date=timezone.now(),
            label_images=run["img_to_label"],
        )

        # 更新运行文件
        run["Labeled"] = True
        run["img_to_label"] = 0
        with open(RUN_DIR, "w") as f:
            json.dump(run, f)


if __name__ == "__main__":
    print("人工标注开始")
    ManualLabel()
    print("人工标注结束")
