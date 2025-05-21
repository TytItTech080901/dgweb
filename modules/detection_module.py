# filepath: /home/cat/Py-server/modules/detection_module.py
from Yolo import detector
import time
import threading
import cv2
import os

class DetectionService:
    """检测服务类，用于管理目标检测"""
    
    def __init__(self, model_path="Yolo/best6_rknn_model", camera_id=None, show_img=False):
        self.detector = None
        self.model_path = model_path
        self.camera_id = camera_id
        self.api_preference = None  # 存储成功的API类型
        
        # 检查是否在无显示环境中，如果是则禁用图像显示
        import os
        if show_img and not self._has_display():
            print("警告: DetectionService检测到无显示环境，已自动禁用图像显示功能")
            self.show_img = False
        else:
            self.show_img = show_img
        
        self.lock = threading.Lock()
        self.initialized = False
        
        # 自动发送相关属性
        self.serial_handler = None  # 串口处理器
        self.auto_send_enabled = False  # 是否启用自动发送
        self.auto_send_thread = None  # 自动发送线程
        self.auto_send_interval = 0.05  # 发送间隔秒数 (默认50ms)
        
        # 错误处理
        self.error_count = 0
        self.max_errors = 3
        self.last_error_time = 0
        self.error_cooldown = 5.0  # 错误冷却时间（秒）
    
    def _try_open_camera(self, camera_id, api_id, api_name, attempt=1):
        """尝试打开单个摄像头
        
        Args:
            camera_id: 摄像头ID
            api_id: API ID
            api_name: API名称
            attempt: 尝试次数
            
        Returns:
            tuple: (cv2.VideoCapture, 是否成功)
        """
        try:
            if isinstance(camera_id, str):
                cap = cv2.VideoCapture(camera_id, api_id)
            else:
                cap = cv2.VideoCapture(int(camera_id), api_id)
                
            if not cap.isOpened():
                print(f"无法打开摄像头 {camera_id} (API: {api_name}, 尝试 {attempt})")
                return None, False
                
            # 设置摄像头参数
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            # 等待摄像头初始化
            time.sleep(0.5)
            
            # 尝试读取第一帧
            ret, frame = cap.read()
            if not ret or frame is None:
                print(f"无法从摄像头 {camera_id} 读取帧 (API: {api_name}, 尝试 {attempt})")
                cap.release()
                return None, False
                
            # 成功读取到帧
            print(f"成功打开摄像头 {camera_id} (API: {api_name}, 尝试 {attempt})")
            print(f"分辨率: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
            print(f"帧率: {cap.get(cv2.CAP_PROP_FPS):.1f}")
            return cap, True
            
        except Exception as e:
            print(f"尝试打开摄像头 {camera_id} 时出错 (API: {api_name}, 尝试 {attempt}): {str(e)}")
            if 'cap' in locals():
                cap.release()
            return None, False

    def _try_camera_apis(self, camera_id):
        """尝试使用不同的API打开摄像头
        
        Args:
            camera_id: 摄像头ID，可以是数字或设备路径
            
        Returns:
            tuple: (cv2.VideoCapture对象, 使用的API) 或 (None, None)
        """
        apis = [
            (cv2.CAP_ANY, "ANY"),
            (cv2.CAP_V4L2, "V4L2"),
            (cv2.CAP_V4L, "V4L"),
        ]
        
        for api_id, api_name in apis:
            print(f"\n尝试对摄像头 {camera_id} 使用 {api_name} API...")
            
            # 每个API尝试3次
            for attempt in range(1, 4):
                cap, success = self._try_open_camera(camera_id, api_id, api_name, attempt)
                if success:
                    return cap, api_name
                elif attempt < 3:  # 不是最后一次尝试
                    print(f"等待1秒后重试...")
                    time.sleep(1)
                    
            print(f"使用 {api_name} API的所有尝试均失败")
            
        return None, None

    def _initialize_camera(self):
        """初始化摄像头，尝试不同的摄像头ID和API
        
        Returns:
            bool: 是否成功初始化摄像头
        """
        print("\n开始初始化摄像头...")
        
        # 如果指定了摄像头ID，优先尝试
        if self.camera_id is not None:
            print(f"尝试使用指定的摄像头ID: {self.camera_id}")
            cap, api = self._try_camera_apis(self.camera_id)
            if cap is not None:
                self.cap = cap
                self.api_preference = api
                print(f"成功初始化指定的摄像头 {self.camera_id}")
                return True
            print("指定的摄像头初始化失败，尝试其他摄像头...")
            
        # 尝试常用的摄像头索引
        camera_ids = [0, 1, 2, 3, 4]
        for camera_id in camera_ids:
            print(f"\n尝试摄像头索引 {camera_id}...")
            cap, api = self._try_camera_apis(camera_id)
            if cap is not None:
                self.cap = cap
                self.camera_id = camera_id
                self.api_preference = api
                print(f"成功初始化摄像头索引 {camera_id}")
                return True
                
        # 尝试设备文件路径
        print("\n尝试通过设备文件路径查找摄像头...")
        import glob
        device_paths = glob.glob('/dev/video[0-9]*')
        for device_path in sorted(device_paths):
            if device_path.endswith(('dec0', 'enc0')):  # 跳过编解码器设备
                print(f"跳过编解码器设备: {device_path}")
                continue
                
            print(f"\n尝试设备路径: {device_path}")
            cap, api = self._try_camera_apis(device_path)
            if cap is not None:
                self.cap = cap
                self.camera_id = device_path
                self.api_preference = api
                print(f"成功通过设备路径初始化摄像头: {device_path}")
                return True
                
        print("\n无法找到可用的摄像头")
        return False
    
    def _is_low_performance_device(self):
        """检测当前设备是否为低性能设备，用于优化模型推理参数
        
        Returns:
            bool: 如果是低性能设备返回True
        """
        try:
            import multiprocessing
            import os
            
            # 检查CPU核心数
            cpu_count = multiprocessing.cpu_count()
            
            # 检查可用内存
            try:
                with open('/proc/meminfo', 'r') as f:
                    mem_info = f.read()
                mem_available = 0
                for line in mem_info.split('\n'):
                    if 'MemAvailable' in line:
                        mem_available = int(line.split()[1]) / 1024  # 转换为MB
                        break
                
                # 如果CPU核心少于4或可用内存小于1.5GB，认为是低性能设备
                is_low_perf = (cpu_count < 4) or (mem_available < 1500)
                
                print(f"性能检测: CPU核心: {cpu_count}, 可用内存: {mem_available:.0f}MB")
                if is_low_perf:
                    print("检测到低性能设备，将优化模型参数以提高响应速度")
                
                return is_low_perf
                
            except Exception:
                # 如果读取内存信息失败，只基于CPU核心判断
                return cpu_count < 4
                
        except Exception as e:
            print(f"性能检测时出错: {e}")
            # 默认非低性能设备
            return False
            
    def _has_display(self):
        """检查当前环境是否支持显示图像
        
        Returns:
            bool: 如果环境支持显示图像则返回True，否则返回False
        """
        try:
            # 检查Linux环境下是否设置了DISPLAY环境变量
            import os
            if os.name == 'posix' and 'DISPLAY' not in os.environ:
                return False
                
            # 尝试创建一个小窗口测试显示功能
            try:
                import numpy as np
                import cv2
                test_window_name = "display_test"
                small_img = np.zeros((10, 10, 3), dtype=np.uint8)
                cv2.imshow(test_window_name, small_img)
                cv2.waitKey(1)
                cv2.destroyWindow(test_window_name)
                return True
            except cv2.error:
                return False
        except Exception as e:
            print(f"显示环境检查失败: {e}")
            return False
            
    def set_serial_handler(self, serial_handler):
        """
        设置串口处理器
        
        Args:
            serial_handler: SerialCommunicationHandler实例
        """
        self.serial_handler = serial_handler
        print("已设置串口处理器到检测服务")
        
    def start_auto_send(self, interval=0.05):
        """
        启动自动发送位置数据
        
        Args:
            interval: 发送间隔秒数
            
        Returns:
            是否成功启动
        """
        # 检查串口处理器
        if not self.serial_handler:
            print("未设置串口处理器，无法启动自动发送")
            return False
        
        # 检查串口连接
        if not self.serial_handler.is_connected():
            print("串口未连接，无法启动自动发送")
            return False
        
        # 检查检测服务是否运行
        if not self.is_running():
            print("检测服务未运行，无法启动自动发送")
            return False
        
        # 如果已启动，先停止
        if self.auto_send_enabled:
            self.stop_auto_send()
        
        # 设置参数并启动线程
        self.auto_send_interval = interval
        self.auto_send_enabled = True
        self.auto_send_thread = threading.Thread(target=self._auto_send_loop, daemon=True)
        self.auto_send_thread.start()
        print(f"已启动坐标自动发送 (间隔: {interval*1000:.0f}ms)")
        return True
    
    def stop_auto_send(self):
        """
        停止自动发送
        
        Returns:
            是否成功停止
        """
        self.auto_send_enabled = False
        
        # 等待线程结束
        if self.auto_send_thread and self.auto_send_thread.is_alive():
            self.auto_send_thread.join(timeout=1.0)
            self.auto_send_thread = None
        
        print("已停止坐标自动发送")
        return True
    
    def _auto_send_loop(self):
        """自动发送位置数据的循环"""
        last_detected = False  # 上次是否检测到目标
        
        while self.auto_send_enabled and self.is_running():
            try:
                # 获取位置数据
                position_data = self.get_position()
                
                # 检查串口连接
                if not self.serial_handler.is_connected():
                    print("串口连接丢失，停止自动发送")
                    break
                
                # 发送检测位置数据 
                _, message = self.serial_handler.send_detection_position(position_data)
                
                # 仅在检测状态变化时打印日志
                if position_data['detected'] != last_detected:
                    last_detected = position_data['detected']
                    if position_data['detected']:
                        print(f"自动发送检测坐标: ({position_data['x']:.3f}, {position_data['y']:.3f})")
                    else:
                        print("自动发送未检测状态")
                
                # 延时
                time.sleep(self.auto_send_interval)
                
            except Exception as e:
                print(f"自动发送坐标异常: {str(e)}")
                time.sleep(0.5)  # 出错后稍作延时
    
    def is_auto_sending(self):
        """是否正在自动发送坐标"""
        return self.auto_send_enabled and self.auto_send_thread and self.auto_send_thread.is_alive()

    def _cleanup(self):
        """清理所有资源"""
        try:
            # 停止自动发送
            if hasattr(self, 'auto_send_enabled') and self.auto_send_enabled:
                self.stop_auto_send()
            
            # 释放检测器资源
            if hasattr(self, 'detector') and self.detector:
                if hasattr(self.detector, 'cleanup'):
                    self.detector.cleanup()
                self.detector = None
            
            # 释放摄像头资源
            if hasattr(self, 'cap') and self.cap:
                self.cap.release()
                self.cap = None
            
            # 重置状态
            self.initialized = False
            print("已清理检测器资源")
            
        except Exception as e:
            print(f"清理资源时出错: {str(e)}")

    def initialize(self):
        """初始化检测服务
        
        Returns:
            bool: 是否成功初始化
        """
        try:
            # 初始化摄像头
            if not self._initialize_camera():
                print("初始化检测服务失败: 无法初始化摄像头")
                return False
            
            # 检查是否是低性能设备
            is_low_perf = self._is_low_performance_device()
            
            print(f"\n正在初始化检测器...")
            print(f"使用摄像头: ID={self.camera_id}, API={self.api_preference}")
            
            # 确保模型路径存在
            if not os.path.exists(self.model_path):
                print(f"初始化检测服务失败: 模型路径不存在 - {self.model_path}")
                self._cleanup()
                return False
                
            try:
                # 创建检测器实例
                self.detector = detector.rknnPoolExecutor(
                    model_path=self.model_path,
                    TPEs=2 if is_low_perf else 4,  # 低性能设备使用较少线程
                    func=detector.thread_safe_predict
                )
                
                # 添加必要的属性到rknnPoolExecutor实例
                self.detector.running = False
                self.detector.detected = False
                self.detector.position = [0.0, 0.0]
                self.detector.width = 0.0
                self.detector.height = 0.0
                self.detector.confidence = 0.0
                self.detector.fps = 0.0
                
                # 预热检测器
                print("预热检测器...")
                ret, frame = self.cap.read()
                if ret:
                    self.detector.put(frame)
                    result, success = self.detector.get()
                    if not success:
                        print("警告: 预热过程中无法获取检测结果")
                
                print("检测器初始化成功")
                self.initialized = True
                return True
                
            except Exception as e:
                print(f"创建检测器实例失败: {str(e)}")
                self._cleanup()
                return False
            
        except Exception as e:
            print(f"初始化检测服务失败: {str(e)}")
            self._cleanup()
            return False
    
    def cleanup(self):
        """清理资源"""
        with self.lock:
            if self.auto_send_enabled:
                self.stop_auto_send()
                
            if self.detector:
                self.detector.cleanup()
                self.detector = None
                
            self.initialized = False
    
    def __del__(self):
        """确保资源被清理"""
        self.cleanup()
        
    def is_running(self):
        """检查服务是否正在运行"""
        return self.initialized and self.detector and self.detector.running
    
    def get_position(self):
        """获取目标位置数据"""
        if not self.is_running():
            return {
                "detected": False,
                "position": [0.0, 0.0],
                "width": 0.0,
                "height": 0.0,
                "confidence": 0.0,
                "fps": 0.0,
                "x": 0.0,  # 兼容自动发送接口
                "y": 0.0   # 兼容自动发送接口
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
    
    def start(self):
        """启动检测服务"""
        if not self.initialized:
            if not self.initialize():
                return False
        
        try:
            with self.lock:
                if not self.detector or not self.detector.running:
                    # 启动检测线程
                    self.process_thread = threading.Thread(
                        target=self._detection_loop,
                        daemon=True
                    )
                    self.detector.running = True
                    self.process_thread.start()
                    print("检测线程已启动")
                    return True
                return True  # 如果已经在运行，返回成功
                
        except Exception as e:
            print(f"启动检测服务失败: {str(e)}")
            self.cleanup()
            return False
            
    def stop(self):
        """停止检测服务"""
        try:
            with self.lock:
                if self.auto_send_enabled:
                    self.stop_auto_send()
                    
                if self.detector:
                    self.detector.running = False
                    
                if hasattr(self, 'process_thread') and self.process_thread:
                    self.process_thread.join(timeout=1.0)
                    
                self.cleanup()
                print("检测服务已停止")
                return True
                
        except Exception as e:
            print(f"停止检测服务时出错: {str(e)}")
            return False
            
    def _detection_loop(self):
        """检测主循环"""
        last_print_time = 0 # 上次打印时间
        print_interval = 1.0 # 打印间隔（秒）
        last_detected_status = False # 上次检测状态
        
        while self.detector and self.detector.running:
            try:
                # 获取一帧图像
                ret, frame = self.cap.read()
                if not ret:
                    print("无法获取摄像头帧")
                    time.sleep(0.01)
                    continue
                    
                # 将帧提交给检测器
                self.detector.put(frame)
                
                # 获取检测结果
                result, success = self.detector.get()
                if not success or result is None:
                    print("无法获取检测结果")
                    time.sleep(0.01)
                    continue
                    
                # 处理检测结果
                # 寻找置信度最高的检测框
                max_conf = 0
                detected = False
                
                if len(result) > 0:
                    result = result[0]  # 获取第一组结果
                    boxes = result.boxes
                    if len(boxes) > 0:
                        # 找出置信度最高的框
                        box_best = max(boxes, key=lambda box: box.conf[0].cpu().numpy())
                        # 获取归一化的坐标 (使用xywhn，范围为[0,1])
                        pos_x, pos_y, width, height = box_best.xywhn[0].cpu().numpy()
                        
                        # 将坐标转换为[-0.5, 0.5]范围，并确保转换为Python内置float类型
                        self.detector.position = [float(pos_x - 0.5), float(pos_y - 0.5)]
                        self.detector.width = float(width)
                        self.detector.height = float(height)
                        self.detector.confidence = float(box_best.conf[0].cpu().numpy())
                        self.detector.detected = True
                        detected = True
                
                if not detected:
                    self.detector.position = [0.0, 0.0]
                    self.detector.width = 0.0
                    self.detector.height = 0.0
                    self.detector.confidence = 0.0
                    self.detector.detected = False
                
                # 每隔一定时间打印状态
                current_time = time.time()
                if current_time - last_print_time >= print_interval:
                    if detected:
                        print(f"检测到目标: ({self.detector.position[0]:.3f}, {self.detector.position[1]:.3f})")
                    elif last_detected_status:
                        print("目标丢失")
                    last_detected_status = detected
                    last_print_time = current_time
                    
            except Exception as e:
                print(f"检测循环发生错误: {str(e)}")
                self.error_count += 1
                self.last_error_time = time.time()
                time.sleep(0.1)  # 发生错误时稍长暂停
