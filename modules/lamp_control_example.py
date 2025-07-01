"""
台灯控制模块使用示例

这个文件展示了如何在主应用中集成和使用台灯控制模块
"""

from flask import Flask
from modules.webcontrol_module import create_lamp_control_blueprint
from serial_handler import SerialHandler

def create_app_with_lamp_control():
    """创建包含台灯控制功能的Flask应用"""
    
    app = Flask(__name__)
    
    # 初始化串口处理器（可选，如果不传入则串口功能为空）
    try:
        serial_handler = SerialHandler()
        print("串口处理器初始化成功")
    except Exception as e:
        print(f"串口处理器初始化失败: {e}")
        serial_handler = None
    
    # 创建台灯控制蓝图
    lamp_control_bp = create_lamp_control_blueprint(serial_handler)
    
    # 注册蓝图
    app.register_blueprint(lamp_control_bp)
    
    return app

# 使用示例
if __name__ == '__main__':
    app = create_app_with_lamp_control()
    app.run(host='0.0.0.0', port=5002, debug=True)

"""
API使用示例:

1. 获取台灯状态:
   GET /api/lamp/status

2. 开关台灯:
   POST /api/lamp/power
   {
       "power": true  // true为开灯，false为关灯
   }

3. 设置亮度:
   POST /api/lamp/brightness
   {
       "brightness": 80  // 0-100
   }

4. 设置色温:
   POST /api/lamp/color_temp
   {
       "color_temp": 4000  // 2700-6500K
   }

5. 设置RGB颜色:
   POST /api/lamp/rgb
   {
       "r": 255,
       "g": 128,
       "b": 0
   }

6. 设置颜色模式:
   POST /api/lamp/color_mode
   {
       "mode": "warm"  // warm, cool, daylight, rgb
   }

7. 设置场景模式:
   POST /api/lamp/scene
   {
       "scene": "reading"  // normal, reading, relax, work
   }

8. 设置定时器:
   POST /api/lamp/timer
   {
       "duration": 30  // 分钟，0为关闭定时器
   }

9. 切换自动模式:
   POST /api/lamp/auto_mode
   {
       "enabled": true  // true为启用，false为关闭
   }

10. 设置预设配置:
    POST /api/lamp/preset
    {
        "power": true,
        "brightness": 80,
        "color_temp": 4000,
        "scene": "reading"
    }
"""
