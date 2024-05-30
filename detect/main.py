# -*- encoding: utf-8 -*-
"""
@File    :   main.py
@Time    :   2024/03/28 09:49:47
@Author  :   Sicheng Chen 
@Contact :   sichengchen@example.com
功能：启动系统所有功能
"""

import json
import time
import subprocess

from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).resolve().parent.parent
DJANGO_DIR = PROJECT_DIR / "mysite" / "manage.py"
SCRIPT_DIR = PROJECT_DIR / "detect" / "utils"
CONFIG_DIR = PROJECT_DIR / "adds" / "config.json"

if __name__ == "__main__":

    # 自动删除一个月前生成的图片和视频
    subprocess.Popen(["python", SCRIPT_DIR / "auto_delete.py"])

    # Django服务器
    subprocess.Popen(["python", DJANGO_DIR, "runserver", "0.0.0.0:8888"])

    # 摄像头读取和发送
    subprocess.Popen(["python", SCRIPT_DIR / "put_frame.py"])

    # 实时检测
    subprocess.Popen(["python", SCRIPT_DIR / "non_still_detection.py"])

    # 加载配置文件
    with open(CONFIG_DIR, "r", encoding="utf8") as f:
        config = json.load(f)

    # 得到配置文件时间戳
    timestamp = CONFIG_DIR.stat().st_mtime

    # 自动更新系统相关
    while True:

        # 若前端修改配置文件则刷新配置文件
        if CONFIG_DIR.stat().st_mtime != timestamp:
            with open(CONFIG_DIR, "r", encoding="utf8") as f:
                config = json.load(f)

        # 到达指定时间自动标注新增图片
        elif config["auto_label"]:
            if datetime.now().strftime("%H:%M") == config["auto_label_time"]:
                # 自动标注
                subprocess.Popen(["python", SCRIPT_DIR / "auto_label.py"])

        # 到达指定时间自动训练新增图片
        elif config["auto_train"]:
            if datetime.now().strftime("%H:%M") == config["auto_train_time"]:
                # 自动训练
                subprocess.Popen(["python", SCRIPT_DIR / "auto_train.py"])

        # 每分钟检测一次
        time.sleep(60)
