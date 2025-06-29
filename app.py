"""
应用主模块 - 系统入口点，整合各模块创建完整应用
"""
import os
import sys
import atexit
from flask import Flask
import time

# 导入配置
from config import OPEN_HOST, OPEN_PORT, SERIAL_BAUDRATE, DEBUG_BUTTON_VISIBLE, ENABLE_CHATBOT, ENABLE_WELCOME_MESSAGE, AUTO_START_CHATBOT_LOOP

# 导入各个功能模块
from modules.database_module import init_database
from modules.video_stream_module import VideoStreamHandler
from modules.posture_module import WebPostureMonitor, PROCESS_WIDTH, PROCESS_HEIGHT
from modules.serial_module import SerialCommunicationHandler
from modules.routes import routes_bp, setup_services
from modules.detection_module import DetectionService
from modules.chatbot_module import ChatbotService

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

    # 创建检测服务实例
    try:
        print("\n==================================================")
        print("正在初始化检测服务...")
        print("使用指定的摄像头索引3...")
        
        # 使用摄像头索引3
        detection_service = DetectionService(
            model_path="Yolo/best6_rknn_model",
            camera_id=3,  # 直接使用摄像头3
            show_img=False  # 生产环境不显示图像
        )
        
        # 初始化检测服务
        if detection_service.initialize():
            detection_available = True
            print("检测服务初始化成功")
            
            try:
                print("正在启动检测服务...")
                if detection_service.start():
                    print("检测服务启动成功")
                else:
                    print("检测服务启动失败")
                    detection_service = None
                    detection_available = False
            except Exception as e:
                print(f"启动检测服务时出错: {str(e)}")
                detection_service = None
                detection_available = False
        else:
            print("检测服务初始化失败")
            detection_service = None
            detection_available = False
            
    except Exception as e:
        print(f"检测服务创建失败: {str(e)}")
        detection_service = None
        detection_available = False


    # 如果串口和检测服务都可用，设置串口处理器
    if detection_available and serial_available:
        try:
            print("将串口处理器设置到检测服务...")
            detection_service.set_serial_handler(serial_handler)
            print("串口处理器设置成功，可以发送检测坐标")
        except Exception as e:
            print(f"设置串口处理器失败: {str(e)}")

    # 初始化语音助手服务
    chatbot_service = None
    if ENABLE_CHATBOT:
        try:
            print("\n==================================================")
            print("正在初始化语音助手服务...")
            chatbot_service = ChatbotService()
            if chatbot_service.initialize():
                print("语音助手服务初始化成功")
                
                # 发送欢迎消息，获取自我介绍
                if ENABLE_WELCOME_MESSAGE:
                    try:
                        print("正在请求语音助手自我介绍...")
                        msg = "你好，请简要介绍一下自己的功能，不要举例,不要使用\"嗨\",不要提到自己机械臂的功能。"
                        response = chatbot_service.send_message(msg)
                        print(f"语音助手自我介绍: {response}")
                        time.sleep(2)
                    except Exception as e:
                        print(f"语音助手自我介绍时出错: {str(e)}")
            else:
                print("语音助手服务初始化失败")
                chatbot_service = None
        except Exception as e:
            print(f"初始化语音助手服务时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            chatbot_service = None

    # 设置路由模块依赖的服务
    setup_services(
        posture_monitor_instance=posture_monitor,
        video_stream_instance=video_stream_handler,
        serial_handler_instance=serial_handler,
        detection_service_instance=detection_service,
        chatbot_service_instance=chatbot_service
    )
    
    # 初始化家长监护定时处理器
    try:
        print("\n==================================================")
        print("正在初始化家长监护定时处理器...")
        from guardian_scheduler import init_guardian_scheduler
        guardian_scheduler = init_guardian_scheduler()
        print("家长监护定时处理器初始化成功")
    except Exception as e:
        print(f"家长监护定时处理器初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        guardian_scheduler = None
    
    # 注册应用退出时的清理函数
    def cleanup():
        print("正在关闭服务器...")
        if posture_monitor:
            posture_monitor.stop()
        if serial_handler and serial_available:
            serial_handler.cleanup()
        if detection_service and detection_available:
            detection_service.stop()
        if chatbot_service:
            print("正在关闭语音助手服务...")
            try:
                chatbot_service.reset()
            except:
                pass
        # 关闭家长监护定时处理器
        try:
            from guardian_scheduler import shutdown_guardian_scheduler
            shutdown_guardian_scheduler()
        except:
            pass
    
    atexit.register(cleanup)
    
    # 如果启用了语音助手并设置为自动启动对话循环，则在单独的线程中启动
    if chatbot_service and AUTO_START_CHATBOT_LOOP:
        import threading

        msg = "现在,你可以随时跟我说话哦!"
        chatbot_service.speak_text(msg)

        def chatbot_loop():
            print("语音助手对话循环已启动，随时准备接收语音指令...")
            try:
                while True:
                    try:
                        chatbot_service.chat_loop()
                    except Exception as e:
                        print(f"语音助手对话循环出错: {str(e)}")
                        time.sleep(2)  # 出错后等待2秒重试
            except KeyboardInterrupt:
                print("语音助手对话循环被手动终止")
                
        # 创建并启动语音助手线程
        chatbot_thread = threading.Thread(target=chatbot_loop, daemon=True)
        chatbot_thread.start()
        print("语音助手线程已启动")
    
    return app

if __name__ == '__main__':
    app = create_app()
    print(f"Starting server on {OPEN_HOST}:{OPEN_PORT}...")
    
    # 注意：Flask 在 debug=True 模式下会启动两个进程，atexit 可能会被调用两次
    # 在生产环境中应使用 Gunicorn 或 uWSGI 等 WSGI 服务器
    app.run(host=OPEN_HOST, port=OPEN_PORT, debug=True, use_reloader=False) # 禁用 reloader 避免监控线程问题
