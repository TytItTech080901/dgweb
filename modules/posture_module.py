"""
姿势分析模块 - 提供姿势和表情分析功能
"""
import os
import sys
import cv2
import time
from datetime import datetime
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

# 更新处理分辨率级别，设置320x240为最低分辨率
RESOLUTION_LEVELS = [
    (640, 480),   # 高分辨率
    (480, 360),   # 中分辨率
    (320, 240)    # 最低分辨率 - 不再使用更低的分辨率以保证分析质量
]
TARGET_FPS = 25.0  # 目标帧率
FPS_THRESHOLD_LOW = 15.0  # 低帧率阈值，低于此值降低分辨率
FPS_THRESHOLD_HIGH = 28.0  # 高帧率阈值，高于此值可以尝试提高分辨率
RESOLUTION_ADJUST_INTERVAL = 5.0  # 分辨率调整间隔（秒）

# 摄像头优化配置
CAMERA_BUFFER_SIZE = 1  # 摄像头缓冲区大小
CAMERA_API_PREFERENCE = cv2.CAP_V4L2  # Linux上使用V4L2后端
CAMERA_FPS_TARGET = 30  # 摄像头目标帧率
CAMERA_FOURCC_OPTIONS = ['MJPG', 'YUYV', 'RGB3']  # 优先使用MJPG编码

# 帧率计算类
class FPSCounter:
    """计算并跟踪帧率"""
    def __init__(self, window_size=10):  # 减小窗口大小为10以获得更实时的帧率
        """
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
                # 修正帧率计算公式: 在窗口内完成的帧数除以时间差
                self.last_fps = len(self.timestamps) / time_diff  # 移除了 -1
            else:
                self.last_fps = 0
        
        return self.last_fps
    
    def get_fps(self):
        """获取当前帧率"""
        return self.last_fps
    
    def get_total_frames(self):
        """获取总帧数"""
        return self.total_frames
    
    def reset(self):
        """重置帧率计数器"""
        self.timestamps.clear()
        self.last_fps = 0
        # 不重置total_frames，这样可以保留总计数

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
        self.camera_fps = CAMERA_FPS_TARGET
        self.camera_buffer_size = CAMERA_BUFFER_SIZE
        self.camera_api = CAMERA_API_PREFERENCE
        self.camera_fourcc = None
        
        # 初始化帧率计数器
        self.capture_fps = FPSCounter()  # 摄像头捕获帧率
        self.pose_process_fps = FPSCounter()  # 姿势处理帧率
        self.emotion_process_fps = FPSCounter()  # 情绪处理帧率
        
        # 存储最新分析结果
        self.pose_result = {
            'angle': 0,
            'is_bad_posture': False,
            'is_occluded': False,
            'status': 'Initialized',
            'posture_type': 'unknown'  # 新增坐姿类型
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
        
        # 性能优化参数
        self.use_separate_grab_retrieve = True  # 使用分离的grab和retrieve操作提高性能
        self.skip_frames_when_slow = True  # 在处理过慢时允许跳帧
        self.skip_count = 0  # 当前跳帧计数
        self.max_consecutive_skips = 3  # 最大连续跳帧数
        
        # 性能监控
        self.performance_stats = {
            'camera_errors': 0,
            'processing_times': deque(maxlen=100),
            'skipped_frames': 0,
            'last_reconnect_time': 0,
            'reconnect_interval': 10.0  # 重连间隔（秒）
        }
        
        # 采样策略
        self.resize_method = 'subsampling'  # 'resize'  or 'subsampling'
        
        # 坐姿图像记录配置
        self.posture_recording_enabled = True  # 是否启用坐姿图像记录
        self.bad_posture_duration_threshold = 3  # 连续不良坐姿超过此秒数才记录
        self.recording_interval = 60  # 两次记录的最小间隔(秒)
        self.bad_posture_start_time = None  # 不良坐姿开始时间
        self.last_recording_time = 0  # 上次记录时间
        self.last_any_recording_time = 0  # 上次任意类型（不良或良好）坐姿的记录时间
        self.continuous_bad_posture = False  # 是否持续处于不良坐姿
        
        # 良好坐姿记录配置
        self.good_posture_recording_enabled = True  # 是否启用良好坐姿记录
        self.good_posture_angle_threshold = 40.0  # 良好坐姿角度阈值(度)，小于此值视为良好坐姿
        self.good_posture_duration_threshold = 5  # 连续良好坐姿超过此秒数才记录(秒)
        self.good_posture_interval = 120  # 良好坐姿记录间隔(秒)
        self.continuous_good_posture = False  # 是否持续处于良好坐姿
        self.good_posture_start_time = None  # 良好坐姿开始时间
        self.last_good_recording_time = 0  # 上次良好坐姿记录时间
        
        # 坐姿类型划分阈值（四档）
        self.posture_thresholds = {
            'excellent': 40.0,  # 0-40度：优秀坐姿
            'good': 50.0,       # 40-50度：良好坐姿
            'fair': 60.0,       # 50-60度：一般坐姿
            'poor': 70.0        # 60-70度：不良坐姿，60度以上：极差坐姿
        }
        
        # 坐姿时间记录
        self.current_posture_type = None    # 当前坐姿类型
        self.posture_start_time = None      # 当前坐姿开始时间
        self.posture_time_recording_enabled = True  # 是否启用坐姿时间记录
    
    # 新增跳采样方法
    def _resize_with_subsampling(self, frame, target_width, target_height):
        """使用跳采样而非直接缩放来调整分辨率，保持原始视角
        
        Args:
            frame: 原始帧图像
            target_width: 目标宽度
            target_height: 目标高度
        
        Returns:
            调整后的帧图像
        """
        if frame is None:
            return None
            
        h, w = frame.shape[:2]
        
        # 计算跳采样间隔
        step_x = max(1, w // target_width)
        step_y = max(1, h // target_height)
        
        # 进行跳采样
        subsampled = frame[::step_y, ::step_x]
        
        # 如果跳采样后的尺寸与目标尺寸不完全匹配，进行最小程度的缩放调整
        actual_h, actual_w = subsampled.shape[:2]
        if actual_w != target_width or actual_h != target_height:
            return cv2.resize(subsampled, (target_width, target_height), 
                             interpolation=cv2.INTER_NEAREST)
        
        return subsampled
    
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
                    smooth_landmarks=True,      # 启用关键点平滑
                    min_detection_confidence=0.6, # 降低到0.6以提高检测率
                    min_tracking_confidence=0.5
                )
                
                # 创建情绪分析器实例
                self.emotion_analyzer = EmotionAnalyzer()
                
                # 重置计数器和性能统计
                self.capture_fps.reset()
                self.pose_process_fps.reset()
                self.emotion_process_fps.reset()
                self.performance_stats['camera_errors'] = 0
                self.performance_stats['skipped_frames'] = 0
                
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
                        self.cap = cv2.VideoCapture(camera_index, self.camera_api)
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
                    self.cap = cv2.VideoCapture(6, self.camera_api)
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
                        self.cap = cv2.VideoCapture(camera_index, self.camera_api)
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
                        self.cap = cv2.VideoCapture(dev_path, self.camera_api)
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
            
            # 优化摄像头配置以提高捕获帧率
            self._optimize_camera_settings()
            
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
            
            # 测试实际帧率
            measured_fps = self._test_camera_fps(self.cap, frames=15)
            print(f"测量的实际摄像头帧率: {measured_fps:.1f} FPS")
            
            # 重置帧率计数器
            self.capture_fps = FPSCounter()
            self.pose_process_fps = FPSCounter()
            self.emotion_process_fps = FPSCounter()
            
            # 初始化遮挡计数器
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
    
    def _optimize_camera_settings(self):
        """优化摄像头设置以提高性能"""
        try:
            if not self.cap or not self.cap.isOpened():
                return False
            
            # 设置缓冲区大小为1，减少延迟
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.camera_buffer_size)
            
            # 尝试设置目标FPS
            self.cap.set(cv2.CAP_PROP_FPS, self.camera_fps)
            
            # 尝试不同的编码格式，优先使用MJPG
            best_format = None
            best_fps = 0
            
            for fourcc_code in CAMERA_FOURCC_OPTIONS:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*fourcc_code)
                    self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
                    # 读取一帧测试格式是否生效
                    ret, test = self.cap.read()
                    if ret:
                        # 测试这个格式下的帧率
                        test_fps = self._test_camera_fps(self.cap, frames=10)
                        print(f"{fourcc_code} 格式下测得帧率: {test_fps:.1f} FPS")
                        
                        if test_fps > best_fps:
                            best_fps = test_fps
                            best_format = fourcc_code
                            self.camera_fourcc = fourcc
                except Exception as e:
                    print(f"设置 {fourcc_code} 格式失败: {e}")
            
            if best_format:
                print(f"选择最佳格式: {best_format} 帧率: {best_fps:.1f} FPS")
                # 再次设置最佳格式
                fourcc = cv2.VideoWriter_fourcc(*best_format)
                self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
            
            # 尝试不同的分辨率以找到最佳性能
            resolutions_to_try = [(640, 480), (480, 360), (320, 240)]
            
            for width, height in resolutions_to_try:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                
                # 检查设置是否成功
                actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                
                print(f"尝试设置分辨率 {width}x{height}, 实际: {actual_width}x{actual_height}")
                
                # 只有在成功设置到接近目标分辨率时才进行测试
                if abs(actual_width - width) < 30 and abs(actual_height - height) < 30:
                    ret, test = self.cap.read()
                    if ret:
                        fps = self._test_camera_fps(self.cap, frames=10)
                        print(f"分辨率 {width}x{height} 下测得帧率: {fps:.1f} FPS")
                        
                        # 如果帧率超过15fps就可以使用这个分辨率
                        if fps >= 15:
                            print(f"选择分辨率 {width}x{height} 帧率足够")
                            break
            
            return True
        except Exception as e:
            print(f"优化摄像头设置失败(非致命错误): {e}")
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
        frames_read = 0
        
        for _ in range(frames):
            if self.use_separate_grab_retrieve:
                if cap.grab():
                    _, _ = cap.retrieve()
                    frames_read += 1
            else:
                ret, _ = cap.read()
                if ret:
                    frames_read += 1
        
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        if elapsed_time > 0 and frames_read > 0:
            return frames_read / elapsed_time
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
            
            # 重置帧率计数器
            self.pose_process_fps.reset()
            self.emotion_process_fps.reset()
        
        # 当帧率足够高时提高分辨率
        elif process_fps > FPS_THRESHOLD_HIGH and self.current_resolution_index > 0:
            self.current_resolution_index -= 1
            self.process_width, self.process_height = RESOLUTION_LEVELS[self.current_resolution_index]
            print(f"帧率足够高 ({process_fps:.1f} FPS)，提高处理分辨率至 {self.process_width}x{self.process_height}")
            self.last_resolution_adjust_time = current_time
            
            # 重置帧率计数器
            self.pose_process_fps.reset()
            self.emotion_process_fps.reset()
    
    def _adjust_skip_frame_strategy(self):
        """根据当前处理性能调整跳帧策略"""
        if not self.skip_frames_when_slow:
            self.skip_count = 0
            return False
        
        # 计算平均处理时间
        avg_processing_time = 0
        if self.performance_stats['processing_times']:
            avg_processing_time = sum(self.performance_stats['processing_times']) / len(self.performance_stats['processing_times'])
        
        # 处理时间超过帧间时间的90%时需要跳帧
        frame_time = 1.0 / self.camera_fps if self.camera_fps > 0 else 0.033  # 默认30fps
        
        if avg_processing_time > frame_time * 0.9:
            # 需要跳帧但不超过最大连续跳帧数
            if self.skip_count < self.max_consecutive_skips:
                self.skip_count += 1
                self.performance_stats['skipped_frames'] += 1
                return True
            else:
                # 达到最大跳帧数，重置计数并处理这一帧
                self.skip_count = 0
                return False
        else:
            # 处理时间可接受，不需要跳帧
            self.skip_count = 0
            return False
    
    def _process_frames(self):
        """处理视频帧的主循环"""
        if not POSTURE_MODULE_AVAILABLE:
            return
        
        last_fps_update_time = time.time()
        consecutive_read_failures = 0
        last_frame_time = time.time()
        last_reconnect_time = time.time()
        
        while self.is_running and self.cap and self.cap.isOpened():
            try:
                current_time = time.time()
                
                # 如果摄像头出现多次错误，尝试重新连接摄像头
                if consecutive_read_failures > 5 and (current_time - self.performance_stats['last_reconnect_time']) > self.performance_stats['reconnect_interval']:
                    print(f"连续 {consecutive_read_failures} 次读取失败，尝试重新初始化摄像头...")
                    self.cap.release()
                    success = self._init_camera()
                    if not success:
                        print("重新初始化摄像头失败，暂停1秒后重试")
                        time.sleep(1)
                        continue
                    consecutive_read_failures = 0
                    self.performance_stats['last_reconnect_time'] = current_time
                
                # 使用分离的grab和retrieve方法提高性能
                if self.use_separate_grab_retrieve:
                    grabbed = self.cap.grab()
                    if not grabbed:
                        consecutive_read_failures += 1
                        self.performance_stats['camera_errors'] += 1
                        time.sleep(0.01)
                        continue
                    
                    ret, frame = self.cap.retrieve()
                    if not ret:
                        consecutive_read_failures += 1
                        self.performance_stats['camera_errors'] += 1
                        print("无法读取摄像头帧")
                        time.sleep(0.01)
                        continue
                else:
                    # 常规读取模式
                    ret, frame = self.cap.read()
                    if not ret:
                        consecutive_read_failures += 1
                        self.performance_stats['camera_errors'] += 1
                        print("无法读取摄像头帧")
                        time.sleep(0.01)
                        continue
                
                # 重置错误计数器
                consecutive_read_failures = 0
                
                # 更新捕获帧率
                self.capture_fps.update()
                
                # 计算帧间隔
                frame_interval = current_time - last_frame_time
                last_frame_time = current_time
                
                # 检查是否需要跳过这一帧以提高性能
                if self._adjust_skip_frame_strategy():
                    # 跳过这一帧，但仍提供最后处理的结果给视频流
                    continue
                
                # 每隔一段时间检查并调整处理分辨率
                self._adjust_processing_resolution()
                
                # 记录处理开始时间
                process_start_time = time.time()
                
                # 调整帧尺寸进行处理 - 根据设置使用跳采样或传统缩放
                if self.resize_method == 'subsampling':
                    # 使用跳采样方法以保持原始视角
                    processed_frame = self._resize_with_subsampling(frame, self.process_width, self.process_height)
                else:
                    # 使用传统缩放方法
                    processed_frame = cv2.resize(frame, (self.process_width, self.process_height))
                
                pose_frame = processed_frame.copy()
                emotion_frame = processed_frame.copy()
                
                # 处理姿势
                pose_results = self._process_pose(pose_frame)
                self.pose_process_fps.update()  # 更新姿势处理帧率
                
                # 处理情绪
                emotion_results = self._process_emotion(emotion_frame)
                self.emotion_process_fps.update()  # 更新情绪处理帧率
                
                # 记录处理时间
                process_time = time.time() - process_start_time
                self.performance_stats['processing_times'].append(process_time)
                
                # 添加处理时间和分辨率信息到显示帧
                # 姿势帧显示处理信息
                size_text = f"{self.process_width}x{self.process_height}"
                cv2.putText(pose_results['display_frame'], 
                          f"Proc: {process_time*1000:.1f}ms {size_text}", 
                          (pose_results['display_frame'].shape[1] - 200, 25), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                
                # 将处理后的帧放入队列供Web端点使用
                if self.video_stream_handler:
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
                
                # 检查并记录不良坐姿
                self._check_and_record_bad_posture(frame, pose_results)
                
                # 每秒更新一次帧率信息
                # 每0.5秒更新一次帧率信息
                if current_time - last_fps_update_time >= 0.5:  # 从1.0改为0.5秒
                    self.fps_info = {
                        'capture_fps': round(self.capture_fps.get_fps(), 1),
                        'pose_process_fps': round(self.pose_process_fps.get_fps(), 1),
                        'emotion_process_fps': round(self.emotion_process_fps.get_fps(), 1),
                        'process_resolution': f"{self.process_width}x{self.process_height}",
                        'avg_process_time_ms': round(sum(self.performance_stats['processing_times']) / 
                                                   max(1, len(self.performance_stats['processing_times'])) * 1000, 1)
                        if self.performance_stats['processing_times'] else 0
                    }
                    last_fps_update_time = current_time
                
                # 根据实际帧率动态调整延迟时间
                current_fps = min(self.pose_process_fps.get_fps(), self.emotion_process_fps.get_fps())
                target_interval = 1.0 / TARGET_FPS
                
                # 如果处理太快，增加一点延迟以减少CPU使用
                # 如果处理太慢，不增加延迟
                if process_time < target_interval * 0.8:  # 如果处理时间远小于目标间隔
                    time.sleep(min(0.001, (target_interval - process_time) * 0.5))
            except Exception as e:
                print(f"处理帧异常: {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(0.1)
    
    def _process_pose(self, frame):
        """处理姿势检测"""
        if not POSTURE_MODULE_AVAILABLE:
            return {
                'display_frame': frame,
                'angle': None,
                'is_bad_posture': False,
                'is_occluded': True,
                'status': 'Module Not Available',
                'posture_type': 'unknown'
            }
        
        results = {
            'display_frame': frame,
            'angle': None,
            'is_bad_posture': False,
            'is_occluded': True,
            'status': 'No Detection',
            'posture_type': 'unknown'
        }
        
        try:
            # 姿势检测
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pose_results = self.pose.process(frame_rgb)
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
            posture_type = 'unknown'
            
            if angle_info[0] is not None:
                angle, is_bad_posture, points = angle_info
                self.last_valid_angle = angle
                
                # 根据角度确定坐姿类型
                if angle <= self.posture_thresholds['excellent']:
                    posture_type = 'excellent'  # 优秀坐姿
                elif angle <= self.posture_thresholds['good']:
                    posture_type = 'good'  # 良好坐姿
                elif angle <= self.posture_thresholds['fair']:
                    posture_type = 'fair'  # 一般坐姿
                else:
                    posture_type = 'poor'  # 不良坐姿
                
                # 记录坐姿时间
                self._record_posture_time(angle, posture_type)
            
            # 绘制姿势关键点和信息
            display_frame = frame.copy()
            
            # 根据当前帧率优化绘制效果
            drawing_style = None
            current_fps = min(self.pose_process_fps.get_fps(), self.emotion_process_fps.get_fps())
            if current_fps < 10:
                # 帧率低，使用简化绘制模式
                mp_drawing.draw_landmarks(
                    display_frame,
                    pose_results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0,255,0), thickness=1, circle_radius=1),
                    mp_drawing.DrawingSpec(color=(255,0,0), thickness=1)
                )
            else:
                # 帧率正常，使用标准绘制模式
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
                # 根据不同坐姿类型设置不同颜色
                posture_color = {
                    'excellent': (0, 255, 0),   # 绿色
                    'good': (0, 255, 128),      # 浅绿色
                    'fair': (0, 128, 255),      # 橙色
                    'poor': (0, 0, 255)         # 红色
                }.get(posture_type, (0, 0, 255))
                
                posture_text = {
                    'excellent': '优秀',
                    'good': '良好',
                    'fair': '一般',
                    'poor': '不良'
                }.get(posture_type, '未知')
                
                text = f"Angle: {angle:.1f}° [{posture_text}]"
                cv2.putText(display_frame, text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, posture_color, 2)
                
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
                'status': occlusion_status if final_occlusion else 'Tracking',
                'posture_type': posture_type
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
            # 更新情绪分析器的所有参数
            self.emotion_analyzer.emotion_smoothing_window = posture_params['emotion_smoothing_window']
            self.emotion_analyzer.mouth_open_ratio_threshold = posture_params['mouth_open_ratio_threshold']
            self.emotion_analyzer.eye_open_ratio_threshold = posture_params['eye_open_ratio_threshold']
            self.emotion_analyzer.brow_down_threshold = posture_params['brow_down_threshold']
            
            # 分析情绪
            emotion_state, face_landmarks, _ = self.emotion_analyzer.analyze(frame)
            
            # 绘制情绪界面
            display_frame = frame.copy()
            if face_landmarks:
                # 根据当前帧率优化绘制效果
                current_fps = min(self.pose_process_fps.get_fps(), self.emotion_process_fps.get_fps())
                if current_fps < 10:
                    # 帧率低，使用简化绘制
                    mp_drawing.draw_landmarks(
                        image=display_frame,
                        landmark_list=face_landmarks,
                        connections=mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=mp_drawing.DrawingSpec(color=(0,255,0), thickness=1, circle_radius=1),
                        connection_drawing_spec=mp_drawing.DrawingSpec(color=(0,255,0), thickness=1)
                    )
                else:
                    # 帧率正常，使用标准绘制
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
        # 添加更多性能统计信息
        extended_info = {
            **self.fps_info,
            'skipped_frames': self.performance_stats['skipped_frames'],
            'camera_errors': self.performance_stats['camera_errors'],
            'adaptive_resolution': self.adaptive_resolution,
            'skip_frames_enabled': self.skip_frames_when_slow
        }
        return extended_info
    
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
            
            # 重置相关计数器
            self.pose_process_fps.reset()
            self.emotion_process_fps.reset()
        
        return True
    
    def set_performance_mode(self, skip_frames=None, use_separate_grab=None):
        """设置性能优化模式
        
        Args:
            skip_frames: 是否在处理过慢时跳帧
            use_separate_grab: 是否使用分离的grab/retrieve操作
        """
        if skip_frames is not None:
            self.skip_frames_when_slow = skip_frames
            print(f"{'启用' if skip_frames else '禁用'}处理过慢时跳帧")
        
        if use_separate_grab is not None:
            self.use_separate_grab_retrieve = use_separate_grab
            print(f"{'启用' if use_separate_grab else '禁用'}分离的grab/retrieve操作")
        
        return True
    
    def get_performance_stats(self):
        """获取性能统计信息"""
        avg_processing_ms = 0
        if self.performance_stats['processing_times']:
            avg_processing_ms = sum(self.performance_stats['processing_times']) / len(self.performance_stats['processing_times']) * 1000
        
        return {
            'skipped_frames': self.performance_stats['skipped_frames'],
            'camera_errors': self.performance_stats['camera_errors'],
            'avg_processing_time_ms': round(avg_processing_ms, 2),
            'capture_fps': round(self.capture_fps.get_fps(), 1),
            'pose_process_fps': round(self.pose_process_fps.get_fps(), 1),
            'emotion_process_fps': round(self.emotion_process_fps.get_fps(), 1),
            'current_resolution': f"{self.process_width}x{self.process_height}",
            'adaptive_mode': self.adaptive_resolution,
            'skip_frames_enabled': self.skip_frames_when_slow
        }

    def _find_available_cameras(self):
        """查找系统中所有可用的摄像头并返回可用的索引列表"""
        available_cameras = []
        
        # 尝试前10个摄像头索引
        for i in range(10):
            try:
                cap = cv2.VideoCapture(i, self.camera_api)
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

    def _check_and_record_bad_posture(self, frame, pose_results):
        """检查并记录不良坐姿
        逻辑：如果坐姿变为不良保存一次，每十分钟只允许保存一次，如果十分钟内没有不良坐姿则保存一次良好坐姿
        每个时间段最多允许存在20张图片，每天最多允许存在240张图片
        """
        if not self.posture_recording_enabled:
            return False
        
        # 检查是否是有效的姿势检测（非遮挡状态）
        if pose_results['is_occluded'] or pose_results['angle'] is None:
            self.continuous_bad_posture = False
            self.bad_posture_start_time = None
            self.continuous_good_posture = False
            self.good_posture_start_time = None
            return False
        
        angle = pose_results['angle']
        current_time = time.time()
        current_datetime = datetime.now()  # 当前时间的datetime对象
        recorded = False
        max_interval = 600  # 10分钟
        
        # 初始化属性（如果尚未定义）
        if not hasattr(self, 'last_any_recording_time'):
            self.last_any_recording_time = 0
        if not hasattr(self, 'continuous_bad_posture'):
            self.continuous_bad_posture = False
        if not hasattr(self, 'continuous_good_posture'):
            self.continuous_good_posture = False
        if not hasattr(self, 'good_posture_start_time'):
            self.good_posture_start_time = None
        if not hasattr(self, 'bad_posture_start_time'):
            self.bad_posture_start_time = None
        
        # 处理不良坐姿
        if pose_results['is_bad_posture']:
            # 如果刚从良好变为不良坐姿，判断是否需要记录
            if not self.continuous_bad_posture:
                self.continuous_bad_posture = True
                self.bad_posture_start_time = current_time
                
                # 检查是否超过了10分钟的时间间隔
                if current_time - self.last_any_recording_time >= max_interval:
                    recorded = self._save_posture_image(
                        frame=frame,
                        angle=angle,
                        is_bad_posture=True,
                        posture_type="Bad",
                        record_type="auto"
                    )
                    if recorded:
                        self.last_any_recording_time = current_time
                        
                        # 获取当前小时和日期
                        current_hour = current_datetime.replace(minute=0, second=0, microsecond=0)
                        current_date = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
                        
                        # 清理当前时间段的图片，保留最新的20张
                        from modules.new_cleanup_functions import cleanup_hourly_images, cleanup_daily_images
                        cleanup_hourly_images(current_hour, 20)
                        
                        # 清理当天的图片，保留最新的240张
                        cleanup_daily_images(current_date, 240)
            
            # 重置良好坐姿状态
            self.continuous_good_posture = False
            self.good_posture_start_time = None
        else:
            # 恢复良好坐姿，重置不良坐姿状态
            self.continuous_bad_posture = False
            self.bad_posture_start_time = None
            
            # 处理良好坐姿
            if angle <= self.good_posture_angle_threshold and self.good_posture_recording_enabled:
                if not self.continuous_good_posture:
                    self.continuous_good_posture = True
                    self.good_posture_start_time = current_time
                
                # 如果10分钟内没有不良坐姿则保存一次良好坐姿
                if (self.good_posture_start_time and current_time - self.last_any_recording_time >= max_interval):
                    recorded = self._save_posture_image(
                        frame=frame,
                        angle=angle,
                        is_bad_posture=False,
                        posture_type="Good",
                        record_type="auto"
                    )
                    if recorded:
                        self.last_any_recording_time = current_time
                        
                        # 获取当前小时和日期
                        current_hour = current_datetime.replace(minute=0, second=0, microsecond=0)
                        current_date = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
                        
                        # 清理当前时间段的图片，保留最新的20张
                        from modules.new_cleanup_functions import cleanup_hourly_images, cleanup_daily_images
                        cleanup_hourly_images(current_hour, 20)
                        
                        # 清理当天的图片，保留最新的240张
                        cleanup_daily_images(current_date, 240)
            else:
                self.continuous_good_posture = False
                self.good_posture_start_time = None
                
        return recorded
        
    def _save_posture_image(self, frame, angle, is_bad_posture, posture_type="Unknown", record_type="manual"):
        """保存坐姿图像
        
        Args:
            frame: 原始视频帧
            angle: 头部角度
            is_bad_posture: 是否是不良坐姿
            posture_type: 坐姿类型描述
            record_type: 记录类型，如'auto'或'manual'
            
        Returns:
            是否成功保存
        """
        try:
            from modules.database_module import save_posture_image
            
            # 获取状态信息
            posture_status = f"{posture_type} Posture - Angle: {angle:.1f}°"
            emotion = self.emotion_result['emotion']
            
            # 添加记录说明
            notes = (
                f"{record_type}记录的{posture_type.lower()}坐姿，角度: {angle:.1f}°, "
                f"情绪: {emotion}, "
                f"处理分辨率: {self.process_width}x{self.process_height}, "
                f"姿势处理帧率: {self.pose_process_fps.get_fps():.1f} FPS"
            )
            
            # 保存图像记录
            result = save_posture_image(
                image=frame,             # 使用原始未处理帧以获得最佳图像质量
                angle=angle,
                is_bad_posture=is_bad_posture,
                posture_status=posture_status,
                emotion=emotion,
                notes=notes
            )
            
            if result:
                print(f"记录{posture_type}坐姿图像成功，ID: {result['id']}")
                return True
            else:
                print(f"记录{posture_type}坐姿图像失败")
                return False
                
        except Exception as e:
            print(f"记录坐姿图像时出错: {str(e)}")
            return False
        
    def set_posture_recording(self, enabled=True, duration_threshold=None, interval=None, 
                         good_posture_enabled=None, good_posture_angle_threshold=None, 
                         good_posture_duration_threshold=None, good_posture_interval=None):
        """设置坐姿图像记录参数
        
        Args:
            enabled: 是否启用坐姿图像记录
            duration_threshold: 连续不良坐姿超过多少秒才记录
            interval: 两次记录的最小间隔(秒)
            good_posture_enabled: 是否启用良好坐姿记录
            good_posture_angle_threshold: 良好坐姿角度阈值(度)，小于此值视为标准良好坐姿
            good_posture_duration_threshold: 连续良好坐姿超过此秒数才记录
            good_posture_interval: 良好坐姿记录间隔(秒)
            
        Returns:
            更新后的设置
        """
        self.posture_recording_enabled = enabled
        
        if duration_threshold is not None and  duration_threshold > 0:
            self.bad_posture_duration_threshold = duration_threshold
            
        if interval is not None and  interval > 0:
            self.recording_interval = interval
            
        # 更新良好坐姿记录设置
        if good_posture_enabled is not None:
            self.good_posture_recording_enabled = good_posture_enabled
            
        if good_posture_angle_threshold is not None and  0 < good_posture_angle_threshold <= 60:
            self.good_posture_angle_threshold = good_posture_angle_threshold
            
        if good_posture_duration_threshold is not None and  good_posture_duration_threshold > 0:
            self.good_posture_duration_threshold = good_posture_duration_threshold
            
        if good_posture_interval is not None and  good_posture_interval > 0:
            self.good_posture_interval = good_posture_interval
            
        print(f"坐姿记录设置已更新: 记录不良坐姿={self.posture_recording_enabled}, " 
              f"不良姿势持续时间阈值={self.bad_posture_duration_threshold}秒, "
              f"不良姿势记录间隔={self.recording_interval}秒, "
              f"记录良好坐姿={self.good_posture_recording_enabled}, "
              f"良好坐姿角度阈值={self.good_posture_angle_threshold}°, "
              f"良好坐姿持续时间={self.good_posture_duration_threshold}秒, "
              f"良好坐姿记录间隔={self.good_posture_interval}秒")
              
        return self.get_posture_recording_settings()
        
    def get_posture_recording_settings(self):
        """获取坐姿图像记录设置"""
        return {
            'enabled': self.posture_recording_enabled,
            'duration_threshold': self.bad_posture_duration_threshold,
            'interval': self.recording_interval,
            'last_recording_time': self.last_recording_time,
            'good_posture_enabled': self.good_posture_recording_enabled,
            'good_posture_angle_threshold': self.good_posture_angle_threshold,
            'good_posture_duration_threshold': self.good_posture_duration_threshold,
            'good_posture_interval': self.good_posture_interval,
            'last_good_recording_time': self.last_good_recording_time
        }

    def _record_posture_time(self, angle, posture_type):
        """记录坐姿时间
        
        根据当前姿势类型记录持续时间，当姿势类型改变时保存上一次记录
        
        Args:
            angle: 当前头部角度
            posture_type: 当前坐姿类型 ('excellent', 'good', 'fair', 'poor')
        """
        from datetime import datetime
        from modules.database_module import record_posture_time
        
        if not self.posture_time_recording_enabled:
            return
            
        current_time = datetime.now()
        
        # 如果是第一次记录或者坐姿类型改变
        if self.current_posture_type is None:
            # 初始化记录
            self.current_posture_type = posture_type
            self.posture_start_time = current_time
            self.last_periodic_record_time = current_time
            return
            
        # 定期记录当前状态（每30秒记录一次当前状态，即使坐姿类型没有改变）
        time_since_last_record = (current_time - self.last_periodic_record_time).total_seconds()
        if time_since_last_record >= 30:  # 每30秒记录一次
            # 计算此周期的持续时间
            duration = time_since_last_record
            
            try:
                # 记录到数据库
                record_posture_time(
                    start_time=self.last_periodic_record_time,
                    end_time=current_time,
                    duration_seconds=duration,
                    angle=angle,
                    posture_type=self.current_posture_type,
                    notes=f"周期性记录的坐姿时间，角度：{angle:.1f}°"
                )
                print(f"周期性记录坐姿：{self.current_posture_type}，持续时间：{duration:.1f}秒")
                
                # 更新上次记录时间
                self.last_periodic_record_time = current_time
                
            except Exception as e:
                print(f"记录坐姿时间失败: {str(e)}")
        
        # 如果坐姿类型改变，记录上一种类型的持续时间
        if posture_type != self.current_posture_type:
            if self.posture_start_time:
                # 计算持续时间（秒）
                duration = (current_time - self.posture_start_time).total_seconds()
                
                # 只记录持续超过1秒的姿势
                if duration >= 1.0:
                    try:
                        # 记录到数据库
                        record_posture_time(
                            start_time=self.posture_start_time,
                            end_time=current_time,
                            duration_seconds=duration,
                            angle=self.last_valid_angle,
                            posture_type=self.current_posture_type,
                            notes=f"状态变化记录的坐姿时间，角度：{self.last_valid_angle:.1f}°"
                        )
                        print(f"状态变化记录坐姿：{self.current_posture_type} -> {posture_type}，持续时间：{duration:.1f}秒")
                    except Exception as e:
                        print(f"记录坐姿时间失败: {str(e)}")
            
            # 更新当前坐姿类型和开始时间
            self.current_posture_type = posture_type
            self.posture_start_time = current_time
            self.last_periodic_record_time = current_time
    
    def set_posture_time_recording(self, enabled=True, thresholds=None):
        """设置坐姿时间记录参数
        
        Args:
            enabled: 是否启用坐姿时间记录
            thresholds: 坐姿类型阈值字典，包含 'excellent', 'good', 'fair', 'poor' 键
        
        Returns:
            更新后的设置
        """
        self.posture_time_recording_enabled = enabled
        
        if thresholds:
            if 'excellent' in thresholds and 0 < thresholds['excellent'] < 90:
                self.posture_thresholds['excellent'] = thresholds['excellent']
                
            if 'good' in thresholds and 0 < thresholds['good'] < 90:
                self.posture_thresholds['good'] = thresholds['good']
                
            if 'fair' in thresholds and 0 < thresholds['fair'] < 90:
                self.posture_thresholds['fair'] = thresholds['fair']
                
            if 'poor' in thresholds and 0 < thresholds['poor'] < 90:
                self.posture_thresholds['poor'] = thresholds['poor']
        
        print(f"坐姿时间记录设置已更新: 启用={self.posture_time_recording_enabled}, "
              f"阈值设置: 优秀坐姿={self.posture_thresholds['excellent']}°, "
              f"良好坐姿={self.posture_thresholds['good']}°, "
              f"一般坐姿={self.posture_thresholds['fair']}°, "
              f"不良坐姿={self.posture_thresholds['poor']}°")
              
        return self.get_posture_time_recording_settings()
    
    def get_posture_time_recording_settings(self):
        """获取坐姿时间记录设置"""
        return {
            'enabled': self.posture_time_recording_enabled,
            'thresholds': self.posture_thresholds
        }
        
    def get_posture_stats(self, time_range='day', custom_start_date=None, custom_end_date=None, with_hourly_data=False):
        """获取坐姿统计数据
        
        Args:
            time_range: 时间范围 'day', 'week', 'month', 'custom'
            custom_start_date: 自定义开始日期，仅当time_range为'custom'时有效
            custom_end_date: 自定义结束日期，仅当time_range为'custom'时有效
            with_hourly_data: 是否返回每小时数据统计
            
        Returns:
            坐姿统计数据字典
        """
        from modules.database_module import get_posture_stats
        
        try:
            stats = get_posture_stats(
                time_range=time_range, 
                custom_start_date=custom_start_date, 
                custom_end_date=custom_end_date,
                with_hourly_data=with_hourly_data
            )
            return stats
        except Exception as e:
            print(f"获取坐姿统计数据失败: {str(e)}")
            return {
                'error': str(e)
            }
