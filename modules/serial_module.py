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
        self.port = port  # 添加port属性
        self.baudrate = baudrate  # 添加baudrate属性
        
        # 检查串口是否成功连接
        self.initialized = self.handler.is_connected()
        
        if self.initialized:
            print(f"串口通信处理器初始化成功: {self.handler.port}")
            self._frame_queue = queue.Queue(maxsize=100)  # 限制队列大小以避免内存溢出
            # 启动帧监控
            self._start_frame_monitor()
        else:
            print(f"串口通信处理器初始化失败: 无法连接到串口设备")
            self._frame_queue = None
    
    def _start_frame_monitor(self):
        """启动帧监控，将收到的帧数据放入队列"""
        if not self.initialized:
            print("串口未连接，跳过帧监控启动")
            return
            
        def frame_callback(frame_data):
            try:
                # 根据帧类型处理数据
                frame_type = frame_data.get('type')
                
                if frame_type == 0xB0:  # 姿态数据帧
                    # 转换弧度为角度以便前端显示
                    frame_data_with_degrees = frame_data.copy()
                    frame_data_with_degrees['yaw_degrees'] = math.degrees(frame_data['yaw'])
                    frame_data_with_degrees['pitch_degrees'] = math.degrees(frame_data['pitch'])
                    # 添加时间戳
                    frame_data_with_degrees['timestamp'] = time.time()
                    
                    # 防止队列满时阻塞，使用非阻塞方式加入队列
                    try:
                        self._frame_queue.put_nowait(frame_data_with_degrees)
                        print(f"收到姿态帧数据: type={frame_data['type']}, yaw={frame_data_with_degrees['yaw_degrees']:.2f}°, pitch={frame_data_with_degrees['pitch_degrees']:.2f}°")
                    except queue.Full:
                        # 如果队列已满，移除最旧的数据再添加
                        try:
                            self._frame_queue.get_nowait()
                            self._frame_queue.put_nowait(frame_data_with_degrees)
                        except:
                            pass  # 忽略可能的错误
                
                elif frame_type == 0xB3:  # 命令响应帧
                    # 添加时间戳
                    frame_data['timestamp'] = time.time()
                    
                    # 构建响应描述
                    active_acks = []
                    if frame_data.get('light_on_ack'):
                        active_acks.append("开灯")
                    if frame_data.get('light_off_ack'):
                        active_acks.append("关灯")
                    if frame_data.get('brightness_up_ack'):
                        active_acks.append("增加亮度")
                    if frame_data.get('brightness_down_ack'):
                        active_acks.append("减少亮度")
                    if frame_data.get('posture_ack'):
                        active_acks.append("姿势提醒")
                    if frame_data.get('eye_rest_ack'):
                        active_acks.append("眼睛休息提醒")
                    
                    ack_str = "、".join(active_acks) if active_acks else "无命令执行"
                    print(f"收到命令响应帧: type={frame_data['type']}, 执行命令: {ack_str}")
                    
                    # 同样放入队列
                    try:
                        self._frame_queue.put_nowait(frame_data)
                    except queue.Full:
                        try:
                            self._frame_queue.get_nowait()
                            self._frame_queue.put_nowait(frame_data)
                        except:
                            pass  # 忽略可能的错误
                
                else:
                    print(f"收到未知类型帧数据: type={frame_data['type']}")
                    
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
    
    def send_command(self, command_data):
        """
        发送控制命令数据
        
        Args:
            command_data: 包含控制命令的字典，可包含以下键值对:
                'light_on': 开灯命令 (布尔值)
                'light_off': 关灯命令 (布尔值)
                'brightness_up': 增加亮度 (布尔值)
                'brightness_down': 减少亮度 (布尔值)
                'posture_reminder': 姿势提醒 (布尔值)
                'eye_rest_reminder': 眼睛休息提醒 (布尔值)
        
        Returns:
            (response, message): 响应数据和消息
        """
        # 提取命令数据，不存在的键默认为False
        light_on = command_data.get('light_on', False)
        light_off = command_data.get('light_off', False)
        brightness_up = command_data.get('brightness_up', False)
        brightness_down = command_data.get('brightness_down', False)
        posture_reminder = command_data.get('posture_reminder', False)
        eye_rest_reminder = command_data.get('eye_rest_reminder', False)
        
        # 发送命令帧
        response = self.handler.send_command(
            light_on=light_on,
            light_off=light_off,
            brightness_up=brightness_up,
            brightness_down=brightness_down,
            posture_reminder=posture_reminder,
            eye_rest_reminder=eye_rest_reminder
        )
        
        # 生成消息
        active_commands = []
        if light_on:
            active_commands.append("开灯")
        if light_off:
            active_commands.append("关灯")
        if brightness_up:
            active_commands.append("增加亮度")
        if brightness_down:
            active_commands.append("减少亮度")
        if posture_reminder:
            active_commands.append("姿势提醒")
        if eye_rest_reminder:
            active_commands.append("眼睛休息提醒")
            
        # 构建描述性消息
        command_str = "、".join(active_commands) if active_commands else "无命令"
        
        if response:
            # 解析响应结果
            success_commands = []
            if response.get('light_on_ack'):
                success_commands.append("开灯")
            if response.get('light_off_ack'):
                success_commands.append("关灯")
            if response.get('brightness_up_ack'):
                success_commands.append("增加亮度")
            if response.get('brightness_down_ack'):
                success_commands.append("减少亮度")
            if response.get('posture_ack'):
                success_commands.append("姿势提醒")
            if response.get('eye_rest_ack'):
                success_commands.append("眼睛休息提醒")
                
            success_str = "、".join(success_commands) if success_commands else "无命令执行成功"
            return response, f"命令({command_str})发送成功，成功执行：{success_str}"
        else:
            return None, f"发送命令({command_str})失败或无响应"
