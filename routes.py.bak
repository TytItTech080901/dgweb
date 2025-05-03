"""
路由模块 - 处理所有Web路由和API请求
"""
from flask import Blueprint, render_template, Response, request, jsonify
import cv2
import json
import time
import os
import re
from datetime import datetime
import numpy as np
from config import DEBUG, DB_CONFIG
from db_handler import DBHandler
from modules.video_stream_module import VideoStreamHandler
from modules.posture_module import WebPostureMonitor, POSTURE_MODULE_AVAILABLE
from serial_handler import SerialHandler

# 创建数据库处理器
db = DBHandler(DB_CONFIG)

# 创建Flask蓝图
routes = Blueprint('routes', __name__)

# 创建视频流处理器
video_stream_handler = VideoStreamHandler()

# 创建姿势监测器
posture_monitor = WebPostureMonitor(video_stream_handler=video_stream_handler)

# 创建串口通信处理器
serial_handler = SerialHandler(monitoring_interval=5)
print("串口通信处理器初始化完成")

# API版本
API_VERSION = "1.0.0"

# 应用状态
app_status = {
    'emotion_analysis_running': False,
    'last_error': '',
    'api_version': API_VERSION
}

# 最后事件时间戳
last_event_time = time.time()

@routes.route('/get_fps_info')
def get_fps_info():
    """获取各种帧率信息"""
    try:
        # 获取姿势监测模块的帧率信息
        posture_fps_info = posture_monitor.get_fps_info()
        
        # 获取视频流模块的帧率信息
        stream_fps_info = video_stream_handler.get_fps_info()
        
        # 合并所有帧率信息
        fps_info = {
            **posture_fps_info,
            **stream_fps_info
        }
        
        return jsonify({
            'status': 'success',
            'capture_fps': fps_info['capture_fps'],
            'pose_process_fps': fps_info['pose_process_fps'],
            'emotion_process_fps': fps_info['emotion_process_fps'],
            'pose_stream_fps': fps_info['pose_stream_fps'],
            'emotion_stream_fps': fps_info['emotion_stream_fps']
        })
    except Exception as e:
        print(f"获取帧率信息出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"获取帧率信息失败: {str(e)}",
            'capture_fps': 0,
            'pose_process_fps': 0,
            'emotion_process_fps': 0,
            'pose_stream_fps': 0,
            'emotion_stream_fps': 0
        })

@routes.route('/set_resolution_mode', methods=['POST'])
def set_resolution_mode():
    """设置分辨率调整模式"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': '无效的请求数据'
            })
            
        # 解析参数
        adaptive = data.get('adaptive', True)
        resolution_index = data.get('resolution_index')
        target = data.get('target', 'both')  # 'processing', 'streaming', 'both'
        
        if target in ['processing', 'both']:
            # 设置处理分辨率模式
            posture_monitor.set_resolution_mode(adaptive, resolution_index)
            
        if target in ['streaming', 'both']:
            # 设置流分辨率模式
            video_stream_handler.set_resolution_mode(adaptive, resolution_index)
            
        if 'quality' in data:
            # 设置流质量
            quality = int(data['quality'])
            video_stream_handler.set_streaming_quality(quality)
            
        return jsonify({
            'status': 'success',
            'message': '分辨率模式已更新',
            'adaptive': adaptive,
            'resolution_index': resolution_index if resolution_index is not None else 'auto',
            'target': target
        })
    except Exception as e:
        print(f"设置分辨率模式出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"设置分辨率模式失败: {str(e)}"
        })

# Serial API路由

@routes.route('/get_serial_status')
def get_serial_status():
    """获取串口连接状态"""
    try:
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
            'message': f"获取串口状态失败: {str(e)}",
            'connected': False
        })

@routes.route('/connect_serial', methods=['POST'])
def connect_serial():
    """连接指定的串口"""
    try:
        data = request.get_json()
        port = data.get('port')
        baudrate = data.get('baudrate', 115200)
        
        if not port:
            return jsonify({
                'status': 'error',
                'message': '必须指定串口设备'
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
            'message': f"连接串口失败: {str(e)}"
        })

@routes.route('/disconnect_serial', methods=['POST'])
def disconnect_serial():
    """断开串口连接"""
    try:
        was_connected = serial_handler.is_connected()
        serial_handler.close()
        
        return jsonify({
            'status': 'success',
            'message': '已断开串口连接' if was_connected else '串口已处于断开状态'
        })
    except Exception as e:
        print(f"断开串口出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"断开串口失败: {str(e)}"
        })

@routes.route('/send_serial_command', methods=['POST'])
def send_serial_command():
    """向串口发送命令"""
    try:
        data = request.get_json()
        command = data.get('command')
        
        if not command:
            return jsonify({
                'status': 'error',
                'message': '命令不能为空'
            })
        
        if not serial_handler.is_connected():
            return jsonify({
                'status': 'error',
                'message': '串口未连接，请先连接串口'
            })
        
        # 发送命令
        success = serial_handler.send_data(command + '\r\n')
        
        # 给点时间让设备处理并响应
        time.sleep(0.1)
        
        # 尝试读取响应
        response = serial_handler.read_data()
        
        # 记录命令和响应到数据库
        try:
            db.record_serial_data(
                sent_data=command,
                received_data=response,
                status="success" if success else "error",
                message="" if success else "发送失败"
            )
        except Exception as db_error:
            print(f"记录串口数据到数据库失败: {str(db_error)}")
        
        if success:
            return jsonify({
                'status': 'success',
                'message': '命令已发送',
                'command': command,
                'response': response
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '发送命令失败',
                'command': command
            })
    except Exception as e:
        print(f"发送串口命令出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"发送串口命令失败: {str(e)}"
        })

@routes.route('/send_frame', methods=['POST'])
def send_frame():
    """向串口发送帧数据"""
    try:
        data = request.get_json()
        yaw = data.get('yaw', 0.0)
        pitch = data.get('pitch', 0.0)
        find_bool = data.get('find_bool', False)
        
        if not serial_handler.is_connected():
            return jsonify({
                'status': 'error',
                'message': '串口未连接，请先连接串口'
            })
        
        # 发送帧数据
        success = serial_handler.send_yaw_pitch(find_bool, yaw, pitch)
        
        # 给点时间让设备处理并响应
        time.sleep(0.1)
        
        # 记录到数据库
        try:
            sent_data = f"yaw={yaw}, pitch={pitch}, find={find_bool}"
            db.record_serial_data(
                sent_data=sent_data,
                received_data="",
                status="success" if success else "error",
                message="" if success else "发送失败"
            )
        except Exception as db_error:
            print(f"记录帧数据到数据库失败: {str(db_error)}")
        
        if success:
            return jsonify({
                'status': 'success',
                'message': '帧数据已发送',
                'response': f"发送了帧数据: yaw={yaw}, pitch={pitch}, find={find_bool}"
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '发送帧数据失败'
            })
    except Exception as e:
        print(f"发送帧数据出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"发送帧数据失败: {str(e)}"
        })

@routes.route('/read_frame')
def read_frame():
    """读取一帧数据"""
    try:
        if not serial_handler.is_connected():
            return jsonify({
                'status': 'error',
                'message': '串口未连接，请先连接串口'
            })
        
        # 读取帧数据
        frame_data = serial_handler.read_frame()
        
        if frame_data:
            return jsonify({
                'status': 'success',
                'frame_data': frame_data
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '没有接收到有效帧数据'
            })
    except Exception as e:
        print(f"读取帧数据出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"读取帧数据失败: {str(e)}"
        })

@routes.route('/get_history')
def get_history():
    """获取串口通信历史记录"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 从数据库获取历史记录
        total_records, records = db.get_serial_history(page, per_page)
        
        # 计算总页数
        total_pages = (total_records + per_page - 1) // per_page
        
        return jsonify({
            'status': 'success',
            'current_page': page,
            'per_page': per_page,
            'total_records': total_records,
            'total_pages': total_pages,
            'records': records
        })
    except Exception as e:
        print(f"获取历史记录出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"获取历史记录失败: {str(e)}"
        })

@routes.route('/clear_history', methods=['POST'])
def clear_history():
    """清空串口通信历史记录"""
    try:
        # 调用数据库清空历史记录
        db.clear_serial_history()
        
        return jsonify({
            'status': 'success',
            'message': '历史记录已清空'
        })
    except Exception as e:
        print(f"清空历史记录出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"清空历史记录失败: {str(e)}"
        })

# 帧事件流端点
@routes.route('/frame_events')
def frame_events():
    def generate():
        """生成事件流"""
        # 初始化事件ID
        event_id = 0
        
        # 启动帧监控
        frame_queue = []
        
        # 初始化最后一次发送心跳包的时间
        last_heartbeat_time = time.time()
        
        # 开始事件循环
        while True:
            # 每15秒发送一次心跳包，保持连接活跃
            current_time = time.time()
            if current_time - last_heartbeat_time > 15:
                heartbeat_data = json.dumps({
                    'type': 'heartbeat',
                    'timestamp': current_time
                })
                yield f"id: {event_id}\ndata: {heartbeat_data}\n\n"
                event_id += 1
                last_heartbeat_time = current_time
            
            # 如果串口已连接，尝试读取一帧数据
            if serial_handler.is_connected():
                frame_data = serial_handler.read_frame()
                if frame_data:
                    # 构造事件数据
                    data = json.dumps(frame_data)
                    yield f"id: {event_id}\ndata: {data}\n\n"
                    event_id += 1
            
            # 短暂休眠，避免过度占用CPU
            time.sleep(0.1)
    
    return Response(generate(), mimetype='text/event-stream')