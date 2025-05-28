#!/usr/bin/env python3
# command_test.py - 测试新的命令帧功能

from serial_handler import SerialHandler
from modules.serial_module import SerialCommunicationHandler
import time

def test_serial_handler_direct():
    """直接测试SerialHandler的命令功能"""
    print("\n===== 测试SerialHandler直接命令发送 =====")
    handler = SerialHandler()
    
    if not handler.is_connected():
        print("错误：串口未连接")
        return False
    
    print("发送开灯命令...")
    response = handler.send_command(light_on=True)
    
    if response:
        print(f"收到响应: {response}")
        if response.get('light_on_ack'):
            print("成功：开灯命令被确认")
        else:
            print("警告：开灯命令未被确认")
    else:
        print("错误：未收到响应")
    
    time.sleep(2)
    
    print("发送关灯命令...")
    response = handler.send_command(light_off=True)
    
    if response:
        print(f"收到响应: {response}")
        if response.get('light_off_ack'):
            print("成功：关灯命令被确认")
        else:
            print("警告：关灯命令未被确认")
    else:
        print("错误：未收到响应")
    
    return True

def test_serial_communication_handler():
    """测试SerialCommunicationHandler的命令功能"""
    print("\n===== 测试SerialCommunicationHandler命令发送 =====")
    handler = SerialCommunicationHandler()
    
    if not handler.is_connected():
        print("错误：串口未连接")
        return False
    
    # 测试开灯
    print("发送开灯命令...")
    response, message = handler.send_command({'light_on': True})
    print(f"消息: {message}")
    
    time.sleep(2)
    
    # 测试调整亮度
    print("发送增加亮度命令...")
    response, message = handler.send_command({'brightness_up': True})
    print(f"消息: {message}")
    
    time.sleep(2)
    
    # 测试姿势提醒
    print("发送姿势提醒命令...")
    response, message = handler.send_command({'posture_reminder': True})
    print(f"消息: {message}")
    
    time.sleep(2)
    
    # 测试关灯
    print("发送关灯命令...")
    response, message = handler.send_command({'light_off': True})
    print(f"消息: {message}")
    
    return True

if __name__ == "__main__":
    print("======= 命令帧功能测试 =======")
    
    # 测试直接使用SerialHandler
    test_serial_handler_direct()
    
    print("\n")
    
    # 测试使用SerialCommunicationHandler
    test_serial_communication_handler()
    
    print("\n======= 测试完成 =======")
