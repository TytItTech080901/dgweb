"""
视频流处理模块 - 提供视频流生成和管理功能
"""
import cv2
import numpy as np
import time
import threading
from collections import deque
import queue
from config import DEBUG

# 帧率和分辨率相关配置
STREAM_FPS_TARGET = 25  # 目标流帧率
MAX_QUEUE_SIZE = 10     # 最大队列大小
DEFAULT_STREAM_WIDTH = 640  # 默认流宽度
DEFAULT_STREAM_HEIGHT = 480  # 默认流高度

# 自适应分辨率配置 - 根据TODO.md更新
STREAM_RESOLUTION_LEVELS = [
    (800, 600),   # 高分辨率
    (640, 480),   # 中分辨率
    (480, 360),   # 低分辨率
    (320, 240)    # 极低分辨率
]
FPS_THRESHOLD_LOW = 15.0  # 低帧率阈值，低于此值降低分辨率
FPS_THRESHOLD_HIGH = 28.0  # 高帧率阈值，高于此值可以尝试提高分辨率
RESOLUTION_ADJUST_INTERVAL = 5.0  # 分辨率调整间隔（秒）

# 帧率计算类
class FPSCounter:
    """计算并跟踪帧率"""
    def __init__(self, window_size=10):  # 减小窗口大小为10以获得更实时的帧率
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
    
    def reset(self):
        """重置帧率计数器"""
        self.timestamps.clear()
        self.last_fps = 0
        # 不重置total_frames，这样可以保留总计数

class VideoStreamHandler:
    """视频流处理类"""
    def __init__(self, process_width=None, process_height=None):
        """初始化视频流处理器
        
        Args:
            process_width: 处理宽度（可选），默认使用DEFAULT_STREAM_WIDTH
            process_height: 处理高度（可选），默认使用DEFAULT_STREAM_HEIGHT
        """
        print(f"DEBUG: 初始化VideoStreamHandler，宽度={process_width}，高度={process_height}")
        # 初始化队列
        self.pose_frame_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
        self.emotion_frame_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
        
        # 默认空帧（灰色）
        self.default_frame = self._create_default_frame()
        print(f"DEBUG: 创建默认帧大小 {self.default_frame.shape}")
        
        # 最后一帧（用于无帧时重复输出）
        self.last_pose_frame = self.default_frame.copy()
        self.last_emotion_frame = self.default_frame.copy()
        
        # 初始化原始帧属性
        self.last_raw_frame = None
        
        # 当前流分辨率（可动态调整）
        self.stream_width = process_width if process_width is not None else DEFAULT_STREAM_WIDTH
        self.stream_height = process_height if process_height is not None else DEFAULT_STREAM_HEIGHT
        self.current_resolution_index = self._get_resolution_index()
        self.last_resolution_adjust_time = 0
        self.adaptive_resolution = True  # 是否启用自适应分辨率
        
        # 添加resize_method属性
        self.resize_method = 'subsampling'  # 'resize' 或 'subsampling'
        
        print(f"DEBUG: 流分辨率设置为 {self.stream_width}x{self.stream_height}，分辨率索引={self.current_resolution_index}")
        
        # 帧率计数器
        self.pose_stream_fps = FPSCounter()
        self.emotion_stream_fps = FPSCounter()
        
        # 初始化锁
        self._pose_lock = threading.Lock()
        self._emotion_lock = threading.Lock()
        
        # 流状态 - 默认不开启视频流传输
        self.is_streaming = False
        
        # 调试信息
        self.debug = DEBUG
        
        # 处理压缩质量
        self.jpeg_quality = 90  # 默认JPEG压缩质量
        self.stream_params = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
        
        # 自适应质量控制
        self.adaptive_quality = True  # 是否启用自适应质量控制
        self.quality_adjust_interval = 3.0  # 质量调整间隔（秒）
        self.last_quality_adjust_time = 0
        
        # 性能监控
        self.performance_stats = {
            'dropped_frames': 0,
            'compression_time': deque(maxlen=50),
            'transmission_time': deque(maxlen=50)
        }
        
        print("DEBUG: VideoStreamHandler初始化完成")
    
    def _create_default_frame(self):
        """创建默认空帧（灰色背景）"""
        frame = np.ones((DEFAULT_STREAM_HEIGHT, DEFAULT_STREAM_WIDTH, 3), dtype=np.uint8) * 200
        
        # 添加提示文本
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = "等待视频流..."
        text_size = cv2.getTextSize(text, font, 1, 2)[0]
        text_x = (DEFAULT_STREAM_WIDTH - text_size[0]) // 2
        text_y = (DEFAULT_STREAM_HEIGHT + text_size[1]) // 2
        
        cv2.putText(frame, text, (text_x, text_y), font, 1, (0, 0, 0), 2)
        
        return frame
        
    def _create_info_frame(self, title, status_text, info_text):
        """创建信息帧，用于显示状态信息但不传输视频流
        
        Args:
            title: 框架标题
            status_text: 状态文本
            info_text: 额外信息文本
            
        Returns:
            带有信息的帧
        """
        # 创建灰色背景帧
        frame = np.ones((DEFAULT_STREAM_HEIGHT, DEFAULT_STREAM_WIDTH, 3), dtype=np.uint8) * 220
        
        # 添加蓝色标题区域
        cv2.rectangle(frame, (0, 0), (DEFAULT_STREAM_WIDTH, 40), (100, 100, 250), -1)
        
        # 添加标题文本
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, title, (20, 30), font, 1, (255, 255, 255), 2)
        
        # 添加状态信息
        cv2.putText(frame, status_text, (DEFAULT_STREAM_WIDTH//2 - 100, DEFAULT_STREAM_HEIGHT//2 - 20), 
                   font, 1, (0, 0, 255), 2)
        
        # 添加提示信息
        cv2.putText(frame, info_text, (DEFAULT_STREAM_WIDTH//2 - 100, DEFAULT_STREAM_HEIGHT//2 + 20), 
                   font, 0.7, (50, 50, 50), 1)
        
        # 添加时间戳
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, DEFAULT_STREAM_HEIGHT - 10), font, 0.5, (100, 100, 100), 1)
        
        return frame
    
    def _get_resolution_index(self):
        """根据当前设置的分辨率获取最接近的索引"""
        min_diff = float('inf')
        best_index = 1  # 默认中等分辨率
        
        for i, (width, height) in enumerate(STREAM_RESOLUTION_LEVELS):
            # 计算与当前设置分辨率的差异（像素总数的差异）
            diff = abs((width * height) - (self.stream_width * self.stream_height))
            if diff < min_diff:
                min_diff = diff
                best_index = i
        
        return best_index

    def add_pose_frame(self, frame):
        """添加姿势分析帧到队列"""
        if frame is None:
            return
            
        with self._pose_lock:
            # 保存原始帧，确保是未经任何处理的原始摄像头图像
            if frame is not None and frame.size > 0:
                # 创建一个深拷贝，以确保原始帧不受后续处理的影响
                self.last_raw_frame = frame.copy()
            
            # 处理用于流传输的帧
            resized_frame = self._prepare_frame_for_streaming(frame)
            self.last_pose_frame = resized_frame
            
            # 尝试向队列添加帧，如果队列满则丢弃旧帧
            if self.pose_frame_queue.full():
                try:
                    self.pose_frame_queue.get_nowait()  # 丢弃最旧的帧
                    self.performance_stats['dropped_frames'] += 1
                except queue.Empty:
                    pass
                    
            try:
                self.pose_frame_queue.put_nowait(resized_frame)
            except queue.Full:
                # 队列已满，忽略
                self.performance_stats['dropped_frames'] += 1
                pass
    
    def add_emotion_frame(self, frame):
        """添加情绪分析帧到队列"""
        if frame is None:
            return
            
        with self._emotion_lock:
            resized_frame = self._prepare_frame_for_streaming(frame)
            self.last_emotion_frame = resized_frame
            
            # 尝试向队列添加帧，如果队列满则丢弃旧帧
            if self.emotion_frame_queue.full():
                try:
                    self.emotion_frame_queue.get_nowait()  # 丢弃最旧的帧
                    self.performance_stats['dropped_frames'] += 1
                except queue.Empty:
                    pass
                    
            try:
                self.emotion_frame_queue.put_nowait(resized_frame)
            except queue.Full:
                # 队列已满，忽略
                self.performance_stats['dropped_frames'] += 1
                pass
    
    def _prepare_frame_for_streaming(self, frame):
        """准备帧用于流传输（调整尺寸和优化图像）"""
        if frame is None:
            return self.default_frame.copy()
            
        # 调整尺寸以匹配当前流分辨率
        if frame.shape[1] != self.stream_width or frame.shape[0] != self.stream_height:
            # 根据设置的调整方法选择跳采样或传统缩放
            if self.resize_method == 'subsampling':
                # 使用跳采样方法保持原始视角
                frame = self._resize_with_subsampling(frame, self.stream_width, self.stream_height)
            else:
                # 使用传统缩放方法
                # 根据当前帧率选择合适的插值方法
                current_fps = min(self.pose_stream_fps.get_fps(), self.emotion_stream_fps.get_fps())
                if current_fps < 10:
                    interpolation = cv2.INTER_NEAREST
                elif current_fps < 20:
                    interpolation = cv2.INTER_LINEAR
                else:
                    interpolation = cv2.INTER_AREA  # 高帧率时可以使用质量更好的插值方法
                    
                frame = cv2.resize(frame, (self.stream_width, self.stream_height), interpolation=interpolation)
        
        # 应用优化处理以提高压缩率
        if self.jpeg_quality < 70:  # 低质量下使用更多优化
            # 应用轻微的模糊以减少压缩伪影
            frame = cv2.GaussianBlur(frame, (3, 3), 0)
            
            # 可选：降低色彩深度
            if self.jpeg_quality < 50:
                frame = cv2.convertScaleAbs(frame, alpha=0.9, beta=10)  # 轻微提高亮度和对比度
        
        return frame
    
    def _adjust_stream_resolution(self, pose_fps, emotion_fps):
        """根据当前帧率动态调整流分辨率"""
        if not self.adaptive_resolution:
            return
            
        current_time = time.time()
        if (current_time - self.last_resolution_adjust_time) < RESOLUTION_ADJUST_INTERVAL:
            return
            
        stream_fps = min(pose_fps, emotion_fps)
        
        # 当流帧率过低时降低分辨率
        if stream_fps < FPS_THRESHOLD_LOW and self.current_resolution_index < len(STREAM_RESOLUTION_LEVELS) - 1:
            self.current_resolution_index += 1
            self.stream_width, self.stream_height = STREAM_RESOLUTION_LEVELS[self.current_resolution_index]
            print(f"流帧率过低 ({stream_fps:.1f} FPS)，降低分辨率至 {self.stream_width}x{self.stream_height}")
            self.last_resolution_adjust_time = current_time
            
            # 重置帧率计数器以便更准确测量新分辨率下的帧率
            self.pose_stream_fps.reset()
            self.emotion_stream_fps.reset()
        
        # 当流帧率足够高时尝试提高分辨率
        elif stream_fps > FPS_THRESHOLD_HIGH and self.current_resolution_index > 0:
            self.current_resolution_index -= 1
            self.stream_width, self.stream_height = STREAM_RESOLUTION_LEVELS[self.current_resolution_index]
            print(f"流帧率足够高 ({stream_fps:.1f} FPS)，提高分辨率至 {self.stream_width}x{self.stream_height}")
            self.last_resolution_adjust_time = current_time
            
            # 重置帧率计数器以便更准确测量新分辨率下的帧率
            self.pose_stream_fps.reset()
            self.emotion_stream_fps.reset()
    
    def _adjust_stream_quality(self, stream_fps):
        """根据当前帧率动态调整压缩质量"""
        if not self.adaptive_quality:
            return
            
        current_time = time.time()
        if (current_time - self.last_quality_adjust_time) < self.quality_adjust_interval:
            return
            
        # 计算平均压缩时间
        avg_compression_time = 0
        if self.performance_stats['compression_time']:
            avg_compression_time = sum(self.performance_stats['compression_time']) / len(self.performance_stats['compression_time'])
        
        # 当帧率过低且分辨率已经是最低时，降低JPEG质量
        if stream_fps < 10 and self.current_resolution_index >= len(STREAM_RESOLUTION_LEVELS) - 1:
            if self.jpeg_quality > 70:
                self.jpeg_quality = 70
                self.stream_params = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
                print(f"帧率低于10FPS，降低JPEG质量至 {self.jpeg_quality}")
            elif self.jpeg_quality > 50 and stream_fps < 7:
                self.jpeg_quality = 50
                self.stream_params = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
                print(f"帧率极低，进一步降低JPEG质量至 {self.jpeg_quality}")
            elif self.jpeg_quality > 30 and stream_fps < 5:
                self.jpeg_quality = 30
                self.stream_params = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
                print(f"帧率严重不足，将JPEG质量降至最低 {self.jpeg_quality}")
        
        # 当帧率恢复时提高JPEG质量
        elif stream_fps > 20:
            if self.jpeg_quality < 90:
                new_quality = min(90, self.jpeg_quality + 10)
                self.jpeg_quality = new_quality
                self.stream_params = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
                print(f"帧率恢复至 {stream_fps:.1f} FPS，提高JPEG质量至 {self.jpeg_quality}")
        
        # 压缩时间过长时降低质量
        elif avg_compression_time > 0.02 and self.jpeg_quality > 50:  # 如果压缩一帧超过20ms
            self.jpeg_quality = max(50, self.jpeg_quality - 10)
            self.stream_params = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
            print(f"压缩时间过长 ({avg_compression_time*1000:.1f}ms)，降低JPEG质量至 {self.jpeg_quality}")
        
        self.last_quality_adjust_time = current_time
    
    def get_pose_frame(self):
        """获取下一帧姿势分析帧"""
        try:
            frame = self.pose_frame_queue.get_nowait()
            self.pose_stream_fps.update()
            
            # 获取当前帧率
            pose_fps = self.pose_stream_fps.get_fps()
            emotion_fps = self.emotion_stream_fps.get_fps()
            
            # 动态调整流分辨率
            self._adjust_stream_resolution(pose_fps, emotion_fps)
            
            # 动态调整流质量
            self._adjust_stream_quality(min(pose_fps, emotion_fps))
            
            return frame
        except queue.Empty:
            # 队列为空，返回上一帧
            if self.debug:
                print("姿势分析帧队列为空，重复使用上一帧")
                
            # 仍然更新帧率计数器（如果重复使用上一帧也计入）
            self.pose_stream_fps.update()
            return self.last_pose_frame
    
    def get_emotion_frame(self):
        """获取下一帧情绪分析帧"""
        try:
            frame = self.emotion_frame_queue.get_nowait()
            self.emotion_stream_fps.update()
            return frame
        except queue.Empty:
            # 队列为空，返回上一帧
            if self.debug:
                print("情绪分析帧队列为空，重复使用上一帧")
                
            # 仍然更新帧率计数器（如果重复使用上一帧也计入）
            self.emotion_stream_fps.update()
            return self.last_emotion_frame
    
    def generate_pose_video_stream(self):
        """生成姿势分析视频流"""
        if not self.is_streaming:
            # 创建静态信息帧，只显示当前头部角度，不传输视频
            static_frame = self._create_info_frame("姿势检测", "视频流已禁用", "仅显示角度信息")
            
            # 压缩并编码为JPEG
            success, encoded_image = cv2.imencode('.jpg', static_frame, self.stream_params)
            if success:
                # 返回静态帧
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + encoded_image.tobytes() + b'\r\n')
                
                # 重要：只返回一帧，而不是持续生成帧
                return
            return
            
        while self.is_streaming:
            # 获取下一帧
            frame = self.get_pose_frame()
            
            # 添加帧率和质量信息
            fps = self.pose_stream_fps.get_fps()
            fps_text = f"FPS: {fps:.1f} Q:{self.jpeg_quality}"
            cv2.putText(frame, fps_text, (10, frame.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # 记录压缩开始时间
            compress_start = time.time()
            
            # 压缩并编码为JPEG
            success, encoded_image = cv2.imencode('.jpg', frame, self.stream_params)
            
            # 记录压缩时间
            compress_time = time.time() - compress_start
            self.performance_stats['compression_time'].append(compress_time)
            
            if not success:
                continue
            
            # 记录传输开始时间
            transmission_start = time.time()
                
            # 生成帧数据
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + encoded_image.tobytes() + b'\r\n'
            )
            
            # 记录传输时间
            transmission_time = time.time() - transmission_start
            self.performance_stats['transmission_time'].append(transmission_time)
            
            # 根据当前帧率动态调整帧间延迟，提高平滑度
            # 帧率低时可以减少延迟，帧率高时增加延迟避免过多帧传输
            if fps < 10:
                delay = 0.01  # 非常低的帧率，使用最小延迟
            elif fps < STREAM_FPS_TARGET:
                delay = 0.03  # 低于目标帧率，使用较小延迟
            else:
                # 帧率达到或超过目标时，调整延迟以匹配目标帧率
                delay = max(0.01, 1.0/STREAM_FPS_TARGET - compress_time - transmission_time)
                
            time.sleep(delay)
    
    def generate_emotion_video_stream(self):
        """生成情绪分析视频流"""
        if not self.is_streaming:
            # 创建静态信息帧，只显示当前情绪信息，不传输视频
            static_frame = self._create_info_frame("情绪检测", "视频流已禁用", "仅显示情绪状态")
            
            # 压缩并编码为JPEG
            success, encoded_image = cv2.imencode('.jpg', static_frame, self.stream_params)
            if success:
                # 返回静态帧
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + encoded_image.tobytes() + b'\r\n')
                
                # 重要：只返回一帧，而不是持续生成帧
                return
            return
            
        while self.is_streaming:
            # 获取下一帧
            frame = self.get_emotion_frame()
            
            # 添加帧率和质量信息
            fps = self.emotion_stream_fps.get_fps()
            fps_text = f"FPS: {fps:.1f} Q:{self.jpeg_quality}"
            cv2.putText(frame, fps_text, (10, frame.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # 记录压缩开始时间
            compress_start = time.time()
            
            # 压缩并编码为JPEG
            success, encoded_image = cv2.imencode('.jpg', frame, self.stream_params)
            
            # 记录压缩时间
            compress_time = time.time() - compress_start
            
            if not success:
                continue
            
            # 记录传输开始时间
            transmission_start = time.time()
                
            # 生成帧数据
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + encoded_image.tobytes() + b'\r\n'
            )
            
            # 记录传输时间
            transmission_time = time.time() - transmission_start
            
            # 根据当前帧率动态调整帧间延迟
            if fps < 10:
                delay = 0.01
            elif fps < STREAM_FPS_TARGET:
                delay = 0.03
            else:
                delay = max(0.01, 1.0/STREAM_FPS_TARGET - compress_time - transmission_time)
                
            time.sleep(delay)
    
    def get_fps_info(self):
        """获取视频流帧率信息"""
        return {
            'pose_stream_fps': round(self.pose_stream_fps.get_fps(), 1),
            'emotion_stream_fps': round(self.emotion_stream_fps.get_fps(), 1),
            'current_resolution': f"{self.stream_width}x{self.stream_height}",
            'jpeg_quality': self.jpeg_quality,
            'dropped_frames': self.performance_stats['dropped_frames'],
            'adaptive_mode': {
                'resolution': self.adaptive_resolution,
                'quality': self.adaptive_quality
            }
        }
    
    def set_resolution_mode(self, adaptive=True, resolution_index=None):
        """设置分辨率模式
        
        Args:
            adaptive: 是否启用自适应分辨率调整
            resolution_index: 如果不使用自适应模式，设置固定分辨率索引
        """
        self.adaptive_resolution = adaptive
        
        if resolution_index is not None and 0 <= resolution_index < len(STREAM_RESOLUTION_LEVELS):
            self.current_resolution_index = resolution_index
            self.stream_width, self.stream_height = STREAM_RESOLUTION_LEVELS[self.current_resolution_index]
            print(f"手动设置流分辨率为 {self.stream_width}x{self.stream_height}")
            
            # 重置帧率计数器以便更准确测量新分辨率下的帧率
            self.pose_stream_fps.reset()
            self.emotion_stream_fps.reset()
        
        return True
    
    def set_streaming_quality(self, quality):
        """设置流传输质量
        
        Args:
            quality: JPEG压缩质量，范围1-100
        """
        if 1 <= quality <= 100:
            self.jpeg_quality = quality
            self.stream_params = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
            print(f"设置JPEG压缩质量为 {self.jpeg_quality}")
            return True
        return False
    
    def set_quality_mode(self, adaptive=True):
        """设置质量调整模式
        
        Args:
            adaptive: 是否启用自适应质量调整
        """
        self.adaptive_quality = adaptive
        print(f"{'启用' if adaptive else '禁用'}自适应质量控制")
        return True
    
    def get_pose_frame_queue(self):
        """获取姿势帧队列（用于路由）"""
        print("DEBUG: 请求获取姿势帧队列")
        return self.pose_frame_queue
    
    def get_emotion_frame_queue(self):
        """获取情绪帧队列（用于路由）"""
        print("DEBUG: 请求获取情绪帧队列")
        return self.emotion_frame_queue
    
    def generate_video_frames(self, frame_queue, is_pose_stream=True):
        """生成视频流帧
        
        这是一个兼容方法，用于支持现有的路由调用
        
        Args:
            frame_queue: 帧队列（通常来自get_pose_frame_queue或get_emotion_frame_queue）
            is_pose_stream: 是否是姿势分析流（True）或情绪分析流（False）
        """
        print(f"DEBUG: 开始生成{'姿势' if is_pose_stream else '情绪'}视频流")
        
        if is_pose_stream:
            return self.generate_pose_video_stream()
        else:
            return self.generate_emotion_video_stream()
    
    def get_performance_stats(self):
        """获取性能统计信息"""
        # 计算平均压缩时间和传输时间
        avg_compression_ms = 0
        if self.performance_stats['compression_time']:
            avg_compression_ms = sum(self.performance_stats['compression_time']) / len(self.performance_stats['compression_time']) * 1000
        
        avg_transmission_ms = 0
        if self.performance_stats['transmission_time']:
            avg_transmission_ms = sum(self.performance_stats['transmission_time']) / len(self.performance_stats['transmission_time']) * 1000
        
        return {
            'dropped_frames': self.performance_stats['dropped_frames'],
            'avg_compression_time_ms': round(avg_compression_ms, 2),
            'avg_transmission_time_ms': round(avg_transmission_ms, 2)
        }
    
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

    # 添加控制视频流传输的方法
    def enable_streaming(self):
        """启用视频流传输"""
        if not self.is_streaming:
            self.is_streaming = True
            print("DEBUG: 视频流传输已启用")
            
            # 预热：确保last_raw_frame已初始化
            if self.last_raw_frame is None:
                # 如果没有原始帧，创建一个纯色的初始帧（不添加任何文本）
                temp_frame = np.ones((self.stream_height, self.stream_width, 3), dtype=np.uint8) * 220
                self.last_raw_frame = temp_frame
                print("DEBUG: 初始化last_raw_frame为纯色帧")
        
        return True
        
    def disable_streaming(self):
        """禁用视频流传输"""
        self.is_streaming = False
        print("DEBUG: 视频流传输已禁用")
        return True
        
    def get_streaming_status(self):
        """获取视频流传输状态"""
        return self.is_streaming
    
    def generate_raw_video_stream(self, resolution_param=None):
        """生成原始视频流（完全无处理）用于家长监护
        
        Args:
            resolution_param: 分辨率参数 ('high', 'medium', 'low') 或直接的(width, height)元组
        """
        # 设置分辨率
        original_width, original_height = self.stream_width, self.stream_height
        
        # 标准化分辨率参数
        if resolution_param:
            if isinstance(resolution_param, str):
                # 根据字符串参数设置分辨率
                resolution_map = {
                    'high': (720, 540),     # 720p equivalent for 4:3
                    'medium': (640, 480),   # 480p 标准
                    'low': (320, 240),      # 240p 低分辨率
                    '720p': (720, 540),
                    '480p': (640, 480),
                    '360p': (480, 360),
                    '240p': (320, 240)
                }
                if resolution_param in resolution_map:
                    self.stream_width, self.stream_height = resolution_map[resolution_param]
            elif isinstance(resolution_param, tuple) and len(resolution_param) == 2:
                # 直接使用提供的宽高
                self.stream_width, self.stream_height = resolution_param
        
        print(f"DEBUG: 家长监护视频流分辨率设置为 {self.stream_width}x{self.stream_height}")
        
        # 如果视频流未启动，返回纯色帧（不添加任何文本）
        if not self.is_streaming:
            # 创建纯色帧，不添加任何文本
            static_frame = np.ones((self.stream_height, self.stream_width, 3), dtype=np.uint8) * 220
            
            # 压缩并编码为JPEG
            success, encoded_image = cv2.imencode('.jpg', static_frame, self.stream_params)
            if success:
                # 返回静态帧
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + encoded_image.tobytes() + b'\r\n')
            
            # 恢复原始分辨率
            self.stream_width, self.stream_height = original_width, original_height
            return
        
        # 计数器，用于周期性检查视频流状态
        frame_count = 0
        
        # 主循环 - 只要流处于活动状态就继续生成帧
        while self.is_streaming:
            try:
                # 获取原始摄像头帧 - 完全不添加任何处理
                frame = None
                
                # 直接访问姿势监测器的摄像头
                try:
                    from app import posture_monitor
                    if posture_monitor and hasattr(posture_monitor, 'cap') and posture_monitor.cap.isOpened():
                        ret, raw_frame = posture_monitor.cap.read()
                        if ret and raw_frame is not None and raw_frame.size > 0:
                            frame = raw_frame.copy()  # 获取完全未处理的原始相机帧
                            # 保存为最新原始帧
                            self.last_raw_frame = frame.copy()
                except Exception as e:
                    print(f"ERROR: 直接访问摄像头失败: {str(e)}")
                
                # 如果直接获取失败，尝试使用最近保存的原始帧
                if frame is None and hasattr(self, 'last_raw_frame') and self.last_raw_frame is not None:
                    frame = self.last_raw_frame.copy()
                
                # 如果没有有效的原始帧，使用纯色帧
                if frame is None or frame.size == 0:
                    frame = np.ones((self.stream_height, self.stream_width, 3), dtype=np.uint8) * 220
                
                # 仅调整分辨率，不添加任何文本或叠加
                if frame.shape[1] != self.stream_width or frame.shape[0] != self.stream_height:
                    try:
                        frame = cv2.resize(frame, (self.stream_width, self.stream_height))
                    except Exception as e:
                        print(f"ERROR: 调整帧大小时出错: {str(e)}")
                        # 使用纯色帧
                        frame = np.ones((self.stream_height, self.stream_width, 3), dtype=np.uint8) * 220
                
                # 压缩并编码为JPEG - 使用高质量设置以保持原始画面质量
                stream_params = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
                success, encoded_image = cv2.imencode('.jpg', frame, stream_params)
                if success:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + encoded_image.tobytes() + b'\r\n')
                else:
                    print("WARNING: 帧编码失败，使用备用帧")
                    # 使用纯色备用帧
                    backup_frame = np.ones((self.stream_height, self.stream_width, 3), dtype=np.uint8) * 200
                    success, backup_encoded = cv2.imencode('.jpg', backup_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                    if success:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + backup_encoded.tobytes() + b'\r\n')
                
                # 每隔50帧检查一次视频流状态
                frame_count += 1
                if frame_count % 50 == 0:
                    if not self.is_streaming:
                        print("DEBUG: 视频流已停止，结束流生成")
                        break
                
                # 控制帧率 - 基于当前系统性能动态调整
                try:
                    # 低性能设备使用较低帧率
                    target_fps = min(STREAM_FPS_TARGET, 15)  # 最高15fps以减轻系统负担
                    sleep_time = max(1.0 / target_fps - 0.01, 0.01)  # 确保至少有一些延迟
                    time.sleep(sleep_time)
                except:
                    # 出错时使用安全的默认值
                    time.sleep(0.067)  # 约15fps
                
            except Exception as e:
                print(f"ERROR: 生成原始视频流出错: {str(e)}")
                # 发送纯色错误帧
                error_frame = np.ones((self.stream_height, self.stream_width, 3), dtype=np.uint8) * 180
                
                try:
                    # 使用高质量设置以确保可以编码
                    success, encoded_image = cv2.imencode('.jpg', error_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                    if success:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + encoded_image.tobytes() + b'\r\n')
                except:
                    # 如果连错误帧都无法编码，使用最简单的空白帧
                    try:
                        blank_frame = np.ones((240, 320, 3), dtype=np.uint8) * 220
                        success, encoded_image = cv2.imencode('.jpg', blank_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                        if success:
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + encoded_image.tobytes() + b'\r\n')
                    except:
                        pass
                
                # 错误后等待较长时间再重试
                time.sleep(2)
        
        # 恢复原始分辨率设置
        self.stream_width, self.stream_height = original_width, original_height
        print("DEBUG: 原始视频流生成结束，已恢复分辨率设置")