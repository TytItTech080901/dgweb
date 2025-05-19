"""
图像清理函数模块 - 提供按时间段和日期清理图像的功能
"""

import mysql.connector
from datetime import datetime, timedelta
import os
from config import DB_CONFIG

# 添加图像存储路径配置
POSTURE_IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'posture_images')

def cleanup_hourly_images(hour_datetime, max_images=20):
    """清理指定小时内的图片，只保留最新的指定数量图片
    
    Args:
        hour_datetime: 小时的datetime对象，精确到小时
        max_images: 该小时内最多保留的图片数量
        
    Returns:
        删除的图片数量
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 获取指定小时的范围
        hour_start = hour_datetime
        hour_end = hour_start + timedelta(hours=1)
        
        # 获取该小时内的图片总数
        cursor.execute("""
            SELECT COUNT(*) FROM posture_images
            WHERE timestamp >= %s AND timestamp < %s
        """, (hour_start, hour_end))
        
        total_images = cursor.fetchone()[0]
        
        # 如果图片数量不超过保留限制，则不需要删除
        if total_images <= max_images:
            cursor.close()
            conn.close()
            print(f"时间段 {hour_start.strftime('%Y-%m-%d %H:00')} 的图片数量({total_images})未超过保留限制({max_images})，无需清理")
            return 0
        
        # 计算需要删除的图片数量
        images_to_delete = total_images - max_images
        
        # 获取需要删除的图片记录，按时间升序（最老的先删）
        cursor.execute("""
            SELECT id, image_path FROM posture_images
            WHERE timestamp >= %s AND timestamp < %s
            ORDER BY timestamp ASC
            LIMIT %s
        """, (hour_start, hour_end, images_to_delete))
        
        delete_records = cursor.fetchall()
        deleted_count = 0
        
        # 逐个删除图片文件和数据库记录
        for image_id, image_path in delete_records:
            # 构建完整文件路径
            if image_path.startswith('/static/'):
                # 获取项目根目录
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                # 构建完整路径
                full_path = os.path.join(project_root, image_path[1:])  # 移除开头的'/'
            else:
                # 如果路径不是以/static/开头，尝试在posture_images目录中查找
                filename = os.path.basename(image_path)
                full_path = os.path.join(POSTURE_IMAGES_DIR, filename)
            
            # 删除物理文件
            if os.path.exists(full_path):
                os.remove(full_path)
            
            # 删除数据库记录
            cursor.execute("DELETE FROM posture_images WHERE id = %s", (image_id,))
            deleted_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"成功清理了 {hour_start.strftime('%Y-%m-%d %H:00')} 时间段的 {deleted_count} 张旧图片，保留了最新的 {max_images} 张图片")
        return deleted_count
        
    except Exception as e:
        print(f"清理小时图片失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0

def cleanup_daily_images(date_datetime, max_images=240):
    """清理指定日期内的图片，只保留最新的指定数量图片
    
    Args:
        date_datetime: 日期的datetime对象，精确到日
        max_images: 该日期内最多保留的图片数量
        
    Returns:
        删除的图片数量
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 获取指定日期的范围
        date_start = date_datetime
        date_end = date_start + timedelta(days=1)
        
        # 获取该日期内的图片总数
        cursor.execute("""
            SELECT COUNT(*) FROM posture_images
            WHERE timestamp >= %s AND timestamp < %s
        """, (date_start, date_end))
        
        total_images = cursor.fetchone()[0]
        
        # 如果图片数量不超过保留限制，则不需要删除
        if total_images <= max_images:
            cursor.close()
            conn.close()
            print(f"日期 {date_start.strftime('%Y-%m-%d')} 的图片数量({total_images})未超过保留限制({max_images})，无需清理")
            return 0
        
        # 计算需要删除的图片数量
        images_to_delete = total_images - max_images
        
        # 获取需要删除的图片记录，按时间升序（最老的先删）
        cursor.execute("""
            SELECT id, image_path FROM posture_images
            WHERE timestamp >= %s AND timestamp < %s
            ORDER BY timestamp ASC
            LIMIT %s
        """, (date_start, date_end, images_to_delete))
        
        delete_records = cursor.fetchall()
        deleted_count = 0
        
        # 逐个删除图片文件和数据库记录
        for image_id, image_path in delete_records:
            # 构建完整文件路径
            if image_path.startswith('/static/'):
                # 获取项目根目录
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                # 构建完整路径
                full_path = os.path.join(project_root, image_path[1:])  # 移除开头的'/'
            else:
                # 如果路径不是以/static/开头，尝试在posture_images目录中查找
                filename = os.path.basename(image_path)
                full_path = os.path.join(POSTURE_IMAGES_DIR, filename)
            
            # 删除物理文件
            if os.path.exists(full_path):
                os.remove(full_path)
            
            # 删除数据库记录
            cursor.execute("DELETE FROM posture_images WHERE id = %s", (image_id,))
            deleted_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"成功清理了 {date_start.strftime('%Y-%m-%d')} 日期的 {deleted_count} 张旧图片，保留了最新的 {max_images} 张图片")
        return deleted_count
        
    except Exception as e:
        print(f"清理日期图片失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0