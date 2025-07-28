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

@app.route('/api/guardian/video_status')
def api_video_status():
    """获取视频状态"""
    return jsonify({
        'status': 'live',
        'isStreaming': True,
        'lastFrame': datetime.now().isoformat()
    })

@app.route('/api/guardian/capture')
def api_capture_photo():
    """拍照功能"""
    try:
        # 模拟拍照
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"capture_{timestamp}.jpg"
        
        return jsonify({
            'success': True,
            'filename': filename,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/guardian/send_message', methods=['POST'])
def api_send_message():
    """发送消息"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        message_type = data.get('type', 'immediate')
        
        # 模拟消息发送
        message = {
            'id': random.randint(1000, 9999),
            'content': content,
            'type': message_type,
            'timestamp': datetime.now().isoformat(),
            'status': 'sent'
        }
        
        return jsonify({
            'success': True,
            'message': message
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/guardian/messages')
def api_get_messages():
    """获取消息历史"""
    # 模拟消息历史
    messages = [
        {
            'id': 1,
            'sender': 'parent',
            'content': '记得保持正确坐姿哦',
            'type': 'sent',
            'timestamp': (datetime.now() - timedelta(hours=1)).isoformat()
        },
        {
            'id': 2,
            'sender': 'scheduled',
            'content': '该休息一下眼睛了',
            'type': 'scheduled',
            'timestamp': (datetime.now() + timedelta(minutes=30)).isoformat()
        }
    ]
    return jsonify(messages)

@app.route('/api/lamp/status')
def api_lamp_status():
    """获取台灯状态"""
    return jsonify({
        'power': True,
        'light': True,
        'brightness': 500,
        'temperature': 5300,
        'mode': 'manual',
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
