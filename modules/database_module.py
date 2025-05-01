"""
数据库操作模块 - 处理所有与数据库相关的操作
"""
import mysql.connector
from datetime import datetime
import pytz
import json
from config import DB_CONFIG

def init_database():
    """初始化数据库表结构"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 创建数据表（如果不存在）
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
        print("数据库表初始化成功")
        return True
    except Exception as e:
        print(f"数据库初始化失败: {str(e)}")
        return False

def save_record_to_db(sent_data, received_data, status="success", message=""):
    """保存通信记录到数据库"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        sql = """INSERT INTO serial_records 
                (sent_data, received_data, status, message, timestamp) 
                VALUES (%s, %s, %s, %s, %s)"""
        current_time = datetime.now(pytz.UTC)
        values = (sent_data, received_data, status, message, current_time)
        
        cursor.execute(sql, values)
        conn.commit()
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"保存记录到数据库失败: {str(e)}")
        return False

def save_frame_to_db(frame_data):
    """将接收到的帧数据保存到数据库"""
    try:
        sent_info = "自动接收的数据帧"
        received_info = json.dumps(frame_data)
        status = "success"
        message = "自动接收到数据帧"
        
        if save_record_to_db(sent_info, received_info, status, message):
            print(f"帧数据已保存到数据库: {received_info}")
            return True
        return False
    except Exception as e:
        print(f"保存帧数据到数据库时出错: {str(e)}")
        return False

def get_history_records(page=1, per_page=10):
    """获取历史记录，支持分页"""
    try:
        offset = (page - 1) * per_page
        
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
        
        return {
            'records': records,
            'total': total,
            'current_page': page,
            'per_page': per_page,
            'total_pages': total_pages
        }
    except Exception as e:
        print(f"获取历史记录失败: {str(e)}")
        return {
            'status': 'error',
            'message': str(e),
            'records': [],
            'total': 0,
            'current_page': page,
            'per_page': per_page,
            'total_pages': 0
        }

def clear_history():
    """清空历史记录"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("TRUNCATE TABLE serial_records")
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"清空历史记录失败: {str(e)}")
        return False