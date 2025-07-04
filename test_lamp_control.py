"""
台灯控制测试脚本 - 用于测试台灯控制功能
"""
from flask import Flask
from modules.lamp_control_module import create_lamp_control_blueprint
from serial_handler import SerialHandler
import os

# 创建测试用Flask应用
app = Flask(__name__, 
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'),
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))

# 创建串口处理器实例（可选）
try:
    # 尝试初始化串口
    serial_handler = SerialHandler()
    print("串口处理器初始化成功")
    serial_available = True
except Exception as e:
    print(f"串口处理器初始化失败: {e}")
    serial_handler = None
    serial_available = False

# 创建台灯控制蓝图
lamp_control_bp = create_lamp_control_blueprint(serial_handler)

# 注册蓝图
app.register_blueprint(lamp_control_bp)

if __name__ == '__main__':
    print("台灯控制测试服务器启动中...")
    
    # 如果串口可用，输出状态信息
    if serial_available:
        print(f"串口已连接到: {serial_handler.port}")
        print(f"波特率: {serial_handler.baudrate}")
        print("可以发送实际控制命令到台灯")
    else:
        print("警告: 串口不可用，将使用模拟模式（不发送实际命令）")
    
    print("\n访问 http://localhost:5003/lamp_control 使用台灯控制界面")
    print("可用的API端点:")
    print("- GET  /api/lamp/status        - 获取台灯状态")
    print("- POST /api/lamp/power         - 设置台灯电源")
    print("- POST /api/lamp/brightness    - 设置台灯亮度")
    print("- POST /api/lamp/color_temp    - 设置台灯色温")
    print("- POST /api/lamp/rgb           - 设置台灯RGB颜色")
    print("- POST /api/lamp/color_mode    - 设置台灯颜色模式")
    print("- POST /api/lamp/scene         - 设置台灯场景模式")
    print("- POST /api/lamp/timer         - 设置台灯定时器")
    print("- POST /api/lamp/auto_mode     - 设置台灯自动模式")
    print("- POST /api/lamp/preset        - 应用台灯预设配置")
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=5003, debug=True)
