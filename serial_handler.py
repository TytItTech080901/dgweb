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

    def pack_frame(self, datatype=0xA0, command=0xFF, data_array=None):
        """
        按照新协议格式打包数据帧
        
        Args:
            datatype: 消息类型 (0xA0: 上位机->下位机, 0xB0: 下位机->上位机)
            command: 命令字
            data_array: 数据域数组，最多7个uint32值 (数据域总共28字节)
        
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
        
        # 数据域 (7个uint32值，每个4字节，总共28字节)
        if data_array is None:
            data_array = [0] * 7
        
        # 确保数据数组不超过7个元素
        data_array = data_array[:7]
        while len(data_array) < 7:
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
        # 检查数据类型和长度
        if not isinstance(data, (bytes, bytearray)):
            print(f"解析失败：数据类型不正确，类型为: {type(data)}")
            return None
            
        # 检查数据长度
        if len(data) < 32:
            print(f"解析失败：数据长度不足，当前长度: {len(data)} 字节")
            return None
            
        # 检查帧头帧尾
        if data[0] != ord('s') or data[31] != ord('e'):
            print(f"解析失败：帧头帧尾标识不匹配, 帧头: 0x{data[0]:02X}, 帧尾: 0x{data[31]:02X}")
            return None
            
        try:
            datatype = data[1]  # 消息类型
            command = data[2]   # 命令字
            
            # 检查消息类型是否有效
            if datatype not in [0xA0, 0xB0]:
                print(f"警告：消息类型不在预期范围内: 0x{datatype:02X}")
            
            # 解析数据域（根据下位机格式，4个uint32值）
            # 1. isLight（是否开灯）: data[3-6]
            # 2. isOpen（是否开机）: data[7-10]
            # 3. tmpLight（亮度）: data[11-14]
            # 4. tmpTemperature（色温）: data[15-18]
            
            data_array = []
            
            # 解析4个uint32值
            for i in range(4):
                start_idx = 3 + i * 4
                end_idx = start_idx + 4
                
                # 确保索引不越界
                if end_idx <= len(data):
                    try:
                        uint32_value = struct.unpack('<I', data[start_idx:end_idx])[0]
                        data_array.append(uint32_value)
                    except struct.error as e:
                        print(f"解析数据域错误，索引[{start_idx}:{end_idx}]: {str(e)}")
                        data_array.append(0)  # 使用默认值
                else:
                    print(f"数据长度不足，无法解析数据域[{i}]")
                    data_array.append(0)  # 使用默认值
            
            # 为了保持向后兼容，将数组扩展到7个元素
            while len(data_array) < 7:
                data_array.append(0)
            
            result = {
                'datatype': datatype,
                'command': command,
                'data': data_array
            }
            
            # 添加更详细的解析字段
            if len(data_array) >= 4:
                result['is_light'] = bool(data_array[0])  # 是否开灯
                result['is_open'] = bool(data_array[1])   # 是否开机
                result['brightness'] = data_array[2]      # 亮度
                result['color_temp'] = data_array[3]      # 色温
            
            print(f"解析成功: {result}")
            return result
            
        except Exception as e:
            print(f"解析新协议帧数据出错: {str(e)}")
            import traceback
            traceback.print_exc()
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
        if not self.is_connected():
            print("发送命令失败：串口未连接")
            return False
            
        try:
            print(f"准备发送命令: 0x{command:02X}, 数据: {data_array}")
            
            # 清空输出缓冲区，避免之前的数据干扰
            self.serial.reset_output_buffer()
            
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
            print(f"  数据域: {frame[3:31].hex()}")
            print(f"  帧尾: 0x{frame[31]:02X} ({'e' if frame[31] == ord('e') else '无效'})")
            
            # 发送命令帧
            success = self.send_data(frame)
            
            if success:
                print("命令帧发送成功")
            else:
                print("命令帧发送失败")
                
            return success
                
        except Exception as e:
            print(f"发送协议命令出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def read_frame(self, timeout=1.0):
        """
        读取一个新协议格式的数据帧并解析
        
        Args:
            timeout: 读取超时时间(秒)，默认1秒
        
        Returns:
            解析后的数据字典，或None如果读取失败
        """
        if not self.is_connected():
            print("读取失败：串口未连接")
            return None
            
        try:
            # 保存原始超时设置
            original_timeout = self.serial.timeout
            self.serial.timeout = timeout
            
            # 尝试读取一个完整帧
            start_time = time.time()
            
            # 首先确认帧头
            header_found = False
            raw_data = bytearray()
            
            # 在超时时间内搜索帧头
            while time.time() - start_time < timeout:
                if self.serial.in_waiting > 0:
                    byte = self.serial.read(1)
                    if byte == b's':  # 找到帧头
                        raw_data = bytearray(byte)
                        header_found = True
                        break
                time.sleep(0.01)  # 短暂休息，避免CPU占用过高
            
            # 如果没找到帧头，就返回None
            if not header_found:
                print("未能在串口数据中找到帧头标识's'")
                self.serial.timeout = original_timeout
                return None
            
            # 读取剩余的31个字节
            remaining_data = self.serial.read(31)
            raw_data.extend(remaining_data)
            
            # 检查是否读取了足够的数据
            if len(raw_data) < 32:
                print(f"读取到不完整的数据帧: {len(raw_data)} 字节")
                print(f"不完整数据(hex): {raw_data.hex()}")
                self.serial.timeout = original_timeout
                return None
                
            # 检查帧尾
            if raw_data[31] != ord('e'):
                print(f"帧尾错误: 0x{raw_data[31]:02X}，应为0x65('e')")
                self.serial.timeout = original_timeout
                return None
            
            print(f"读取到完整的数据帧: 32 字节")
            print(f"数据帧(hex): {raw_data.hex()}")
            print(f"帧结构分析:")
            print(f"  帧头: 0x{raw_data[0]:02X} ({'s' if raw_data[0] == ord('s') else '无效'})")
            print(f"  数据类型: 0x{raw_data[1]:02X}")
            print(f"  命令字: 0x{raw_data[2]:02X}")
            print(f"  数据域: {raw_data[3:31].hex()}")
            print(f"  帧尾: 0x{raw_data[31]:02X} ({'e' if raw_data[31] == ord('e') else '无效'})")
            
            # 恢复原始超时设置
            self.serial.timeout = original_timeout
            
            # 解析帧数据
            return self.parse_frame(raw_data)
            
        except Exception as e:
            print(f"读取协议帧数据出错: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 恢复原始超时设置
            if hasattr(self, 'serial') and self.serial:
                self.serial.timeout = original_timeout
                
            return None
        
    def request_data(self, command, data_array=None):
        """
        发送命令并等待响应
        
        Args:
            command: 命令字
            data_array: 数据域数组 (可选)
        
        Returns:
            解析后的响应数据字典，或None如果读取失败
        """
        if not self.send_command(command, data_array):
            print("发送命令失败")
            return None
        
        # 先清空接收缓冲区
        self.serial.reset_input_buffer()
        
        # 等待一段时间以接收响应
        time.sleep(0.1)

        # 尝试读取响应帧
        cnt = 0
        data = self.read_frame()
        # 检查data是否为None，并检查data中是否有datatype字段
        while (data is None or data.get('datatype') != 0xB0) and cnt < 10:
            print(f"未收到预期的响应帧，尝试重新读取... (尝试次数: {cnt})")
            # 等待一段时间再读取
            time.sleep(0.1)
            data = self.read_frame()
            cnt += 1
        
        if cnt >= 10:
            print("错误：未收到预期的响应帧，可能是设备未响应或连接问题。")
            return None
            
        return data

    def send_command_setting_light(self, brightness, color_temp):
        """
        发送设置台灯亮度和色温的命令
        
        Args:
            brightness: 亮度值 (0-100)
            color_temp: 色温值 (0-100)
        
        Returns:
            是否发送成功
        """
        if not self.is_connected():
            print("发送失败：串口未连接")
            return False
        
        # 限制亮度和色温范围
        brightness = max(0, min(100, brightness))

        #数据转换
        temp_brightness = brightness * 10  # 转换为0-1000的范围
        
        # 打包数据
        data_array = [temp_brightness, color_temp] + [0] * 6

        return self.send_command(0x16, data_array)
