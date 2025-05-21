import cv2
import time
import os
import numpy as np
from ultralytics import YOLO
from threading import Thread
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed

class rknnPoolExecutor:
    def __init__(self, model_path, TPEs, func):
        self.TPEs = TPEs
        self.queue = queue.Queue()
        self.pool = ThreadPoolExecutor(max_workers=TPEs)
        self.models = self.__init_models(model_path, TPEs)
        self.func = func
        self.num = 0

    def put(self, frame):
        self.queue.put(
            self.pool.submit(self.func, self.models[self.num % self.TPEs], frame)
        )
        self.num += 1

    def get(self):
        if self.queue.empty():
            return None, False
        temp = []
        temp.append(self.queue.get())
        for frame in as_completed(temp):
            return frame.result(), True

    def __init_models(self, model_path, TPEs):
        rknn_list = []
        for i in range(TPEs):
            # 在初始化模型时直接指定task='detect'
            rknn_list.append(YOLO(model_path, task='detect'))
        return rknn_list


def thread_safe_predict(model, frame):
    """安全的模型预测函数
    
    Args:
        model: YOLO模型实例
        frame: 要处理的图像帧
        
    Returns:
        模型预测结果
    """
    try:
        # 明确指定task为detect以避免警告
        # 添加conf和iou参数以减少假阳性检测，设置较低的置信度阈值以确保敏感性
        outputs = model(frame, verbose=False, task='detect', conf=0.25, iou=0.45)
        return outputs
    except Exception as e:
        # 使用更简洁的错误信息，避免过多错误输出
        if not hasattr(thread_safe_predict, 'error_count'):
            thread_safe_predict.error_count = 0
            
        thread_safe_predict.error_count += 1
        
        # 每10次错误才输出一次，避免刷屏
        if thread_safe_predict.error_count % 10 == 1:
            print(f"模型预测错误 ({thread_safe_predict.error_count}): {e}")
        return None

class Detector:
    def __init__(self, TPEs=4, model_path="Yolo/best6_rknn_model", camera_id=None, show_img=False):
        """
        实例化目标检测器

        Args:
            TPEs (int): 线程池的线程数，默认4
            model_path (str): 模型路径
            camera_id (int, optional): 摄像头ID，若为None则自动查找可用摄像头
            show_img (bool): 是否显示图像，默认False
            
        此检测器使用YOLO模型进行目标检测，支持多线程处理以提高性能。
        检测结果包括目标位置(x,y)，置信度和FPS信息。
        坐标系统采用[-0.5, 0.5]范围的归一化坐标。
        """
        self.TPEs = TPEs
        self.model_path = model_path
        self.camera_id = camera_id  # 可以为None，初始化时会自动查找
        
        # 如果要求显示图像，先检查是否有显示环境
        if show_img and not self._has_display():
            print("警告: 检测到无显示环境，已自动禁用图像显示功能")
            self.show_img = False
            self._display_warning_shown = True
        else:
            self.show_img = show_img
            
        self.running = False
        self.fps = 0.0
        self.frames = 0
        self.position = [0.0, 0.0]
        self.width = 0.0
        self.height = 0.0
        self.confidence = 0.0
        self.detected = False
        self.cap = None
        self.pool = None
        self._last_frame_time = time.time()
        self._frame_count = 0
        self._fps_update_interval = 1.0  # 每秒更新一次FPS

    def _has_display(self):
        """检查当前环境是否支持显示图像
        
        Returns:
            bool: 如果环境支持显示图像则返回True，否则返回False
        """
        try:
            # 检查Linux环境下是否设置了DISPLAY
            if os.name == 'posix' and 'DISPLAY' not in os.environ:
                return False
                
            # 尝试创建一个小窗口测试显示功能
            test_window_name = "display_test"
            try:
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
            
    def _find_available_cameras(self):
        """查找所有可用的摄像头设备
        
        Returns:
            list: 可用摄像头ID列表
        """
        available_cameras = []
        camera_api_preference = cv2.CAP_V4L2  # Linux上使用V4L2后端，效果更好
        
        print("开始扫描可用摄像头...")
        
        # 方法1：使用传统的枚举方式查找所有摄像头
        for i in range(0, 10):  # 检查0-9号摄像头
            try:
                print(f"尝试检测摄像头索引 {i}...")
                cap = cv2.VideoCapture(i, camera_api_preference)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        available_cameras.append(i)
                        print(f"发现可用摄像头: 索引 {i}, 分辨率: {frame.shape[1]}x{frame.shape[0]}")
                    else:
                        print(f"摄像头索引 {i} 无法读取帧")
                    cap.release()
                else:
                    print(f"摄像头索引 {i} 无法打开")
            except Exception as e:
                print(f"检测摄像头 {i} 时出错: {e}")
                continue
        
        # 方法2：使用设备文件路径尝试打开摄像头        
        try:
            import glob
            video_devices = glob.glob('/dev/video*')
            for device in video_devices:
                try:
                    index = int(device.replace('/dev/video', ''))
                    # 如果已经尝试过这个索引，跳过
                    if index in available_cameras:
                        continue
                        
                    print(f"尝试通过设备路径打开 {device}...")
                    # 尝试直接使用设备路径
                    cap = cv2.VideoCapture(device, camera_api_preference)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            available_cameras.append(index)
                            print(f"通过设备文件发现可用摄像头: {device} (索引 {index})")
                        else:
                            print(f"设备 {device} 无法读取帧")
                        cap.release()
                    else:
                        print(f"无法打开设备 {device}")
                except Exception as e:
                    print(f"尝试设备 {device} 时出错: {e}")
        except Exception as e:
            print(f"通过设备文件查找摄像头失败: {e}")

        # 方法3：尝试特定索引（如WebPostureMonitor使用的索引6）
        special_indices = [6, 1, 4]  # 根据观察特别尝试这些索引
        for idx in special_indices:
            if idx in available_cameras:
                continue
                
            try:
                print(f"尝试特殊索引 {idx}...")
                cap = cv2.VideoCapture(idx, camera_api_preference)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        available_cameras.append(idx)
                        print(f"发现特殊索引摄像头: {idx}")
                    cap.release()
            except Exception:
                pass

        print(f"找到可用摄像头: {available_cameras}")
        return available_cameras

    def initialize(self):
        """初始化检测器资源：摄像头和线程池"""
        try:
            print(f"正在初始化检测器，摄像头ID: {self.camera_id}")
            # 初始化模型池
            self.pool = rknnPoolExecutor(
                model_path=self.model_path,
                TPEs=self.TPEs,
                func=thread_safe_predict
            )
            
            # 尝试打开摄像头
            success = False
            tried_camera_ids = []
            camera_api_preference = cv2.CAP_V4L2  # Linux上使用V4L2后端
            
            # 先获取所有可用的摄像头
            available_cameras = self._find_available_cameras()
            
            # 尝试1：如果用户明确指定了摄像头ID，先尝试这个ID
            if self.camera_id is not None:
                try:
                    print(f"尝试打开用户指定的摄像头 ID: {self.camera_id}...")
                    
                    # 使用V4L2后端打开摄像头
                    self.cap = cv2.VideoCapture(self.camera_id, camera_api_preference)
                    if self.cap.isOpened():
                        ret, test_frame = self.cap.read()
                        if ret and test_frame is not None:
                            success = True
                            print(f"成功打开摄像头 ID: {self.camera_id}")
                        else:
                            print(f"摄像头 ID {self.camera_id} 无法读取帧")
                            self.cap.release()
                    else:
                        print(f"摄像头 ID {self.camera_id} 无法打开")
                except Exception as e:
                    print(f"打开指定摄像头 {self.camera_id} 失败: {e}")
                    if self.cap:
                        self.cap.release()
                
                tried_camera_ids.append(self.camera_id)
            
            # 尝试2: 如果有前面发现的可用摄像头，尝试这些摄像头
            if not success and available_cameras:
                # 过滤掉已经尝试过的ID
                available_cameras = [cam for cam in available_cameras if cam not in tried_camera_ids]
                
                if available_cameras:
                    print(f"尝试使用发现的可用摄像头: {available_cameras}")
                    for camera_id in available_cameras:
                        try:
                            print(f"尝试打开备选摄像头 ID: {camera_id}...")
                            self.cap = cv2.VideoCapture(camera_id, camera_api_preference)
                            if self.cap.isOpened():
                                ret, test_frame = self.cap.read()
                                if ret and test_frame is not None:
                                    self.camera_id = camera_id  # 更新为实际使用的摄像头ID
                                    success = True
                                    print(f"成功打开备选摄像头 ID: {camera_id}")
                                    break
                                else:
                                    print(f"备选摄像头 ID {camera_id} 无法读取帧")
                                    self.cap.release()
                            else:
                                print(f"备选摄像头 ID {camera_id} 无法打开")
                        except Exception as e:
                            print(f"尝试摄像头 {camera_id} 时出错: {e}")
                            if self.cap:
                                self.cap.release()
                        tried_camera_ids.append(camera_id)
            
            # 尝试3：直接使用设备路径打开摄像头
            if not success:
                device_paths = ['/dev/video0', '/dev/video1', '/dev/video2', '/dev/video4', '/dev/video6']
                print(f"尝试使用设备路径方式打开摄像头: {device_paths}")
                for dev_path in device_paths:
                    try:
                        print(f"尝试使用设备路径 {dev_path} 访问摄像头...")
                        self.cap = cv2.VideoCapture(dev_path, camera_api_preference)
                        if self.cap.isOpened():
                            ret, test_frame = self.cap.read()
                            if ret and test_frame is not None:
                                # 获取此设备对应的索引，用于后续配置
                                try:
                                    index = int(dev_path.replace('/dev/video', ''))
                                    self.camera_id = index
                                except:
                                    self.camera_id = dev_path
                                    
                                print(f"通过设备路径 {dev_path} 找到可用摄像头, 对应ID: {self.camera_id}")
                                success = True
                                break
                            else:
                                print(f"设备路径 {dev_path} 无法读取帧")
                                self.cap.release()
                        else:
                            print(f"设备路径 {dev_path} 无法打开")
                    except Exception as e:
                        print(f"尝试设备路径 {dev_path} 失败: {e}")
                        if self.cap:
                            self.cap.release()
                    tried_camera_ids.append(dev_path)
                    
            # 尝试4: 如果仍未成功，尝试一些常见的摄像头ID和不同的参数设置
            if not success:
                priority_camera_ids = [1, 4, 0, 2, 5, 6, 3]  # 优先尝试索引 1 和 4，因为已知它们可能可用
                # 过滤掉已尝试过的ID
                priority_camera_ids = [cam for cam in priority_camera_ids if cam not in tried_camera_ids]
                
                if priority_camera_ids:
                    print(f"尝试常见摄像头ID（优先顺序）: {priority_camera_ids}")
                    for camera_id in priority_camera_ids:
                        for api in [camera_api_preference, cv2.CAP_ANY]:  # 尝试两种不同的API
                            try:
                                print(f"尝试打开摄像头 ID: {camera_id} 使用API: {api}...")
                                self.cap = cv2.VideoCapture(camera_id, api)
                                if self.cap.isOpened():
                                    ret, test_frame = self.cap.read()
                                    if ret and test_frame is not None:
                                        self.camera_id = camera_id  # 更新为实际使用的摄像头ID
                                        success = True
                                        print(f"成功打开摄像头 ID: {camera_id} 使用API: {api}")
                                        break
                                    else:
                                        print(f"摄像头 ID {camera_id} 使用API {api} 无法读取帧")
                                        self.cap.release()
                                else:
                                    print(f"摄像头 ID {camera_id} 使用API {api} 无法打开")
                            except Exception as e:
                                print(f"尝试摄像头 {camera_id} 使用API {api} 失败: {e}")
                                if self.cap:
                                    self.cap.release()
                        
                        if success:
                            break
                        tried_camera_ids.append(camera_id)
                        
            if not success:
                raise IOError(f"无法找到可用的摄像头，尝试过的ID: {tried_camera_ids}")
            
            # 优化摄像头设置
            print("开始优化摄像头设置...")
            self._optimize_camera_settings()
            
            # 测试摄像头实际帧率
            measured_fps = self._test_camera_fps(self.cap, frames=15)
            print(f"测量的实际摄像头帧率: {measured_fps:.1f} FPS")
            
            print("摄像头打开并优化成功，开始初始化推理管线...")
            
            # 初始化异步所需要的帧
            for i in range(self.TPEs + 1):
                ret, frame = self.cap.read()
                if not ret:
                    raise IOError("无法读取摄像头帧")
                self.pool.put(frame)
                
            # 重置所有状态参数
            self._last_frame_time = time.time()
            self._frame_count = 0
            self.fps = 0.0
            self.frames = 0
            self.detected = False
            self.position = [0.0, 0.0]
            self.width = 0.0
            self.height = 0.0
            self.confidence = 0.0
            self.running = False  # 初始化时不要设置为True，由start方法来设置
            print(f"检测器初始化完成，使用摄像头ID: {self.camera_id}")
            return True

        except Exception as e:
            print(f"初始化检测器失败: {str(e)}")
            self.cleanup()
            return False

    def process_frame(self):
        """处理帧数据"""
        if not self.cap or not self.cap.isOpened() or not self.running:
            return False
        
        try:
            # 读取新帧
            ret, frame = self.cap.read()
            if not ret:
                print("读取帧失败")
                return False
            
            # 更新帧计数
            self.frames += 1
            
            # 将帧提交到处理池并获取上一帧的结果
            inference_start = time.time()
            self.pool.put(frame)
            results, success = self.pool.get()
            if not success:
                return False
            
            # 检查推理时间
            inference_time = time.time() - inference_start
            # 移除推理时间警告，因为在一些设备上推理本来就需要较长时间
            
            # 更新检测结果
            self.detected = False
            
            # 处理检测结果
            for result in results:
                boxes = result.boxes
                if len(boxes) > 0:
                    # 找出置信度最高的框
                    box_best = max(boxes, key=lambda box: box.conf[0].cpu().numpy())
                    # 获取归一化的坐标 (使用xywhn，更符合camera.py中的逻辑)
                    pos_x, pos_y, width, height = box_best.xywhn[0].cpu().numpy()
                    
                    # 将坐标转换为[-0.5, 0.5]范围(与camera.py一致)，并确保转换为Python内置float类型
                    self.position[0] = float(pos_x - 0.5)
                    self.position[1] = float(pos_y - 0.5)
                    self.width = float(width)
                    self.height = float(height)
                    self.confidence = float(box_best.conf[0].cpu().numpy())
                    self.detected = True
                    
                    if self.show_img:
                        # 绘制框
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                            confidence = float(box.conf[0].cpu().numpy())
                            class_id = int(box.cls[0].cpu().numpy())
                            class_name = "target"  # 默认目标名称
                            
                            # 只绘制最好的框（也可以绘制所有框）
                            if box is box_best:
                                label = f"{class_name} {confidence:.2f}"
                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                cv2.putText(
                                    frame,
                                    label,
                                    (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.9,
                                    (0, 255, 0),
                                    2,
                                )
                else:
                    # 没有检测到物体，确保使用Python内置类型
                    self.position = [0.0, 0.0]  # Python内置float
                    self.width = 0.0
                    self.height = 0.0
                    self.confidence = 0.0
                    self.detected = False

            # 显示图像（如果需要）
            if self.show_img:
                try:
                    # 显示帧率
                    cv2.putText(
                        frame,
                        f"FPS: {int(self.fps)}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2,
                        cv2.LINE_AA,
                    )
                    cv2.imshow('Detection', frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        self.running = False
                        return False
                except Exception as e:
                    if not hasattr(self, '_display_error_shown'):
                        print(f"显示图像时出错: {e}")
                        print("警告: 已禁用图像显示功能")
                        self._display_error_shown = True
                        self.show_img = False  # 自动关闭图像显示                # 更新FPS计算 - 每30帧计算一次
            if self.frames % 30 == 0:
                current_time = time.time()
                elapsed = current_time - self._last_frame_time
                if elapsed > 0:  # 确保不会除以零
                    self.fps = 30 / elapsed
                    if self.fps < 5:  # 只在帧率极低时输出警告（低于5FPS）
                        print(f"帧率低: {self.fps:.1f} FPS")
                self._last_frame_time = current_time
                
            return True

        except Exception as e:
            print(f"处理帧时出错: {str(e)}")
            return False

    def _detection_loop(self):
        """检测主循环，在单独线程中运行"""

    def start(self):
        """启动检测循环"""
        if self.running:
            print("检测器已在运行中")
            return False
            
        # 如果没有初始化，先初始化
        if not self.cap or not self.pool:
            if not self.initialize():
                print("初始化检测器失败，无法启动")
                return False
            
        self.running = True
        print("启动检测线程")
        self.detection_thread = Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
        return True

    def _detection_loop(self):
        """检测主循环，在单独线程中运行"""
        print("检测循环开始运行")
        loopTime = time.time()
        initTime = time.time()
        frames_processed = 0
        
        while self.running and self.cap and self.cap.isOpened():
            if not self.process_frame():
                print("处理帧失败，检测循环中断")
                break
                
            frames_processed += 1
                
        # 计算总平均帧率
        elapsed = time.time() - initTime
        if elapsed > 0 and frames_processed > 0:
            avg_fps = frames_processed / elapsed
            print(f"检测循环结束，处理了 {frames_processed} 帧，平均帧率: {avg_fps:.2f} FPS")
        else:
            print("检测循环结束，未处理任何帧")

    def stop(self):
        """停止检测循环"""
        if not self.running:
            print("检测器已经停止")
            return True
            
        print("正在停止检测器...")
        self.running = False
        
        # 等待线程结束
        if hasattr(self, 'detection_thread') and self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=2.0)
            if self.detection_thread.is_alive():
                print("警告: 检测线程未能在超时时间内终止")
                
        self.cleanup()
        print("检测器已停止")
        return True
        
    def cleanup(self):
        """清理资源"""
        self.running = False
        
        # 释放摄像头
        if hasattr(self, 'cap') and self.cap is not None:
            try:
                self.cap.release()
            except Exception as e:
                print(f"释放摄像头时出错: {e}")
            finally:
                self.cap = None
            
        # 释放窗口
        if hasattr(self, 'show_img') and self.show_img:
            try:
                cv2.destroyAllWindows()
            except Exception as e:
                print(f"释放窗口时出错: {e}")
            
        # 释放线程池
        if hasattr(self, 'pool') and self.pool is not None:
            try:
                del self.pool
            except Exception as e:
                print(f"释放线程池时出错: {e}")
            finally:
                self.pool = None
            
        print("已清理检测器资源")

    def get_position(self):
        """获取当前检测到的目标位置信息"""
        # 增加FPS信息并确保所有值都是Python内置类型
        return {
            "detected": bool(self.detected),
            "x": float(self.position[0]),
            "y": float(self.position[1]),
            "w": float(self.width),
            "h": float(self.height),
            "confidence": float(self.confidence),
            "fps": float(self.fps)  # 添加fps信息
        }
    
    def _test_camera_fps(self, cap, frames=10):
        """测试摄像头实际帧率
        
        Args:
            cap: 摄像头对象
            frames: 测试帧数
            
        Returns:
            float: 测量的帧率
        """
        if not cap or not cap.isOpened():
            return 0
            
        # 丢弃前几帧以稳定摄像头
        for _ in range(3):
            cap.grab()
            
        # 测量获取指定数量帧所需的时间
        start_time = time.time()
        frames_read = 0
        
        for _ in range(frames):
            ret, _ = cap.read()
            if ret:
                frames_read += 1
        
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        if elapsed_time > 0 and frames_read > 0:
            fps = frames_read / elapsed_time
            print(f"测量的实际摄像头帧率: {fps:.1f} FPS")
            return fps
        else:
            return 0

    def _optimize_camera_settings(self):
        """优化摄像头设置以提高性能"""
        if not self.cap or not self.cap.isOpened():
            return False
            
        try:
            # 设置缓冲区大小为1，减少延迟
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # 设置目标FPS为30
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # 尝试不同的编码格式，优先使用MJPG（通常性能更好）
            fourcc_options = ['MJPG', 'YUYV', 'RGB3']
            best_format = None
            best_fps = 0
            
            for fourcc_code in fourcc_options:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*fourcc_code)
                    self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
                    # 读取一帧测试格式是否生效
                    ret, test = self.cap.read()
                    if ret:
                        # 测试这个格式下的帧率
                        test_fps = self._test_camera_fps(self.cap, frames=5)
                        print(f"{fourcc_code} 格式下测得帧率: {test_fps:.1f} FPS")
                        
                        if test_fps > best_fps:
                            best_fps = test_fps
                            best_format = fourcc_code
                except Exception as e:
                    print(f"设置 {fourcc_code} 格式失败: {e}")
            
            # 设置找到的最佳格式
            if best_format:
                print(f"选择最佳格式: {best_format} 帧率: {best_fps:.1f} FPS")
                fourcc = cv2.VideoWriter_fourcc(*best_format)
                self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
            
            # 尝试不同的分辨率
            resolutions_to_try = [(640, 480), (800, 600), (1280, 720)]
            for width, height in resolutions_to_try:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                
                # 验证设置是否生效
                actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                print(f"尝试设置分辨率 {width}x{height}, 实际: {actual_width}x{actual_height}")
                
                # 测试当前分辨率下的帧率，如果帧率足够高就保留这个分辨率
                if abs(actual_width - width) < 30 and abs(actual_height - height) < 30:
                    fps = self._test_camera_fps(self.cap, frames=5)
                    if fps >= 15:  # 如果帧率超过15fps就可以使用这个分辨率
                        print(f"选择分辨率 {width}x{height} 帧率足够")
                        break
            
            # 打印最终的摄像头配置
            final_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            final_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            final_fps = self.cap.get(cv2.CAP_PROP_FPS)
            final_format = int(self.cap.get(cv2.CAP_PROP_FOURCC))
            
            try:
                format_chars = "".join([chr((int(final_format) >> (8 * i)) & 0xFF) for i in range(4)])
                print(f"摄像头最终配置: {final_width}x{final_height}@{final_fps}fps, 格式: {format_chars}")
            except:
                print(f"摄像头最终配置: {final_width}x{final_height}@{final_fps}fps")
                
            return True
        except Exception as e:
            print(f"优化摄像头设置失败: {e}")
            return False

    def __del__(self):
        """析构函数，确保资源被释放"""
        self.cleanup()


def main():
    """测试检测器的主函数"""
    # 1. 创建Detector实例
    detector = Detector(
        TPEs=4,
        model_path="Yolo/best6_rknn_model",
        camera_id=1,
        show_img=True  # 设置为True可以看到检测效果
    )
    
    # 2. 初始化检测器
    if not detector.initialize():
        print("初始化失败")
        return
    
    # 3. 启动检测循环
    detector.start()
    
    try:
        # 4. 使用检测结果
        for _ in range(100):  # 循环100次
            # 获取当前检测到的目标位置信息
            position_info = detector.get_position()
            
            # 输出检测结果
            if position_info["detected"]:
                print(f"检测到目标: 位置 x={position_info['x']:.3f}, y={position_info['y']:.3f}, " +
                      f"置信度={position_info['confidence']:.2f}, FPS={position_info['fps']:.1f}")
            else:
                print(f"未检测到目标, FPS={position_info['fps']:.1f}")
                
            # 每隔0.1秒获取一次检测结果
            time.sleep(0.1)
            
            # 检查是否还在运行
            if not detector.running:
                print("检测器已停止运行")
                break
    except KeyboardInterrupt:
        print("用户中断程序")
    finally:
        # 5. 停止检测并释放资源
        detector.stop()
    

if __name__ == "__main__":
    # 运行主函数
    main()
