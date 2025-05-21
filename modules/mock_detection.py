#!/usr/bin/env python3
"""虚拟检测模块，提供固定的测试数据"""
import time
import threading

class MockDetector:
    """模拟检测器，生成固定的测试数据"""
    def __init__(self):
        self.running = False
        self.detected = True
        self.position = [0.1, -0.2]  # 固定坐标
        self.width = 0.3
        self.height = 0.4
        self.confidence = 0.95
        self.fps = 30.0
    
    def get_position(self):
        """获取模拟位置数据"""
        return {
            "detected": bool(self.detected),
            "x": float(self.position[0]),
            "y": float(self.position[1]),
            "w": float(self.width),
            "h": float(self.height),
            "confidence": float(self.confidence),
            "fps": float(self.fps)
        }

class MockDetectionService:
    """模拟检测服务，提供API兼容的接口"""
    def __init__(self):
        print("初始化虚拟检测服务...")
        self.detector = MockDetector()
        self.lock = threading.Lock()
        self.initialized = True
        self.serial_handler = None
    
    def initialize(self):
        """初始化检测服务（始终返回成功）"""
        print("虚拟检测服务初始化成功")
        return True
    
    def is_running(self):
        """检查服务是否正在运行"""
        return self.detector.running
    
    def start(self):
        """启动检测服务"""
        with self.lock:
            self.detector.running = True
        print("虚拟检测服务启动成功")
        return True
    
    def stop(self):
        """停止检测服务"""
        with self.lock:
            self.detector.running = False
        print("虚拟检测服务已停止")
        return True
    
    def get_position(self):
        """获取目标位置数据（固定返回测试数据）"""
        if not self.is_running():
            return {
                "detected": False,
                "position": [0.0, 0.0],
                "width": 0.0,
                "height": 0.0,
                "confidence": 0.0,
                "fps": 0.0,
                "x": 0.0,
                "y": 0.0
            }
            
        with self.lock:
            # 确保所有值都是Python内置类型，避免float32等numpy类型导致JSON序列化问题
            position = [float(p) for p in self.detector.position]
            return {
                "detected": bool(self.detector.detected),
                "position": position,
                "width": float(self.detector.width),
                "height": float(self.detector.height),
                "confidence": float(self.detector.confidence),
                "fps": float(self.detector.fps),
                "x": float(position[0]),  # 兼容自动发送接口
                "y": float(position[1])   # 兼容自动发送接口
            }
    
    def set_serial_handler(self, handler):
        """设置串口处理器（虚拟实现）"""
        self.serial_handler = handler
        return True
    
    def start_auto_send(self):
        """启动位置自动发送（虚拟实现）"""
        if not self.is_running():
            return False, "检测服务未运行"
        if not self.serial_handler:
            return False, "未设置串口处理器"
        return True, "已启动自动发送"
    
    def stop_auto_send(self):
        """停止位置自动发送（虚拟实现）"""
        return True, "已停止自动发送"
    
    def is_auto_sending(self):
        """检查是否正在自动发送（虚拟实现）"""
        return False

# 导出虚拟检测服务类
__all__ = ['MockDetectionService']
