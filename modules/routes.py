"""
路由模块 - 处理所有API路由请求
"""
from flask import Blueprint, render_template, jsonify, request, Response, stream_with_context
import json
import queue
import time
from modules.database_module import save_record_to_db, get_history_records, clear_history, clear_all_posture_records
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
    return render_template('main.html')

# 路由：调试页面
@routes_bp.route('/debug')
def debug():
    return render_template('debug.html')

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
        if posture_monitor  and posture_monitor.is_running:
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
        })

# 视频流路由别名 - 兼容前端
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

# 路由：获取坐姿图像记录设置
@routes_bp.route('/api/get_posture_recording_settings')
def get_posture_recording_settings():
    """获取坐姿图像记录设置"""
    global posture_monitor
    
    try:
        if not posture_monitor:
            return jsonify({
                'status': 'error',
                'message': '姿势分析系统未初始化',
                'settings': None
            })
        
        settings = posture_monitor.get_posture_recording_settings()
        
        return jsonify({
            'status': 'success',
            'message': '获取坐姿图像记录设置成功',
            'settings': settings
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取坐姿图像记录设置失败: {str(e)}',
            'settings': None
        })

# 路由：更新坐姿图像记录设置
@routes_bp.route('/api/update_posture_recording_settings', methods=['POST'])
def update_posture_recording_settings():
    """更新坐姿图像记录设置"""
    global posture_monitor
    
    try:
        if not posture_monitor:
            return jsonify({
                'status': 'error',
                'message': '姿势分析系统未初始化'
            })
        
        # 获取请求参数
        data = request.json
        enabled = data.get('enabled')
        duration_threshold = data.get('duration_threshold')
        interval = data.get('interval')
        
        # 新增良好坐姿记录参数
        good_posture_enabled = data.get('good_posture_enabled')
        good_posture_angle_threshold = data.get('good_posture_angle_threshold')
        good_posture_duration_threshold = data.get('good_posture_duration_threshold')
        good_posture_interval = data.get('good_posture_interval')
        
        if (enabled is None and duration_threshold is None and interval is None and
            good_posture_enabled is None and good_posture_angle_threshold is None and
            good_posture_duration_threshold is None and good_posture_interval is None):
            return jsonify({
                'status': 'error',
                'message': '未提供任何更新参数'
            })
        
        # 更新设置
        settings = posture_monitor.set_posture_recording(
            enabled=enabled,
            duration_threshold=duration_threshold,
            interval=interval,
            good_posture_enabled=good_posture_enabled,
            good_posture_angle_threshold=good_posture_angle_threshold,
            good_posture_duration_threshold=good_posture_duration_threshold,
            good_posture_interval=good_posture_interval
        )
        
        return jsonify({
            'status': 'success',
            'message': '坐姿图像记录设置已更新',
            'settings': settings
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'更新坐姿图像记录设置失败: {str(e)}'
        })

# 路由：获取坐姿图像记录列表
@routes_bp.route('/api/get_posture_images')
def get_posture_images():
    """获取坐姿图像记录列表，支持分页和筛选"""
    try:
        from modules.database_module import get_posture_images as db_get_posture_images
        
        # 获取请求参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        bad_posture_only = request.args.get('bad_posture_only', 'false').lower() == 'true'
        
        # 查询数据库
        result = db_get_posture_images(page, per_page, bad_posture_only)
        
        return jsonify({
            'status': 'success',
            'message': '获取坐姿图像记录成功',
            **result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取坐姿图像记录失败: {str(e)}',
            'records': [],
            'pagination': {
                'total': 0,
                'page': 1,
                'per_page': 10,
                'total_pages': 0
            }
        })

# 路由：删除坐姿图像记录
@routes_bp.route('/api/delete_posture_image', methods=['POST'])
def delete_posture_image():
    """删除指定的坐姿图像记录"""
    try:
        from modules.database_module import delete_posture_image as db_delete_posture_image
        
        # 获取请求参数
        data = request.json
        image_id = data.get('image_id')
        
        if not image_id:
            return jsonify({
                'status': 'error',
                'message': '未提供图像ID'
            })
        
        # 执行删除
        success = db_delete_posture_image(image_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'已删除坐姿图像记录 (ID: {image_id})'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'未找到ID为 {image_id} 的坐姿图像记录'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'删除坐姿图像记录失败: {str(e)}'
        })

# 路由：清空坐姿图像记录
@routes_bp.route('/api/clear_posture_images', methods=['POST'])
def clear_posture_images():
    """清空坐姿图像记录"""
    try:
        from modules.database_module import clear_posture_images as db_clear_posture_images
        
        # 获取请求参数
        data = request.json
        days_to_keep = data.get('days_to_keep')
        
        # 执行清空
        deleted_count = db_clear_posture_images(days_to_keep)
        
        message = f'已删除 {deleted_count} 条坐姿图像记录'
        if days_to_keep:
            message = f'已删除 {deleted_count} 条{days_to_keep}天前的坐姿图像记录'
            
        return jsonify({
            'status': 'success',
            'message': message,
            'deleted_count': deleted_count
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'清空坐姿图像记录失败: {str(e)}'
        })

# 路由：手动记录当前坐姿图像
@routes_bp.route('/api/capture_posture_image', methods=['POST'])
def capture_posture_image():
    """手动记录当前坐姿图像"""
    global posture_monitor
    
    try:
        if not posture_monitor or not posture_monitor.is_running:
            return jsonify({
                'status': 'error',
                'message': '姿势分析系统未运行'
            })
        
        from modules.database_module import save_posture_image
        
        # 获取请求参数
        data = request.json
        notes = data.get('notes', '手动记录的坐姿图像')
        
        # 获取当前帧
        if not hasattr(posture_monitor, 'cap') or not posture_monitor.cap.isOpened():
            return jsonify({
                'status': 'error',
                'message': '摄像头未就绪'
            })
            
        # 读取当前帧
        ret, frame = posture_monitor.cap.read()
        if not ret:
            return jsonify({
                'status': 'error',
                'message': '无法获取当前摄像头帧'
            })
        
        # 获取当前姿势状态
        angle = posture_monitor.pose_result.get('angle', 0)
        is_bad_posture = posture_monitor.pose_result.get('is_bad_posture', False)
        posture_status = f"{'Bad' if is_bad_posture else 'Good'} Posture - Angle: {angle:.1f}°"
        emotion = posture_monitor.emotion_result.get('emotion', 'UNKNOWN')
        
        # 保存图像记录
        result = save_posture_image(
            image=frame,
            angle=angle,
            is_bad_posture=is_bad_posture,
            posture_status=posture_status,
            emotion=emotion,
            notes=notes
        )
        
        if result:
            return jsonify({
                'status': 'success',
                'message': '成功记录当前坐姿图像',
                'image': result
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '保存坐姿图像失败'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'记录坐姿图像失败: {str(e)}'
        })

# 路由：查看更多坐姿图像记录页面
@routes_bp.route('/posture-records')
def posture_records_page():
    """显示坐姿图像记录详情页面"""
    return render_template('posture_records.html')

# 路由：获取坐姿统计数据
@routes_bp.route('/api/get_posture_stats')
def get_posture_stats():
    """获取坐姿统计数据
    
    支持的参数:
    - time_range: 预设时间范围 'day', 'week', 'month', 'custom'
    - start_date: 自定义开始日期 (格式: YYYY-MM-DD，仅当time_range为'custom'时有效)
    - end_date: 自定义结束日期 (格式: YYYY-MM-DD，仅当time_range为'custom'时有效)
    - with_hourly_data: 是否返回每小时数据，'true'或'false'，默认为'false'
    """
    global posture_monitor
    
    try:
        # 获取时间范围参数
        time_range = request.args.get('time_range', 'day')
        if time_range not in ['day', 'week', 'month', 'custom']:
            time_range = 'day'
        
        # 处理自定义日期范围
        custom_start_date = None
        custom_end_date = None
        
        if time_range == 'custom':
            try:
                from datetime import datetime
                # 解析自定义日期参数
                start_date_str = request.args.get('start_date')
                end_date_str = request.args.get('end_date')
                
                if start_date_str and end_date_str:
                    custom_start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                    custom_end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                    # 设置start_date的时间为00:00:00
                    custom_start_date = custom_start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    # 设置end_date的时间为23:59:59
                    custom_end_date = custom_end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                else:
                    # 如果未提供有效的自定义日期，则使用"今天"作为默认值
                    time_range = 'day'
            except ValueError:
                # 日期格式无效，回退到"今天"
                time_range = 'day'
        
        # 是否需要返回每小时数据
        with_hourly_data = request.args.get('with_hourly_data', 'false').lower() == 'true'
        
        # 检查姿势监测器是否已初始化
        if not posture_monitor:
            return jsonify({
                'status': 'error',
                'message': '姿势分析系统未初始化',
                'posture_stats': {
                    'good': {'seconds': 0, 'percentage': 0, 'formatted_time': '0h 0m'},
                    'mild': {'seconds': 0, 'percentage': 0, 'formatted_time': '0h 0m'},
                    'moderate': {'seconds': 0, 'percentage': 0, 'formatted_time': '0h 0m'},
                    'severe': {'seconds': 0, 'percentage': 0, 'formatted_time': '0h 0m'},
                    'total_time': {'seconds': 0, 'formatted_time': '0h 0m'},
                    'good_posture_percentage': 0,
                    'time_range': time_range
                }
            })
        
        # 直接从模块导入函数
        from modules.database_module import get_posture_stats as db_get_posture_stats
        
        # 获取姿势统计数据
        stats = db_get_posture_stats(
            time_range=time_range, 
            custom_start_date=custom_start_date, 
            custom_end_date=custom_end_date,
            with_hourly_data=with_hourly_data
        )
        
        # 添加查询区间的文字描述
        time_range_description = ""
        if time_range == 'day':
            time_range_description = "今日数据"
        elif time_range == 'week':
            time_range_description = "本周数据"
        elif time_range == 'month':
            time_range_description = "本月数据"
        elif time_range == 'custom':
            from datetime import datetime
            time_range_description = f"{custom_start_date.strftime('%Y-%m-%d')}至{custom_end_date.strftime('%Y-%m-%d')}数据"
        
        stats['time_range_description'] = time_range_description
        
        return jsonify({
            'status': 'success',
            'posture_stats': stats
        })
    except Exception as e:
        print(f"获取坐姿统计数据出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f"获取坐姿统计数据失败: {str(e)}",
            'posture_stats': {
                'good': {'seconds': 0, 'percentage': 0, 'formatted_time': '0h 0m'},
                'mild': {'seconds': 0, 'percentage': 0, 'formatted_time': '0h 0m'},
                'moderate': {'seconds': 0, 'percentage': 0, 'formatted_time': '0h 0m'},
                'severe': {'seconds': 0, 'percentage': 0, 'formatted_time': '0h 0m'},
                'total_time': {'seconds': 0, 'formatted_time': '0h 0m'},
                'good_posture_percentage': 0,
                'time_range': time_range
            }
        })

# 路由：设置坐姿类型阈值
@routes_bp.route('/api/set_posture_thresholds', methods=['POST'])
def set_posture_thresholds():
    """设置坐姿类型阈值"""
    global posture_monitor
    
    try:
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': '无效的请求数据'
            })
            
        # 解析参数
        enabled = data.get('enabled', True)
        thresholds = data.get('thresholds', {})
        
        if not posture_monitor:
            return jsonify({
                'status': 'error',
                'message': '姿势分析系统未初始化'
            })
        
        # 将前端传来的阈值键名转换为后端使用的键名
        backend_thresholds = {}
        if 'good' in thresholds:
            backend_thresholds['good'] = thresholds['good']
        if 'mild' in thresholds:
            backend_thresholds['mild'] = thresholds['mild']
        if 'moderate' in thresholds:
            backend_thresholds['moderate'] = thresholds['moderate']
        
        # 更新坐姿时间记录设置
        settings = posture_monitor.set_posture_time_recording(enabled, backend_thresholds)
        
        return jsonify({
            'status': 'success',
            'message': '坐姿阈值设置已更新',
            'settings': settings
        })
    except Exception as e:
        print(f"设置坐姿阈值出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"设置坐姿阈值失败: {str(e)}"
        })

# 路由：导出所有坐姿历史记录
@routes_bp.route('/api/export_all_posture_records')
def export_all_posture_records():
    """导出所有坐姿历史记录，包括统计数据、图像记录和时间记录"""
    try:
        from modules.database_module import export_all_posture_records as db_export_records
        
        # 获取时间范围参数
        time_range = request.args.get('time_range', 'all')
        if time_range not in ['all', 'day', 'week', 'month', 'custom']:
            time_range = 'all'
        
        # 处理自定义日期范围
        custom_start_date = None
        custom_end_date = None
        
        if time_range == 'custom':
            try:
                from datetime import datetime
                # 解析自定义日期参数
                start_date_str = request.args.get('start_date')
                end_date_str = request.args.get('end_date')
                
                if start_date_str  and end_date_str:
                    custom_start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                    custom_end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                    # 设置start_date的时间为00:00:00
                    custom_start_date = custom_start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    # 设置end_date的时间为23:59:59
                    custom_end_date = custom_end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                else:
                    # 如果未提供有效的自定义日期，则使用"全部"作为默认值
                    time_range = 'all'
            except ValueError:
                # 日期格式无效，回退到"全部"
                time_range = 'all'
        
        # 获取所有坐姿记录
        records = db_export_records(
            time_range=time_range,
            start_date=custom_start_date,
            end_date=custom_end_date
        )
        
        # 添加查询区间的文字描述
        time_range_description = ""
        if time_range == 'day':
            time_range_description = "今日数据"
        elif time_range == 'week':
            time_range_description = "本周数据"
        elif time_range == 'month':
            time_range_description = "本月数据"
        elif time_range == 'custom'  and custom_start_date  and custom_end_date:
            time_range_description = f"{custom_start_date.strftime('%Y-%m-%d')}至{custom_end_date.strftime('%Y-%m-%d')}数据"
        else:
            time_range_description = "所有历史数据"
        
        records['time_range_description'] = time_range_description
        
        return jsonify({
            'status': 'success',
            'message': f'成功导出{time_range_description}，共{records["image_records"]["count"]}条图像记录  and {records["time_records"]["count"]}条时间记录',
            'records': records
        })
    except Exception as e:
        print(f"导出所有坐姿历史记录出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'导出坐姿历史记录失败: {str(e)}'
        })

# 路由：清空所有坐姿记录
@routes_bp.route('/api/clear_all_posture_records', methods=['POST'])
def clear_all_posture_records_route():
    """清空所有坐姿记录，包括图像记录和时间记录"""
    try:
        print("正在执行清空所有坐姿记录...")
        result = clear_all_posture_records()
        print(f"清空结果: {result}")
        
        if result and result.get('status') == 'success':
            return jsonify({
                'status': 'success', 
                'message': result.get('message', '所有坐姿记录已清空')
            })
        else:
            error_msg = result.get('message', '清空坐姿记录失败') if result else '清空坐姿记录失败'
            print(f"清空失败: {error_msg}")
            return jsonify({
                'status': 'error', 
                'message': error_msg
            })
    except Exception as e:
        print(f"执行清空所有坐姿记录时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'清空坐姿记录时发生错误: {str(e)}'
        })

@routes_bp.route('/api/posture/history/all', methods=['GET'])
def get_all_posture_history():
    """获取所有坐姿历史记录，包括图像记录和时间记录"""
    try:
        # 从查询参数中获取时间范围
        time_range = request.args.get('range', 'all')
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        
        # 获取所有历史记录
        result = get_all_posture_records(time_range, start_date, end_date)
        
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取坐姿历史记录失败: {str(e)}'
        }), 500

@routes_bp.route('/api/posture/history/clear', methods=['POST'])
def clear_posture_history():
    """清空坐姿历史记录"""
    try:
        # 获取请求参数
        data = request.get_json()
        days_to_keep = data.get('days_to_keep', None)
        
        if days_to_keep is not None:
            try:
                days_to_keep = int(days_to_keep)
            except ValueError:
                days_to_keep = None
        
        # 执行清空操作
        result = clear_all_posture_records(days_to_keep)
        
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'清空坐姿历史记录失败: {str(e)}'
        }), 500

@routes_bp.route('/posture/history', methods=['GET'])
def view_posture_history():
    """渲染坐姿历史记录页面"""
    return render_template('posture_history.html', title='坐姿历史记录')
