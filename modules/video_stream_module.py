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
        
        # 流状态
        self.is_streaming = True
        
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