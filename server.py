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

app = Flask(__name__)

# 创建事件队列，用于SSE (Server-Sent Events)
frame_queue = queue.Queue(maxsize=100)

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