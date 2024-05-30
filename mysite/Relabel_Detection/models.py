# -*- encoding: utf-8 -*-
"""
@File    :   models.py
@Time    :   2024/04/09 13:29:55
@Author  :   Sicheng Chen 
@Contact :   sichengchen@example.com
"""
from django.db import models


class ImageHistory(models.Model):
    image_date = models.DateTimeField()
    image_path = models.CharField(max_length=50)
    labeled = models.BooleanField(default=False)
    trained = models.BooleanField(default=False)


class VideoHistory(models.Model):
    video_date = models.DateTimeField()
    video_path = models.CharField(max_length=50)


class ModelHistory(models.Model):
    model_date = models.DateTimeField()
    pt_path = models.CharField(max_length=50)
    onnx_path = models.CharField(max_length=50)
    log_path = models.CharField(max_length=50)


class DetectionHistory(models.Model):
    start_date = models.DateTimeField()
    product_model = models.CharField(max_length=2)
    place = models.BooleanField(default=False)
    check_MBB = models.BooleanField(default=False)
    tape = models.BooleanField(default=False)


class LabelHistory(models.Model):
    label_date = models.DateTimeField()
    label_images = models.IntegerField(default=0)


class ConfigHistory(models.Model):
    change_time = models.DateTimeField()
    changes = models.TextField(default="无任何修改")
