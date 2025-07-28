from flask import Flask, render_template, jsonify, request, send_from_directory
import os
import json
from datetime import datetime, timedelta
import random

app = Flask(__name__, static_folder='static', static_url_path='/static')

# 配置
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 设备检测
def is_mobile():
    user_agent = request.headers.get('User-Agent', '').lower()
    mobile_agents = ['android', 'iphone', 'ipad', 'mobile', 'tablet']
    return any(agent in user_agent for agent in mobile_agents)

# 路由
@app.route('/')
def index():
    # 根据设备类型返回不同模板
    if is_mobile():
        return render_template('home.html')
    else:
        return render_template('home.html')  # 暂时都返回移动端

@app.route('/mobile/home')
def mobile_home():
    return render_template('home.html')

@app.route('/mobile/guardian')
def mobile_guardian():
    return render_template('guardian.html')

@app.route('/mobile/remote')
def mobile_remote():
    return render_template('remote.html')

@app.route('/mobile/settings')
def mobile_settings():
    return render_template('settings.html')

@app.route('/mobile/settings/notifications')
def mobile_settings_notifications():
    return render_template('settings_notifications.html')

@app.route('/mobile/settings/monitor')
def mobile_settings_monitor():
    return render_template('settings_monitor.html')

@app.route('/mobile/settings/account')
def mobile_settings_account():
    return render_template('settings_account.html')

@app.route('/mobile/settings/system')
def mobile_settings_system():
    return render_template('settings_system.html')

@app.route('/mobile/tool/<tool_name>')
def mobile_tool_detail(tool_name):
    return render_template('tool_detail.html', tool_name=tool_name)

# 独立工具页面路由
@app.route('/posture')
def posture():
    return render_template('posture.html')

@app.route('/eye')
def eye():
    return render_template('eye.html')

@app.route('/emotion')
def emotion():
    return render_template('emotion.html')

# 静态文件路由
@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')

@app.route('/video_feed')
def video_feed():
    return jsonify({'url': '/static/asserts/WechatIMG69.jpg'})

# API端点
@app.route('/api/home/stats')
def api_home_stats():
    """获取首页统计数据"""
    # 模拟数据
    stats = {
        'studyTime': f"{random.randint(3, 6)}.{random.randint(0, 9)}h",
        'postureScore': f"{random.randint(75, 95)}%",
        'eyeRest': str(random.randint(8, 20)),
        'lastUpdate': datetime.now().isoformat()
    }
    return jsonify(stats)

# 坐姿检测API接口
@app.route('/api/posture/data')
def api_posture_data():
    """获取坐姿数据"""
    range_type = request.args.get('range', 'day')
    
    # 模拟数据
    if range_type == 'day':
        data = {
            'goodPostureTime': '3.2h',
            'mildBadPostureTime': '1.2h',
            'badPostureTime': '0.6h',
            'postureRate': '64%',
            'pieData': [64, 24, 12],
            'heatmapData': [85, 78, 72, 65, 58, 82, 90, 88]
        }
    elif range_type == 'week':
        data = {
            'goodPostureTime': '22.4h',
            'mildBadPostureTime': '8.4h',
            'badPostureTime': '4.2h',
            'postureRate': '68%',
            'pieData': [68, 22, 10],
            'heatmapData': [88, 82, 75, 68, 72, 85, 92, 89]
        }
    else:  # month
        data = {
            'goodPostureTime': '96.0h',
            'mildBadPostureTime': '36.0h',
            'badPostureTime': '18.0h',
            'postureRate': '72%',
            'pieData': [72, 20, 8],
            'heatmapData': [90, 85, 78, 72, 75, 88, 94, 91]
        }
    
    return jsonify(data)

@app.route('/api/posture/images')
def api_posture_images():
    """获取坐姿图像记录"""
    # 模拟图像数据
    images = [
        {
            'id': 1,
            'url': '/static/placeholder.jpg',
            'time': '2025-05-28 21:39:01',
            'status': 'good'
        },
        {
            'id': 2,
            'url': '/static/placeholder.jpg',
            'time': '2025-05-28 21:40:33',
            'status': 'warning'
        },
        {
            'id': 3,
            'url': '/static/placeholder.jpg',
            'time': '2025-05-28 21:41:21',
            'status': 'good'
        },
        {
            'id': 4,
            'url': '/static/placeholder.jpg',
            'time': '2025-05-28 21:42:32',
            'status': 'bad'
        },
        {
            'id': 5,
            'url': '/static/placeholder.jpg',
            'time': '2025-05-28 22:04:03',
            'status': 'good'
        },
        {
            'id': 6,
            'url': '/static/placeholder.jpg',
            'time': '2025-05-28 22:14:34',
            'status': 'warning'
        }
    ]
    
    return jsonify({
        'status': 'success',
        'images': images
    })

@app.route('/api/posture/distribution')
def api_posture_distribution():
    """获取坐姿分布数据"""
    range_type = request.args.get('range', 'day')
    
    # 模拟分布数据
    if range_type == 'day':
        data = {
            'heatmapData': [85, 78, 72, 65, 58, 82, 90, 88]
        }
    elif range_type == 'week':
        data = {
            'heatmapData': [88, 82, 75, 68, 72, 85, 92, 89]
        }
    else:  # month
        data = {
            'heatmapData': [90, 85, 78, 72, 75, 88, 94, 91]
        }
    
    return jsonify(data)

# 用眼情况API接口
@app.route('/api/eye/data')
def api_eye_data():
    """获取用眼数据"""
    # 模拟用眼数据
    data = {
        'continuousTime': '2.5小时',
        'blinkRate': '15次/分钟',
        'screenDistance': '45cm',
        'weeklyData': [65, 72, 68, 75, 82, 58, 45],
        'feedback': [
            { 'type': 'positive', 'text': '本周平均远眺次数：4.3 次/天', 'icon': 'bi-check-circle-fill' },
            { 'type': 'positive', 'text': '当前环境光照：良好', 'icon': 'bi-brightness-high-fill' },
            { 'type': 'positive', 'text': '色温状态：柔和', 'icon': 'bi-thermometer-sun' },
            { 'type': 'warning', 'text': '昨日连续用眼超时：72 分钟', 'icon': 'bi-exclamation-triangle-fill' }
        ]
    }
    
    return jsonify(data)

@app.route('/api/eye/feedback')
def api_eye_feedback():
    """获取用眼反馈数据"""
    # 模拟反馈数据
    feedback = [
        { 'type': 'positive', 'text': '本周平均远眺次数：4.3 次/天', 'icon': 'bi-check-circle-fill' },
        { 'type': 'positive', 'text': '当前环境光照：良好', 'icon': 'bi-brightness-high-fill' },
        { 'type': 'positive', 'text': '色温状态：柔和', 'icon': 'bi-thermometer-sun' },
        { 'type': 'warning', 'text': '昨日连续用眼超时：72 分钟', 'icon': 'bi-exclamation-triangle-fill' },
        { 'type': 'positive', 'text': '护眼模式已开启', 'icon': 'bi-shield-check' },
        { 'type': 'info', 'text': '建议每30分钟休息5分钟', 'icon': 'bi-info-circle' }
    ]
    
    return jsonify({
        'status': 'success',
        'feedback': feedback
    })

@app.route('/api/eye/weekly')
def api_eye_weekly():
    """获取用眼周数据"""
    # 模拟周数据
    data = {
        'weeklyData': [65, 72, 68, 75, 82, 58, 45],
        'summary': {
            'averageIntensity': 66.4,
            'maxIntensity': 82,
            'minIntensity': 45,
            'improvement': '+12%'
        }
    }
    
    return jsonify(data)

# 情绪识别API接口
@app.route('/api/emotion/data')
def api_emotion_data():
    """获取情绪数据"""
    # 模拟情绪数据
    data = {
        'dominantEmotion': '高兴',
        'emotionScore': 4.2,
        'stability': '良好',
        'stabilityChange': 15,
        'timeline': [
            { 'time': '15:30', 'emotion': '高兴', 'emoji': '😊' },
            { 'time': '14:45', 'emotion': '平静', 'emoji': '😐' },
            { 'time': '14:20', 'emotion': '焦虑', 'emoji': '😟' },
            { 'time': '13:55', 'emotion': '高兴', 'emoji': '😊' },
            { 'time': '13:30', 'emotion': '兴奋', 'emoji': '🤩' },
            { 'time': '13:05', 'emotion': '平静', 'emoji': '😐' }
        ],
        'distribution': {
            '高兴': 40,
            '平静': 35,
            '焦虑': 15,
            '兴奋': 10
        },
        'trend': [4.2, 3.8, 4.0, 3.5, 4.5, 4.2, 4.0]
    }
    
    return jsonify(data)

# 家长监护API接口
@app.route('/api/guardian/scheduled_messages')
def api_guardian_scheduled_messages():
    """获取定时消息列表"""
    # 模拟定时消息数据
    messages = [
        {
            'id': 1,
            'content': '记得保持正确坐姿哦',
            'scheduledTime': '2025-01-20T10:30:00Z',
            'status': 'pending'
        },
        {
            'id': 2,
            'content': '该休息一下眼睛了',
            'scheduledTime': '2025-01-20T11:00:00Z',
            'status': 'pending'
        },
        {
            'id': 3,
            'content': '记得喝水补充水分',
            'scheduledTime': '2025-01-20T11:30:00Z',
            'status': 'pending'
        }
    ]
    
    return jsonify(messages)

@app.route('/api/guardian/messages', methods=['GET'])
def api_guardian_messages():
    """获取消息历史"""
    # 模拟消息历史数据
    messages = [
        {
            'id': 1,
            'sender': 'parent',
            'content': '记得保持正确坐姿哦',
            'type': 'immediate',
            'timestamp': '2025-01-20T09:30:00Z'
        },
        {
            'id': 2,
            'sender': 'parent',
            'content': '该休息一下眼睛了',
            'type': 'immediate',
            'timestamp': '2025-01-20T09:00:00Z'
        },
        {
            'id': 3,
            'sender': 'system',
            'content': '检测到坐姿不良，已自动提醒',
            'type': 'system',
            'timestamp': '2025-01-20T08:45:00Z'
        }
    ]
    
    return jsonify(messages)

@app.route('/api/guardian/send_message', methods=['POST'])
def api_guardian_send_message():
    """发送消息"""
    data = request.get_json()
    message_content = data.get('content', '')
    
    # 模拟发送消息
    response = {
        'status': 'success',
        'message': '消息发送成功',
        'data': {
            'id': random.randint(1000, 9999),
            'content': message_content,
            'timestamp': datetime.now().isoformat()
        }
    }
    
    return jsonify(response)

# 远程控制API接口
@app.route('/api/lamp/power', methods=['POST'])
def api_lamp_power():
    """控制台灯电源"""
    data = request.get_json()
    power = data.get('power', False)
    
    # 模拟台灯控制
    response = {
        'status': 'success',
        'message': f'台灯已{"开启" if power else "关闭"}',
        'data': {
            'power': power
        }
    }
    
    return jsonify(response)

@app.route('/api/lamp/brightness', methods=['POST'])
def api_lamp_brightness():
    """控制台灯亮度"""
    data = request.get_json()
    brightness = data.get('brightness', 500)
    
    # 模拟亮度控制
    response = {
        'status': 'success',
        'message': f'亮度已调整为{brightness}',
        'data': {
            'brightness': brightness
        }
    }
    
    return jsonify(response)

@app.route('/api/lamp/color_temp', methods=['POST'])
def api_lamp_color_temp():
    """控制台灯色温"""
    data = request.get_json()
    color_temp = data.get('color_temp', 5300)
    
    # 模拟色温控制
    response = {
        'status': 'success',
        'message': f'色温已调整为{color_temp}K',
        'data': {
            'color_temp': color_temp
        }
    }
    
    return jsonify(response)

@app.route('/api/lamp/settings', methods=['POST'])
def api_lamp_settings():
    """应用台灯设置"""
    data = request.get_json()
    
    # 模拟设置应用
    response = {
        'status': 'success',
        'message': '设置已应用',
        'data': data
    }
    
    return jsonify(response)

@app.route('/api/lamp/scene', methods=['POST'])
def api_lamp_scene():
    """切换台灯场景"""
    data = request.get_json()
    scene = data.get('scene', 'normal')
    
    # 模拟场景切换
    response = {
        'status': 'success',
        'message': f'已切换到{scene}模式',
        'data': {
            'scene': scene
        }
    }
    
    return jsonify(response)

@app.route('/api/lamp/timer', methods=['POST'])
def api_lamp_timer():
    """设置台灯定时器"""
    data = request.get_json()
    timer_enabled = data.get('timer_enabled', False)
    timer_duration = data.get('timer_duration', 30)
    
    # 模拟定时器设置
    response = {
        'status': 'success',
        'message': f'定时器已{"开启" if timer_enabled else "关闭"}，时长{timer_duration}分钟',
        'data': {
            'timer_enabled': timer_enabled,
            'timer_duration': timer_duration
        }
    }
    
    return jsonify(response)

@app.route('/api/lamp/status')
def api_lamp_status():
    """获取台灯状态"""
    return jsonify({
        'status': 'success',
        'data': {
            'power': True,
            'brightness': 500,
            'color_temp': 5300,
            'mode': 'manual'
        },
        'lastUpdate': datetime.now().isoformat()
    })

@app.route('/api/lamp/control/<action>', methods=['POST'])
def api_lamp_control(action):
    """台灯控制"""
    try:
        data = request.get_json() or {}
        value = data.get('value')
        
        # 模拟控制响应
        response = {
            'success': True,
            'action': action,
            'value': value,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/notifications')
def api_notification_settings():
    """获取通知设置"""
    return jsonify({
        'posture': True,
        'eye': True,
        'emotion': False,
        'report': True
    })

@app.route('/api/settings/notifications', methods=['POST'])
def api_update_notification_settings():
    """更新通知设置"""
    try:
        data = request.get_json()
        # 模拟保存设置
        return jsonify({'success': True, 'settings': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tool/<tool_name>/data')
def api_tool_data(tool_name):
    """获取工具数据"""
    if tool_name == 'posture':
        return jsonify({
            'goodPostureTime': '3.2h',
            'mildBadPostureTime': '1.2h',
            'badPostureTime': '0.6h',
            'postureRate': '64%',
            'chartData': {
                'labels': ['良好坐姿', '轻度不良', '不良坐姿'],
                'data': [64, 24, 12]
            }
        })
    elif tool_name == 'eye':
        return jsonify({
            'continuousTime': '2.5小时',
            'blinkRate': '15次/分钟',
            'distance': '45cm',
            'restCount': 12
        })
    elif tool_name == 'emotion':
        return jsonify({
            'dominantEmotion': '高兴',
            'emotionScore': 4.2,
            'stability': '良好',
            'improvement': '15%'
        })
    else:
        return jsonify({'error': 'Unknown tool'}), 404

@app.route('/api/tool/<tool_name>/images')
def api_tool_images(tool_name):
    """获取工具相关图片"""
    # 模拟图片数据
    images = []
    for i in range(10):
        timestamp = datetime.now() - timedelta(hours=i)
        images.append({
            'id': i + 1,
            'url': f'/static/posture_images/posture_{timestamp.strftime("%Y%m%d_%H%M%S")}_{random.randint(10000000, 99999999)}.jpg',
            'timestamp': timestamp.isoformat(),
            'type': tool_name
        })
    
    return jsonify(images)

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# 开发模式下的调试路由
@app.route('/debug')
def debug():
    """调试页面"""
    return jsonify({
        'user_agent': request.headers.get('User-Agent'),
        'is_mobile': is_mobile(),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
