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

# 自适应分辨率配置
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

class VideoStreamHandler:
    """视频流处理类"""
    def __init__(self):
        """初始化视频流处理器"""
        # 初始化队列
        self.pose_frame_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
        self.emotion_frame_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
        
        # 默认空帧（灰色）
        self.default_frame = self._create_default_frame()
        
        # 最后一帧（用于无帧时重复输出）
        self.last_pose_frame = self.default_frame.copy()
        self.last_emotion_frame = self.default_frame.copy()
        
        # 当前流分辨率（可动态调整）
        self.stream_width = DEFAULT_STREAM_WIDTH
        self.stream_height = DEFAULT_STREAM_HEIGHT
        self.current_resolution_index = 1  # 从中等分辨率开始
        self.last_resolution_adjust_time = 0
        self.adaptive_resolution = True  # 是否启用自适应分辨率
        
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
                except queue.Empty:
                    pass
                    
            try:
                self.pose_frame_queue.put_nowait(resized_frame)
            except queue.Full:
                # 队列已满，忽略
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
                except queue.Empty:
                    pass
                    
            try:
                self.emotion_frame_queue.put_nowait(resized_frame)
            except queue.Full:
                # 队列已满，忽略
                pass
    
    def _prepare_frame_for_streaming(self, frame):
        """准备帧用于流传输（调整尺寸）"""
        if frame is None:
            return self.default_frame.copy()
            
        # 调整尺寸以匹配当前流分辨率
        if frame.shape[1] != self.stream_width or frame.shape[0] != self.stream_height:
            frame = cv2.resize(frame, (self.stream_width, self.stream_height))
        
        # 如果需要进一步的图像处理，可以在这里添加
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
            
            # 如果帧率非常低，尝试降低JPEG质量以提高传输速度
            if stream_fps < 10 and self.jpeg_quality > 70:
                self.jpeg_quality = 70
                self.stream_params = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
                print(f"帧率极低，降低JPEG质量至 {self.jpeg_quality}")
        
        # 当流帧率足够高时尝试提高分辨率
        elif stream_fps > FPS_THRESHOLD_HIGH and self.current_resolution_index > 0:
            self.current_resolution_index -= 1
            self.stream_width, self.stream_height = STREAM_RESOLUTION_LEVELS[self.current_resolution_index]
            print(f"流帧率足够高 ({stream_fps:.1f} FPS)，提高分辨率至 {self.stream_width}x{self.stream_height}")
            self.last_resolution_adjust_time = current_time
            
            # 恢复JPEG质量
            if self.jpeg_quality < 90:
                self.jpeg_quality = 90
                self.stream_params = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
                print(f"帧率充足，恢复JPEG质量至 {self.jpeg_quality}")
    
    def get_pose_frame(self):
        """获取下一帧姿势分析帧"""
        try:
            frame = self.pose_frame_queue.get_nowait()
            self.pose_stream_fps.update()
            
            # 动态调整流分辨率
            self._adjust_stream_resolution(
                self.pose_stream_fps.get_fps(),
                self.emotion_stream_fps.get_fps()
            )
            
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
            
            # 添加帧率信息
            fps = self.pose_stream_fps.get_fps()
            cv2.putText(frame, f"Stream FPS: {fps:.1f}", (10, frame.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # 压缩并编码为JPEG
            success, encoded_image = cv2.imencode('.jpg', frame, self.stream_params)
            
            if not success:
                continue
                
            # 生成帧数据
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + encoded_image.tobytes() + b'\r\n'
            )
            
            # 控制帧率，避免过快传输
            time.sleep(max(0, 1.0/STREAM_FPS_TARGET - 0.01))
    
    def generate_emotion_video_stream(self):
        """生成情绪分析视频流"""
        while self.is_streaming:
            # 获取下一帧
            frame = self.get_emotion_frame()
            
            # 添加帧率信息
            fps = self.emotion_stream_fps.get_fps()
            cv2.putText(frame, f"Stream FPS: {fps:.1f}", (10, frame.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # 压缩并编码为JPEG
            success, encoded_image = cv2.imencode('.jpg', frame, self.stream_params)
            
            if not success:
                continue
                
            # 生成帧数据
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + encoded_image.tobytes() + b'\r\n'
            )
            
            # 控制帧率，避免过快传输
            time.sleep(max(0, 1.0/STREAM_FPS_TARGET - 0.01))
    
    def get_fps_info(self):
        """获取视频流帧率信息"""
        return {
            'pose_stream_fps': self.pose_stream_fps.get_fps(),
            'emotion_stream_fps': self.emotion_stream_fps.get_fps()
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