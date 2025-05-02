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