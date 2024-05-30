# -*- encoding: utf-8 -*-
"""
@File    :   forms.py
@Time    :   2024/05/10 16:34:08
@Author  :   Sicheng Chen 
@Contact :   sichengchen@example.com
"""

import json
from pathlib import Path
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import ModelHistory


PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_DIR / "adds" / "config.json"


class SettingsForm(forms.Form):
    pt_weight_path = forms.ChoiceField(label="PT权重")
    onnx_weight_path = forms.ChoiceField(label="ONNX权重")

    auto_train_time = forms.CharField(label="训练时间", max_length=20)
    auto_label_time = forms.CharField(label="标注时间", max_length=20)
    port = forms.CharField(label="报警灯", max_length=5)

    sender_email = forms.EmailField(label="发送者E-mail", max_length=100)
    receiver_email = forms.EmailField(label="接收者E-mail", max_length=100)

    camera_index = forms.IntegerField(label="摄像头")
    video_width = forms.IntegerField(label="视频宽度(px)")
    video_height = forms.IntegerField(label="视频高度(px)")
    chances = forms.IntegerField(label="判定成功次数")
    train_epoch = forms.IntegerField(label="训练轮次")
    failed_time = forms.IntegerField(label="判定阈值时间(s)")
    model_input = forms.IntegerField(label="输入图像尺寸(px)")
    inference_interval = forms.IntegerField(label="检测间隔")
    difference = forms.IntegerField(label="灰度差")

    iou = forms.FloatField(label="IoU")
    conf = forms.FloatField(label="置信度")

    show_inference = forms.BooleanField(label="实时推理", required=False)
    alarm = forms.BooleanField(label="警报系统", required=False)
    save_video = forms.BooleanField(label="保存视频", required=False)
    auto_label = forms.BooleanField(label="自动标注", required=False)
    auto_train = forms.BooleanField(label="自动训练", required=False)
    email = forms.BooleanField(label="发送邮件", required=False)

    def __init__(self, *args, **kwargs):
        super(SettingsForm, self).__init__(*args, **kwargs)

        with open(CONFIG_DIR, "r", encoding="utf8") as f:
            config = json.load(f)

        self.fields["pt_weight_path"].choices = [
            (model.pt_path, Path(model.pt_path).name)
            for model in ModelHistory.objects.all().order_by("-model_date")
        ]
        self.initial["pt_weight_path"] = config["pt_weight_path"]

        self.fields["onnx_weight_path"].choices = [
            (model.onnx_path, Path(model.onnx_path).name)
            for model in ModelHistory.objects.all().order_by("-model_date")
        ]
        self.initial["onnx_weight_path"] = config["onnx_weight_path"]


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
