"""
数据库操作模块 - 处理所有与数据库相关的操作
"""
import mysql.connector
from datetime import datetime, timedelta
import pytz
import json
import os
from config import DB_CONFIG

# 添加图像存储路径配置
POSTURE_IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'posture_images')

# 确保图像存储目录存在
os.makedirs(POSTURE_IMAGES_DIR, exist_ok=True)

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
        
        # 创建坐姿图像记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posture_images (
                id INT AUTO_INCREMENT PRIMARY KEY,
                image_path VARCHAR(255) NOT NULL,
                angle FLOAT,
                is_bad_posture BOOLEAN DEFAULT FALSE,
                posture_status VARCHAR(50),
                emotion VARCHAR(50),
                timestamp DATETIME(6),
                notes TEXT
            )
        """)
        
        # 创建坐姿时间记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posture_time_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                start_time DATETIME(6) NOT NULL,
                end_time DATETIME(6) NOT NULL,
                duration_seconds FLOAT NOT NULL,
                angle FLOAT,
                posture_type ENUM('good', 'mild', 'moderate', 'severe') NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                notes TEXT
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

def save_posture_image(image, angle, is_bad_posture, posture_status, emotion, notes=""):
    """保存坐姿图像并记录到数据库
    
    Args:
        image: OpenCV图像对象 (numpy.ndarray)
        angle: 头部角度
        is_bad_posture: 是否是不良坐姿
        posture_status: 坐姿状态描述
        emotion: 表情状态
        notes: 附加说明
        
    Returns:
        成功时返回图像ID和路径，失败时返回None
    """
    import cv2
    from uuid import uuid4
    
    try:
        # 生成唯一文件名
        timestamp = datetime.now()
        filename = f"posture_{timestamp.strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}.jpg"
        image_path = os.path.join(POSTURE_IMAGES_DIR, filename)
        
        # 保存图像
        cv2.imwrite(image_path, image)
        
        # 相对路径，用于前端访问
        relative_path = f"/static/posture_images/{filename}"
        
        # 保存图像记录到数据库
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        sql = """INSERT INTO posture_images 
                (image_path, angle, is_bad_posture, posture_status, emotion, timestamp, notes) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        
        values = (
            relative_path,
            angle,
            is_bad_posture,
            posture_status,
            emotion,
            timestamp,
            notes
        )
        
        cursor.execute(sql, values)
        conn.commit()
        image_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        print(f"保存坐姿图像成功，ID: {image_id}, 路径: {relative_path}")
        
        return {
            "id": image_id,
            "path": relative_path
        }
    except Exception as e:
        print(f"保存坐姿图像失败: {str(e)}")
        return None

def get_posture_images(page=1, per_page=10, bad_posture_only=False):
    """获取坐姿图像记录，支持分页和筛选
    
    Args:
        page: 页码，从1开始
        per_page: 每页记录数
        bad_posture_only: 是否只获取不良坐姿记录
    
    Returns:
        包含图像记录和分页信息的字典
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 计算总记录数
        count_sql = "SELECT COUNT(*) as count FROM posture_images"
        if (bad_posture_only):
            count_sql += " WHERE is_bad_posture = TRUE"
        
        cursor.execute(count_sql)
        total_count = cursor.fetchone()['count']
        
        # 分页查询
        offset = (page - 1) * per_page
        
        query_sql = """
            SELECT id, image_path, angle, is_bad_posture, posture_status, emotion, 
                   timestamp, notes
            FROM posture_images
        """
        
        if bad_posture_only:
            query_sql += " WHERE is_bad_posture = TRUE"
            
        query_sql += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
        
        cursor.execute(query_sql, (per_page, offset))
        records = cursor.fetchall()
        
        # 处理时间戳格式
        for record in records:
            if 'timestamp' in record and record['timestamp']:
                record['timestamp'] = record['timestamp'].isoformat()
        
        cursor.close()
        conn.close()
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return {
            'records': records,
            'pagination': {
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages
            }
        }
    except Exception as e:
        print(f"获取坐姿图像记录失败: {str(e)}")
        return {
            'records': [],
            'pagination': {
                'total': 0,
                'page': page,
                'per_page': per_page,
                'total_pages': 0
            },
            'error': str(e)
        }

def delete_posture_image(image_id):
    """删除指定的坐姿图像记录及文件
    
    Args:
        image_id: 图像记录ID
    
    Returns:
        操作是否成功
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 先获取图像路径
        cursor.execute("SELECT image_path FROM posture_images WHERE id = %s", (image_id,))
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            conn.close()
            return False
            
        image_path = result[0]
        
        # 从数据库中删除记录
        cursor.execute("DELETE FROM posture_images WHERE id = %s", (image_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        # 删除物理文件
        try:
            # 正确处理路径：从/static/posture_images/filename.jpg转换为实际的文件系统路径
            if image_path.startswith('/static/'):
                # 获取项目根目录
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                # 构建完整路径 (不需要重复添加'static'目录)
                full_path = os.path.join(project_root, image_path[1:])  # 移除开头的'/'
            else:
                # 如果路径不是以/static/开头，尝试在posture_images目录中查找
                filename = os.path.basename(image_path)
                full_path = os.path.join(POSTURE_IMAGES_DIR, filename)
            
            if os.path.exists(full_path):
                os.remove(full_path)
                print(f"已删除文件: {full_path}")
            else:
                print(f"警告: 文件不存在: {full_path}")
        except Exception as e:
            print(f"删除图像文件时出错: {str(e)}")
        
        return True
    except Exception as e:
        print(f"删除坐姿图像记录失败: {str(e)}")
        return False

def clear_posture_images(days_to_keep=None):
    """清空坐姿图像记录
    
    Args:
        days_to_keep: 保留多少天内的记录，None表示全部清空
    
    Returns:
        删除的记录数
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 获取要删除的图像路径
        if days_to_keep is not None:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cursor.execute("SELECT id, image_path FROM posture_images WHERE timestamp < %s", (cutoff_date,))
        else:
            cursor.execute("SELECT id, image_path FROM posture_images")
            
        images_to_delete = cursor.fetchall()
        
        # 删除记录
        deleted_count = 0
        for image_id, image_path in images_to_delete:
            # 从数据库删除
            cursor.execute("DELETE FROM posture_images WHERE id = %s", (image_id,))
            
            # 删除文件
            if image_path.startswith('/static/'):
                image_path = image_path[8:]  # 移除'/static/'前缀
                
            full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', image_path)
            
            if os.path.exists(full_path):
                os.remove(full_path)
                
            deleted_count += 1
            
        conn.commit()
        cursor.close()
        conn.close()
        
        return deleted_count
    except Exception as e:
        print(f"清空坐姿图像记录失败: {str(e)}")
        return 0
    
def get_history_records(page=1, per_page=10):
    """获取历史记录，支持分页"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 计算总记录数
        cursor.execute("SELECT COUNT(*) as count FROM serial_records")
        total_count = cursor.fetchone()['count']
        
        # 分页查询
        offset = (page - 1) * per_page
        
        query = """
            SELECT id, sent_data, received_data, status, message, timestamp
            FROM serial_records
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, (per_page, offset))
        records = cursor.fetchall()
        
        # 处理时间戳格式
        for record in records:
            if 'timestamp' in record and record['timestamp']:
                record['timestamp'] = record['timestamp'].isoformat()
        
        cursor.close()
        conn.close()
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return {
            'records': records,
            'pagination': {
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages
            }
        }
    except Exception as e:
        print(f"获取历史记录失败: {str(e)}")
        return {
            'records': [],
            'pagination': {
                'total': 0,
                'page': page,
                'per_page': per_page,
                'total_pages': 0
            },
            'error': str(e)
        }

def clear_history():
    """清空历史记录"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM serial_records")
        conn.commit()
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"清空历史记录失败: {str(e)}")
        return False

def record_posture_time(start_time, end_time, duration_seconds, angle, posture_type, notes=""):
    """记录坐姿时间段
    
    Args:
        start_time: 开始时间 (datetime对象)
        end_time: 结束时间 (datetime对象)
        duration_seconds: 持续时间(秒)
        angle: 头部角度平均值
        posture_type: 坐姿类型('excellent', 'good', 'fair', 'poor')
        notes: 备注信息
        
    Returns:
        成功返回记录ID，失败返回None
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        sql = """INSERT INTO posture_time_records 
                (start_time, end_time, duration_seconds, angle, posture_type, notes) 
                VALUES (%s, %s, %s, %s, %s, %s)"""
        
        values = (
            start_time,
            end_time,
            duration_seconds,
            angle,
            posture_type,
            notes
        )
        
        cursor.execute(sql, values)
        conn.commit()
        record_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        print(f"记录坐姿时间成功，ID: {record_id}, 类型: {posture_type}, 持续: {duration_seconds}秒")
        
        return record_id
    except Exception as e:
        print(f"记录坐姿时间失败: {str(e)}")
        return None

def get_posture_stats(time_range='day'):
    """获取坐姿统计数据
    
    Args:
        time_range: 时间范围 'day', 'week', 'month'
    
    Returns:
        包含各类坐姿占比和时长的字典
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 根据时间范围确定查询的开始时间
        now = datetime.now()
        if time_range == 'day':
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == 'week':
            # 获取本周一的日期
            days_since_monday = now.weekday()
            start_time = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == 'month':
            # 获取本月1日的日期
            start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            # 默认为今天
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 查询每种坐姿类型的总时长
        query = """
            SELECT 
                posture_type,
                SUM(duration_seconds) as total_seconds
            FROM posture_time_records
            WHERE start_time >= %s
            GROUP BY posture_type
        """
        
        cursor.execute(query, (start_time,))
        results = cursor.fetchall()
        
        # 计算总监测时间
        cursor.execute("""
            SELECT SUM(duration_seconds) as grand_total
            FROM posture_time_records
            WHERE start_time >= %s
        """, (start_time,))
        
        total_result = cursor.fetchone()
        total_time = total_result['grand_total'] if total_result and total_result['grand_total'] else 0
        
        # 初始化结果字典，使用新的四档坐姿类型
        stats = {
            'good': {'seconds': 0, 'percentage': 0, 'formatted_time': '0h 0m'},
            'mild': {'seconds': 0, 'percentage': 0, 'formatted_time': '0h 0m'},
            'moderate': {'seconds': 0, 'percentage': 0, 'formatted_time': '0h 0m'},
            'severe': {'seconds': 0, 'percentage': 0, 'formatted_time': '0h 0m'},
            'total_time': {'seconds': total_time, 'formatted_time': format_seconds(total_time)},
            'time_range': time_range,
            'start_time': start_time.isoformat() if start_time else None,
            'end_time': now.isoformat()
        }
        
        # 填充结果
        for result in results:
            posture_type = result['posture_type']
            seconds = result['total_seconds'] if result['total_seconds'] else 0
            
            # 确保posture_type是有效的键
            if posture_type in stats:
                stats[posture_type]['seconds'] = seconds
                stats[posture_type]['formatted_time'] = format_seconds(seconds)
                
                if total_time > 0:
                    stats[posture_type]['percentage'] = round((seconds / total_time) * 100, 1)
                else:
                    stats[posture_type]['percentage'] = 0
        
        # 计算总的良好坐姿比例
        good_posture_seconds = stats['good']['seconds']
        if total_time > 0:
            stats['good_posture_percentage'] = round((good_posture_seconds / total_time) * 100, 1)
        else:
            stats['good_posture_percentage'] = 0
        
        cursor.close()
        conn.close()
        
        return stats
    except Exception as e:
        print(f"获取坐姿统计数据失败: {str(e)}")
        return {
            'good': {'seconds': 0, 'percentage': 0, 'formatted_time': '0h 0m'},
            'mild': {'seconds': 0, 'percentage': 0, 'formatted_time': '0h 0m'},
            'moderate': {'seconds': 0, 'percentage': 0, 'formatted_time': '0h 0m'},
            'severe': {'seconds': 0, 'percentage': 0, 'formatted_time': '0h 0m'},
            'total_time': {'seconds': 0, 'formatted_time': '0h 0m'},
            'time_range': time_range,
            'error': str(e)
        }

def format_seconds(seconds):
    """将秒数格式化为可读时间格式
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化后的时间字符串，例如: "2h 30m" 或 "45m"
    """
    if not seconds:
        return "0m"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def clear_posture_time_records(days_to_keep=None):
    """清除坐姿时间记录
    
    Args:
        days_to_keep: 保留多少天内的记录，None表示全部清空
        
    Returns:
        删除的记录数
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        if days_to_keep is not None:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cursor.execute("DELETE FROM posture_time_records WHERE end_time < %s", (cutoff_date,))
        else:
            cursor.execute("DELETE FROM posture_time_records")
            
        deleted_count = cursor.rowcount
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"清除了 {deleted_count} 条坐姿时间记录")
        return deleted_count
    except Exception as e:
        print(f"清除坐姿时间记录失败: {str(e)}")
        return 0