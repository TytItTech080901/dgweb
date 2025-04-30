import serial
import time
from serial.tools import list_ports

class SerialHandler:
    def __init__(self, port=None, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        if port is None:
            self.port = self.find_available_port()
        self.connect()
    
    def find_available_port(self):
        """自动查找可用的串口设备"""
        ports = list_ports.comports()
        for port in ports:
            try:
                test_serial = serial.Serial(port.device, self.baudrate, timeout=1)
                test_serial.close()
                return port.device
            except:
                continue
        return None

    def connect(self):
        if not self.port:
            print("未找到可用串口")
            return
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # 等待串口初始化
            print(f"成功连接到串口: {self.port}")
        except Exception as e:
            print(f"无法打开串口 {self.port}: {str(e)}")
            self.serial = None

    def is_connected(self):
        return self.serial is not None and self.serial.is_open
        
    def send_data(self, data):
        if not self.is_connected():
            print("串口未连接")
            return False
        try:
            if isinstance(data, str):
                data = data.encode()
            self.serial.write(data)
            return True
        except Exception as e:
            print(f"发送数据错误: {str(e)}")
            return False
        
    def read_data(self):
        if not self.is_connected():
            return "串口未连接"
        try:
            response = self.serial.readline()
            return response.decode().strip()
        except Exception as e:
            return f"读取数据错误: {str(e)}"
        
    def __del__(self):
        if hasattr(self, 'serial') and self.serial:
            self.serial.close()