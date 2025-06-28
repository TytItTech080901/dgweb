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

        #串口初始化成功
        self.initialized = True

    def find_available_port(self):
        """自动查找可用的串口设备"""
        # 打印所有可用串口设备以便调试
        ports = list_ports.comports()
        print("可用串口设备:")
        for port in ports:
            print(f"  - {port.device}: {port.description} [{port.hwid}]")
        
        # 首先尝试查找STM Virtual COM Port设备或Lampbot设备
        for port in ports:
            if ("0483:5740" in port.hwid or 
                "STMicroelectronics Virtual COM Port" in port.description or
                "Lampbot Virtual ComPort" in port.description or
                "Virtual COM Port" in port.description):
                try:
                    print(f"尝试连接VCP设备: {port.device}")
                    self._fix_permission(port.device)
                    test_serial = serial.Serial(port.device, self.baudrate, timeout=1)
                    test_serial.close()
                    print(f"找到VCP设备: {port.device}")
                    return port.device
                except Exception as e:
                    print(f"无法连接到VCP设备 {port.device}: {str(e)}")
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
                stat_info = os.stat(port_path)
                current_mode = stat_info.st_mode & 0o777
                print(f"串口设备 {port_path} 当前权限: {oct(current_mode)}")
                
                # 检查是否为字符设备
                import stat
                if not stat.S_ISCHR(stat_info.st_mode):
                    print(f"{port_path} 不是字符设备")
                    return False
                
                # 检查是否有读写权限（对于组用户）
                if current_mode & 0o060:  # 检查组读写权限
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
                
            return True  # 即使权限修改失败，也尝试连接
        except Exception as e:
            print(f"尝试修复权限时出错: {str(e)}")
            return True  # 即使出错，也尝试连接

    def connect(self):
        if not self.port:
            print("连接失败：未找到可用串口")
            return False # 返回连接状态
        try:
            # 尝试修复权限
            self._fix_permission(self.port)
            
            # 尝试关闭现有连接（如果存在且打开）
            self.close()
            self.serial = serial.Serial(
                port=self.port, 
                baudrate=self.baudrate, 
                timeout=1,
                bytesize=serial.EIGHTBITS,  # 8位数据位
                parity=serial.PARITY_NONE,  # 无校验
                stopbits=serial.STOPBITS_ONE,  # 1位停止位
                xonxoff=False,  # 软件流控制
                rtscts=False,   # 硬件流控制
                dsrdtr=False    # DTR/DSR流控制
            )
            time.sleep(self.reconnect_delay) # 等待串口初始化
            
            if self.serial.is_open:
                print(f"成功连接到串口: {self.port}")
                print(f"串口配置: 波特率={self.serial.baudrate}, 数据位={self.serial.bytesize}, 校验位={self.serial.parity}, 停止位={self.serial.stopbits}")
                print(f"流控制: XON/XOFF={self.serial.xonxoff}, RTS/CTS={self.serial.rtscts}, DTR/DSR={self.serial.dsrdtr}")
                
                # 清空缓冲区
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
                print("已清空串口输入输出缓冲区")
                
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
            
            # 添加调试信息：显示发送的原始数据
            print(f"准备发送数据长度: {len(data)} 字节")
            print(f"发送数据(hex): {data.hex() if isinstance(data, bytes) else 'Not bytes'}")
            print(f"发送数据(raw): {list(data) if isinstance(data, (bytes, bytearray)) else data}")
            
            self.serial.write(data)
            self.serial.flush()  # 强制刷新缓冲区
            print("执行发送程序")
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

    # def pack_frame(self, find_bool, yaw, pitch, type_byte=0xA0):
    #     """
    #     按照上位机发送帧格式打包数据:
    #     char start = 's';  //0 帧头取 's'
    #     char type = 0xA0;  //1 消息类型：上->下：0xA0
    #     char find_bool;    //2 是否追踪
    #     float yaw;         //3-6 yaw数据
    #     float pitch;       //7-10 pitch数据
    #     char end = 'e';    //31 帧尾取'e'
    #     """
    #     frame = bytearray(32)  # 创建32字节的数据帧
    #     frame[0] = ord('s')    # 帧头 's'
    #     frame[1] = type_byte   # 消息类型 0xA0
    #     frame[2] = 1 if find_bool else 0  # 是否追踪
        
    #     # 打包 yaw (float, 4字节)，使用小端字节序
    #     yaw_bytes = struct.pack('<f', float(yaw))
    #     frame[3:7] = yaw_bytes
        
    #     # 打包 pitch (float, 4字节)，使用小端字节序
    #     pitch_bytes = struct.pack('<f', float(pitch))
    #     frame[7:11] = pitch_bytes
        
    #     # 帧尾
    #     frame[31] = ord('e')
        
    #     return bytes(frame)

    # def parse_frame(self, data):
    #     """
    #     解析下位机发送的帧数据:
    #     支持多种协议格式:
    #     1. 原有协议 (0xB0姿态数据, 0xB3命令响应)
    #     2. 新协议 (0xB0设备状态上报)
    #     """
    #     if not isinstance(data, (bytes, bytearray)) or len(data) < 32:
    #         return None
            
    #     if data[0] != ord('s') or data[31] != ord('e'):
    #         return None  # 帧头或帧尾不匹配
            
    #     try:
    #         msg_type = data[1]  # 消息类型，根据类型解析不同的数据
            
    #         # 根据消息类型解析不同的数据
    #         if msg_type == 0xB0:  # 可能是姿态数据帧或新协议状态帧
    #             # 先尝试按新协议解析
    #             new_protocol_data = self.parse_new_protocol_frame(data)
    #             if new_protocol_data:
    #                 # 如果是新协议的0xB0帧，包含设备状态信息
    #                 return {
    #                     'type': msg_type,
    #                     'protocol': 'new',
    #                     'command': new_protocol_data['command'],
    #                     'device_power': new_protocol_data['data'][0],      # 是否开机
    #                     'device_light': new_protocol_data['data'][1],      # 是否开灯
    #                     'device_brightness': new_protocol_data['data'][2], # 光照亮度 (0-1000)
    #                     'device_colortemp': new_protocol_data['data'][3],  # 光照色温 (3000K-6500K)
    #                     'data': new_protocol_data['data']  # 保留原始数据数组
    #                 }
    #             else:
    #                 # 按原协议解析姿态数据
    #                 yaw = struct.unpack('<f', data[2:6])[0]
    #                 pitch = struct.unpack('<f', data[6:10])[0]
                    
    #                 return {
    #                     'type': msg_type,
    #                     'protocol': 'legacy',
    #                     'yaw': yaw,
    #                     'pitch': pitch
    #                 }
                    
    #         elif msg_type == 0xB3:  # 命令响应帧(旧协议)
    #             # 解析确认字段
    #             light_on_ack = data[2] == 1
    #             light_off_ack = data[3] == 1
    #             brightness_up_ack = data[4] == 1
    #             brightness_down_ack = data[5] == 1
    #             posture_ack = data[6] == 1
    #             eye_rest_ack = data[7] == 1
                
    #             return {
    #                 'type': msg_type,
    #                 'protocol': 'legacy',
    #                 'light_on_ack': light_on_ack,
    #                 'light_off_ack': light_off_ack,
    #                 'brightness_up_ack': brightness_up_ack,
    #                 'brightness_down_ack': brightness_down_ack,
    #                 'posture_ack': posture_ack,
    #                 'eye_rest_ack': eye_rest_ack
    #             }
    #         else:
    #             print(f"未知的消息类型: {msg_type}")
    #             return None
    #     except Exception as e:
    #         print(f"解析帧数据出错: {str(e)}")
    #         return None

    def pack_frame(self, datatype=0xA0, command=0xFF, data_array=None):
        """
        按照新协议格式打包数据帧
        
        Args:
            datatype: 消息类型 (0xA0: 上位机->下位机, 0xB0: 下位机->上位机)
            command: 命令字
            data_array: 数据域数组，最多8个uint32值
        
        Returns:
            打包好的32字节数据帧
        """
        frame = bytearray(32)
        
        # 帧头 's' (0x73)
        frame[0] = ord('s')
        
        # 消息类型
        frame[1] = datatype
        
        # 命令字
        frame[2] = command
        
        # 数据域 (8个uint32值，每个4字节)
        if data_array is None:
            data_array = [0] * 8
        
        # 确保数据数组不超过8个元素
        data_array = data_array[:8]
        while len(data_array) < 8:
            data_array.append(0)
        
        # 打包数据域，使用小端字节序
        for i, value in enumerate(data_array):
            uint32_bytes = struct.pack('<I', int(value))  # 'I' 表示无符号32位整数，小端
            start_idx = 3 + i * 4
            end_idx = start_idx + 4
            frame[start_idx:end_idx] = uint32_bytes
        
        # 帧尾 'e' (0x65) 在第31字节（索引31）
        frame[31] = ord('e')
        
        # 调试信息：验证帧结构
        print(f"帧结构验证:")
        print(f"  帧长度: {len(frame)} 字节")
        print(f"  帧头[0]: 0x{frame[0]:02X} (应该是0x73='s')")
        print(f"  数据类型[1]: 0x{frame[1]:02X}")
        print(f"  命令字[2]: 0x{frame[2]:02X}")
        print(f"  数据域[3-30]: {frame[3:31].hex()}")
        print(f"  帧尾[31]: 0x{frame[31]:02X} (应该是0x65='e')")
        
        return bytes(frame)
    
    def parse_frame(self, data):
        """
        解析新协议格式的数据帧
        
        Args:
            data: 接收到的32字节数据
        
        Returns:
            解析后的数据字典，包含datatype, command, data数组
        """
        if not isinstance(data, (bytes, bytearray)) or len(data) < 32:
            return None
            
        if data[0] != ord('s') or data[31] != ord('e'):
            return None  # 帧头或帧尾不匹配
            
        try:
            datatype = data[1]  # 消息类型
            command = data[2]   # 命令字
            
            # 解析数据域 (8个uint32值)
            data_array = []
            for i in range(8):
                start_idx = 3 + i * 4
                end_idx = start_idx + 4
                uint32_value = struct.unpack('<I', data[start_idx:end_idx])[0]
                data_array.append(uint32_value)
            
            return {
                'datatype': datatype,
                'command': command,
                'data': data_array
            }
        except Exception as e:
            print(f"解析新协议帧数据出错: {str(e)}")
            return None
    
    def send_command(self, command, data_array=None):
        """
        发送新协议控制命令
        
        Args:
            command: 命令字 (如0x00=开机, 0x01=关机等)
            data_array: 数据域数组 (可选)
        
        Returns:
            是否发送成功
        """
        try:
            print(f"准备发送命令: 0x{command:02X}, 数据: {data_array}")
            
            # 打包新协议命令帧
            frame = self.pack_frame(
                datatype=0xA0,  # 上位机->下位机
                command=command,
                data_array=data_array
            )
            
            print(f"打包后的帧数据长度: {len(frame)} 字节")
            print(f"帧数据(hex): {frame.hex()}")
            print(f"帧结构分析:")
            print(f"  帧头: 0x{frame[0]:02X} ({'s' if frame[0] == ord('s') else '无效'})")
            print(f"  数据类型: 0x{frame[1]:02X}")
            print(f"  命令字: 0x{frame[2]:02X}")
            print(f"  数据域: {[frame[3+i*4:7+i*4].hex() for i in range(8)]}")
            print(f"  帧尾: 0x{frame[31]:02X} ({'e' if frame[31] == ord('e') else '无效'})")
            
            # 发送命令帧
            return self.send_data(frame)
                
        except Exception as e:
            print(f"发送协议命令出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def read_frame(self):
        """读取一个新协议格式的数据帧并解析"""
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
            print(f"读取协议帧数据出错: {str(e)}")
            return None

