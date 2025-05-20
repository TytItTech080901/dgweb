# filepath: /home/cat/Py-server/modules/detection_module.py
from Yolo import detector
import time
import threading
import cv2

class DetectionService:
    def __init__(self, model_path="Yolo/best6_rknn_model", camera_id=None, show_img=False):
        self.detector = None
        self.model_path = model_path
        self.camera_id = camera_id  # camera_id=None将使用自动发现可用摄像头
        
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

    def initialize(self):
        """初始化检测服务"""
        if self.initialized:
            return True
            
        try:
            with self.lock:
                print("=" * 50)
                print("正在初始化检测服务...")
                
                # 在初始化YOLO检测器前先输出摄像头状态信息
                print("当前传入的摄像头ID: {}".format(
                    self.camera_id if self.camera_id is not None else "None (将自动查找可用摄像头)")
                )
                
                # 可以尝试先查看系统中可用的设备
                try:
                    import glob
                    video_devices = sorted(glob.glob('/dev/video*'))
                    if video_devices:
                        print(f"系统中可用的视频设备: {video_devices}")
                    else:
                        print("未在系统中找到视频设备文件")
                except Exception as e:
                    print(f"列出视频设备时出错: {e}")
                
                # 创建检测器实例，传入的camera_id可能为None，会触发自动查找
                print("创建YOLO检测器实例...")
                # 在检测器初始化时配置模型路径和TPEs参数
                tpe_count = 2 if self._is_low_performance_device() else 4
                print(f"基于性能测试，使用线程池大小: {tpe_count}")
                
                self.detector = detector.Detector(
                    model_path=self.model_path,
                    camera_id=self.camera_id,  # 可以是None，会自动寻找可用摄像头
                    show_img=self.show_img,
                    TPEs=tpe_count  # 根据设备性能调整线程池大小
                )
                
                # 尝试初始化检测器，最多重试2次
                retry_count = 0
                max_retries = 2
                success = False
                
                while retry_count <= max_retries and not success:
                    try:
                        if retry_count > 0:
                            print(f"第 {retry_count} 次重试初始化检测器...")
                            # 如果重试，切换尝试的摄像头ID，优先考虑1和4
                            preferred_ids = [1, 4]
                            for preferred_id in preferred_ids:
                                if retry_count == 1 and preferred_id != self.camera_id:
                                    self.detector.camera_id = preferred_id
                                    print(f"重试时尝试优先使用摄像头ID: {preferred_id}")
                                    break
                        else:
                            print("首次尝试初始化检测器...")
                            
                        success = self.detector.initialize()
                        
                        if success:
                            break
                            
                    except Exception as e:
                        print(f"初始化尝试 {retry_count+1} 失败: {e}")
                        
                    retry_count += 1
                    time.sleep(1)  # 等待1秒后重试
                
                if success:
                    self.initialized = True
                    self.error_count = 0
                    # 如果成功初始化，保存实际使用的摄像头ID
                    self.camera_id = self.detector.camera_id
                    print(f"检测服务初始化成功，使用摄像头ID: {self.camera_id}")
                    
                    # 添加额外的结果日志
                    try:
                        # 检测摄像头是否仍然有效
                        if self.detector.cap and self.detector.cap.isOpened():
                            width = self.detector.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                            height = self.detector.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                            fps = self.detector.cap.get(cv2.CAP_PROP_FPS)
                            print(f"摄像头工作正常，当前配置: {width}x{height}@{fps}fps")
                        else:
                            print("警告：摄像头状态异常，可能需要重新初始化")
                    except Exception as e:
                        print(f"获取摄像头状态时出错: {e}")
                        
                    print("=" * 50)
                    return True
                else:
                    raise RuntimeError("检测器初始化失败，所有尝试都没有成功")
                    
        except Exception as e:
            print(f"初始化检测服务失败: {str(e)}")
            print("建议：")
            print("1. 检查摄像头物理连接")
            print("2. 检查摄像头是否被其他应用程序占用")
            print("3. 尝试重启应用后再试")
            print("4. 如果问题仍然存在，请尝试指定具体的摄像头ID")
            print("=" * 50)
            self.cleanup()
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
        last_print_time = 0  # 上次打印时间
        print_interval = 1.0  # 打印间隔（秒）
        last_detected_status = False  # 上次检测状态
        
        while self.detector and self.detector.running:
            try:
                if not self.detector.process_frame():
                    print("处理帧失败")
                    time.sleep(0.01)  # 短暂暂停避免CPU过载
                    continue
                
                # 定期打印位置信息或检测状态变化时打印
                current_time = time.time()
                current_detected = self.detector.detected
                
                if (current_time - last_print_time >= print_interval or 
                    current_detected != last_detected_status):
                    
                    # 检测状态变化时打印更明显的提示
                    if current_detected != last_detected_status:
                        if current_detected:
                            print("\n=== 状态变化：检测到新目标 ===")
                        else:
                            print("\n=== 状态变化：目标丢失 ===")
                    
                    if current_detected:
                        print(f"检测到目标: 位置=({self.detector.position[0]:.3f}, {self.detector.position[1]:.3f}), " +
                              f"置信度={self.detector.confidence:.2f}, FPS={self.detector.fps:.1f}")
                    else:
                        print(f"未检测到目标，FPS={self.detector.fps:.1f}")
                    
                    last_print_time = current_time
                    last_detected_status = current_detected
                
                # 检查错误次数
                if self.error_count >= self.max_errors:
                    current_time = time.time()
                    if current_time - self.last_error_time >= self.error_cooldown:
                        # 重置错误计数
                        self.error_count = 0
                    else:
                        print(f"错误次数过多，等待冷却期结束 ({self.error_cooldown}秒)")
                        break
                        
            except Exception as e:
                print(f"检测循环发生错误: {str(e)}")
                self.error_count += 1
                self.last_error_time = time.time()
                time.sleep(0.1)  # 发生错误时稍长暂停
