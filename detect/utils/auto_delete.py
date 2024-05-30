# -*- encoding: utf-8 -*-
"""
@File    :   auto_delete.py
@Time    :   2024/05/29 08:28:08
@Author  :   Sicheng Chen 
@Contact :   sichengchen@example.com
功能：删除系统中一个月前生成的图片和视频
"""

import os
import sys
import time
import django

from pathlib import Path
from django.utils import timezone

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DIR = PROJECT_DIR / "media"
DJANGO_DIR = PROJECT_DIR / "mysite"
if str(DJANGO_DIR) not in sys.path:
    sys.path.append(str(DJANGO_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from Relabel_Detection.models import ImageHistory, VideoHistory


def delete_old_files():

    # 获取当前时间的时间戳
    current_time = time.time()

    # 计算要保留的时间戳（以秒为单位）
    threshold_time = current_time - 30 * 86400  # 一个月

    # 遍历目录中的文件和文件夹
    for f in MEDIA_DIR.glob("*"):

        # 如果文件的修改时间早于阈值时间，则删除文件
        if f.stat().st_mtime < threshold_time:
            if f.name != "example.mp4" and f.name != "labels.txt":
                f.unlink()

                # 在系统数据库中删除记录
                if f.suffix == ".jpg":
                    ImageHistory.objects.filter(image_path=str(f)).delete()
                elif f.suffix == ".mp4":
                    VideoHistory.objects.filter(video_path=str(f)).delete()


if __name__ == "__main__":
    delete_old_files()
    print("已自动删除旧文件")
