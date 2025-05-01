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

# 创建数据库处理器
db = DBHandler(DB_CONFIG)

# 创建Flask蓝图
routes = Blueprint('routes', __name__)

# 创建视频流处理器
video_stream_handler = VideoStreamHandler()

# 创建姿势监测器
posture_monitor = WebPostureMonitor(video_stream_handler=video_stream_handler)

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