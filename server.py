from flask import Flask, render_template, jsonify, request, Response, stream_with_context
from serial_handler import SerialHandler
import mysql.connector
from datetime import datetime
import pytz
from config import DB_CONFIG, OPEN_HOST, SERIAL_BAUDRATE
import atexit # 用于注册程序退出时的清理函数
import json
import threading
import queue
import cv2
import numpy as np
import base64
import os
import sys
import time  # 添加time模块导入

# 将父目录添加到系统路径，以便导入posture_analysis模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 从姿势分析项目导入所需的类和变量
try:
    from posture_analysis.realtime_posture_analysis import (
        PostureMonitor, EmotionAnalyzer, EmotionState,
        EMOTION_SMOOTHING_WINDOW, MOUTH_OPEN_RATIO_THRESHOLD,
        EYE_OPEN_RATIO_THRESHOLD, BROW_DOWN_THRESHOLD,
        CAMERA_WIDTH, CAMERA_HEIGHT, PROCESS_WIDTH, PROCESS_HEIGHT
    )
except ImportError as e:
    print(f"导入姿势分析模块失败：{str(e)}")
    # 创建一个占位符类，用于在导入失败时避免程序崩溃
    class PostureMonitor:
        def __init__(self):
            print("警告：姿势分析模块未导入，功能受限")
        
        def start(self):
            pass
            
        def stop(self):
            pass
            
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

app = Flask(__name__)

# 创建事件队列，用于SSE (Server-Sent Events)
frame_queue = queue.Queue(maxsize=100)

# 姿势和情绪分析参数
posture_params = {
    'emotion_smoothing_window': EMOTION_SMOOTHING_WINDOW,
    'mouth_open_ratio_threshold': MOUTH_OPEN_RATIO_THRESHOLD,
    'eye_open_ratio_threshold': EYE_OPEN_RATIO_THRESHOLD,
    'brow_down_threshold': BROW_DOWN_THRESHOLD
}

# 创建视频流队列
pose_frame_queue = queue.Queue(maxsize=10)
emotion_frame_queue = queue.Queue(maxsize=10)

# 存储姿势分析系统实例
posture_monitor = None
posture_monitor_thread = None
is_posture_monitor_running = False

# 姿势分析结果队列
pose_result_queue = queue.Queue(maxsize=10)

# 初始化串口处理器
serial_handler = None
try:
    serial_handler = SerialHandler(port=None, baudrate=SERIAL_BAUDRATE)
    if serial_handler and serial_handler.port: # 确保找到了端口再启动监控
        serial_handler.start_monitoring()
        
        # 添加帧数据监控，收到数据时自动保存到数据库并添加到事件队列
        def frame_callback(frame_data):
            try:
                # 保存到数据库
                save_frame_to_db(frame_data)
                # 添加到事件队列以供前端获取
                if frame_queue.full():
                    try:
                        # 队列满时，移除最旧的数据
                        frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                frame_queue.put(frame_data)
            except Exception as e:
                print(f"处理帧数据回调时出错: {str(e)}")
        
        # 启动帧监控
        serial_handler.start_frame_monitor(callback=frame_callback)
except Exception as e:
    print(f"警告：串口处理器初始化失败 - {str(e)}")
    serial_handler = None # 确保失败时 handler 为 None

# 自定义的PostureMonitor类，适配Web服务器使用
class WebPostureMonitor:
    """适配Web服务的姿势监测器"""
    def __init__(self):
        self.cap = None
        self.pose = None
        self.emotion_analyzer = None
        self.is_running = False
        self.thread = None
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
    
    def start(self):
        """启动姿势分析线程"""
        if self.is_running:
            return False
        
        try:
            # 导入所需模块
            import mediapipe as mp
            import cv2
            from posture_analysis.realtime_posture_analysis import (
                mp_pose, mp_face_mesh, check_occlusion, calculate_head_angle,
                EmotionAnalyzer, EmotionState, VISIBILITY_THRESHOLD, HEAD_ANGLE_THRESHOLD,
                OCCLUSION_FRAMES_THRESHOLD, CLEAR_FRAMES_THRESHOLD
            )
            
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
        for i in range(10):  # 尝试前10个摄像头设备
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
                cap.set(cv2.CAP_PROP_FPS, 30)
                print(f"摄像头初始化成功: /dev/video{i}")
                return cap
            cap.release()
        print("未检测到可用摄像头设备")
        return None
    
    def _process_frames(self):
        """处理视频帧的主循环"""
        from posture_analysis.realtime_posture_analysis import (
            check_occlusion, calculate_head_angle, mp_drawing, mp_drawing_styles,
            OCCLUSION_FRAMES_THRESHOLD, CLEAR_FRAMES_THRESHOLD
        )
        
        while self.is_running and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if not ret:
                    print("无法读取摄像头帧")
                    time.sleep(0.5)
                    continue
                
                # 调整帧尺寸进行处理
                processed_frame = cv2.resize(frame, (PROCESS_WIDTH, PROCESS_HEIGHT))
                pose_frame = processed_frame.copy()
                emotion_frame = processed_frame.copy()
                
                # 处理姿势
                pose_results = self._process_pose(pose_frame)
                
                # 处理情绪
                emotion_results = self._process_emotion(emotion_frame)
                
                # 将处理后的帧放入队列供Web端点使用
                if not pose_frame_queue.full():
                    pose_frame_queue.put(pose_results['display_frame'])
                
                if not emotion_frame_queue.full():
                    emotion_frame_queue.put(emotion_results['display_frame'])
                
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
                
                time.sleep(0.03)  # 限制处理速率，约30fps
            except Exception as e:
                print(f"处理帧异常: {str(e)}")
                time.sleep(0.5)
    
    def _process_pose(self, frame):
        """处理姿势检测"""
        from posture_analysis.realtime_posture_analysis import (
            check_occlusion, calculate_head_angle, mp_drawing, mp_drawing_styles, mp_pose,
            OCCLUSION_FRAMES_THRESHOLD, CLEAR_FRAMES_THRESHOLD, HEAD_ANGLE_THRESHOLD
        )
        
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
        from posture_analysis.realtime_posture_analysis import mp_drawing, mp_face_mesh, mp_drawing_styles
        
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
            
            return True
        except Exception as e:
            print(f"更新情绪参数失败: {str(e)}")
            return False

def save_frame_to_db(frame_data):
    """将接收到的帧数据保存到数据库"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 格式化帧数据以便存储
        sent_info = "自动接收的数据帧"
        received_info = json.dumps(frame_data)
        status = "success"
        message = "自动接收到数据帧"
        
        sql = """INSERT INTO serial_records 
                (sent_data, received_data, status, message, timestamp) 
                VALUES (%s, %s, %s, %s, %s)"""
        current_time = datetime.now(pytz.UTC)
        values = (sent_info, received_info, status, message, current_time)
        
        cursor.execute(sql, values)
        conn.commit()
        
        cursor.close()
        conn.close()
        print(f"帧数据已保存到数据库: {received_info}")
    except Exception as e:
        print(f"保存帧数据到数据库时出错: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_data', methods=['POST'])
def send_data():
    data = request.json.get('data')
    response = "未连接"
    status = "error"
    message = "串口未连接"
    
    if not serial_handler or not serial_handler.is_connected():
        message = "串口未连接"
    else:
        # 尝试发送数据到串口
        if not serial_handler.send_data(data):
            message = "发送数据失败"
        else:
            # 接收串口响应
            response = serial_handler.read_data()
            status = "success"
            message = "发送成功"
    
    # 无论成功失败都保存到数据库
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        sql = """INSERT INTO serial_records 
                (sent_data, received_data, status, message, timestamp) 
                VALUES (%s, %s, %s, %s, %s)"""
        # 使用UTC时间
        current_time = datetime.now(pytz.UTC)
        values = (data, response, status, message, current_time)
        
        cursor.execute(sql, values)
        conn.commit()
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"数据库写入失败: {str(e)}")
        return jsonify({'status': 'error', 'message': '数据库写入失败'})
    
    return jsonify({
        'status': status,
        'message': message,
        'response': response
    })

@app.route('/get_history')
def get_history():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    offset = (page - 1) * per_page
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 获取总记录数
        cursor.execute("SELECT COUNT(*) as total FROM serial_records")
        total = cursor.fetchone()['total']
        
        # 获取分页数据 - 使用简单的倒序查询
        query = """
            SELECT id, sent_data, received_data, status, message, timestamp
            FROM serial_records
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (per_page, offset))
        records = cursor.fetchall()
        
        # 计算记录编号
        total_pages = (total + per_page - 1) // per_page
        for i, record in enumerate(records):
            record['record_number'] = total - offset - i
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'records': records,
            'total': total,
            'current_page': page,
            'per_page': per_page,
            'total_pages': total_pages
        })
    except Exception as e:
        print(f"获取历史记录失败: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/clear_history', methods=['POST'])
def clear_history():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("TRUNCATE TABLE serial_records")
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'status': 'success', 'message': '历史记录已清空'})
    except Exception as e:
        print(f"清空历史记录失败: {str(e)}")
        return jsonify({'status': 'error', 'message': '清空历史记录失败'})

@app.route('/send_frame', methods=['POST'])
def send_frame():
    """发送按照帧格式打包的yaw和pitch数据"""
    try:
        # 获取请求参数
        data = request.json
        find_bool = data.get('find_bool', False)
        yaw = data.get('yaw', 0.0)
        pitch = data.get('pitch', 0.0)
        
        response_data = "未连接"
        status = "error"
        message = "串口未连接"
        
        if not serial_handler or not serial_handler.is_connected():
            message = "串口未连接"
        else:
            # 发送帧格式数据
            if serial_handler.send_yaw_pitch(find_bool, yaw, pitch):
                # 尝试读取响应帧
                response_frame = serial_handler.read_frame()
                if response_frame:
                    response_data = str(response_frame)
                    status = "success"
                    message = "帧数据发送成功，收到响应"
                else:
                    response_data = "无响应"
                    status = "success"
                    message = "帧数据发送成功，未收到响应"
            else:
                message = "发送帧数据失败"
        
        # 保存到数据库
        try:
            sent_info = f"yaw:{yaw}, pitch:{pitch}, find_bool:{find_bool}"
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            sql = """INSERT INTO serial_records 
                    (sent_data, received_data, status, message, timestamp) 
                    VALUES (%s, %s, %s, %s, %s)"""
            current_time = datetime.now(pytz.UTC)
            values = (sent_info, response_data, status, message, current_time)
            
            cursor.execute(sql, values)
            conn.commit()
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"数据库写入失败: {str(e)}")
        
        return jsonify({
            'status': status,
            'message': message,
            'response': response_data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"处理请求时出错: {str(e)}",
            'response': '发送失败'
        })

@app.route('/read_frame', methods=['GET'])
def read_frame_api():
    """读取一帧数据并解析"""
    try:
        status = "error"
        message = "串口未连接"
        frame_data = None
        
        if not serial_handler or not serial_handler.is_connected():
            message = "串口未连接"
        else:
            # 读取帧数据
            frame_data = serial_handler.read_frame()
            if frame_data:
                status = "success"
                message = "成功读取帧数据"
            else:
                message = "未读取到帧数据"
        
        return jsonify({
            'status': status,
            'message': message,
            'frame_data': frame_data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"读取帧数据时出错: {str(e)}",
            'frame_data': None
        })

@app.route('/frame_events')
def frame_events():
    """SSE端点，向前端推送接收到的帧数据"""
    def event_stream():
        while True:
            try:
                # 从队列获取最新数据，最多等待30秒
                frame_data = frame_queue.get(timeout=30)
                # 发送事件
                yield f"data: {json.dumps(frame_data)}\n\n"
            except queue.Empty:
                # 超时时发送心跳保持连接
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
            except Exception as e:
                print(f"发送事件流时出错: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )

@app.route('/start_posture_analysis', methods=['POST'])
def start_posture_analysis():
    """启动姿势分析系统"""
    global posture_monitor
    
    try:
        if (posture_monitor and posture_monitor.is_running):
            return jsonify({
                'status': 'success',
                'message': '姿势分析系统已经在运行中'
            })
        
        if not posture_monitor:
            posture_monitor = WebPostureMonitor()
        
        success = posture_monitor.start()
        
        if (success):
            return jsonify({
                'status': 'success',
                'message': '姿势分析系统启动成功'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '启动姿势分析系统失败'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'启动姿势分析系统出错: {str(e)}'
        })

@app.route('/stop_posture_analysis', methods=['POST'])
def stop_posture_analysis():
    """停止姿势分析系统"""
    global posture_monitor
    
    try:
        if not posture_monitor or not posture_monitor.is_running:
            return jsonify({
                'status': 'success',
                'message': '姿势分析系统未运行'
            })
        
        success = posture_monitor.stop()
        
        if success:
            return jsonify({
                'status': 'success',
                'message': '姿势分析系统已停止'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '停止姿势分析系统失败'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'停止姿势分析系统出错: {str(e)}'
        })

@app.route('/get_pose_status')
def get_pose_status():
    """获取当前姿势分析状态"""
    global posture_monitor
    
    try:
        if not posture_monitor:
            return jsonify({
                'status': 'error',
                'message': '姿势分析系统未初始化',
                'is_running': False,
                'pose_data': None,
                'emotion_data': None
            })
        
        return jsonify({
            'status': 'success',
            'message': '获取姿势分析状态成功',
            'is_running': posture_monitor.is_running,
            'pose_data': posture_monitor.pose_result,
            'emotion_data': posture_monitor.emotion_result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取姿势分析状态出错: {str(e)}',
            'is_running': False,
            'pose_data': None,
            'emotion_data': None
        })

@app.route('/get_emotion_params')
def get_emotion_params():
    """获取情绪分析参数"""
    global posture_params
    
    try:
        return jsonify({
            'status': 'success',
            'params': posture_params
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取情绪分析参数出错: {str(e)}'
        })

@app.route('/update_emotion_params', methods=['POST'])
def update_emotion_params():
    """更新情绪分析参数"""
    global posture_monitor, posture_params
    
    try:
        params = request.json
        
        # 验证参数
        if 'emotion_smoothing_window' in params:
            value = int(params['emotion_smoothing_window'])
            if 1 <= value <= 30:
                posture_params['emotion_smoothing_window'] = value
            else:
                return jsonify({
                    'status': 'error',
                    'message': '情绪平滑窗口参数无效，应在1-30之间'
                })
        
        if 'mouth_open_ratio_threshold' in params:
            value = float(params['mouth_open_ratio_threshold'])
            if 0.1 <= value <= 1.0:
                posture_params['mouth_open_ratio_threshold'] = value
            else:
                return jsonify({
                    'status': 'error',
                    'message': '嘴部开合比阈值无效，应在0.1-1.0之间'
                })
        
        if 'eye_open_ratio_threshold' in params:
            value = float(params['eye_open_ratio_threshold'])
            if 0.05 <= value <= 0.5:
                posture_params['eye_open_ratio_threshold'] = value
            else:
                return jsonify({
                    'status': 'error',
                    'message': '眼睛开合比阈值无效，应在0.05-0.5之间'
                })
        
        if 'brow_down_threshold' in params:
            value = float(params['brow_down_threshold'])
            if 0.01 <= value <= 0.2:
                posture_params['brow_down_threshold'] = value
            else:
                return jsonify({
                    'status': 'error',
                    'message': '眉毛下压阈值无效，应在0.01-0.2之间'
                })
        
        # 如果有运行中的分析器，同步更新参数
        if posture_monitor and posture_monitor.is_running and posture_monitor.emotion_analyzer:
            posture_monitor.emotion_analyzer.emotion_smoothing_window = posture_params['emotion_smoothing_window']
        
        return jsonify({
            'status': 'success',
            'message': '情绪分析参数更新成功',
            'params': posture_params
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'更新情绪分析参数出错: {str(e)}'
        })

def generate_video_frames(frame_queue):
    """生成视频帧序列"""
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
            empty_frame = np.zeros((PROCESS_HEIGHT, PROCESS_WIDTH, 3), dtype=np.uint8)
            text = "等待视频流..."
            cv2.putText(empty_frame, text, (10, PROCESS_HEIGHT//2), 
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

@app.route('/video_pose')
def video_pose():
    """姿势检测视频流端点"""
    return Response(
        generate_video_frames(pose_frame_queue),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/video_emotion')
def video_emotion():
    """情绪分析视频流端点"""
    return Response(
        generate_video_frames(emotion_frame_queue),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

def init_database():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS serial_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sent_data TEXT,
                received_data TEXT,
                status VARCHAR(50),
                message TEXT,
                timestamp DATETIME(6)
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("Database table initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {str(e)}")

# 确保在程序退出时停止监控和关闭串口
def cleanup():
    print("正在关闭服务器...")
    if serial_handler:
        # 停止帧监控
        if hasattr(serial_handler, '_frame_monitor_active'):
            serial_handler.stop_frame_monitor()
        # 停止连接监控
        serial_handler.stop_monitoring()
        serial_handler.close()

atexit.register(cleanup)

if __name__ == '__main__':
    # 初始化姿势分析系统
    posture_monitor = WebPostureMonitor()
    
    init_database()  # Initialize database table
    # 使用配置文件中定义的端口
    try:
        from config import OPEN_PORT
        port = OPEN_PORT
    except ImportError:
        port = 5000
    print(f"Starting server on {OPEN_HOST}:{port}...")
    # 注意：Flask 在 debug=True 模式下会启动两个进程，atexit 可能会被调用两次
    # 在生产环境中应使用 Gunicorn 或 uWSGI 等 WSGI 服务器
    app.run(host=OPEN_HOST, port=port, debug=True, use_reloader=False) # 禁用 reloader 避免监控线程问题