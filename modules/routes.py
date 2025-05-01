"""
路由模块 - 处理所有API路由请求
"""
from flask import Blueprint, render_template, jsonify, request, Response, stream_with_context
import json
import queue
from modules.database_module import save_record_to_db, get_history_records, clear_history
from modules.posture_module import WebPostureMonitor, posture_params

# 创建蓝图
routes_bp = Blueprint('routes', __name__)

# 全局变量
posture_monitor = None
video_stream_handler = None
serial_handler = None

# 设置依赖服务
def setup_services(posture_monitor_instance=None, video_stream_instance=None, serial_handler_instance=None):
    """设置各个服务模块实例"""
    global posture_monitor, video_stream_handler, serial_handler
    posture_monitor = posture_monitor_instance
    video_stream_handler = video_stream_instance
    serial_handler = serial_handler_instance

# 路由：首页
@routes_bp.route('/')
def index():
    return render_template('index.html')

# 路由：发送文本数据
@routes_bp.route('/send_data', methods=['POST'])
def send_data():
    data = request.json.get('data')
    response = "未连接"
    status = "error"
    message = "串口未连接"
    
    if not serial_handler or not serial_handler.is_connected():
        message = "串口未连接"
    else:
        # 尝试发送数据到串口
        response, message = serial_handler.send_data(data)
        if response:
            status = "success"
    
    # 无论成功失败都保存到数据库
    save_record_to_db(data, response, status, message)
    
    return jsonify({
        'status': status,
        'message': message,
        'response': response
    })

# 路由：获取历史记录
@routes_bp.route('/get_history')
def get_history():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    result = get_history_records(page, per_page)
    return jsonify(result)

# 路由：清空历史记录
@routes_bp.route('/clear_history', methods=['POST'])
def clear_history_route():
    if clear_history():
        return jsonify({'status': 'success', 'message': '历史记录已清空'})
    else:
        return jsonify({'status': 'error', 'message': '清空历史记录失败'})

# 路由：发送帧数据
@routes_bp.route('/send_frame', methods=['POST'])
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
            response_frame, message = serial_handler.send_frame(find_bool, yaw, pitch)
            if response_frame:
                response_data = str(response_frame)
                status = "success"
            elif "成功" in message:
                response_data = "无响应"
                status = "success"
        
        # 保存到数据库
        sent_info = f"yaw:{yaw}, pitch:{pitch}, find_bool:{find_bool}"
        save_record_to_db(sent_info, response_data, status, message)
        
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

# 路由：读取帧数据
@routes_bp.route('/read_frame', methods=['GET'])
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
            frame_data, message = serial_handler.read_frame()
            if frame_data:
                status = "success"
        
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

# 路由：SSE帧数据事件流
@routes_bp.route('/frame_events')
def frame_events():
    """SSE端点，向前端推送接收到的帧数据"""
    def event_stream():
        if not serial_handler:
            yield f"data: {json.dumps({'error': '串口未初始化'})}\n\n"
            return
            
        frame_queue = serial_handler.get_frame_queue()
        
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

# 路由：启动姿势分析
@routes_bp.route('/start_posture_analysis', methods=['POST'])
def start_posture_analysis():
    """启动姿势分析系统"""
    global posture_monitor
    
    try:
        if not posture_monitor:
            return jsonify({
                'status': 'error',
                'message': '姿势分析系统未初始化'
            })
            
        if posture_monitor.is_running:
            return jsonify({
                'status': 'success',
                'message': '姿势分析系统已经在运行中'
            })
        
        success = posture_monitor.start()
        
        if success:
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

# 路由：停止姿势分析
@routes_bp.route('/stop_posture_analysis', methods=['POST'])
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

# 路由：获取姿势状态
@routes_bp.route('/get_pose_status')
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

# 新增路由：获取帧率信息
@routes_bp.route('/get_fps_info')
def get_fps_info():
    """获取所有帧率信息（包括捕获帧率、处理帧率和视频流帧率）"""
    global posture_monitor, video_stream_handler
    
    try:
        # 初始化返回数据
        fps_data = {
            'status': 'success',
            'capture_fps': 0,  # 图像接收帧率
            'pose_process_fps': 0,  # 姿势处理帧率
            'emotion_process_fps': 0,  # 情绪处理帧率
            'pose_stream_fps': 0,  # 姿势视频流帧率
            'emotion_stream_fps': 0  # 情绪视频流帧率
        }
        
        # 获取姿势分析模块的帧率数据
        if posture_monitor and posture_monitor.is_running:
            posture_fps_info = posture_monitor.get_fps_info()
            fps_data.update({
                'capture_fps': posture_fps_info.get('capture_fps', 0),
                'pose_process_fps': posture_fps_info.get('pose_process_fps', 0),
                'emotion_process_fps': posture_fps_info.get('emotion_process_fps', 0)
            })
        
        # 获取视频流模块的帧率数据
        if video_stream_handler:
            stream_fps_info = video_stream_handler.get_fps_info()
            fps_data.update({
                'pose_stream_fps': stream_fps_info.get('pose_stream_fps', 0),
                'emotion_stream_fps': stream_fps_info.get('emotion_stream_fps', 0)
            })
        
        return jsonify(fps_data)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取帧率信息出错: {str(e)}',
            'capture_fps': 0,
            'pose_process_fps': 0,
            'emotion_process_fps': 0,
            'pose_stream_fps': 0,
            'emotion_stream_fps': 0
        })

# 路由：获取情绪参数
@routes_bp.route('/get_emotion_params')
def get_emotion_params():
    """获取情绪分析参数"""
    global posture_monitor, posture_params
    
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

# 路由：更新情绪参数
@routes_bp.route('/update_emotion_params', methods=['POST'])
def update_emotion_params():
    """更新情绪分析参数"""
    global posture_monitor
    
    try:
        if not posture_monitor:
            return jsonify({
                'status': 'error',
                'message': '姿势分析系统未初始化'
            })
            
        params = request.json
        
        # 验证并更新参数
        success = posture_monitor.update_emotion_params(params)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': '情绪分析参数更新成功',
                'params': posture_monitor.get_emotion_params()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '更新情绪分析参数失败'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'更新情绪分析参数出错: {str(e)}'
        })

# 路由：姿势检测视频流
@routes_bp.route('/video_pose')
def video_pose():
    """姿势检测视频流端点"""
    if not video_stream_handler:
        # 返回空的响应
        return Response("视频流处理器未初始化", status=500)
        
    return Response(
        video_stream_handler.generate_video_frames(video_stream_handler.get_pose_frame_queue(), is_pose_stream=True),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# 路由：情绪分析视频流
@routes_bp.route('/video_emotion')
def video_emotion():
    """情绪分析视频流端点"""
    if not video_stream_handler:
        # 返回空的响应
        return Response("视频流处理器未初始化", status=500)
        
    return Response(
        video_stream_handler.generate_video_frames(video_stream_handler.get_emotion_frame_queue(), is_pose_stream=False),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )