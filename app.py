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
    print("\n========== 开始初始化应用 ==========")
    # 初始化Flask应用
    app = Flask(__name__)
    
    # 注册路由蓝图
    app.register_blueprint(routes_bp)
    print("路由蓝图注册完成")
    
    # 初始化数据库
    init_database()
    print("数据库初始化完成")
    
    # 初始化视频流处理器
    try:
        print("正在初始化视频流处理器...")
        video_stream_handler = VideoStreamHandler(
            process_width=PROCESS_WIDTH,
            process_height=PROCESS_HEIGHT
        )
        print("视频流处理器初始化成功")
    except Exception as e:
        print(f"视频流处理器初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        video_stream_handler = None
    
    # 初始化姿势分析器 (先于串口初始化，确保其不依赖串口)
    try:
        print("正在初始化姿势分析器...")
        posture_monitor = WebPostureMonitor(video_stream_handler=video_stream_handler)
        print("姿势分析器初始化成功")
    except Exception as e:
        print(f"姿势分析器初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        posture_monitor = None
    
    # 自动启动姿势分析系统
    if posture_monitor:
        try:
            print("正在启动姿势分析系统...")
            posture_start_success = posture_monitor.start()
            if posture_start_success:
                print("姿势分析系统自动启动成功")
            else:
                print("警告：姿势分析系统自动启动失败，请手动启动")
        except Exception as e:
            print(f"启动姿势分析系统时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            posture_start_success = False
    else:
        print("姿势分析器未成功初始化，无法启动姿势分析系统")
        posture_start_success = False
    
    # 尝试初始化串口通信处理器，允许失败
    try:
        serial_handler = SerialCommunicationHandler(baudrate=SERIAL_BAUDRATE)
        serial_available = serial_handler is not None and hasattr(serial_handler, 'initialized') and serial_handler.initialized
    except Exception as e:
        print(f"串口通信初始化失败，但不影响姿势分析系统: {str(e)}")
        serial_handler = None
        serial_available = False
    
    # 通知用户串口和姿势分析系统的状态
    if serial_available:
        print("串口通信系统初始化成功")
    else:
        print("串口通信系统未启动，但姿势分析系统可以正常工作")
    
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
        if serial_handler and serial_available:
            serial_handler.cleanup()
    
    atexit.register(cleanup)
    
    return app

if __name__ == '__main__':
    app = create_app()
    print(f"Starting server on {OPEN_HOST}:{OPEN_PORT}...")
    
    # 注意：Flask 在 debug=True 模式下会启动两个进程，atexit 可能会被调用两次
    # 在生产环境中应使用 Gunicorn 或 uWSGI 等 WSGI 服务器
    app.run(host=OPEN_HOST, port=OPEN_PORT, debug=True, use_reloader=False) # 禁用 reloader 避免监控线程问题