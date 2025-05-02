"""
姿势分析模块 - 提供姿势和表情分析功能
"""
import os
import sys
import cv2
import time
import threading
import queue
from collections import deque
from config import DB_CONFIG

# 尝试导入posture_analysis模块
try:
    # 确保能找到posture_analysis包
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.dirname(parent_dir))
    
    from posture_analysis.realtime_posture_analysis import (
        PostureMonitor, EmotionAnalyzer, EmotionState,
        EMOTION_SMOOTHING_WINDOW, MOUTH_OPEN_RATIO_THRESHOLD,
        EYE_OPEN_RATIO_THRESHOLD, BROW_DOWN_THRESHOLD,
        CAMERA_WIDTH, CAMERA_HEIGHT, PROCESS_WIDTH, PROCESS_HEIGHT,
        mp_pose, mp_face_mesh, check_occlusion, calculate_head_angle, 
        mp_drawing, mp_drawing_styles, VISIBILITY_THRESHOLD, HEAD_ANGLE_THRESHOLD,
        OCCLUSION_FRAMES_THRESHOLD, CLEAR_FRAMES_THRESHOLD
    )
    POSTURE_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"导入姿势分析模块失败：{str(e)}")
    POSTURE_MODULE_AVAILABLE = False
    
    # 定义占位符常量和类，避免程序崩溃
    class EmotionState:
        NEUTRAL = 0
        HAPPY = 1
        ANGRY = 3
        SAD = 4
    
    EMOTION_SMOOTHING_WINDOW = 7
    MOUTH_OPEN_RATIO_THRESHOLD = 0.45
    EYE_OPEN_RATIO_THRESHOLD = 0.25
    BROW_DOWN_THRESHOLD = 0.04
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    PROCESS_WIDTH = 320
    PROCESS_HEIGHT = 240
    OCCLUSION_FRAMES_THRESHOLD = 10
    CLEAR_FRAMES_THRESHOLD = 5
    HEAD_ANGLE_THRESHOLD = 45

# 全局参数设置
posture_params = {
    'emotion_smoothing_window': EMOTION_SMOOTHING_WINDOW,
    'mouth_open_ratio_threshold': MOUTH_OPEN_RATIO_THRESHOLD,
    'eye_open_ratio_threshold': EYE_OPEN_RATIO_THRESHOLD,
    'brow_down_threshold': BROW_DOWN_THRESHOLD
}

# 分辨率和性能相关参数
DEFAULT_PROCESS_WIDTH = PROCESS_WIDTH
DEFAULT_PROCESS_HEIGHT = PROCESS_HEIGHT
RESOLUTION_LEVELS = [
    (640, 480),   # 高分辨率
    (480, 360),   # 中分辨率
    (320, 240),   # 低分辨率
    (240, 180)    # 极低分辨率
]
TARGET_FPS = 25.0  # 目标帧率
FPS_THRESHOLD_LOW = 15.0  # 低帧率阈值，低于此值降低分辨率
FPS_THRESHOLD_HIGH = 28.0  # 高帧率阈值，高于此值可以尝试提高分辨率
RESOLUTION_ADJUST_INTERVAL = 5.0  # 分辨率调整间隔（秒）

# 帧率计算类
class FPSCounter:
    """计算并跟踪帧率"""
    def __init__(self, window_size=30):
        """初始化帧率计数器
        
        Args:
            window_size: 计算平均帧率的时间窗口大小（帧数）
        """
        self.window_size = window_size
        self.timestamps = deque(maxlen=window_size)
        self.last_fps = 0
        self.total_frames = 0
    
    def update(self):
        """记录一帧的时间戳并更新帧率"""
        self.timestamps.append(time.time())
        self.total_frames += 1
        
        # 至少需要2个时间戳才能计算帧率
        if len(self.timestamps) >= 2:
            # 计算时间差（秒）
            time_diff = self.timestamps[-1] - self.timestamps[0]
            if time_diff > 0:
                # 计算当前窗口内的平均帧率
                self.last_fps = (len(self.timestamps) - 1) / time_diff
            else:
                self.last_fps = 0
        
        return self.last_fps
    
    def get_fps(self):
        """获取当前帧率"""
        return self.last_fps
    
    def get_total_frames(self):
        """获取总帧数"""
        return self.total_frames

class WebPostureMonitor:
    """适配Web服务的姿势监测器"""
    def __init__(self, video_stream_handler=None):
        self.cap = None
        self.pose = None
        self.emotion_analyzer = None
        self.is_running = False
        self.thread = None
        self.video_stream_handler = video_stream_handler
        
        # 初始化处理分辨率
        self.process_width = DEFAULT_PROCESS_WIDTH
        self.process_height = DEFAULT_PROCESS_HEIGHT
        self.current_resolution_index = 1  # 从中等分辨率开始
        self.last_resolution_adjust_time = 0
        self.adaptive_resolution = True  # 是否启用自适应分辨率
        
        # 初始化摄像头参数
        self.camera_fps = 30  # 尝试设置摄像头的FPS
        self.camera_buffer_size = 1  # 摄像头缓冲区大小，小值减少延迟
        
        # 初始化帧率计数器
        self.capture_fps = FPSCounter()  # 摄像头捕获帧率
        self.pose_process_fps = FPSCounter()  # 姿势处理帧率
        self.emotion_process_fps = FPSCounter()  # 情绪处理帧率
        
        # 存储最新分析结果
        self.pose_result = {
            'angle': 0,
            'is_bad_posture': False,
            'is_occluded': False,
            'status': 'Initialized'
        }
        self.emotion_result = {
            'emotion': 'NEUTRAL',
            'emotion_code': 0
        }
        
        # 帧率信息
        self.fps_info = {
            'capture_fps': 0,
            'pose_process_fps': 0,
            'emotion_process_fps': 0
        }
        
        # 初始化遮挡计数器
        self.occlusion_counter = 0
        self.clear_counter = 0
        self.last_valid_angle = None
    
    def start(self):
        """启动姿势分析线程"""
        if self.is_running:
            print("分析系统已经在运行中")
            return True
            
        self.is_running = True
        success = self._init_camera()
        
        if not success or not self.cap or not self.cap.isOpened():
            self.is_running = False
            print("无法初始化摄像头，姿势分析系统启动失败")
            return False
            
        if POSTURE_MODULE_AVAILABLE:
            try:
                print("正在初始化姿势分析和情绪分析组件...")
                
                # 使用正确的MediaPipe姿势检测
                self.pose = mp_pose.Pose(
                    static_image_mode=False,    # 视频流模式
                    model_complexity=1,         # 模型复杂度（0-2）降低以提高性能
                    min_detection_confidence=0.6, # 降低到0.6以提高检测率
                    min_tracking_confidence=0.5
                )
                
                # 创建情绪分析器实例
                self.emotion_analyzer = EmotionAnalyzer()
                
                # 启动处理线程
                self.thread = threading.Thread(target=self._process_frames)
                self.thread.daemon = True
                self.thread.start()
                
                print("姿势分析系统启动成功")
                return True
            except Exception as e:
                self.is_running = False
                print(f"启动姿势分析系统失败，错误详情: {e}")
                import traceback
                traceback.print_exc()  # 打印详细错误堆栈
                return False
        else:
            self.is_running = False
            print("姿势分析模块不可用，请检查posture_analysis包是否正确安装")
            return False
    
    def stop(self):
        """停止姿势分析线程"""
        self.is_running = False
        
        if self.thread:
            try:
                self.thread.join(timeout=2.0)
            except Exception:
                pass
            self.thread = None
            
        if self.cap:
            self.cap.release()
            self.cap = None
            
        print("姿势分析系统已停止")
        return True
    
    def _init_camera(self):
        """初始化摄像头设备"""
        try:
            # 先使用_find_available_cameras找到所有可用的摄像头
            available_cameras = self._find_available_cameras()
            camera_found = False
            
            if available_cameras:
                # 首先尝试available_cameras中的相机
                for camera_index in available_cameras:
                    try:
                        print(f"尝试初始化摄像头索引 {camera_index}...")
                        self.cap = cv2.VideoCapture(camera_index)
                        if self.cap.isOpened():
                            # 读取一帧验证相机是否真正可用
                            ret, test_frame = self.cap.read()
                            if ret and test_frame is not None:
                                print(f"找到可用摄像头：索引 {camera_index}")
                                camera_found = True
                                break
                            else:
                                print(f"摄像头索引 {camera_index} 无法读取帧")
                                self.cap.release()
                    except Exception as e:
                        print(f"尝试摄像头索引 {camera_index} 失败: {e}")
                        if self.cap:
                            self.cap.release()
            
            # 如果上面的方法没找到摄像头，尝试直接使用索引6（对应Bus 006）
            if not camera_found:
                try:
                    print("尝试直接访问Bus 006上的摄像头 (索引6)...")
                    # 使用V4L2后端，这在Linux上对USB摄像头效果更好
                    self.cap = cv2.VideoCapture(6, cv2.CAP_V4L2)
                    if self.cap.isOpened():
                        ret, test_frame = self.cap.read()
                        if ret and test_frame is not None:
                            print("成功连接到索引6的摄像头")
                            camera_found = True
                    else:
                        print("无法打开索引6的摄像头")
                except Exception as e:
                    print(f"尝试访问索引6摄像头失败: {e}")
            
            # 继续尝试更多相机索引
            if not camera_found:
                for camera_index in range(10):
                    if camera_index in available_cameras:
                        continue  # 已经尝试过
                    try:
                        print(f"尝试初始化扩展搜索摄像头索引 {camera_index}...")
                        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
                        if self.cap.isOpened():
                            ret, test_frame = self.cap.read()
                            if ret and test_frame is not None:
                                print(f"扩展搜索找到可用摄像头：索引 {camera_index}")
                                camera_found = True
                                break
                            else:
                                self.cap.release()
                    except Exception as e:
                        print(f"扩展搜索摄像头索引 {camera_index} 失败: {e}")
                        if self.cap:
                            self.cap.release()
            
            # 最后尝试直接设备路径
            if not camera_found:
                for dev_path in ["/dev/video0", "/dev/video1", "/dev/video2", "/dev/video6"]:
                    try:
                        print(f"尝试使用设备路径 {dev_path} 访问摄像头...")
                        self.cap = cv2.VideoCapture(dev_path, cv2.CAP_V4L2)
                        if self.cap.isOpened():
                            ret, test_frame = self.cap.read()
                            if ret and test_frame is not None:
                                print(f"通过设备路径 {dev_path} 找到可用摄像头")
                                camera_found = True
                                break
                            else:
                                self.cap.release()
                    except Exception as e:
                        print(f"尝试设备路径 {dev_path} 失败: {e}")
                        if self.cap:
                            self.cap.release()
            
            if not camera_found or not self.cap or not self.cap.isOpened():
                print("未找到可用摄像头")
                return False
                
            # 获取摄像头原始属性
            original_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            original_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            original_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            print(f"摄像头原始属性: {original_width}x{original_height}@{original_fps}fps")
            
            # 专门针对Microdia USB 2.0相机(0c45:636b)的配置
            try:
                print("检测到Microdia USB 2.0相机，应用专用配置...")
                
                # Microdia相机通常支持这些分辨率
                microdia_resolutions = [(640, 480), (352, 288), (320, 240)]
                resolution_set = False
                
                for width, height in microdia_resolutions:
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                    
                    # 确认是否设置成功
                    actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    
                    if abs(actual_width - width) < 30 and abs(actual_height - height) < 30:
                        print(f"成功设置Microdia相机分辨率: {width}x{height}")
                        resolution_set = True
                        break
                
                # 尝试设置其他参数
                self.cap.set(cv2.CAP_PROP_FPS, 15)  # 降低帧率以提高稳定性
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 最小缓冲区减少延迟
                
                # 尝试不同的格式
                for fourcc_code in ['MJPG', 'YUYV', 'RGB3']:
                    try:
                        fourcc = cv2.VideoWriter_fourcc(*fourcc_code)
                        self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
                        # 读取一帧测试格式是否生效
                        ret, test = self.cap.read()
                        if ret:
                            print(f"成功应用{fourcc_code}格式")
                            break
                    except Exception as e:
                        print(f"设置{fourcc_code}格式失败: {e}")
                
                # 验证最终配置
                ret, test_frame = self.cap.read()
                if ret and test_frame is not None:
                    actual_width = test_frame.shape[1]
                    actual_height = test_frame.shape[0]
                    print(f"Microdia相机配置验证成功，实际帧大小: {actual_width}x{actual_height}")
                else:
                    print("警告: Microdia相机配置后无法读取帧，将尝试使用默认配置")
                    # 重新打开摄像头使用默认配置
                    self.cap.release()
                    self.cap = cv2.VideoCapture(6, cv2.CAP_V4L2)
            except Exception as e:
                print(f"应用Microdia相机专用配置失败(非致命错误): {e}")
            
            # 验证摄像头是否能够正常读取帧
            ret, test_frame = self.cap.read()
            if not ret or test_frame is None:
                print("摄像头无法读取帧，初始化失败")
                if self.cap:
                    self.cap.release()
                    self.cap = None
                return False
                
            # 获取实际的摄像头属性
            actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            actual_format = int(self.cap.get(cv2.CAP_PROP_FOURCC))
            
            # 将4字节格式代码转换为可读字符串
            try:
                format_chars = "".join([chr((int(actual_format) >> (8 * i)) & 0xFF) for i in range(4)])
                print(f"摄像头最终配置: {actual_width}x{actual_height}@{actual_fps}fps, 格式: {format_chars}")
            except:
                print(f"摄像头最终配置: {actual_width}x{actual_height}@{actual_fps}fps")
            
            # 重置帧率计数器
            self.capture_fps = FPSCounter()
            self.pose_process_fps = FPSCounter()
            self.emotion_process_fps = FPSCounter()
            
            # 初始化遮挡计数器（之前代码中缺少这些初始化）
            self.occlusion_counter = 0
            self.clear_counter = 0
            self.last_valid_angle = None
            
            return True
        except Exception as e:
            print(f"初始化摄像头失败: {e}")
            if self.cap:
                self.cap.release()
                self.cap = None
            return False
    
    def _test_camera_fps(self, cap, frames=20):
        """测试摄像头的实际FPS"""
        if not cap or not cap.isOpened():
            return 0
            
        # 丢弃前几帧以稳定摄像头
        for _ in range(5):
            cap.grab()
            
        # 测量获取指定数量帧所需的时间
        start_time = time.time()
        for _ in range(frames):
            cap.grab()
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        if elapsed_time > 0:
            return frames / elapsed_time
        else:
            return 0
    
    def _adjust_processing_resolution(self):
        """根据当前帧率动态调整处理分辨率"""
        current_time = time.time()
        
        # 检查是否到达调整间隔
        if not self.adaptive_resolution or (current_time - self.last_resolution_adjust_time) < RESOLUTION_ADJUST_INTERVAL:
            return
            
        capture_fps = self.capture_fps.get_fps()
        process_fps = min(self.pose_process_fps.get_fps(), self.emotion_process_fps.get_fps())
        
        # 当帧率过低时降低分辨率
        if process_fps < FPS_THRESHOLD_LOW and self.current_resolution_index < len(RESOLUTION_LEVELS) - 1:
            self.current_resolution_index += 1
            self.process_width, self.process_height = RESOLUTION_LEVELS[self.current_resolution_index]
            print(f"帧率过低 ({process_fps:.1f} FPS)，降低处理分辨率至 {self.process_width}x{self.process_height}")
            self.last_resolution_adjust_time = current_time
        
        # 当帧率足够高时提高分辨率
        elif process_fps > FPS_THRESHOLD_HIGH and self.current_resolution_index > 0:
            self.current_resolution_index -= 1
            self.process_width, self.process_height = RESOLUTION_LEVELS[self.current_resolution_index]
            print(f"帧率足够高 ({process_fps:.1f} FPS)，提高处理分辨率至 {self.process_width}x{self.process_height}")
            self.last_resolution_adjust_time = current_time
    
    def _process_frames(self):
        """处理视频帧的主循环"""
        if not POSTURE_MODULE_AVAILABLE:
            return
        
        last_fps_update_time = time.time()
        consecutive_read_failures = 0
        
        while self.is_running and self.cap and self.cap.isOpened():
            try:
                # 读取帧，使用grabbing和retrieving分离方式提高效率
                grabbed = self.cap.grab()
                if not grabbed:
                    consecutive_read_failures += 1
                    if consecutive_read_failures > 5:
                        print("连续多次无法获取摄像头帧，尝试重新初始化摄像头...")
                        self._init_camera()
                        consecutive_read_failures = 0
                    time.sleep(0.01)
                    continue
                
                consecutive_read_failures = 0
                ret, frame = self.cap.retrieve()
                if not ret:
                    print("无法读取摄像头帧")
                    time.sleep(0.01)
                    continue
                
                # 更新捕获帧率
                self.capture_fps.update()
                
                # 每隔一段时间检查并调整处理分辨率
                self._adjust_processing_resolution()
                
                # 调整帧尺寸进行处理
                processed_frame = cv2.resize(frame, (self.process_width, self.process_height))
                pose_frame = processed_frame.copy()
                emotion_frame = processed_frame.copy()
                
                # 处理姿势
                pose_start_time = time.time()
                pose_results = self._process_pose(pose_frame)
                self.pose_process_fps.update()  # 更新姿势处理帧率
                
                # 处理情绪
                emotion_start_time = time.time()
                emotion_results = self._process_emotion(emotion_frame)
                self.emotion_process_fps.update()  # 更新情绪处理帧率
                
                # 调整输出视频尺寸，确保与当前处理分辨率匹配
                if self.video_stream_handler:
                    # 将处理后的帧放入队列供Web端点使用
                    self.video_stream_handler.add_pose_frame(pose_results['display_frame'])
                    self.video_stream_handler.add_emotion_frame(emotion_results['display_frame'])
                
                # 更新结果状态
                self.pose_result = {
                    'angle': pose_results['angle'] if pose_results['angle'] is not None else 0,
                    'is_bad_posture': pose_results['is_bad_posture'],
                    'is_occluded': pose_results['is_occluded'],
                    'status': pose_results['status']
                }
                
                self.emotion_result = {
                    'emotion': emotion_results['emotion'].name if emotion_results['emotion'] else 'UNKNOWN',
                    'emotion_code': emotion_results['emotion'].value if emotion_results['emotion'] else -1
                }
                
                # 每秒更新一次帧率信息
                current_time = time.time()
                if current_time - last_fps_update_time >= 1.0:
                    self.fps_info = {
                        'capture_fps': round(self.capture_fps.get_fps(), 1),
                        'pose_process_fps': round(self.pose_process_fps.get_fps(), 1),
                        'emotion_process_fps': round(self.emotion_process_fps.get_fps(), 1)
                    }
                    last_fps_update_time = current_time
                
                # 根据实际帧率动态调整延迟时间
                current_fps = min(self.pose_process_fps.get_fps(), self.emotion_process_fps.get_fps())
                if current_fps > TARGET_FPS:
                    # 如果帧率过高，增加一点延迟以减少CPU使用
                    time.sleep(0.001)
                else:
                    # 帧率正常或过低，尽可能快地处理
                    time.sleep(0.0001)
            except Exception as e:
                print(f"处理帧异常: {str(e)}")
                time.sleep(0.1)
    
    def _process_pose(self, frame):
        """处理姿势检测"""
        if not POSTURE_MODULE_AVAILABLE:
            return {
                'display_frame': frame,
                'angle': None,
                'is_bad_posture': False,
                'is_occluded': True,
                'status': 'Module Not Available'
            }
        
        results = {
            'display_frame': frame,
            'angle': None,
            'is_bad_posture': False,
            'is_occluded': True,
            'status': 'No Detection'
        }
        
        try:
            # 姿势检测
            pose_results = self.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if not pose_results.pose_landmarks:
                return results
            
            # 遮挡检测
            is_occluded, occlusion_status = check_occlusion(pose_results.pose_landmarks.landmark)
            self._update_occlusion_counters(is_occluded)
            final_occlusion = self.occlusion_counter >= OCCLUSION_FRAMES_THRESHOLD
            valid_detection = self.clear_counter >= CLEAR_FRAMES_THRESHOLD
            
            # 头部角度计算
            angle_info = calculate_head_angle(pose_results.pose_landmarks.landmark, frame.shape)
            angle = None
            is_bad_posture = False
            points = {}
            
            if angle_info[0] is not None:
                angle, is_bad_posture, points = angle_info
                self.last_valid_angle = angle
            
            # 绘制姿势关键点和信息
            display_frame = frame.copy()
            mp_drawing.draw_landmarks(
                display_frame,
                pose_results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
            )
            
            # 绘制状态信息
            state_text = f"State: {'Occluded' if final_occlusion else 'Tracking'}"
            color = (0, 0, 255) if final_occlusion else (0, 255, 0)
            cv2.putText(display_frame, state_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # 绘制角度信息
            if angle is not None and valid_detection and not final_occlusion:
                status_color = (0, 0, 255) if is_bad_posture else (0, 255, 0)
                text = f"Angle: {angle:.1f}° {'[BAD]' if is_bad_posture else '[GOOD]'}"
                cv2.putText(display_frame, text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
                
                if points:
                    cv2.line(display_frame, tuple(points['mid_shoulder']), tuple(points['nose']), (0, 255, 0), 2)
            elif final_occlusion and self.last_valid_angle:
                text = f"Occluded | Last: {self.last_valid_angle:.1f}°"
                cv2.putText(display_frame, text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # 更新结果
            results = {
                'display_frame': display_frame,
                'angle': angle if angle is not None else (self.last_valid_angle if final_occlusion else None),
                'is_bad_posture': is_bad_posture,
                'is_occluded': final_occlusion,
                'status': occlusion_status if final_occlusion else 'Tracking'
            }
            
            return results
        except Exception as e:
            print(f"姿势处理异常: {str(e)}")
            return results
    
    def _process_emotion(self, frame):
        """处理情绪分析"""
        if not POSTURE_MODULE_AVAILABLE:
            return {
                'display_frame': frame,
                'emotion': None,
                'face_landmarks': None
            }
        
        results = {
            'display_frame': frame,
            'emotion': None,
            'face_landmarks': None
        }
        
        try:
            # 更新情绪分析器参数
            self.emotion_analyzer.emotion_smoothing_window = posture_params['emotion_smoothing_window']
            
            # 分析情绪
            emotion_state, face_landmarks, _ = self.emotion_analyzer.analyze(frame)
            
            # 绘制情绪界面
            display_frame = frame.copy()
            if face_landmarks:
                mp_drawing.draw_landmarks(
                    image=display_frame,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_CONTOURS,
                    connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style()
                )
                
                # 显示当前情绪状态
                emotion_text = f"Emotion: {emotion_state.name}"
                cv2.putText(display_frame, emotion_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 250), 2)
            
            results = {
                'display_frame': display_frame,
                'emotion': emotion_state,
                'face_landmarks': face_landmarks
            }
            
            return results
        except Exception as e:
            print(f"情绪处理异常: {str(e)}")
            return results
    
    def _update_occlusion_counters(self, is_occluded):
        """更新遮挡状态计数器"""
        if is_occluded:
            self.occlusion_counter = min(self.occlusion_counter + 1, OCCLUSION_FRAMES_THRESHOLD)
            self.clear_counter = max(0, self.clear_counter - 1)
        else:
            self.clear_counter = min(self.clear_counter + 1, CLEAR_FRAMES_THRESHOLD)
            self.occlusion_counter = max(0, self.occlusion_counter - 1)
    
    def get_emotion_params(self):
        """获取当前情绪分析参数"""
        return {
            'emotion_smoothing_window': posture_params['emotion_smoothing_window'],
            'mouth_open_ratio_threshold': posture_params['mouth_open_ratio_threshold'],
            'eye_open_ratio_threshold': posture_params['eye_open_ratio_threshold'],
            'brow_down_threshold': posture_params['brow_down_threshold']
        }
    
    def update_emotion_params(self, params):
        """更新情绪分析参数"""
        global posture_params
        try:
            if 'emotion_smoothing_window' in params:
                value = int(params['emotion_smoothing_window'])
                if 1 <= value <= 30:
                    posture_params['emotion_smoothing_window'] = value
            
            if 'mouth_open_ratio_threshold' in params:
                value = float(params['mouth_open_ratio_threshold'])
                if 0.1 <= value <= 1.0:
                    posture_params['mouth_open_ratio_threshold'] = value
            
            if 'eye_open_ratio_threshold' in params:
                value = float(params['eye_open_ratio_threshold'])
                if 0.05 <= value <= 0.5:
                    posture_params['eye_open_ratio_threshold'] = value
            
            if 'brow_down_threshold' in params:
                value = float(params['brow_down_threshold'])
                if 0.01 <= value <= 0.2:
                    posture_params['brow_down_threshold'] = value
            
            # 如果分析器已启动，同步更新参数
            if self.is_running and self.emotion_analyzer:
                self.emotion_analyzer.emotion_smoothing_window = posture_params['emotion_smoothing_window']
            
            return True
        except Exception as e:
            print(f"更新情绪参数失败: {str(e)}")
            return False
    
    def get_fps_info(self):
        """获取帧率信息"""
        return self.fps_info
    
    def set_resolution_mode(self, adaptive=True, resolution_index=None):
        """设置分辨率模式
        
        Args:
            adaptive: 是否启用自适应分辨率调整
            resolution_index: 如果不使用自适应模式，设置固定分辨率索引
        """
        self.adaptive_resolution = adaptive
        
        if resolution_index is not None and 0 <= resolution_index < len(RESOLUTION_LEVELS):
            self.current_resolution_index = resolution_index
            self.process_width, self.process_height = RESOLUTION_LEVELS[self.current_resolution_index]
            print(f"手动设置处理分辨率为 {self.process_width}x{self.process_height}")
        
        return True

    def _find_available_cameras(self):
        """查找系统中所有可用的摄像头并返回可用的索引列表"""
        available_cameras = []
        
        # 尝试前10个摄像头索引
        for i in range(10):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        print(f"摄像头索引 {i} 可用，分辨率: {frame.shape[1]}x{frame.shape[0]}")
                        available_cameras.append(i)
                    else:
                        print(f"摄像头索引 {i} 打开成功但无法读取帧")
                cap.release()
            except Exception as e:
                print(f"测试摄像头索引 {i} 失败: {e}")
        
        if available_cameras:
            print(f"找到 {len(available_cameras)} 个可用摄像头: {available_cameras}")
        else:
            print("未找到任何可用摄像头")
        
        return available_cameras