"""
路由模块 - 处理所有API路由请求
"""
from flask import Blueprint, render_template, jsonify, request, Response, stream_with_context
import json
import queue
import time
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
@routes_bp.route('/api/send_data', methods=['POST'])
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
@routes_bp.route('/api/get_history')
def get_history():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    result = get_history_records(page, per_page)
    return jsonify(result)

# 路由：清空历史记录
@routes_bp.route('/api/clear_history', methods=['POST'])
def clear_history_route():
    if clear_history():
        return jsonify({'status': 'success', 'message': '历史记录已清空'})
    else:
        return jsonify({'status': 'error', 'message': '清空历史记录失败'})

# 路由：发送帧数据
@routes_bp.route('/api/send_frame', methods=['POST'])
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
@routes_bp.route('/api/read_frame', methods=['GET'])
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
@routes_bp.route('/api/frame_events')
def frame_events():
    """SSE端点，向前端推送接收到的帧数据"""
    def event_stream():
        if not serial_handler:
            # 如果串口未初始化，发送空闲状态信息而不是立即退出
            yield f"data: {json.dumps({'status': 'idle', 'message': '串口未初始化', 'type': 'status'})}\n\n"
            # 每30秒发送一次心跳保持连接
            while True:
                try:
                    time.sleep(30)
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                except Exception:
                    break
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
@routes_bp.route('/api/start_posture_analysis', methods=['POST'])
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
@routes_bp.route('/api/stop_posture_analysis', methods=['POST'])
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
@routes_bp.route('/api/get_pose_status')
def get_pose_status():
    """获取当前姿势分析状态"""
    global posture_monitor, video_stream_handler
    
    try:
        print("DEBUG: 请求获取姿势分析状态")
        
        # 检查是否有视频流但姿势分析未初始化的情况
        if not posture_monitor:
            print("WARNING: 姿势分析系统对象未初始化，但前端请求了状态")
            # 检查视频流处理器是否在工作
            if video_stream_handler:
                # 视频流正常但姿势分析未初始化，尝试修正状态
                print("INFO: 视频流处理器存在但姿势分析未初始化")
                return jsonify({
                    'status': 'partial',  # 新状态：部分可用
                    'message': '视频流可用但姿势分析未正确初始化',
                    'is_running': False,
                    'pose_data': {'status': 'Video Only', 'angle': 0, 'is_bad_posture': False, 'is_occluded': True},
                    'emotion_data': {'emotion': 'UNKNOWN', 'emotion_code': -1}
                })
            else:
                print("ERROR: 姿势分析系统和视频流均未初始化")
                return jsonify({
                    'status': 'error',
                    'message': '姿势分析系统未初始化',
                    'is_running': False,
                    'pose_data': None,
                    'emotion_data': None
                })
        
        # 正常情况下返回完整状态信息
        print(f"DEBUG: 姿势分析系统状态 - 运行中: {posture_monitor.is_running}")
        return jsonify({
            'status': 'success',
            'message': '获取姿势分析状态成功',
            'is_running': posture_monitor.is_running,
            'pose_data': posture_monitor.pose_result,
            'emotion_data': posture_monitor.emotion_result
        })
    except Exception as e:
        print(f"ERROR: 获取姿势分析状态出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取姿势分析状态出错: {str(e)}',
            'is_running': False,
            'pose_data': None,
            'emotion_data': None
        })

# 路由：获取帧率信息
@routes_bp.route('/api/get_fps_info')
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
@routes_bp.route('/api/get_emotion_params')
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
@routes_bp.route('/api/update_emotion_params', methods=['POST'])
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
@routes_bp.route('/api/video_pose')
def video_pose():
    """姿势检测视频流端点"""
    print("DEBUG: 请求姿势检测视频流")
    
    if not video_stream_handler:
        print("ERROR: 视频流处理器未初始化")
        # 返回空的响应
        return Response("视频流处理器未初始化", status=500)
    
    print("DEBUG: 开始生成姿势视频流响应")
    return Response(
        video_stream_handler.generate_video_frames(video_stream_handler.get_pose_frame_queue(), is_pose_stream=True),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# 路由：情绪分析视频流
@routes_bp.route('/api/video_emotion')
def video_emotion():
    """情绪分析视频流端点"""
    print("DEBUG: 请求情绪分析视频流")
    
    if not video_stream_handler:
        print("ERROR: 视频流处理器未初始化")
        # 返回空的响应
        return Response("视频流处理器未初始化", status=500)
    
    print("DEBUG: 开始生成情绪视频流响应")
    return Response(
        video_stream_handler.generate_video_frames(video_stream_handler.get_emotion_frame_queue(), is_pose_stream=False),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# 路由：获取串口状态
@routes_bp.route('/api/get_serial_status')
def get_serial_status():
    """获取串口连接状态"""
    global serial_handler
    
    try:
        if not serial_handler:
            return jsonify({
                'status': 'error',
                'message': '串口处理器未初始化',
                'connected': False
            })
            
        connected = serial_handler.is_connected()
        port = serial_handler.port if connected else None
        baudrate = serial_handler.baudrate if connected else None
        
        return jsonify({
            'status': 'success',
            'connected': connected,
            'port': port,
            'baudrate': baudrate
        })
    except Exception as e:
        print(f"获取串口状态出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取串口状态失败: {str(e)}',
            'connected': False
        })

# 路由：连接串口
@routes_bp.route('/api/connect_serial', methods=['POST'])
def connect_serial():
    """连接指定的串口"""
    global serial_handler
    
    try:
        if not serial_handler:
            return jsonify({
                'status': 'error',
                'message': '串口处理器未初始化',
                'connected': False
            })
            
        data = request.json
        port = data.get('port')
        baudrate = data.get('baudrate', 115200)
        
        if not port:
            return jsonify({
                'status': 'error',
                'message': '必须指定串口设备路径'
            })
            
        # 先断开现有连接
        serial_handler.close()
        
        # 设置新的串口参数
        serial_handler.port = port
        serial_handler.baudrate = baudrate
        
        # 尝试连接
        connection_success = serial_handler.connect()
        
        if connection_success:
            return jsonify({
                'status': 'success',
                'message': f'成功连接到串口: {port}, 波特率: {baudrate}',
                'port': port,
                'baudrate': baudrate
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'无法连接到串口: {port}'
            })
    except Exception as e:
        print(f"连接串口出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'连接串口失败: {str(e)}'
        })# 视频流路由别名 - 兼容前端
@routes_bp.route('/pose_video_feed')
def pose_video_feed_alias():
    """姿势分析视频流别名"""
    print("DEBUG: 通过别名请求姿势分析视频流")
    
    if not video_stream_handler:
        print("ERROR: 视频流处理器未初始化")
        return Response("视频流处理器未初始化", status=500)
    
    return Response(
        video_stream_handler.generate_video_frames(video_stream_handler.get_pose_frame_queue(), is_pose_stream=True),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@routes_bp.route('/emotion_video_feed')
def emotion_video_feed_alias():
    """情绪分析视频流别名"""
    print("DEBUG: 通过别名请求情绪分析视频流")
    
    if not video_stream_handler:
        print("ERROR: 视频流处理器未初始化")
        return Response("视频流处理器未初始化", status=500)
    
    return Response(
        video_stream_handler.generate_video_frames(video_stream_handler.get_emotion_frame_queue(), is_pose_stream=False),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# 添加串口指令发送路由
@routes_bp.route('/api/send_serial_command', methods=['POST'])
def send_serial_command():
    """向串口发送命令"""
    global serial_handler
    
    try:
        data = request.json
        command = data.get('command')
        
        if not command:
            return jsonify({
                'status': 'error',
                'message': '命令不能为空'
            })
        
        if not serial_handler or not serial_handler.is_connected():
            return jsonify({
                'status': 'error',
                'message': '串口未连接，请先连接串口'
            })
        
        # 发送命令
        response_data, message = serial_handler.send_data(command + '\r\n')
        
        # 记录命令和响应到数据库
        status = "success" if response_data else "error"
        save_record_to_db(command, response_data, status, message)
        
        return jsonify({
            'status': status,
            'message': message or '命令已发送',
            'command': command,
            'response': response_data or "无响应"
        })
    except Exception as e:
        print(f"发送串口命令出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'发送串口命令失败: {str(e)}'
        })

# 设置分辨率模式
@routes_bp.route('/api/set_resolution_mode', methods=['POST'])
def set_resolution_mode():
    """设置分辨率调整模式"""
    global posture_monitor, video_stream_handler
    
    try:
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': '无效的请求数据'
            })
            
        # 解析参数
        adaptive = data.get('adaptive', True)
        resolution_index = data.get('resolution_index')
        target = data.get('target', 'both')  # 'processing', 'streaming', 'both'
        quality = data.get('quality', 90)
        
        # 更新处理分辨率
        if posture_monitor and target in ['processing', 'both']:
            posture_monitor.set_resolution_mode(adaptive, resolution_index)
            
        # 更新流分辨率
        if video_stream_handler and target in ['streaming', 'both']:
            video_stream_handler.set_resolution_mode(adaptive, resolution_index)
            # 如果指定了质量参数，也设置流质量
            if quality is not None:
                video_stream_handler.set_streaming_quality(int(quality))
                
        return jsonify({
            'status': 'success',
            'message': '分辨率模式已更新',
            'adaptive': adaptive,
            'resolution_index': resolution_index if resolution_index is not None else 'auto',
            'target': target,
            'quality': quality
        })
    except Exception as e:
        print(f"设置分辨率模式出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'设置分辨率模式失败: {str(e)}'
        })

# 兼容路由 - 支持旧版前端
@routes_bp.route('/get_pose_status')
def get_pose_status_compat():
    """获取姿势状态的兼容路由（无API前缀）"""
    return get_pose_status()
