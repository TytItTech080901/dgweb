"""
数据库处理模块 - 提供数据库操作功能
"""
import mysql.connector
import time
from datetime import datetime

class DBHandler:
    def __init__(self, config):
        """初始化数据库处理器
        
        Args:
            config: 数据库配置字典，包含host, user, password, database等
        """
        self.config = config
        self.ensure_table_exists()
    
    def get_connection(self):
        """获取数据库连接"""
        try:
            return mysql.connector.connect(**self.config)
        except Exception as e:
            print(f"数据库连接失败: {str(e)}")
            return None
    
    def ensure_table_exists(self):
        """确保必要的数据表存在"""
        try:
            conn = self.get_connection()
            if not conn:
                print("无法创建数据表: 数据库连接失败")
                return False
            
            cursor = conn.cursor()
            
            # 创建串口通信历史记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS serial_history (
                    record_number INT AUTO_INCREMENT PRIMARY KEY,
                    sent_data TEXT,
                    received_data TEXT,
                    status VARCHAR(50),
                    message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建坐姿记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posture_records (
                    id VARCHAR(36) PRIMARY KEY,
                    status VARCHAR(20) NOT NULL,
                    score FLOAT,
                    image_path VARCHAR(255),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details TEXT,
                    deleted BOOLEAN DEFAULT FALSE
                )
            """)
            
            # 创建坐姿设置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posture_settings (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    threshold_good FLOAT DEFAULT 0.8,
                    threshold_warning FLOAT DEFAULT 0.6,
                    detection_interval INT DEFAULT 60,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 检查是否有默认设置，如果没有则添加
            cursor.execute("SELECT COUNT(*) FROM posture_settings")
            if (cursor.fetchone()[0] == 0):
                cursor.execute("""
                    INSERT INTO posture_settings 
                    (threshold_good, threshold_warning, detection_interval) 
                    VALUES (0.8, 0.6, 60)
                """)
            
            # 创建家长留言表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS guardian_messages (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    sender VARCHAR(50) NOT NULL COMMENT '发送者身份(妈妈/爸爸)',
                    content TEXT NOT NULL COMMENT '留言内容',
                    message_type ENUM('immediate', 'scheduled') DEFAULT 'immediate' COMMENT '发送类型',
                    send_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',
                    scheduled_time TIMESTAMP NULL COMMENT '定时发送时间',
                    status ENUM('pending', 'sent', 'delivered', 'failed') DEFAULT 'pending' COMMENT '消息状态',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_send_time (send_time),
                    INDEX idx_status (status),
                    INDEX idx_message_type (message_type)
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("数据表检查/创建成功")
            return True
        except Exception as e:
            print(f"确保数据表存在时出错: {str(e)}")
            return False
    
    def record_serial_data(self, sent_data, received_data, status="success", message=""):
        """记录串口通信数据
        
        Args:
            sent_data: 发送的数据
            received_data: 收到的响应
            status: 状态 (success/error)
            message: 附加消息
        
        Returns:
            成功返回True，失败返回False
        """
        try:
            conn = self.get_connection()
            if not conn:
                print("记录串口数据失败: 数据库连接失败")
                return False
            
            cursor = conn.cursor()
            
            # 插入记录
            query = """
                INSERT INTO serial_history 
                (sent_data, received_data, status, message) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (
                sent_data, 
                received_data, 
                status, 
                message
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
        except Exception as e:
            print(f"记录串口数据失败: {str(e)}")
            return False
    
    def get_serial_history(self, page=1, per_page=10):
        """获取串口通信历史记录
        
        Args:
            page: 页码 (从1开始)
            per_page: 每页记录数
            
        Returns:
            元组 (总记录数, 记录列表)
        """
        try:
            conn = self.get_connection()
            if not conn:
                print("获取串口历史失败: 数据库连接失败")
                return 0, []
            
            cursor = conn.cursor(dictionary=True)
            
            # 计算总记录数
            cursor.execute("SELECT COUNT(*) as count FROM serial_history")
            result = cursor.fetchone()
            total_records = result['count'] if result else 0
            
            # 计算偏移量
            offset = (page - 1) * per_page
            
            # 获取分页数据，按时间倒序排列
            query = """
                SELECT * FROM serial_history 
                ORDER BY timestamp DESC 
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, (per_page, offset))
            records = cursor.fetchall()
            
            # 转换datetime对象为字符串
            for record in records:
                if 'timestamp' in record and isinstance(record['timestamp'], datetime):
                    record['timestamp'] = record['timestamp'].isoformat()
            
            cursor.close()
            conn.close()
            
            return total_records, records
        except Exception as e:
            print(f"获取串口历史失败: {str(e)}")
            return 0, []
    
    def clear_serial_history(self):
        """清空串口通信历史记录
        
        Returns:
            成功返回True，失败返回False
        """
        try:
            conn = self.get_connection()
            if not conn:
                print("清空串口历史失败: 数据库连接失败")
                return False
            
            cursor = conn.cursor()
            
            # 清空表
            cursor.execute("DELETE FROM serial_history")
            
            # 重置自增ID (MySQL特性)
            cursor.execute("ALTER TABLE serial_history AUTO_INCREMENT = 1")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
        except Exception as e:
            print(f"清空串口历史失败: {str(e)}")
            return False
    
    def save_posture_record(self, record_id, status, score, image_path, details=None):
        """保存坐姿记录
        
        Args:
            record_id: 记录ID（唯一标识符）
            status: 坐姿状态（good/bad/warning）
            score: 坐姿评分
            image_path: 图片路径
            details: 额外详细信息（JSON格式字符串）
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            conn = self.get_connection()
            if not conn:
                print("保存坐姿记录失败: 数据库连接失败")
                return False
            
            cursor = conn.cursor()
            
            # 插入记录
            query = """
                INSERT INTO posture_records 
                (id, status, score, image_path, details) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                record_id,
                status,
                score,
                image_path,
                details
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
        except Exception as e:
            print(f"保存坐姿记录失败: {str(e)}")
            return False
    
    def get_posture_records(self, page=1, per_page=20, sort_by='time', sort_order='desc', filter_status='all', search=''):
        """获取坐姿记录列表
        
        Args:
            page: 页码 (从1开始)
            per_page: 每页记录数
            sort_by: 排序字段 ('time', 'status')
            sort_order: 排序方向 ('asc', 'desc')
            filter_status: 筛选状态 ('all', 'good', 'bad', 'warning')
            search: 搜索关键词
            
        Returns:
            元组 (总记录数, 记录列表)
        """
        try:
            conn = self.get_connection()
            if not conn:
                print("获取坐姿记录失败: 数据库连接失败")
                return 0, []
            
            cursor = conn.cursor(dictionary=True)
            
            # 构建 WHERE 子句
            where_clauses = ["deleted = 0"]
            params = []
            
            if filter_status != 'all':
                where_clauses.append("status = %s")
                params.append(filter_status)
            
            if search:
                where_clauses.append("(id LIKE %s OR status LIKE %s OR details LIKE %s)")
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            where_clause = " AND ".join(where_clauses)
            
            # 构建 ORDER BY 子句
            order_field = "timestamp" if sort_by == 'time' else "status"
            order_direction = "ASC" if sort_order == 'asc' else "DESC"
            
            # 计算总记录数
            count_query = f"SELECT COUNT(*) as count FROM posture_records WHERE {where_clause}"
            cursor.execute(count_query, params)
            result = cursor.fetchone()
            total_records = result['count'] if result else 0
            
            # 计算偏移量
            offset = (page - 1) * per_page
            
            # 获取分页数据
            query = f"""
                SELECT * FROM posture_records 
                WHERE {where_clause}
                ORDER BY {order_field} {order_direction} 
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, params + [per_page, offset])
            records = cursor.fetchall()
            
            # 转换datetime对象为字符串
            for record in records:
                if 'timestamp' in record and isinstance(record['timestamp'], datetime):
                    record['timestamp'] = record['timestamp'].isoformat()
            
            cursor.close()
            conn.close()
            
            return total_records, records
        except Exception as e:
            print(f"获取坐姿记录失败: {str(e)}")
            return 0, []
    
    def delete_posture_record(self, record_id):
        """删除坐姿记录（软删除）
        
        Args:
            record_id: 记录ID
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            conn = self.get_connection()
            if not conn:
                print("删除坐姿记录失败: 数据库连接失败")
                return False
            
            cursor = conn.cursor()
            
            # 软删除记录（标记为已删除）
            query = """
                UPDATE posture_records
                SET deleted = 1
                WHERE id = %s
            """
            cursor.execute(query, (record_id,))
            
            success = cursor.rowcount > 0
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return success
        except Exception as e:
            print(f"删除坐姿记录失败: {str(e)}")
            return False
    
    def clear_posture_records(self):
        """清空坐姿记录（软删除所有记录）
        
        Returns:
            成功返回True，失败返回False
        """
        try:
            conn = self.get_connection()
            if not conn:
                print("清空坐姿记录失败: 数据库连接失败")
                return False
            
            cursor = conn.cursor()
            
            # 将所有记录标记为已删除
            query = "UPDATE posture_records SET deleted = 1"
            cursor.execute(query)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
        except Exception as e:
            print(f"清空坐姿记录失败: {str(e)}")
            return False
    
    def get_posture_summary_stats(self):
        """获取坐姿记录的统计摘要
        
        Returns:
            包含统计数据的字典
        """
        try:
            conn = self.get_connection()
            if not conn:
                print("获取坐姿统计信息失败: 数据库连接失败")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # 获取总记录数
            cursor.execute("""
                SELECT COUNT(*) as total_records
                FROM posture_records
                WHERE deleted = 0
            """)
            result = cursor.fetchone()
            total_records = result['total_records'] if result else 0
            
            # 获取良好姿势数量
            cursor.execute("""
                SELECT COUNT(*) as good_postures
                FROM posture_records
                WHERE status = 'good' AND deleted = 0
            """)
            result = cursor.fetchone()
            good_postures = result['good_postures'] if result else 0
            
            # 获取不良姿势数量
            cursor.execute("""
                SELECT COUNT(*) as bad_postures
                FROM posture_records
                WHERE status = 'bad' AND deleted = 0
            """)
            result = cursor.fetchone()
            bad_postures = result['bad_postures'] if result else 0
            
            # 获取警告姿势数量
            cursor.execute("""
                SELECT COUNT(*) as warning_postures
                FROM posture_records
                WHERE status = 'warning' AND deleted = 0
            """)
            result = cursor.fetchone()
            warning_postures = result['warning_postures'] if result else 0
            
            # 计算不良比例
            bad_ratio = (bad_postures + warning_postures) / total_records if total_records > 0 else 0
            
            cursor.close()
            conn.close()
            
            return {
                'total_records': total_records,
                'good_postures': good_postures,
                'bad_postures': bad_postures,
                'warning_postures': warning_postures,
                'bad_ratio': bad_ratio
            }
        except Exception as e:
            print(f"获取坐姿统计信息失败: {str(e)}")
            return {}
            
    def get_hourly_posture_distribution(self, time_range='day', custom_start_date=None, custom_end_date=None):
        """获取不同时段的不良坐姿分布数据
        
        Args:
            time_range: 时间范围 'day', 'week', 'month', 'custom'
            custom_start_date: 自定义开始日期（datetime对象）
            custom_end_date: 自定义结束日期（datetime对象）
            
        Returns:
            不同时段的不良坐姿分布数据字典
        """
        try:
            from datetime import datetime, timedelta
            import traceback
            
            conn = self.get_connection()
            if not conn:
                print("获取时段坐姿分布数据失败: 数据库连接失败")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # 确定查询的日期范围
            now = datetime.now()
            start_date = None
            end_date = None
            
            if time_range == 'day':
                # 今天的数据
                start_date = datetime(now.year, now.month, now.day, 0, 0, 0)
                end_date = now
            elif time_range == 'week':
                # 本周的数据（从周一开始）
                days_since_monday = now.weekday()
                start_date = datetime(now.year, now.month, now.day, 0, 0, 0) - timedelta(days=days_since_monday)
                end_date = now
            elif time_range == 'month':
                # 本月的数据
                start_date = datetime(now.year, now.month, 1, 0, 0, 0)
                end_date = now
            elif time_range == 'custom' and custom_start_date and custom_end_date:
                # 自定义日期范围
                start_date = custom_start_date
                end_date = custom_end_date
            else:
                # 默认使用今天的数据
                start_date = datetime(now.year, now.month, now.day, 0, 0, 0)
                end_date = now
            
            # 定义时段范围
            time_periods = [
                {"start": 8, "end": 10, "label": "8-10"},
                {"start": 10, "end": 12, "label": "10-12"},
                {"start": 12, "end": 14, "label": "12-14"},
                {"start": 14, "end": 16, "label": "14-16"},
                {"start": 16, "end": 18, "label": "16-18"},
                {"start": 18, "end": 20, "label": "18-20"}
            ]
            
            # 初始化时段数据
            period_counts = {period["label"]: 0 for period in time_periods}
            
            # 查询不良坐姿记录
            query = """
                SELECT 
                    start_time,
                    HOUR(start_time) as hour,
                    posture_type
                FROM posture_time_records
                WHERE start_time >= %s AND end_time <= %s
                AND (posture_type = 'fair' OR posture_type = 'poor')
            """
            
            cursor.execute(query, (start_date, end_date))
            records = cursor.fetchall()
            
            # 统计每个时段的不良坐姿次数
            for record in records:
                hour = record['hour']
                
                # 找到对应的时段
                for period in time_periods:
                    if period["start"] <= hour < period["end"]:
                        period_counts[period["label"]] += 1
                        break
            
            # 形成最终结果
            labels = [period["label"] for period in time_periods]
            data = [period_counts[period["label"]] for period in time_periods]
            
            cursor.close()
            conn.close()
            
            return {
                'labels': labels,
                'data': data,
                'time_range': time_range,
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            }
        except Exception as e:
            print(f"获取时段坐姿分布数据失败: {str(e)}")
            traceback.print_exc()
            return {
                'error': str(e),
                'labels': ["8-10", "10-12", "12-14", "14-16", "16-18", "18-20"],
                'data': [0, 0, 0, 0, 0, 0]
            }
        
    # 家长留言系统方法
    def send_guardian_message(self, sender, content, message_type='immediate', scheduled_time=None):
        """发送家长留言
        
        Args:
            sender: 发送者身份 ('妈妈' 或 '爸爸')
            content: 留言内容
            message_type: 消息类型 ('immediate' 或 'scheduled')
            scheduled_time: 定时发送时间 (仅当message_type='scheduled'时使用)
        
        Returns:
            dict: 包含状态和消息ID的字典
        """
        try:
            conn = self.get_connection()
            if not conn:
                return {'status': 'error', 'message': '数据库连接失败'}
            
            cursor = conn.cursor()
            
            # 验证发送者身份
            if sender not in ['妈妈', '爸爸']:
                return {'status': 'error', 'message': '无效的发送者身份'}
            
            # 验证留言内容
            if not content or len(content.strip()) == 0:
                return {'status': 'error', 'message': '留言内容不能为空'}
            
            if len(content) > 200:
                return {'status': 'error', 'message': '留言内容不能超过200个字符'}
            
            # 验证定时发送参数
            if message_type == 'scheduled':
                print(f"DEBUG: 处理定时发送，原始时间: {scheduled_time}")
                
                if not scheduled_time:
                    return {'status': 'error', 'message': '定时发送必须指定发送时间'}
                
                # 检查定时时间是否在未来
                current_time = datetime.now()
                print(f"DEBUG: 当前时间: {current_time}")
                
                if isinstance(scheduled_time, str):
                    try:
                        # 处理UTC时间转换为本地时间
                        if scheduled_time.endswith('Z'):
                            # 移除Z后缀并解析为UTC时间
                            utc_time_str = scheduled_time[:-1]
                            utc_time = datetime.fromisoformat(utc_time_str)
                            print(f"DEBUG: UTC时间: {utc_time}")
                            
                            # 将UTC时间转换为本地时间（加8小时）
                            from datetime import timedelta
                            scheduled_time = utc_time + timedelta(hours=8)
                            print(f"DEBUG: 转换为本地时间: {scheduled_time}")
                        else:
                            # 直接解析为本地时间
                            scheduled_time = datetime.fromisoformat(scheduled_time)
                            print(f"DEBUG: 直接解析的本地时间: {scheduled_time}")
                        
                    except ValueError as e:
                        print(f"ERROR: 时间格式解析错误: {str(e)}")
                        return {'status': 'error', 'message': '无效的时间格式'}
                
                # 确保两个datetime对象都不带时区信息进行比较
                if hasattr(scheduled_time, 'tzinfo') and scheduled_time.tzinfo is not None:
                    scheduled_time = scheduled_time.replace(tzinfo=None)
                if hasattr(current_time, 'tzinfo') and current_time.tzinfo is not None:
                    current_time = current_time.replace(tzinfo=None)
                
                print(f"DEBUG: 时间比较 - 定时时间: {scheduled_time}, 当前时间: {current_time}")
                
                # 增加30秒的缓冲时间，避免网络延迟导致的问题
                from datetime import timedelta
                buffer_current_time = current_time + timedelta(seconds=30)
                print(f"DEBUG: 缓冲后的当前时间: {buffer_current_time}")
                
                if scheduled_time <= buffer_current_time:
                    print("ERROR: 定时发送时间不在未来（考虑30秒缓冲）")
                    return {'status': 'error', 'message': '定时发送时间必须在当前时间30秒之后'}
            
            # 设置消息状态
            status = 'sent' if message_type == 'immediate' else 'pending'
            print(f"DEBUG: 消息状态设置为: {status}")
            
            # 插入留言记录
            query = """
                INSERT INTO guardian_messages 
                (sender, content, message_type, scheduled_time, status) 
                VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (sender, content.strip(), message_type, scheduled_time, status))
            message_id = cursor.lastrowid
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                'status': 'success',
                'message': '留言发送成功' if message_type == 'immediate' else '留言已安排定时发送',
                'message_id': message_id
            }
            
        except Exception as e:
            print(f"ERROR: 发送家长留言时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'status': 'error', 'message': f'发送失败: {str(e)}'}
    
    def get_guardian_messages(self, limit=50, offset=0):
        """获取家长留言历史
        
        Args:
            limit: 返回的最大记录数
            offset: 偏移量（用于分页）
        
        Returns:
            dict: 包含状态和留言列表的字典
        """
        try:
            conn = self.get_connection()
            if not conn:
                return {'status': 'error', 'message': '数据库连接失败'}
            
            cursor = conn.cursor(dictionary=True)
            
            # 查询留言记录，按发送时间倒序排列
            query = """
                SELECT 
                    id,
                    sender,
                    content,
                    message_type,
                    send_time,
                    scheduled_time,
                    status,
                    created_at
                FROM guardian_messages 
                ORDER BY send_time DESC, created_at DESC
                LIMIT %s OFFSET %s
            """
            
            cursor.execute(query, (limit, offset))
            messages = cursor.fetchall()
            
            # 获取总数
            cursor.execute("SELECT COUNT(*) as total FROM guardian_messages")
            total_count = cursor.fetchone()['total']
            
            cursor.close()
            conn.close()
            
            # 格式化时间字段
            for message in messages:
                if message['send_time']:
                    message['send_time'] = message['send_time'].strftime('%Y-%m-%d %H:%M:%S')
                if message['scheduled_time']:
                    message['scheduled_time'] = message['scheduled_time'].strftime('%Y-%m-%d %H:%M:%S')
                if message['created_at']:
                    message['created_at'] = message['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'status': 'success',
                'messages': messages,
                'total': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            print(f"获取家长留言历史时出错: {str(e)}")
            return {'status': 'error', 'message': f'获取失败: {str(e)}'}
    
    def update_message_status(self, message_id, status):
        """更新留言状态
        
        Args:
            message_id: 留言ID
            status: 新状态 ('pending', 'sent', 'delivered', 'failed')
        
        Returns:
            dict: 操作结果
        """
        try:
            conn = self.get_connection()
            if not conn:
                return {'status': 'error', 'message': '数据库连接失败'}
            
            cursor = conn.cursor()
            
            # 验证状态值
            valid_statuses = ['pending', 'sent', 'delivered', 'failed']
            if status not in valid_statuses:
                return {'status': 'error', 'message': '无效的状态值'}
            
            # 更新状态
            query = "UPDATE guardian_messages SET status = %s WHERE id = %s"
            cursor.execute(query, (status, message_id))
            
            if cursor.rowcount == 0:
                cursor.close()
                conn.close()
                return {'status': 'error', 'message': '留言记录不存在'}
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return {'status': 'success', 'message': '状态更新成功'}
            
        except Exception as e:
            print(f"更新留言状态时出错: {str(e)}")
            return {'status': 'error', 'message': f'更新失败: {str(e)}'}
    
    def get_pending_scheduled_messages(self):
        """获取待发送的定时留言
        
        Returns:
            list: 待发送的定时留言列表
        """
        try:
            conn = self.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # 查询到达发送时间的待发送定时留言
            query = """
                SELECT id, sender, content, scheduled_time 
                FROM guardian_messages 
                WHERE message_type = 'scheduled' 
                AND status = 'pending' 
                AND scheduled_time <= NOW()
                ORDER BY scheduled_time ASC
            """
            
            cursor.execute(query)
            messages = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return messages
            
        except Exception as e:
            print(f"获取待发送定时留言时出错: {str(e)}")
            return []