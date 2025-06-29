"""
家长监护定时留言处理器
"""
import time
import threading
from datetime import datetime
from db_handler import DBHandler
from config import DB_CONFIG

class GuardianMessageScheduler:
    """家长留言定时发送处理器"""
    
    def __init__(self, db_handler=None, check_interval=60):
        """初始化定时留言处理器
        
        Args:
            db_handler: 数据库处理器实例
            check_interval: 检查间隔（秒），默认60秒
        """
        self.db = db_handler or DBHandler(DB_CONFIG)
        self.check_interval = check_interval
        self.running = False
        self.scheduler_thread = None
        self._stop_event = threading.Event()
        
        print("家长留言定时处理器初始化完成")
    
    def start(self):
        """启动定时检查"""
        if self.running:
            print("定时留言处理器已在运行")
            return
        
        self.running = True
        self._stop_event.clear()
        self.scheduler_thread = threading.Thread(target=self._schedule_loop, daemon=True)
        self.scheduler_thread.start()
        print("定时留言处理器已启动")
    
    def stop(self):
        """停止定时检查"""
        if not self.running:
            return
        
        self.running = False
        self._stop_event.set()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        print("定时留言处理器已停止")
    
    def _schedule_loop(self):
        """定时检查循环"""
        while self.running and not self._stop_event.is_set():
            try:
                self._process_scheduled_messages()
            except Exception as e:
                print(f"处理定时留言时出错: {str(e)}")
            
            # 等待下一次检查，但可以被停止事件中断
            self._stop_event.wait(self.check_interval)
    
    def _process_scheduled_messages(self):
        """处理到期的定时留言"""
        try:
            # 获取待发送的定时留言
            pending_messages = self.db.get_pending_scheduled_messages()
            
            if not pending_messages:
                return
            
            print(f"发现 {len(pending_messages)} 条待发送的定时留言")
            
            for message in pending_messages:
                try:
                    message_id = message['id']
                    sender = message['sender']
                    content = message['content']
                    scheduled_time = message['scheduled_time']
                    
                    # 模拟发送留言（在实际应用中，这里可能是发送到设备、推送通知等）
                    success = self._send_message_to_device(message_id, sender, content)
                    
                    if success:
                        # 更新状态为已发送
                        self.db.update_message_status(message_id, 'sent')
                        print(f"定时留言已发送: ID={message_id}, 发送者={sender}")
                    else:
                        # 更新状态为发送失败
                        self.db.update_message_status(message_id, 'failed')
                        print(f"定时留言发送失败: ID={message_id}, 发送者={sender}")
                
                except Exception as e:
                    print(f"处理单条定时留言时出错: {str(e)}")
                    # 尝试将状态设为失败
                    try:
                        if 'message_id' in locals():
                            self.db.update_message_status(message_id, 'failed')
                    except:
                        pass
                        
        except Exception as e:
            print(f"获取待发送定时留言时出错: {str(e)}")
    
    def _send_message_to_device(self, message_id, sender, content):
        """发送留言到设备（模拟实现）
        
        Args:
            message_id: 留言ID
            sender: 发送者
            content: 留言内容
        
        Returns:
            bool: 发送是否成功
        """
        try:
            # 在实际应用中，这里可能是：
            # 1. 通过串口发送到台灯设备
            # 2. 发送推送通知到设备
            # 3. 通过其他通信方式传递消息
            
            # 这里使用简单的日志记录来模拟发送
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] 留言发送: {sender} -> {content[:30]}{'...' if len(content) > 30 else ''}")
            
            # 模拟发送成功（在实际应用中需要根据具体的发送结果来判断）
            return True
            
        except Exception as e:
            print(f"发送留言到设备时出错: {str(e)}")
            return False
    
    def get_status(self):
        """获取处理器状态"""
        return {
            'running': self.running,
            'check_interval': self.check_interval,
            'thread_alive': self.scheduler_thread.is_alive() if self.scheduler_thread else False
        }
    
    def force_check(self):
        """强制执行一次检查"""
        if not self.running:
            print("定时留言处理器未运行，无法执行强制检查")
            return False
        
        try:
            self._process_scheduled_messages()
            return True
        except Exception as e:
            print(f"强制检查定时留言时出错: {str(e)}")
            return False

# 全局实例
guardian_scheduler = None

def init_guardian_scheduler():
    """初始化家长监护定时处理器"""
    global guardian_scheduler
    
    if guardian_scheduler is None:
        guardian_scheduler = GuardianMessageScheduler()
        guardian_scheduler.start()
        print("家长监护定时处理器全局实例已创建并启动")
    
    return guardian_scheduler

def get_guardian_scheduler():
    """获取家长监护定时处理器实例"""
    global guardian_scheduler
    
    if guardian_scheduler is None:
        return init_guardian_scheduler()
    
    return guardian_scheduler

def shutdown_guardian_scheduler():
    """关闭家长监护定时处理器"""
    global guardian_scheduler
    
    if guardian_scheduler:
        guardian_scheduler.stop()
        guardian_scheduler = None
        print("家长监护定时处理器已关闭")
