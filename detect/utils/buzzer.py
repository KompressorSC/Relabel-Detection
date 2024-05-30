# -*- encoding: utf-8 -*-
"""
@File    :   buzzer.py
@Time    :   2024/05/08 13:48:17
@Author  :   Sicheng Chen 
@Contact :   sichengchen@example.com
功能：报警灯通信，详情参考 
adds/Official Instruction.pdf
"""

import time
import json
import serial

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_DIR / "adds" / "config.json"

# 加载配置文件
with open(CONFIG_DIR, "r", encoding="utf8") as f:
    config = json.load(f)


# 自动生成Modbus CRC16校验码
def CRC16(data):
    data = bytearray.fromhex(data)
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for i in range(8):
            if crc & 1:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1

    crc = crc & 0xFFFF
    return data + crc.to_bytes(2, "little")


# 绿灯常亮
def green_light():
    ser = serial.Serial(config["port"], 9600, timeout=0.1)

    data = CRC16("FF0600C20013")
    # data = CRC16("FF0600060010")  # 修改音量
    ser.write(data)
    ser.read()  # 不加无法正常工作


# 灯光关闭
def turn_off():
    ser = serial.Serial(config["port"], 9600, timeout=0.1)

    data = CRC16("FF0600C20060")
    ser.write(data)
    ser.read()  # 不加无法正常工作


# 放干燥剂
def put_desiccant():
    ser = serial.Serial(config["port"], 9600, timeout=0.1)

    data = CRC16("FF0621030001")  # 播放第一段语音且红灯慢闪
    ser.write(data)
    ser.read()  # 不加无法正常工作


# 检查密封
def check_MBB():
    ser = serial.Serial(config["port"], 9600, timeout=0.1)

    data = CRC16("FF0621030002")  # 播放第二段语音且红灯慢闪
    ser.write(data)
    ser.read()  # 不加无法正常工作


# 贴胶带
def tape_ESD():
    ser = serial.Serial(config["port"], 9600, timeout=0.1)

    data = CRC16("FF0621030003")  # 播放第三段语音且红灯慢闪
    ser.write(data)
    ser.read()  # 不加无法正常工作


if __name__ == "__main__":
    green_light()
    time.sleep(2)
    put_desiccant()
    time.sleep(2)
    check_MBB()
    time.sleep(2)
    tape_ESD()
    time.sleep(2)
    turn_off()
