"""
应用主模块 - 系统入口点，整合各模块创建完整应用
"""
import os
import sys
import atexit
from flask import Flask
import time

# 导入配置
from config import OPEN_HOST, OPEN_PORT, SERIAL_BAUDRATE

# 导入各个功能模块
from modules.database_module import init_database
from modules.video_stream_module import VideoStreamHandler
from modules.posture_module import WebPostureMonitor, PROCESS_WIDTH, PROCESS_HEIGHT
from modules.serial_module import SerialCommunicationHandler
from modules.routes import routes_bp, setup_services

def create_app():
    """创建并配置Flask应用"""
    # 初始化Flask应用
    app = Flask(__name__)
    
    # 注册路由蓝图
    app.register_blueprint(routes_bp)
    
    # 初始化数据库
    init_database()
    
    # 初始化视频流处理器
    video_stream_handler = VideoStreamHandler(
        process_width=PROCESS_WIDTH,
        process_height=PROCESS_HEIGHT
    )
    
    # 初始化串口通信处理器
    serial_handler = SerialCommunicationHandler(baudrate=SERIAL_BAUDRATE)
    
    # 初始化姿势分析器
    posture_monitor = WebPostureMonitor(video_stream_handler=video_stream_handler)
    
    # 设置路由模块依赖的服务
    setup_services(
        posture_monitor_instance=posture_monitor,
        video_stream_instance=video_stream_handler,
        serial_handler_instance=serial_handler
    )
    
    # 注册应用退出时的清理函数
    def cleanup():
        print("正在关闭服务器...")
        if posture_monitor:
            posture_monitor.stop()
        if serial_handler:
            serial_handler.cleanup()
    
    atexit.register(cleanup)
    
    return app

if __name__ == '__main__':
    app = create_app()
    print(f"Starting server on {OPEN_HOST}:{OPEN_PORT}...")
    
    # 注意：Flask 在 debug=True 模式下会启动两个进程，atexit 可能会被调用两次
    # 在生产环境中应使用 Gunicorn 或 uWSGI 等 WSGI 服务器
    app.run(host=OPEN_HOST, port=OPEN_PORT, debug=True, use_reloader=False) # 禁用 reloader 避免监控线程问题