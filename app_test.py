import os
import re
from flask import Flask, render_template, send_from_directory, request, jsonify

app = Flask(__name__)

def is_mobile():
    user_agent = request.headers.get('User-Agent')
    mobile_pattern = r'Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini'
    return bool(user_agent and re.search(mobile_pattern, user_agent))

@app.route('/')
def index():
    # 根据设备类型返回不同模板
    if is_mobile():
        return render_template('mobile.html')
    else:
        return render_template('main.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# 模拟视频流
@app.route('/video_feed')
def video_feed():
    # 返回一个简单的占位图像URL或处理
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'placeholder.jpg', mimetype='image/jpeg')

# 添加模拟的API
@app.route('/get_pose_status')
def get_pose_status():
    # 模拟的响应
    return jsonify({
        'status': 'success',
        'is_running': True
    })

@app.route('/start_pose_analysis')
def start_pose_analysis():
    return jsonify({
        'status': 'success',
        'message': '姿势分析已启动'
    })

@app.route('/stop_pose_analysis')
def stop_pose_analysis():
    return jsonify({
        'status': 'success',
        'message': '姿势分析已停止'
    })

@app.route('/lamp_status')
def lamp_status():
    # 模拟台灯状态
    return jsonify({
        'status': 'success',
        'is_on': True,
        'brightness': 80,
        'color': 'warm',
        'mode': 'reading'
    })

@app.route('/get_posture_records')
def get_posture_records():
    # 模拟姿势记录数据
    records = [
        {
            'id': 1,
            'timestamp': 1722010800,  # 2025-07-26 10:00:00
            'posture_type': '正确姿势',
            'confidence': 0.95
        },
        {
            'id': 2,
            'timestamp': 1722014400,  # 2025-07-26 11:00:00
            'posture_type': '低头',
            'confidence': 0.87
        },
        {
            'id': 3,
            'timestamp': 1722018000,  # 2025-07-26 12:00:00
            'posture_type': '前倾',
            'confidence': 0.91
        }
    ]
    return jsonify({
        'status': 'success',
        'records': records
    })

@app.route('/get_posture_stats')
def get_posture_stats():
    # 模拟姿势统计数据
    stats = {
        'correct': 75,
        'head_down': 15,
        'leaning_forward': 8,
        'leaning_side': 2,
        'other': 0
    }
    return jsonify({
        'status': 'success',
        'stats': stats
    })

@app.route('/lamp_control/<action>')
def lamp_control(action):
    # 模拟台灯控制
    valid_actions = ['on', 'off', 'brighter', 'dimmer', 'reading_mode', 
                     'study_mode', 'rest_mode', 'night_mode']
    
    if action in valid_actions:
        return jsonify({
            'status': 'success',
            'message': f'台灯已{action}'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': '无效的操作'
        })

@app.route('/lamp_control/<action>/<value>')
def lamp_control_with_value(action, value):
    # 支持带参数的台灯控制（如亮度、色温）
    if action in ['brightness', 'temperature']:
        return jsonify({
            'status': 'success',
            'message': f'{action}已调节至{value}'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': '无效的操作'
        })

@app.route('/lamp_control/mode/<mode>')
def lamp_mode_control(mode):
    # 台灯模式控制
    valid_modes = ['reading', 'study', 'rest', 'night']
    if mode in valid_modes:
        return jsonify({
            'status': 'success',
            'message': f'已切换至{mode}模式'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': '无效的模式'
        })

@app.route('/capture_photo')
def capture_photo():
    # 模拟拍照功能
    return jsonify({
        'status': 'success',
        'message': '照片已保存',
        'filename': f'photo_{int(__import__("time").time())}.jpg'
    })

@app.route('/send_message', methods=['POST'])
def send_message():
    # 模拟消息发送
    data = request.get_json()
    if data and 'content' in data:
        return jsonify({
            'status': 'success',
            'message': '消息已发送'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': '消息内容不能为空'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
