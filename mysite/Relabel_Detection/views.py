# -*- encoding: utf-8 -*-
"""
@File    :   views.py
@Time    :   2024/03/26 11:17:53
@Author  :   Sicheng Chen 
@Contact :   sichengchen@example.com
"""

import json
import shutil
import websocket
import subprocess

from pathlib import Path
from datetime import datetime
from django.urls import reverse
from django.utils import timezone
from django.views.generic import FormView
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse

from .forms import *
from .models import *

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DIR = PROJECT_DIR / "media"
ADDS_DIR = PROJECT_DIR / "adds"
RUN_DIR = ADDS_DIR / "run.json"
CONFIG_DIR = ADDS_DIR / "config.json"
LAST_CONFIG_DIR = ADDS_DIR / "config_last.json"
DEFAULT_CONFIG_DIR = ADDS_DIR / "config_default.json"
SCRIPT_DIR = PROJECT_DIR / "detect" / "utils"
LABEL_LIST = {
    "pt_weight_path": "PT权重",
    "onnx_weight_path": "ONNX权重",
    "train_epoch": "训练轮次",
    "auto_train_time": "训练时间",
    "auto_label_time": "标注时间",
    "sender_email": "发送者E-mail",
    "receiver_email": "接收者E-mail",
    "camera_index": "摄像头索引",
    "video_width": "视频宽度",
    "video_height": "视频高度",
    "chances": "判定成功次数",
    "failed_time": "判定阈值时间",
    "model_input": "输入图像尺寸",
    "conf": "置信度",
    "iou": "IoU",
    "show_inference": "实时推理",
    "alarm": "警报系统",
    "save_video": "保存视频",
    "auto_label": "自动标注",
    "auto_train": "自动训练",
    "email": "发送邮件",
    "difference": "灰度差",
    "inference_interval": "检测间隔",
    "port": "报警灯USB串口",
}


@csrf_exempt
def main(request):
    with open(CONFIG_DIR, "r", encoding="utf8") as f:
        config = json.load(f)

    # 初始化最新文件的路径和时间戳
    latest_file_path = None
    latest_file_time = 0

    for file in MEDIA_DIR.glob("*.mp4"):
        # 获取文件时间戳
        file_time = file.stat().st_mtime
        if file_time > latest_file_time:
            latest_file_time = file_time
            latest_file_path = file

    # 上传视频
    if request.method == "GET":
        context = {
            "video": latest_file_path,
            "user": request.user,
        }

        return render(request, "main.html", context)

    else:
        try:
            # 保存截图
            image = request.FILES["image"]
            image_path = MEDIA_DIR / image.name

            with open(image_path, "wb+") as f:
                for chunk in image.chunks():
                    f.write(chunk)

            ImageHistory.objects.create(
                image_date=timezone.now(),
                image_path=image_path,
            )

            return JsonResponse({"message": "截图保存成功"})

        except:
            # 删除截图
            data = json.loads(request.body)
            image_path = MEDIA_DIR / data.get("delete")
            image_path.unlink()
            ImageHistory.objects.filter(image_path=image_path).delete()
            return JsonResponse({"message": "截图删除成功"})


@csrf_exempt
def video(request):
    # 使用流传输传输视频流
    def gen_video():
        ws = websocket.create_connection("ws://localhost:5900", ping_interval=None)

        while True:
            yield (
                b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + ws.recv() + b"\r\n"
            )

        # ws.close()

    return StreamingHttpResponse(
        gen_video(),
        content_type="multipart/x-mixed-replace; boundary=frame",
    )


@csrf_exempt
@login_required
def live(request):
    with open(CONFIG_DIR, "r", encoding="utf8") as f:
        config = json.load(f)

    if request.method == "GET":
        # 上传实时画面
        return render(request, "live.html")

    else:
        try:
            # 保存截图
            image = request.FILES["image"]
            image_path = MEDIA_DIR / image.name

            with open(image_path, "wb+") as f:
                for chunk in image.chunks():
                    f.write(chunk)

            ImageHistory.objects.create(
                image_date=timezone.now(),
                image_path=image_path,
            )

            return JsonResponse({"message": "截图成功"})

        except:
            # 删除截图
            data = json.loads(request.body)
            image_path = MEDIA_DIR / data.get("delete")
            image_path.unlink()
            ImageHistory.objects.filter(image_path=image_path).delete()
            return JsonResponse({"message": "图像删除成功"})


@csrf_exempt
@login_required
def settings(request):
    # 修改前的配置文件
    with open(CONFIG_DIR, "r") as f:
        config = json.load(f)

    if request.method == "POST":
        # 修改后的配置文件
        form = SettingsForm(request.POST)

        if form.is_valid():
            new_config = form.cleaned_data

            with open(CONFIG_DIR, "w") as f:
                json.dump(new_config, f)

            # 保存为上次设置
            with open(LAST_CONFIG_DIR, "w") as f:
                json.dump(config, f)

            # 上传修改记录到数据库
            for key in new_config.keys():
                if new_config[key] != config[key]:
                    ConfigHistory.objects.create(
                        change_time=timezone.now(),
                        changes=f"将{LABEL_LIST[key]}从{config[key]}修改为{new_config[key]}",
                    )

        else:
            data = json.loads(request.body)
            operation = data.get("operation")

            # 恢复默认设置
            if operation == "default":
                shutil.copy(DEFAULT_CONFIG_DIR, CONFIG_DIR)

            # 恢复上次设置
            elif operation == "restore":
                shutil.copy(LAST_CONFIG_DIR, CONFIG_DIR)

            # 调用其他脚本
            else:
                subprocess.run(["python", SCRIPT_DIR / f"{operation}.py"])

    else:
        form = SettingsForm(initial=config)

    # 渲染设置页面
    return render(request, "settings.html", {"form": form})


@csrf_exempt
@login_required
def history(request):
    if request.method == "GET":
        image_history = ImageHistory.objects.all().order_by("-image_date")
        video_history = VideoHistory.objects.all().order_by("-video_date")
        model_history = ModelHistory.objects.all().order_by("-model_date")
        detection_history = DetectionHistory.objects.all().order_by("-start_date")
        label_history = LabelHistory.objects.all().order_by("-label_date")
        config_history = ConfigHistory.objects.all().order_by("-change_time")

        return render(
            request,
            "history.html",
            {
                "image_history": image_history,
                "video_history": video_history,
                "model_history": model_history,
                "detection_history": detection_history,
                "label_history": label_history,
                "config_history": config_history,
            },
        )

    else:
        history = globals()[json.loads(request.body).get("type")]
        delete_id = json.loads(request.body).get("id")

        # 删除图片和标签
        if hasattr(history, "image_path"):

            image_pth = Path(history.objects.get(id=delete_id).image_path)
            if image_pth.exists():
                image_pth.unlink()

            label_pth = image_pth.with_suffix(".txt")
            if label_pth.exists():
                label_pth.unlink()

        # 删除视频
        elif hasattr(history, "video_path"):
            video_pth = Path(history.objects.get(id=delete_id).video_path)

            if video_pth.exists():
                video_pth.unlink()

        # 删除模型权重和日志
        elif hasattr(history, "pt_path"):

            pt_pth = Path(history.objects.get(id=delete_id).pt_path)
            onnx_pth = Path(history.objects.get(id=delete_id).onnx_path)
            log_pth = history.objects.get(id=delete_id).log_path

            if pt_pth.exists():
                pt_pth.unlink()

            if onnx_pth.exists():
                onnx_pth.unlink()

            try:
                shutil.rmtree(log_pth)
            except:
                pass

        # 删除数据库中的记录
        history.objects.filter(id=delete_id).delete()

        return JsonResponse({"message": "删除成功"})


class LoginView(FormView):
    form_class = AuthenticationForm
    template_name = "login.html"
    success_url = "/Relabel_Detection/history/"  # 登录成功后重定向的URL

    def form_valid(self, form):
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(request=self.request, username=username, password=password)

        if user is not None:
            login(self.request, user)
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            return redirect(request, "/Relabel_Detection/login/")
    else:
        form = UserRegistrationForm()
    return render(request, "register.html", {"form": form})
