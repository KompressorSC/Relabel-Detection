# -*- encoding: utf-8 -*-
"""
@File    :   auto_train.py
@Time    :   2024/04/26 13:28:33
@Author  :   Sicheng Chen 
@Contact :   sichengchen@example.com
功能：自动使用经过系统维护人员修改标注的图像训练模型
"""

import os
import sys
import django
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DIR = PROJECT_DIR / "media"
DJANGO_DIR = PROJECT_DIR / "mysite"
WEIGHT_DIR = PROJECT_DIR / "detect" / "weights"
ADDS_DIR = PROJECT_DIR / "adds"
RUN_DIR = ADDS_DIR / "run.json"
CONFIG_DIR = ADDS_DIR / "config.json"
DATASET_DIR = ADDS_DIR / "dataset.yaml"

if str(DJANGO_DIR) not in sys.path:
    sys.path.append(str(DJANGO_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

import time
import math
import json
import yaml
import shutil
import random

from ultralytics import YOLO
from datetime import datetime
from django.utils import timezone

from Relabel_Detection.models import ImageHistory, ModelHistory


class AutoTrain:
    def __init__(self):

        # 加载配置文件
        with open(CONFIG_DIR, "r", encoding="utf8") as f:
            self.config = json.load(f)

        # 加载运行文件
        with open(RUN_DIR, "r", encoding="utf8") as f:
            self.run = json.load(f)

        # 未经过人工标注则返回
        if not self.run["Labeled"]:
            return

        # 扫描新增图像
        self.image_list = []
        for f in MEDIA_DIR.glob("*.jpg"):
            self.image_list.append(f)

        # 若没有人工标注的图像则返回
        if self.image_list == []:
            self.run["Labeled"] = False
            with open(RUN_DIR, "w") as f:
                json.dump(self.run, f)
            return

        self.create_datasets()
        self.train_and_quantize_model()

        # 更新配置文件
        self.config["pt_weight_path"] = str(self.pt_weight_path)
        self.config["onnx_weight_path"] = str(self.onnx_weight_path)
        with open(CONFIG_DIR, "w") as f:
            json.dump(self.config, f)

        self.run["Labeled"] = False
        with open(RUN_DIR, "w") as f:
            json.dump(self.run, f)

    def move_images(self, imgs, list_path):
        for img in imgs:
            # 移动图像到数据集
            shutil.copy(img, list_path)
            new_img = list_path / img.name
            img.unlink()

            # 如果有标签则移动标签到数据集
            label = img.with_suffix(".txt")
            try:
                shutil.copy(label, list_path)
                label.unlink()
            except:
                pass

            # 更新数据库信息
            ImageHistory.objects.filter(image_path=img).update(trained=True)
            ImageHistory.objects.filter(image_path=img).update(image_path=new_img)

    def create_datasets(self):
        # 初始化训练开始时间
        self.strnow = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

        # 创建数据集目录
        self.outcome_path = MEDIA_DIR / self.strnow

        self.train_path = self.outcome_path / "train"
        self.val_path = self.outcome_path / "val"

        self.train_path.mkdir(parents=True, exist_ok=True)
        self.val_path.mkdir(parents=True, exist_ok=True)

        # 创建验证集和训练集
        self.val_size = math.ceil(0.2 * len(self.image_list))
        self.val_list = random.sample(self.image_list, self.val_size)

        self.train_list = []
        for img in self.image_list:
            if img not in self.val_list:
                self.train_list.append(img)

        self.move_images(self.train_list, self.train_path)
        self.move_images(self.val_list, self.val_path)

        # 修改数据集配置文件
        with open(DATASET_DIR, "r") as f:
            self.dataset = yaml.safe_load(f)

        self.dataset["train"] = str(self.train_path)
        self.dataset["val"] = str(self.val_path)

        with open(DATASET_DIR, "w") as f:
            yaml.safe_dump(self.dataset, f)

    def train_and_quantize_model(self):
        # 训练模型
        self.model = YOLO(self.config["pt_weight_path"])
        self.model.train(
            data=DATASET_DIR,
            epochs=self.config["train_epoch"],
            amp=False,
            project="detect\\logs",
            name=self.strnow,
        )

        # 移动权重到指定文件夹
        self.weight_path = PROJECT_DIR / "detect" / "logs" / self.strnow / "weights"
        self.pt_weight_path = (WEIGHT_DIR / self.strnow).with_suffix(".pt")
        self.onnx_weight_path = (WEIGHT_DIR / self.strnow).with_suffix(".onnx")
        shutil.move(self.weight_path / "best.pt", self.pt_weight_path)
        shutil.rmtree(self.weight_path)

        # 量化模型
        self.model = YOLO(self.pt_weight_path)
        self.model.export(format="onnx")

        # 写入数据库
        ModelHistory.objects.create(
            model_date=timezone.now(),
            pt_path=self.pt_weight_path,
            onnx_path=self.onnx_weight_path,
            log_path=self.weight_path.parent,
        )


if __name__ == "__main__":
    print("自动训练开始")
    AutoTrain()
    print("自动训练结束")
