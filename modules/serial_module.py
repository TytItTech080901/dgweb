"""
串口通信模块 - 处理与串口设备通信的功能
"""
import threading
import time
import json
import queue
from serial_handler import SerialHandler
from config import SERIAL_BAUDRATE
from modules.database_module import save_frame_to_db

class SerialCommunicationHandler:
    """串口通信处理器类，管理串口通信相关功能"""
    
    def __init__(self, baudrate=SERIAL_BAUDRATE):
        """初始化串口通信处理器"""
        self.frame_queue = queue.Queue(maxsize=100)
        self.serial_handler = None
        self.baudrate = baudrate
        self.initialized = False
        self._init_serial_handler()
    
    def _init_serial_handler(self):
        """初始化串口处理器"""
        try:
            self.serial_handler = SerialHandler(port=None, baudrate=self.baudrate)
            if self.serial_handler and self.serial_handler.port:  # 确保找到了端口再启动监控
                self.serial_handler.start_monitoring()
                
                # 添加帧数据监控，收到数据时自动保存到数据库并添加到事件队列
                def frame_callback(frame_data):
                    try:
                        # 保存到数据库
                        save_frame_to_db(frame_data)
                        # 添加到事件队列以供前端获取
                        if self.frame_queue.full():
                            try:
                                # 队列满时，移除最旧的数据
                                self.frame_queue.get_nowait()
                            except queue.Empty:
                                pass
                        self.frame_queue.put(frame_data)
                    except Exception as e:
                        print(f"处理帧数据回调时出错: {str(e)}")
                
                # 启动帧监控
                self.serial_handler.start_frame_monitor(callback=frame_callback)
                self.initialized = True
                return True
            else:
                print("未找到可用的串口设备")
                return False
        except Exception as e:
            print(f"警告：串口处理器初始化失败 - {str(e)}")
            self.serial_handler = None  # 确保失败时 handler 为 None
            return False
    
    def send_data(self, data):
        """发送文本数据到串口"""
        if not self.serial_handler or not self.serial_handler.is_connected():
            return None, "串口未连接"
        
        # 尝试发送数据到串口
        if not self.serial_handler.send_data(data):
            return None, "发送数据失败"
        
        # 接收串口响应
        response = self.serial_handler.read_data()
        return response, "发送成功"
    
    def send_frame(self, find_bool, yaw, pitch):
        """发送按照帧格式打包的yaw和pitch数据"""
        if not self.serial_handler or not self.serial_handler.is_connected():
            return None, "串口未连接"
        
        # 发送帧格式数据
        if self.serial_handler.send_yaw_pitch(find_bool, yaw, pitch):
            # 尝试读取响应帧
            response_frame = self.serial_handler.read_frame()
            if response_frame:
                return response_frame, "帧数据发送成功，收到响应"
            else:
                return None, "帧数据发送成功，未收到响应"
        else:
            return None, "发送帧数据失败"
    
    def read_frame(self):
        """读取一帧数据并解析"""
        if not self.serial_handler or not self.serial_handler.is_connected():
            return None, "串口未连接"
        
        # 读取帧数据
        frame_data = self.serial_handler.read_frame()
        if frame_data:
            return frame_data, "成功读取帧数据"
        else:
            return None, "未读取到帧数据"
    
    def get_frame_queue(self):
        """获取帧数据队列"""
        return self.frame_queue
    
    def is_connected(self):
        """检查串口是否连接"""
        return self.serial_handler and self.serial_handler.is_connected()
    
    def cleanup(self):
        """清理资源"""
        if self.serial_handler:
            # 停止帧监控
            if hasattr(self.serial_handler, '_frame_monitor_active'):
                self.serial_handler.stop_frame_monitor()
            # 停止连接监控
            self.serial_handler.stop_monitoring()
            self.serial_handler.close()