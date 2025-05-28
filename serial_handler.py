import serial
import time
from serial.tools import list_ports
import threading
import os
import subprocess
import struct

class SerialHandler:
    def __init__(self, port=None, baudrate=115200, monitoring_interval=5, max_reconnect_attempts=3, reconnect_delay=2):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.monitoring_interval = monitoring_interval # 监测间隔（秒）
        self.max_reconnect_attempts = max_reconnect_attempts # 最大重连次数
        self.reconnect_delay = reconnect_delay # 重连尝试间隔（秒）
        self._reconnect_attempts = 0 # 当前重连尝试次数
        self._monitoring_active = False # 监控线程活动状态
        self._monitor_thread = None # 监控线程对象

        if port is None:
            self.port = self.find_available_port()
        self.connect()
        # 启动监控线程
        self.start_monitoring()

    def find_available_port(self):
        """自动查找可用的串口设备"""
        # 打印所有可用串口设备以便调试
        ports = list_ports.comports()
        print("可用串口设备:")
        for port in ports:
            print(f"  - {port.device}: {port.description} [{port.hwid}]")
        
        # 首先尝试查找STM Virtual COM Port设备
        for port in ports:
            if "0483:5740" in port.hwid or "STMicroelectronics Virtual COM Port" in port.description:
                try:
                    print(f"尝试连接STM设备: {port.device}")
                    self._fix_permission(port.device)
                    test_serial = serial.Serial(port.device, self.baudrate, timeout=1)
                    test_serial.close()
                    print(f"找到STM Virtual COM Port设备: {port.device}")
                    return port.device
                except Exception as e:
                    print(f"无法连接到STM设备 {port.device}: {str(e)}")
                    continue
        
        # 尝试直接使用/dev/ttyACM0
        try:
            print("尝试直接连接到 /dev/ttyACM0")
            # 尝试修复权限问题
            self._fix_permission('/dev/ttyACM0')
            test_serial = serial.Serial('/dev/ttyACM0', self.baudrate, timeout=1)
            test_serial.close()
            print("成功连接到 /dev/ttyACM0")
            return '/dev/ttyACM0'
        except Exception as e:
            print(f"无法连接到 /dev/ttyACM0: {str(e)}")
                
        # 如果没有找到STM设备，尝试其他串口
        for port in ports:
            try:
                print(f"尝试连接其他串口: {port.device}")
                # 尝试修复权限问题
                self._fix_permission(port.device)
                test_serial = serial.Serial(port.device, self.baudrate, timeout=1)
                test_serial.close()
                print(f"成功连接到串口: {port.device}")
                return port.device
            except Exception as e:
                print(f"无法连接到串口 {port.device}: {str(e)}")
                continue
        
        print("未找到任何可用串口设备")
        return None

    def _fix_permission(self, port_path):
        """尝试修复串口设备的权限问题"""
        try:
            # 检查文件是否存在
            if not os.path.exists(port_path):
                print(f"串口设备 {port_path} 不存在")
                return False
            
            # 检查当前权限
            try:
                current_mode = os.stat(port_path).st_mode & 0o777
                if current_mode & 0o006:  # 检查是否有读写权限
                    print(f"串口设备 {port_path} 已有足够权限: {oct(current_mode)}")
                    return True
            except Exception as e:
                print(f"无法获取 {port_path} 权限信息: {str(e)}")
            
            # 尝试使用chmod修改权限
            try:
                print(f"尝试修改 {port_path} 权限为 666")
                subprocess.run(['sudo', 'chmod', '666', port_path], check=True)
                print(f"已修改 {port_path} 权限为 666")
                return True
            except Exception as e:
                print(f"无法修改 {port_path} 权限: {str(e)}")
                
            return False
        except Exception as e:
            print(f"尝试修复权限时出错: {str(e)}")
            return False

    def connect(self):
        if not self.port:
            print("连接失败：未找到可用串口")
            return False # 返回连接状态
        try:
            # 尝试修复权限
            self._fix_permission(self.port)
            
            # 尝试关闭现有连接（如果存在且打开）
            self.close()
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(self.reconnect_delay) # 等待串口初始化
            if self.serial.is_open:
                print(f"成功连接到串口: {self.port}")
                self._reconnect_attempts = 0 # 连接成功，重置尝试次数
                return True # 返回连接状态
            else:
                print(f"无法打开串口 {self.port} (is_open is False)")
                self.serial = None
                return False
        except serial.SerialException as e:
            print(f"无法打开串口 {self.port}: {str(e)}")
            self.serial = None
            return False # 返回连接状态
        except Exception as e:
            print(f"连接串口时发生未知错误 {self.port}: {str(e)}")
            self.serial = None
            return False # 返回连接状态

    def is_connected(self):
        # 检查串口对象是否存在并且是打开状态
        # 不再尝试读取DSR线状态，因为不是所有设备都支持或正确报告此状态
        try:
            return self.serial is not None and self.serial.is_open
        except Exception as e:
            print(f"检查串口连接状态时出错: {str(e)}")
            return False

    def check_and_reconnect(self):
        """检查连接状态，如果断开则尝试重连"""
        if not self.is_connected():
            print(f"串口 {self.port} 连接丢失，尝试重连...")
            if self._reconnect_attempts < self.max_reconnect_attempts:
                self._reconnect_attempts += 1
                print(f"重连尝试 {self._reconnect_attempts}/{self.max_reconnect_attempts}...")
                # 尝试重新查找端口并连接
                self.port = self.find_available_port()
                if self.connect():
                    print(f"串口 {self.port} 重连成功")
                else:
                    print(f"串口 {self.port} 重连失败")
                    time.sleep(self.reconnect_delay) # 等待一段时间再试
            else:
                # 达到最大重连次数
                print(f"错误：串口 {self.port} 多次重连失败，请检查设备连接或驱动程序。")
                # 可以选择在这里停止监控或继续尝试，这里选择继续尝试，但只打印一次错误
                if self._reconnect_attempts == self.max_reconnect_attempts:
                     self._reconnect_attempts += 1 # 增加一次，避免重复打印错误
        else:
            # 如果连接正常，确保重置尝试次数
            if self._reconnect_attempts > 0:
                print(f"串口 {self.port} 连接已恢复。")
                self._reconnect_attempts = 0

    def _monitor_loop(self):
        """监控线程的主循环"""
        print(f"启动串口 {self.port} 连接监控，间隔 {self.monitoring_interval} 秒...")
        while self._monitoring_active:
            self.check_and_reconnect()
            time.sleep(self.monitoring_interval)
        print(f"串口 {self.port} 连接监控已停止。")

    def start_monitoring(self):
        """启动后台监控线程"""
        if not self._monitoring_active and self.port: # 只有找到端口才启动监控
            self._monitoring_active = True
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()

    def stop_monitoring(self):
        """停止后台监控线程"""
        self._monitoring_active = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join() # 等待线程结束

    def send_data(self, data):
        if not self.is_connected():
            print("发送失败：串口未连接")
            return False
        try:
            if isinstance(data, str):
                data = data.encode()
            self.serial.write(data)
            return True
        except Exception as e:
            print(f"发送数据错误: {str(e)}")
            # 发送错误也可能意味着连接丢失
            self._reconnect_attempts = self.max_reconnect_attempts + 1 # 标记为需要立即重连
            return False

    def read_data(self):
        if not self.is_connected():
            return "读取失败：串口未连接"
        try:
            # 增加一个小的读取超时，避免永久阻塞
            if self.serial.in_waiting > 0:
                response = self.serial.readline()
                return response.decode(errors='ignore').strip() # 忽略解码错误
            else:
                return "" # 没有数据可读
        except serial.SerialException as e:
             print(f"读取数据时串口错误: {str(e)}")
             self._reconnect_attempts = self.max_reconnect_attempts + 1 # 标记为需要立即重连
             return f"读取数据错误: {str(e)}"
        except Exception as e:
            print(f"读取数据时发生未知错误: {str(e)}")
            return f"读取数据错误: {str(e)}"

    def close(self):
        """安全地关闭串口连接"""
        if self.serial and self.serial.is_open:
            try:
                self.serial.close()
                print(f"串口 {self.port} 已关闭。")
            except Exception as e:
                print(f"关闭串口 {self.port} 时出错: {str(e)}")
        self.serial = None # 清理串口对象引用

    def __del__(self):
        # 确保在对象销毁时停止监控并关闭串口
        if hasattr(self, '_frame_monitor_active'):
            self.stop_frame_monitor()
        self.stop_monitoring()
        self.close()

    def pack_frame(self, find_bool, yaw, pitch, type_byte=0xA0):
        """
        按照上位机发送帧格式打包数据:
        char start = 's';  //0 帧头取 's'
        char type = 0xA0;  //1 消息类型：上->下：0xA0
        char find_bool;    //2 是否追踪
        float yaw;         //3-6 yaw数据
        float pitch;       //7-10 pitch数据
        char end = 'e';    //31 帧尾取'e'
        """
        frame = bytearray(32)  # 创建32字节的数据帧
        frame[0] = ord('s')    # 帧头 's'
        frame[1] = type_byte   # 消息类型 0xA0
        frame[2] = 1 if find_bool else 0  # 是否追踪
        
        # 打包 yaw (float, 4字节)，使用小端字节序
        yaw_bytes = struct.pack('<f', float(yaw))
        frame[3:7] = yaw_bytes
        
        # 打包 pitch (float, 4字节)，使用小端字节序
        pitch_bytes = struct.pack('<f', float(pitch))
        frame[7:11] = pitch_bytes
        
        # 帧尾
        frame[31] = ord('e')
        
        return bytes(frame)

    def parse_frame(self, data):
        """
        解析下位机发送的帧数据:
        char start = 's';  //0 帧头取 's'
        char type;         //1 消息类型：下->上：0xB0, 0xB3等
        
        对于0xB0(姿态数据):
        float yaw;         //2-5 yaw数据
        float pitch;       //6-9 pitch数据
        
        对于0xB3(命令响应):
        char light_on_ack;       //2 开灯命令确认
        char light_off_ack;      //3 关灯命令确认
        char brightness_up_ack;  //4 增加亮度命令确认
        char brightness_down_ack;//5 减少亮度命令确认
        char posture_ack;        //6 姿势提醒命令确认
        char eye_rest_ack;       //7 眼睛休息提醒命令确认
        
        char end = 'e';    //31 帧尾取'e'
        """
        if not isinstance(data, (bytes, bytearray)) or len(data) < 32:
            return None
            
        if data[0] != ord('s') or data[31] != ord('e'):
            return None  # 帧头或帧尾不匹配
            
        try:
            msg_type = data[1]  # 消息类型，根据类型解析不同的数据
            
            # 根据消息类型解析不同的数据
            if msg_type == 0xB0:  # 姿态数据帧
                # 解析 yaw (2-5) 和 pitch (6-9)，使用小端字节序
                yaw = struct.unpack('<f', data[2:6])[0]
                pitch = struct.unpack('<f', data[6:10])[0]
                
                return {
                    'type': msg_type,
                    'yaw': yaw,
                    'pitch': pitch
                }
            elif msg_type == 0xB3:  # 命令响应帧
                # 解析确认字段
                light_on_ack = data[2] == 1
                light_off_ack = data[3] == 1
                brightness_up_ack = data[4] == 1
                brightness_down_ack = data[5] == 1
                posture_ack = data[6] == 1
                eye_rest_ack = data[7] == 1
                
                return {
                    'type': msg_type,
                    'light_on_ack': light_on_ack,
                    'light_off_ack': light_off_ack,
                    'brightness_up_ack': brightness_up_ack,
                    'brightness_down_ack': brightness_down_ack,
                    'posture_ack': posture_ack,
                    'eye_rest_ack': eye_rest_ack
                }
            else:
                print(f"未知的消息类型: {msg_type}")
                return None
        except Exception as e:
            print(f"解析帧数据出错: {str(e)}")
            return None

    def send_yaw_pitch(self, find_bool, yaw, pitch):
        """发送带有 yaw 和 pitch 的数据帧"""
        try:
            frame = self.pack_frame(find_bool, yaw, pitch)
            return self.send_data(frame)
        except Exception as e:
            print(f"发送 yaw/pitch 数据出错: {str(e)}")
            return False

    def read_frame(self):
        """读取一个完整的数据帧并解析"""
        if not self.is_connected():
            return None
            
        try:
            # 读取32字节的完整帧
            raw_data = self.serial.read(32)
            if len(raw_data) == 32:
                return self.parse_frame(raw_data)
            else:
                return None
        except Exception as e:
            print(f"读取帧数据出错: {str(e)}")
            return None
            
    def start_frame_monitor(self, callback=None):
        """启动帧监控线程，收到数据时自动调用回调函数"""
        self._frame_monitor_active = True
        self._frame_monitor_thread = threading.Thread(
            target=self._frame_monitor_loop, 
            args=(callback,),
            daemon=True
        )
        self._frame_monitor_thread.start()
        
    def stop_frame_monitor(self):
        """停止帧监控线程"""
        self._frame_monitor_active = False
        if hasattr(self, '_frame_monitor_thread') and self._frame_monitor_thread.is_alive():
            self._frame_monitor_thread.join(timeout=1.0)
            
    def _frame_monitor_loop(self, callback):
        """帧监控线程的主循环"""
        print("启动帧数据监控...")
        while self._frame_monitor_active:
            if self.is_connected() and self.serial.in_waiting >= 32:
                frame_data = self.read_frame()
                if frame_data and callback:
                    # 如果读取到有效帧数据且设置了回调函数，则调用回调
                    callback(frame_data)
            time.sleep(0.01)  # 短暂休眠，避免过度占用CPU
        print("帧数据监控已停止")

    def pack_detection_frame(self, find_bool, x, y, w, h, conf=0.0, type_byte=0xA2):
        """
        打包检测坐标数据帧
        
        Args:
            find_bool: 是否找到目标 (布尔值)
            x: 目标中心x坐标 (-0.5到0.5)
            y: 目标中心y坐标 (-0.5到0.5)
            w: 目标宽度 (0到1)
            h: 目标高度 (0到1)
            conf: 检测置信度 (0到1)
            type_byte: 帧类型 (默认0xA2 - 检测坐标帧)
        
        Returns:
            打包好的数据帧字节
        """
        # 创建32字节的数据帧
        frame = bytearray(32)
        
        # 帧头
        frame[0] = ord('s')
        
        # 消息类型
        frame[1] = type_byte  # 0xA2: 检测坐标帧
        
        # 是否找到目标
        frame[2] = 1 if find_bool else 0
        
        # x, y坐标 (使用小端字节序)
        x_bytes = struct.pack('<f', float(x))
        y_bytes = struct.pack('<f', float(y))
        
        # 复制x坐标到帧
        for i in range(4):
            frame[3 + i] = x_bytes[i]
        
        # 复制y坐标到帧
        for i in range(4):
            frame[7 + i] = y_bytes[i]
        
        # w, h尺寸数据 (可选)
        w_bytes = struct.pack('<f', float(w))
        h_bytes = struct.pack('<f', float(h))
        
        # 复制w到帧
        for i in range(4):
            frame[11 + i] = w_bytes[i]
        
        # 复制h到帧
        for i in range(4):
            frame[15 + i] = h_bytes[i]
        
        # 置信度数据
        conf_bytes = struct.pack('<f', float(conf))
        for i in range(4):
            frame[19 + i] = conf_bytes[i]
        
        # 帧尾
        frame[31] = ord('e')
        
        return bytes(frame)

    def send_detection_data(self, find_bool, x, y, w, h, conf=0.0):
        """
        发送检测坐标数据
        
        Args:
            find_bool: 是否找到目标
            x, y: 目标中心坐标
            w, h: 目标尺寸
            conf: 检测置信度
        
        Returns:
            是否发送成功
        """
        # 打包数据帧
        frame = self.pack_detection_frame(find_bool, x, y, w, h, conf)
        # 发送数据帧
        return self.send_data(frame)

    def pack_command_frame(self, light_on=False, light_off=False, brightness_up=False, brightness_down=False, posture_reminder=False, eye_rest_reminder=False, type_byte=0xA3):
        """
        打包控制命令帧
        
        Args:
            light_on: 开灯命令 (布尔值)
            light_off: 关灯命令 (布尔值)
            brightness_up: 增加亮度 (布尔值)
            brightness_down: 减少亮度 (布尔值)
            posture_reminder: 姿势提醒 (布尔值)
            eye_rest_reminder: 眼睛休息提醒 (布尔值)
            type_byte: 帧类型 (默认0xA3 - 控制命令帧)
        
        Returns:
            打包好的数据帧字节
        """
        # 创建32字节的数据帧
        frame = bytearray(32)
        
        # 帧头
        frame[0] = ord('s')
        
        # 消息类型
        frame[1] = type_byte  # 0xA3: 控制命令帧
        
        # 控制位
        frame[2] = 1 if light_on else 0            # 开灯控制位
        frame[3] = 1 if light_off else 0           # 关灯控制位
        frame[4] = 1 if brightness_up else 0       # 增加亮度控制位
        frame[5] = 1 if brightness_down else 0     # 减少亮度控制位
        frame[6] = 1 if posture_reminder else 0    # 姿势提醒控制位
        frame[7] = 1 if eye_rest_reminder else 0   # 眼睛休息提醒控制位
        
        # 保留位 (预留给未来功能)
        for i in range(8, 31):
            frame[i] = 0
        
        # 帧尾
        frame[31] = ord('e')
        
        return bytes(frame)

    def parse_command_response(self, data):
        """
        解析命令响应帧数据:
        char start = 's';  //0 帧头取 's'
        char type = 0xB3;  //1 消息类型：下->上：0xB3
        char light_on_ack;       //2 开灯命令确认
        char light_off_ack;      //3 关灯命令确认
        char brightness_up_ack;  //4 增加亮度命令确认
        char brightness_down_ack;//5 减少亮度命令确认
        char posture_ack;        //6 姿势提醒命令确认
        char eye_rest_ack;       //7 眼睛休息提醒命令确认
        char end = 'e';    //31 帧尾取'e'
        """
        if not isinstance(data, (bytes, bytearray)) or len(data) < 32:
            return None
            
        if data[0] != ord('s') or data[31] != ord('e'):
            return None  # 帧头或帧尾不匹配
            
        try:
            msg_type = data[1]  # 消息类型，应为0xB3
            
            if msg_type != 0xB3:
                return None  # 消息类型不匹配
                
            # 解析确认字段
            light_on_ack = data[2] == 1
            light_off_ack = data[3] == 1
            brightness_up_ack = data[4] == 1
            brightness_down_ack = data[5] == 1
            posture_ack = data[6] == 1
            eye_rest_ack = data[7] == 1
            
            return {
                'type': msg_type,
                'light_on_ack': light_on_ack,
                'light_off_ack': light_off_ack,
                'brightness_up_ack': brightness_up_ack,
                'brightness_down_ack': brightness_down_ack,
                'posture_ack': posture_ack,
                'eye_rest_ack': eye_rest_ack
            }
        except Exception as e:
            print(f"解析命令响应帧数据出错: {str(e)}")
            return None

    def send_command(self, light_on=False, light_off=False, brightness_up=False, brightness_down=False, posture_reminder=False, eye_rest_reminder=False):
        """
        发送控制命令并读取响应
        
        Args:
            light_on: 开灯命令 (布尔值)
            light_off: 关灯命令 (布尔值)
            brightness_up: 增加亮度 (布尔值)
            brightness_down: 减少亮度 (布尔值)
            posture_reminder: 姿势提醒 (布尔值)
            eye_rest_reminder: 眼睛休息提醒 (布尔值)
        
        Returns:
            命令响应数据或None(如果发送失败)
        """
        try:
            # 打包命令帧
            frame = self.pack_command_frame(
                light_on, light_off, 
                brightness_up, brightness_down,
                posture_reminder, eye_rest_reminder
            )
            
            # 发送命令帧
            if not self.send_data(frame):
                print("发送命令帧失败")
                return None
                
            # 等待并读取响应帧
            time.sleep(0.1)  # 给设备一些响应时间
            
            # 如果有足够的数据可读，尝试读取响应帧
            if self.is_connected() and self.serial.in_waiting >= 32:
                raw_data = self.serial.read(32)
                if len(raw_data) == 32:
                    return self.parse_command_response(raw_data)
            
            return None
        except Exception as e:
            print(f"发送命令出错: {str(e)}")
            return None

