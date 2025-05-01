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
    
    def start(self):
        """启动姿势分析线程"""
        if self.is_running or not POSTURE_MODULE_AVAILABLE:
            return False
        
        try:
            # 初始化摄像头
            self.cap = self._init_camera()
            if not self.cap:
                print("无法初始化摄像头")
                return False
            
            # 初始化姿势检测
            self.pose = mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5
            )
            
            # 初始化情绪分析器，使用全局参数设置
            self.emotion_analyzer = EmotionAnalyzer()
            self.emotion_analyzer.emotion_smoothing_window = posture_params['emotion_smoothing_window']
            
            # 计数器和状态变量
            self.occlusion_counter = 0
            self.clear_counter = 0
            self.last_valid_angle = None
            
            # 启动处理线程
            self.is_running = True
            self.thread = threading.Thread(target=self._process_frames, daemon=True)
            self.thread.start()
            
            return True
        except Exception as e:
            print(f"启动姿势分析失败: {str(e)}")
            self.stop()
            return False
    
    def stop(self):
        """停止姿势分析线程"""
        self.is_running = False
        
        if self.thread:
            try:
                self.thread.join(timeout=2.0)
            except:
                pass
            self.thread = None
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        if self.pose:
            self.pose.close()
            self.pose = None
        
        if self.emotion_analyzer and hasattr(self.emotion_analyzer, 'face_mesh'):
            self.emotion_analyzer.face_mesh.close()
        
        self.emotion_analyzer = None
        return True
    
    def _init_camera(self):
        """初始化摄像头设备"""
        print("开始初始化摄像头...")
        
        # 首先尝试使用指定的摄像头 (Bus 008 Device 006: ID 0c45:6366)
        # 在Linux上，摄像头通常映射为/dev/videoX设备
        
        # 1. 检查可用的视频设备
        import glob
        import subprocess
        import re
        
        available_devices = glob.glob('/dev/video*')
        print(f"系统中找到以下视频设备: {available_devices}")
        
        # 2. 获取详细设备信息
        try:
            result = subprocess.run(['v4l2-ctl', '--list-devices'], capture_output=True, text=True)
            print(f"摄像头设备列表:\n{result.stdout}")
        except:
            print("无法使用v4l2-ctl列出设备，将尝试其他方法")
        
        # 3. 尝试不同的方法来打开摄像头
        # 方法1: 直接尝试特定设备
        specific_devices = [6, 0, 2, 4, 8] # 首先尝试设备6(Bus 008中的设备), 然后是其他常见设备
        for device_num in specific_devices:
            try:
                device_path = f"/dev/video{device_num}"
                print(f"尝试打开摄像头: {device_path}")
                cap = cv2.VideoCapture(device_num)
                if cap.isOpened():
                    # 设置参数
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    # 读取一帧测试是否正常工作
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None and test_frame.size > 0:
                        print(f"摄像头初始化成功: {device_path}")
                        return cap
                    else:
                        print(f"摄像头能打开但无法读取帧: {device_path}")
                        cap.release()
                else:
                    print(f"无法打开摄像头: {device_path}")
            except Exception as e:
                print(f"尝试打开 {device_num} 时出错: {str(e)}")
        
        # 方法2: 尝试通过GStreamer打开设备
        try:
            for device_num in specific_devices:
                device_path = f"/dev/video{device_num}"
                print(f"尝试使用GStreamer打开摄像头: {device_path}")
                gst_str = f"v4l2src device={device_path} ! video/x-raw,width={CAMERA_WIDTH},height={CAMERA_HEIGHT} ! videoconvert ! appsink"
                cap = cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
                if cap.isOpened():
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None and test_frame.size > 0:
                        print(f"GStreamer摄像头初始化成功: {device_path}")
                        return cap
                    else:
                        print(f"GStreamer摄像头能打开但无法读取帧: {device_path}")
                        cap.release()
                else:
                    print(f"无法通过GStreamer打开摄像头: {device_path}")
        except Exception as e:
            print(f"尝试使用GStreamer时出错: {str(e)}")
        
        # 方法3: 最后尝试常规的OpenCV循环
        print("尝试查找所有可能的摄像头设备...")
        for i in range(10):  # 尝试前10个摄像头设备
            try:
                print(f"尝试打开摄像头索引: {i}")
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    # 测试是否能读取帧
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None and test_frame.size > 0:
                        print(f"成功找到并初始化摄像头: index={i}")
                        return cap
                    else:
                        print(f"摄像头 {i} 能打开但无法读取帧")
                        cap.release()
                else:
                    print(f"无法打开摄像头索引: {i}")
            except Exception as e:
                print(f"尝试摄像头 {i} 时出错: {str(e)}")
            
            if cap.isOpened():
                cap.release()
        
        print("警告: 未检测到可用摄像头设备")
        return None
    
    def _process_frames(self):
        """处理视频帧的主循环"""
        if not POSTURE_MODULE_AVAILABLE:
            return
        
        last_fps_update_time = time.time()
        
        while self.is_running and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if not ret:
                    print("无法读取摄像头帧")
                    time.sleep(0.5)
                    continue
                
                # 更新捕获帧率
                self.capture_fps.update()
                
                # 调整帧尺寸进行处理
                processed_frame = cv2.resize(frame, (PROCESS_WIDTH, PROCESS_HEIGHT))
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
                
                # 每秒更新一次帧率信息
                current_time = time.time()
                if current_time - last_fps_update_time >= 1.0:
                    self.fps_info = {
                        'capture_fps': round(self.capture_fps.get_fps(), 1),
                        'pose_process_fps': round(self.pose_process_fps.get_fps(), 1),
                        'emotion_process_fps': round(self.emotion_process_fps.get_fps(), 1)
                    }
                    last_fps_update_time = current_time
                
                time.sleep(0.03)  # 限制处理速率，约30fps
            except Exception as e:
                print(f"处理帧异常: {str(e)}")
                time.sleep(0.5)
    
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