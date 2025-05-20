"""
串口通信模块 - 处理与下位机的通信
"""
import queue
import math
import time
from serial_handler import SerialHandler

class SerialCommunicationHandler:
    """
    串口通信处理器 - 包装SerialHandler类，添加特定于应用的功能
    """
    def __init__(self, port=None, baudrate=115200):
        self.handler = SerialHandler(port=port, baudrate=baudrate)
        self.initialized = True
        self.port = port  # 添加port属性
        self.baudrate = baudrate  # 添加baudrate属性
        self._frame_queue = queue.Queue(maxsize=100)  # 限制队列大小以避免内存溢出
        # 启动帧监控
        self._start_frame_monitor()
    
    def _start_frame_monitor(self):
        """启动帧监控，将收到的帧数据放入队列"""
        def frame_callback(frame_data):
            try:
                # 转换弧度为角度以便前端显示
                frame_data_with_degrees = frame_data.copy()
                frame_data_with_degrees['yaw_degrees'] = math.degrees(frame_data['yaw'])
                frame_data_with_degrees['pitch_degrees'] = math.degrees(frame_data['pitch'])
                # 添加时间戳
                frame_data_with_degrees['timestamp'] = time.time()
                
                # 防止队列满时阻塞，使用非阻塞方式加入队列
                try:
                    self._frame_queue.put_nowait(frame_data_with_degrees)
                    print(f"收到新帧数据: type={frame_data['type']}, yaw={frame_data_with_degrees['yaw_degrees']:.2f}°, pitch={frame_data_with_degrees['pitch_degrees']:.2f}°")
                except queue.Full:
                    # 如果队列已满，移除最旧的数据再添加
                    try:
                        self._frame_queue.get_nowait()
                        self._frame_queue.put_nowait(frame_data_with_degrees)
                    except:
                        pass  # 忽略可能的错误
            except Exception as e:
                print(f"处理帧数据时出错: {str(e)}")
        
        # 启动帧监控
        if hasattr(self.handler, 'start_frame_monitor'):
            self.handler.start_frame_monitor(callback=frame_callback)
            print("已启动帧数据监控")
    
    def _stop_frame_monitor(self):
        """停止帧监控"""
        if hasattr(self.handler, 'stop_frame_monitor'):
            self.handler.stop_frame_monitor()
            print("已停止帧数据监控")
    
    def close(self):
        """关闭串口连接"""
        self._stop_frame_monitor()
        if hasattr(self, 'handler') and self.handler:
            self.handler.close()
    
    def is_connected(self):
        """检查串口是否已连接"""
        return self.handler.is_connected()
    
    def connect(self):
        """连接到串口"""
        # 先设置处理器的端口和波特率
        self.handler.port = self.port
        self.handler.baudrate = self.baudrate
        success = self.handler.connect()
        if success:
            # 重新启动帧监控
            self._start_frame_monitor()
        return success
    
    def send_data(self, data):
        """发送数据到串口，并返回响应"""
        success = self.handler.send_data(data)
        if success:
            # 读取响应(如果有)
            response = self.handler.read_data()
            return response, "数据发送成功"
        else:
            return None, "发送数据失败"
    
    def send_frame(self, find_bool, yaw, pitch):
        """发送帧数据，转换为弧度制"""
        # 将角度值转换为弧度值
        yaw_rad = math.radians(yaw)    # 将度转换为弧度
        pitch_rad = math.radians(pitch) # 将度转换为弧度
        
        success = self.handler.send_yaw_pitch(find_bool, yaw_rad, pitch_rad)
        if success:
            # 读取响应(如果有)
            response = self.handler.read_data()
            return response, "帧数据发送成功"
        else:
            return None, "发送帧数据失败"
    
    def read_frame(self):
        """读取一帧数据"""
        frame_data = self.handler.read_frame()
        if frame_data:
            # 将弧度值转换为角度值用于显示
            frame_data['yaw_degrees'] = math.degrees(frame_data['yaw'])
            frame_data['pitch_degrees'] = math.degrees(frame_data['pitch'])
            return frame_data, "帧数据读取成功"
        return None, "读取帧数据失败或无数据"
    
    def get_frame_queue(self):
        """获取帧数据队列以供事件流使用"""
        return self._frame_queue
    
    def cleanup(self):
        """清理资源"""
        self._stop_frame_monitor()
        self.close()
    
    def send_detection_position(self, position_data):
        """
        发送检测位置数据
        
        Args:
            position_data: 包含检测位置的字典 {'detected': bool, 'x': float, 'y': float, 'w': float, 'h': float, 'confidence': float}
        
        Returns:
            (response, message): 响应数据和消息
        """
        # 提取位置数据
        detected = position_data.get('detected', False)
        x = position_data.get('x', 0.0)
        y = position_data.get('y', 0.0)
        w = position_data.get('w', 0.0)
        h = position_data.get('h', 0.0)
        confidence = position_data.get('confidence', 0.0)
        
        # 发送检测位置帧
        success = self.handler.send_detection_data(detected, x, y, w, h, confidence)
        
        if success:
            # 读取响应(如果有)
            response = self.handler.read_data()
            if detected:
                return response, f"检测位置数据发送成功: x={x:.3f}, y={y:.3f}"
            else:
                return response, "已发送未检测到目标的信息"
        else:
            return None, "发送检测位置数据失败"
