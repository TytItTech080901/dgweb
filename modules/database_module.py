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
    print(f"尝试删除坐姿图像记录，ID: {image_id}")
    try:
        # 尝试连接数据库
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 先获取图像路径
        cursor.execute("SELECT image_path FROM posture_images WHERE id = %s", (image_id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"错误：未找到ID为 {image_id} 的坐姿图像记录")
            cursor.close()
            conn.close()
            return False
            
        image_path = result[0]
        print(f"找到图像记录，路径: {image_path}")
        
        # 从数据库中删除记录
        cursor.execute("DELETE FROM posture_images WHERE id = %s", (image_id,))
        conn.commit()
        
        db_deleted = cursor.rowcount > 0
        if db_deleted:
            print(f"已从数据库删除图像记录，ID: {image_id}")
        else:
            print(f"警告：数据库删除操作未影响任何记录，ID: {image_id}")
        
        cursor.close()
        conn.close()
        
        # 删除物理文件
        file_deleted = False
        try:
            # 处理文件路径
            # 如果路径以/static/开头
            if image_path.startswith('/static/'):
                # 获取项目根目录
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                # 构建完整路径
                full_path = os.path.join(project_root, image_path[1:])  # 移除开头的'/'
                print(f"尝试删除文件: {full_path}")
            else:
                # 如果路径不是以/static/开头，尝试在posture_images目录中查找
                filename = os.path.basename(image_path)
                full_path = os.path.join(POSTURE_IMAGES_DIR, filename)
                print(f"尝试删除文件: {full_path}")
            
            if os.path.exists(full_path):
                os.remove(full_path)
                file_deleted = True
                print(f"成功删除文件: {full_path}")
            else:
                print(f"警告: 文件不存在: {full_path}")
                # 尽管文件不存在，我们仍然认为操作成功，因为数据库记录已删除
                file_deleted = True
        except Exception as e:
            print(f"删除图像文件时出错: {str(e)}")
            # 文件删除失败，但数据库记录已删除，我们仍然返回True
            # 因为主要目标是从数据库中删除记录
        
        # 如果数据库删除成功，即使文件删除失败也返回True
        return db_deleted
        
    except Exception as e:
        print(f"删除坐姿图像记录失败: {str(e)}")
        import traceback
        traceback.print_exc()  # 打印完整的堆栈跟踪以便调试
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

def get_posture_stats(time_range='day', custom_start_date=None, custom_end_date=None, with_hourly_data=False):
    """获取坐姿统计数据
    
    Args:
        time_range: 时间范围 'day', 'week', 'month', 'custom'
        custom_start_date: 自定义开始日期 (datetime对象)，仅当time_range为'custom'时有效
        custom_end_date: 自定义结束日期 (datetime对象)，仅当time_range为'custom'时有效
        with_hourly_data: 是否返回每小时数据统计
        
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
        elif time_range == 'custom' and custom_start_date and custom_end_date:
            # 使用自定义日期范围
            start_time = custom_start_date
            now = custom_end_date
        else:
            # 默认为今天
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 优化查询 - 添加索引提示
        query = """
            SELECT 
                posture_type,
                SUM(duration_seconds) as total_seconds
            FROM posture_time_records
            WHERE start_time >= %s AND end_time <= %s
            GROUP BY posture_type
        """
        
        cursor.execute(query, (start_time, now))
        results = cursor.fetchall()
        
        # 计算总监测时间
        cursor.execute("""
            SELECT SUM(duration_seconds) as grand_total
            FROM posture_time_records
            WHERE start_time >= %s AND end_time <= %s
        """, (start_time, now))
        
        total_result = cursor.fetchone()
        total_time = total_result['grand_total'] if total_result and total_result['grand_total'] else 0
        
        # 初始化结果字典，使用前端期望的类型名称格式
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
        
        # 数据库类型到前端类型的映射
        type_mapping = {
            'excellent': 'good',   # 数据库中的excellent映射到前端的good
            'good': 'good',        # 数据库中的good也映射到前端的good
            'fair': 'mild',        # 数据库中的fair映射到前端的mild
            'poor': 'moderate'     # 数据库中的poor映射到前端的moderate
            # 其他未知类型自动映射为severe
        }
        
        # 填充结果
        for result in results:
            db_posture_type = result['posture_type']
            seconds = result['total_seconds'] if result['total_seconds'] else 0
            
            # 映射数据库类型到前端类型
            frontend_type = type_mapping.get(db_posture_type, 'severe')
            
            if frontend_type in stats:
                stats[frontend_type]['seconds'] += seconds
                stats[frontend_type]['formatted_time'] = format_seconds(stats[frontend_type]['seconds'])
                
                if total_time > 0:
                    stats[frontend_type]['percentage'] = round((stats[frontend_type]['seconds'] / total_time) * 100, 1)
                else:
                    stats[frontend_type]['percentage'] = 0
        
        # 计算总的良好坐姿比例
        good_posture_seconds = stats['good']['seconds']
        if total_time > 0:
            stats['good_posture_percentage'] = round((good_posture_seconds / total_time) * 100, 1)
        else:
            stats['good_posture_percentage'] = 0
        
        # 添加每小时数据
        if with_hourly_data:
            hourly_data = get_hourly_posture_data(start_time, now)
            stats['hourly_data'] = hourly_data
        
        cursor.close()
        conn.close()
        
        return stats
    except Exception as e:
        print(f"获取坐姿统计数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
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

def get_hourly_posture_data(start_time, end_time):
    """获取按小时统计的坐姿数据
    
    Args:
        start_time: 开始时间 (datetime对象)
        end_time: 结束时间 (datetime对象)
    
    Returns:
        包含每小时坐姿分布的列表
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 初始化结果
        hourly_data = []
        
        # 根据时间跨度调整查询粒度
        time_diff = end_time - start_time
        
        # 如果时间跨度大于3天，按日统计
        if time_diff.days > 3:
            # 生成日期范围
            current_date = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            while current_date <= end_time:
                next_date = current_date + timedelta(days=1)
                
                # 查询各类坐姿时长
                query = """
                    SELECT 
                        posture_type,
                        SUM(duration_seconds) as total_seconds
                    FROM posture_time_records
                    WHERE start_time >= %s AND end_time < %s
                    GROUP BY posture_type
                """
                
                cursor.execute(query, (current_date, next_date))
                results = cursor.fetchall()
                
                # 初始化当天数据
                day_data = {
                    'timestamp': current_date.isoformat(),
                    'label': current_date.strftime('%m-%d'),
                    'good': 0,
                    'mild': 0, 
                    'moderate': 0,
                    'severe': 0,
                    'total': 0
                }
                
                # 填充坐姿数据
                for result in results:
                    posture_type = result['posture_type']
                    seconds = float(result['total_seconds']) if result['total_seconds'] else 0
                    
                    if posture_type in day_data:
                        day_data[posture_type] = seconds
                        day_data['total'] += seconds
                
                hourly_data.append(day_data)
                current_date = next_date
                
        # 否则按小时统计
        else:
            # 生成小时范围
            current_hour = start_time.replace(minute=0, second=0, microsecond=0)
            while current_hour <= end_time:
                next_hour = current_hour + timedelta(hours=1)
                
                # 查询各类坐姿时长
                query = """
                    SELECT 
                        posture_type,
                        SUM(duration_seconds) as total_seconds
                    FROM posture_time_records
                    WHERE start_time >= %s AND end_time < %s
                    GROUP BY posture_type
                """
                
                cursor.execute(query, (current_hour, next_hour))
                results = cursor.fetchall()
                
                # 初始化当小时数据
                hour_data = {
                    'timestamp': current_hour.isoformat(),
                    'label': current_hour.strftime('%H:%M'),
                    'good': 0,
                    'mild': 0, 
                    'moderate': 0,
                    'severe': 0,
                    'total': 0
                }
                
                # 填充坐姿数据
                for result in results:
                    posture_type = result['posture_type']
                    seconds = float(result['total_seconds']) if result['total_seconds'] else 0
                    
                    if posture_type in hour_data:
                        hour_data[posture_type] = seconds
                        hour_data['total'] += seconds
                
                hourly_data.append(hour_data)
                current_hour = next_hour
        
        cursor.close()
        conn.close()
        
        return hourly_data
        
    except Exception as e:
        print(f"获取按小时坐姿数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def export_all_posture_records(time_range='all', start_date=None, end_date=None):
    """导出所有坐姿相关记录，包括图像记录和时间记录
    
    Args:
        time_range: 时间范围 'all', 'day', 'week', 'month', 'custom'
        start_date: 自定义开始日期 (datetime对象)，仅当time_range为'custom'时有效
        end_date: 自定义结束日期 (datetime对象)，仅当time_range为'custom'时有效
        
    Returns:
        包含所有坐姿记录的字典
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
        elif time_range == 'custom' and start_date and end_date:
            # 使用自定义日期范围
            start_time = start_date
            now = end_date
        else:
            # 默认为全部
            start_time = datetime(2000, 1, 1)  # 很早的日期
        
        # 获取图像记录
        image_query = """
            SELECT id, image_path, angle, is_bad_posture, posture_status, emotion, 
                   timestamp, notes
            FROM posture_images
            WHERE timestamp >= %s AND timestamp <= %s
            ORDER BY timestamp DESC
        """
        
        cursor.execute(image_query, (start_time, now))
        image_records = cursor.fetchall()
        
        # 处理时间戳格式
        for record in image_records:
            if 'timestamp' in record and record['timestamp']:
                record['timestamp'] = record['timestamp'].isoformat()
        
        # 获取时间记录
        time_query = """
            SELECT id, start_time, end_time, duration_seconds, angle, 
                   posture_type, notes
            FROM posture_time_records
            WHERE start_time >= %s AND end_time <= %s
            ORDER BY start_time DESC
        """
        
        cursor.execute(time_query, (start_time, now))
        time_records = cursor.fetchall()
        
        # 处理时间戳格式
        for record in time_records:
            if 'start_time' in record and record['start_time']:
                record['start_time'] = record['start_time'].isoformat()
            if 'end_time' in record and record['end_time']:
                record['end_time'] = record['end_time'].isoformat()
        
        cursor.close()
        conn.close()
        
        # 构建结果
        result = {
            'image_records': {
                'count': len(image_records),
                'records': image_records
            },
            'time_records': {
                'count': len(time_records),
                'records': time_records
            },
            'time_range': time_range,
            'start_time': start_time.isoformat() if start_time else None,
            'end_time': now.isoformat()
        }
        
        # 获取统计数据
        stats = get_posture_stats(time_range, start_date, end_date, with_hourly_data=False)
        result['stats'] = stats
        
        return result
    except Exception as e:
        print(f"导出所有坐姿记录失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'image_records': {
                'count': 0,
                'records': []
            },
            'time_records': {
                'count': 0,
                'records': []
            },
            'time_range': time_range,
            'error': str(e)
        }

def get_all_posture_records(time_range='all', start_date=None, end_date=None):
    """
    获取所有坐姿历史记录，包括图像记录和时间记录
    
    参数:
    - time_range: 时间范围，可以是 'all', 'day', 'week', 'month', 'custom'
    - start_date: 自定义时间范围的开始日期，格式为 'YYYY-MM-DD'
    - end_date: 自定义时间范围的结束日期，格式为 'YYYY-MM-DD'
    
    返回:
    - 包含所有记录的字典
    """
    import sqlite3
    from datetime import datetime, timedelta
    import os
    from config import DATABASE_PATH
    
    # 确定日期范围
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    time_range_description = "所有记录"
    
    if time_range == 'day':
        # 今天的记录
        start_time = today
        end_time = today + timedelta(days=1) - timedelta(microseconds=1)
        time_range_description = f"今日记录 ({today.strftime('%Y-%m-%d')})"
    
    elif time_range == 'week':
        # 本周的记录（从周一开始）
        days_since_monday = today.weekday()
        start_time = today - timedelta(days=days_since_monday)
        end_time = start_time + timedelta(days=7) - timedelta(microseconds=1)
        time_range_description = f"本周记录 ({start_time.strftime('%Y-%m-%d')} 至 {end_time.strftime('%Y-%m-%d')})"
    
    elif time_range == 'month':
        # 本月的记录
        start_time = today.replace(day=1)
        if start_time.month == 12:
            end_time = datetime(start_time.year + 1, 1, 1) - timedelta(microseconds=1)
        else:
            end_time = datetime(start_time.year, start_time.month + 1, 1) - timedelta(microseconds=1)
        time_range_description = f"本月记录 ({start_time.strftime('%Y-%m-%d')} 至 {end_time.strftime('%Y-%m-%d')})"
    
    elif time_range == 'custom' and start_date and end_date:
        # 自定义时间范围
        try:
            start_time = datetime.strptime(start_date, '%Y-%m-%d')
            end_time = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1) - timedelta(microseconds=1)
            time_range_description = f"自定义时间范围 ({start_date} 至 {end_date})"
        except ValueError:
            # 日期格式错误，使用所有记录
            start_time = None
            end_time = None
            time_range_description = "所有记录（日期格式错误）"
    
    else:
        # 默认为所有记录
        start_time = None
        end_time = None
    
    # 连接数据库
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 准备时间条件字符串
    time_condition = ""
    params = []
    
    if start_time and end_time:
        time_condition = "WHERE timestamp BETWEEN ? AND ?"
        params = [start_time.strftime('%Y-%m-%d %H:%M:%S'), end_time.strftime('%Y-%m-%d %H:%M:%S')]
    
    # 获取坐姿图像记录
    cursor.execute(f"""
        SELECT * FROM posture_images {time_condition} ORDER BY timestamp DESC
    """, params)
    
    image_records = []
    for row in cursor.fetchall():
        record = dict(row)
        # 转换时间戳格式
        if 'timestamp' in record:
            record['formatted_timestamp'] = record['timestamp']
            try:
                dt = datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S')
                record['formatted_timestamp'] = dt.strftime('%Y年%m月%d日 %H:%M:%S')
            except ValueError:
                pass
        image_records.append(record)
    
    # 获取坐姿时间记录
    cursor.execute(f"""
        SELECT * FROM posture_time_records {time_condition} ORDER BY start_time DESC
    """, params)
    
    time_records = []
    for row in cursor.fetchall():
        record = dict(row)
        # 转换时间戳格式
        for time_field in ['start_time', 'end_time']:
            if time_field in record:
                field_formatted = f"formatted_{time_field}"
                record[field_formatted] = record[time_field]
                try:
                    dt = datetime.strptime(record[time_field], '%Y-%m-%d %H:%M:%S')
                    record[field_formatted] = dt.strftime('%Y年%m月%d日 %H:%M:%S')
                except ValueError:
                    pass
        
        # 计算持续时间（秒）
        try:
            start = datetime.strptime(record['start_time'], '%Y-%m-%d %H:%M:%S')
            end = datetime.strptime(record['end_time'], '%Y-%m-%d %H:%M:%S')
            duration_seconds = (end - start).total_seconds()
            record['duration_seconds'] = duration_seconds
            
            # 格式化持续时间
            minutes, seconds = divmod(duration_seconds, 60)
            hours, minutes = divmod(minutes, 60)
            record['formatted_duration'] = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        except (ValueError, KeyError):
            record['duration_seconds'] = 0
            record['formatted_duration'] = "00:00:00"
        
        time_records.append(record)
    
    # 关闭数据库连接
    conn.close()
    
    # 计算统计数据
    stats = calculate_posture_stats(time_records)
    
    return {
        'status': 'success',
        'time_range': time_range,
        'time_range_description': time_range_description,
        'image_records': {
            'count': len(image_records),
            'records': image_records
        },
        'time_records': {
            'count': len(time_records),
            'records': time_records
        },
        'stats': stats
    }

def calculate_posture_stats(time_records):
    """计算坐姿记录的统计数据"""
    total_seconds = 0
    good_seconds = 0
    mild_seconds = 0
    moderate_seconds = 0
    severe_seconds = 0
    
    for record in time_records:
        if 'duration_seconds' in record and 'posture_type' in record:
            seconds = record['duration_seconds']
            total_seconds += seconds
            
            if record['posture_type'] == 'good':
                good_seconds += seconds
            elif record['posture_type'] == 'mild':
                mild_seconds += seconds
            elif record['posture_type'] == 'moderate':
                moderate_seconds += seconds
            elif record['posture_type'] == 'severe':
                severe_seconds += seconds
    
    # 格式化时间
    def format_time(seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    # 计算百分比
    def calculate_percentage(part, total):
        if total == 0:
            return 0
        return round((part / total) * 100, 2)
    
    return {
        'total_seconds': total_seconds,
        'total_time': format_time(total_seconds),
        'good': {
            'seconds': good_seconds,
            'formatted_time': format_time(good_seconds),
            'percentage': calculate_percentage(good_seconds, total_seconds)
        },
        'mild': {
            'seconds': mild_seconds,
            'formatted_time': format_time(mild_seconds),
            'percentage': calculate_percentage(mild_seconds, total_seconds)
        },
        'moderate': {
            'seconds': moderate_seconds,
            'formatted_time': format_time(moderate_seconds),
            'percentage': calculate_percentage(moderate_seconds, total_seconds)
        },
        'severe': {
            'seconds': severe_seconds,
            'formatted_time': format_time(severe_seconds),
            'percentage': calculate_percentage(severe_seconds, total_seconds)
        }
    }

def clear_all_posture_records(days_to_keep=None):
    """
    清空所有坐姿记录，包括图像记录和时间记录
    
    参数:
    - days_to_keep: 保留最近几天的记录，为None表示清空所有记录
    
    返回:
    - 包含操作结果的字典
    """
    try:
        # 使用已定义的MySQL连接配置
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 删除指定时间范围外的数据
        if days_to_keep is not None and days_to_keep > 0:
            # 计算保留日期的时间戳
            keep_after = datetime.now() - timedelta(days=days_to_keep)
            
            # 删除老数据
            cursor.execute("DELETE FROM posture_images WHERE timestamp < %s", (keep_after,))
            image_deleted_count = cursor.rowcount
            cursor.execute("DELETE FROM posture_time_records WHERE start_time < %s", (keep_after,))
            time_deleted_count = cursor.rowcount
            
            # 获取保留的图像文件名
            cursor.execute("SELECT image_path FROM posture_images")
            kept_images = [row[0] for row in cursor.fetchall()]
            
            # 删除不在数据库中的图像文件
            image_count = 0
            for root, dirs, files in os.walk(POSTURE_IMAGES_DIR):
                for file in files:
                    if file.startswith("posture_") and file.endswith((".jpg", ".png", ".jpeg")):
                        file_path = os.path.join(root, file)
                        relative_path = f"/static/posture_images/{file}"
                        if relative_path not in kept_images:
                            try:
                                os.remove(file_path)
                                image_count += 1
                            except Exception as e:
                                print(f"删除图像文件 {file} 失败: {str(e)}")
            
            # 提交事务
            conn.commit()
            
            msg = f"已清除 {days_to_keep} 天前的所有坐姿记录，删除了 {image_deleted_count} 条图像记录和 {time_deleted_count} 条时间记录"
            print(msg)
        else:
            # 获取要删除的图像文件路径
            cursor.execute("SELECT image_path FROM posture_images")
            image_paths = cursor.fetchall()
            
            # 清空表
            cursor.execute("DELETE FROM posture_images")
            image_deleted_count = cursor.rowcount
            cursor.execute("DELETE FROM posture_time_records")
            time_deleted_count = cursor.rowcount
            
            # 删除图像文件
            image_count = 0
            for root, dirs, files in os.walk(POSTURE_IMAGES_DIR):
                for file in files:
                    if file.startswith("posture_") and file.endswith((".jpg", ".png", ".jpeg")):
                        try:
                            os.remove(os.path.join(root, file))
                            image_count += 1
                        except Exception as e:
                            print(f"删除图像文件 {file} 失败: {str(e)}")
            
            # 提交事务
            conn.commit()
            
            msg = f"已清空所有坐姿记录，删除了 {image_deleted_count} 条图像记录和 {time_deleted_count} 条时间记录，共 {image_count} 个图像文件"
            print(msg)
        
        # 关闭数据库连接
        cursor.close()
        conn.close()
        
        return {
            'status': 'success',
            'message': msg
        }
    except Exception as e:
        print(f"清空坐姿记录失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'message': f"清空坐姿记录失败: {str(e)}"
        }