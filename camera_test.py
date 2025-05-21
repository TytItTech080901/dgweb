#!/usr/bin/env python3
"""测试系统上可用的摄像头"""
import cv2
import time
import os

def check_camera_indices():
    """检查所有可能的摄像头索引"""
    available_cameras = []
    
    # 方法1：使用不同的API尝试索引0-9
    print("=== 方法1：尝试摄像头索引 0-9 与不同的API ===")
    apis = [cv2.CAP_ANY, cv2.CAP_V4L2, cv2.CAP_V4L]  # 尝试不同的API
    
    for i in range(10):
        for api in apis:
            try:
                api_name = {
                    cv2.CAP_ANY: "ANY",
                    cv2.CAP_V4L2: "V4L2",
                    cv2.CAP_V4L: "V4L"
                }.get(api, str(api))
                
                print(f"尝试打开摄像头索引 {i} 使用API: {api_name}...")
                cap = cv2.VideoCapture(i, api)
                if cap.isOpened():
                    # 设置关键的摄像头参数
                    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        print(f"✓ 摄像头索引 {i} 使用API {api_name} 可用: 分辨率 {frame_width}x{frame_height}")
                        # 获取更多摄像头信息
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        format = cap.get(cv2.CAP_PROP_FORMAT)
                        print(f"  - FPS: {fps}")
                        print(f"  - 格式: {format}")
                        print(f"  - 帧大小: {frame.shape}")
                        if i not in [x[0] for x in available_cameras]:
                            available_cameras.append((i, api_name))
                    else:
                        print(f"× 摄像头索引 {i} 使用API {api_name} 无法读取帧")
                    cap.release()
                else:
                    print(f"× 摄像头索引 {i} 使用API {api_name} 无法打开")
            except Exception as e:
                print(f"× 检测摄像头 {i} 使用API {api_name} 时出错: {e}")
                if cap:
                    cap.release()
    
    # 方法2：检查设备文件
    print("\n=== 方法2：检查设备文件 ===")
    try:
        import glob
        video_devices = glob.glob('/dev/video*')
        if not video_devices:
            print("未找到任何视频设备文件")
        else:
            for device in sorted(video_devices):
                try:
                    print(f"找到设备文件: {device}")
                    if device.startswith('/dev/video'):
                        index = int(device.replace('/dev/video', ''))
                        if not any(index == x[0] for x in available_cameras):
                            print(f"尝试通过设备路径打开 {device}...")
                            for api in apis:
                                api_name = {
                                    cv2.CAP_ANY: "ANY",
                                    cv2.CAP_V4L2: "V4L2",
                                    cv2.CAP_V4L: "V4L"
                                }.get(api, str(api))
                                
                                try:
                                    cap = cv2.VideoCapture(device, api)
                                    if cap.isOpened():
                                        # 设置关键的摄像头参数
                                        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
                                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                                        cap.set(cv2.CAP_PROP_FPS, 30)
                                        
                                        ret, frame = cap.read()
                                        if ret and frame is not None:
                                            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                                            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                                            fps = cap.get(cv2.CAP_PROP_FPS)
                                            format = cap.get(cv2.CAP_PROP_FORMAT)
                                            print(f"✓ 设备 {device} 使用API {api_name} 可用:")
                                            print(f"  - 分辨率: {frame_width}x{frame_height}")
                                            print(f"  - FPS: {fps}")
                                            print(f"  - 格式: {format}")
                                            print(f"  - 帧大小: {frame.shape}")
                                            if (index, api_name) not in available_cameras:
                                                available_cameras.append((index, api_name))
                                        else:
                                            print(f"× 设备 {device} 使用API {api_name} 无法读取帧")
                                    else:
                                        print(f"× 设备 {device} 使用API {api_name} 无法打开")
                                except Exception as e:
                                    print(f"× 尝试设备 {device} 使用API {api_name} 时出错: {e}")
                                finally:
                                    if 'cap' in locals():
                                        cap.release()
                except Exception as e:
                    print(f"处理设备 {device} 时出错: {e}")
    except Exception as e:
        print(f"检查设备文件时出错: {e}")

    # 打印摘要
    print("\n=== 摄像头检测摘要 ===")
    if available_cameras:
        print("可用的摄像头:")
        for idx, api in available_cameras:
            print(f"- 索引 {idx} (API: {api})")
    else:
        print("没有找到可用的摄像头")
    
    return available_cameras

if __name__ == "__main__":
    check_camera_indices()
