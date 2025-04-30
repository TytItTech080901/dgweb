from flask import Flask, render_template, jsonify, request
from serial_handler import SerialHandler
import mysql.connector
from datetime import datetime
import pytz
from config import DB_CONFIG, OPEN_HOST, SERIAL_BAUDRATE

app = Flask(__name__)

# 初始化串口处理器
try:
    serial_handler = SerialHandler(port=None, baudrate=SERIAL_BAUDRATE)
except Exception as e:
    print(f"警告：串口初始化失败 - {str(e)}")
    serial_handler = None

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

if __name__ == '__main__':
    init_database()  # Initialize database table
    print(f"Starting server on {OPEN_HOST}:5000...")
    app.run(host=OPEN_HOST, port=5000, debug=True)