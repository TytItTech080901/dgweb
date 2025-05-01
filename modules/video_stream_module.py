"""
视频流模块 - 负责处理视频流相关功能
"""
import cv2
import numpy as np
import queue
import time

class VideoStreamHandler:
    """视频流处理器类，封装视频流相关的功能"""
    
    def __init__(self, process_width=320, process_height=240):
        """初始化视频流处理器"""
        self.process_width = process_width
        self.process_height = process_height
        # 创建视频帧队列
        self.pose_frame_queue = queue.Queue(maxsize=10)
        self.emotion_frame_queue = queue.Queue(maxsize=10)
    
    def generate_video_frames(self, frame_queue):
        """生成视频帧序列，用于Flask的视频流响应"""
        while True:
            try:
                # 尝试从队列获取帧，设置超时避免永久阻塞
                frame = frame_queue.get(timeout=1.0)
                
                # 编码图像为JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    continue
                    
                # 转换为HTTP响应格式
                frame_data = buffer.tobytes()
                yield (b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
            
            except queue.Empty:
                # 队列为空时发送占位帧，避免连接断开
                # 创建一个简单的黑色帧
                empty_frame = np.zeros((self.process_height, self.process_width, 3), dtype=np.uint8)
                text = "等待视频流..."
                cv2.putText(empty_frame, text, (10, self.process_height//2), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                ret, buffer = cv2.imencode('.jpg', empty_frame)
                if ret:
                    frame_data = buffer.tobytes()
                    yield (b'--frame\r\n'
                          b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
                
                # 短暂等待，避免过度消耗CPU
                time.sleep(0.5)
            
            except Exception as e:
                print(f"生成视频流异常: {str(e)}")
                time.sleep(0.5)
    
    def get_pose_frame_queue(self):
        """获取姿势分析帧队列"""
        return self.pose_frame_queue
    
    def get_emotion_frame_queue(self):
        """获取情绪分析帧队列"""
        return self.emotion_frame_queue
        
    def add_pose_frame(self, frame):
        """添加一帧姿势分析结果到队列"""
        if self.pose_frame_queue.full():
            try:
                self.pose_frame_queue.get_nowait()  # 删除旧数据
            except queue.Empty:
                pass
        self.pose_frame_queue.put(frame)
    
    def add_emotion_frame(self, frame):
        """添加一帧情绪分析结果到队列"""
        if self.emotion_frame_queue.full():
            try:
                self.emotion_frame_queue.get_nowait()  # 删除旧数据
            except queue.Empty:
                pass
        self.emotion_frame_queue.put(frame)