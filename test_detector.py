#!/usr/bin/env python3
from Yolo.detector import Detector
import time

print("创建检测器实例...")
d = Detector(show_img=False)

print("初始化检测器...")
success = d.initialize()
print(f"初始化结果: {success}")

if success:
    print("启动检测...")
    d.start()
    
    # 等待一段时间让检测器运行起来
    time.sleep(3)
    
    # 获取位置信息
    print("获取位置信息...")
    pos = d.get_position()
    print(f"位置信息: {pos}")
    
    # 停止检测器
    print("停止检测器...")
    d.stop()
    
print("测试完成")
