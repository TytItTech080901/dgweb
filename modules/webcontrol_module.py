"""
台灯远程控制模块 - 提供台灯控制的所有API接口
"""
from flask import Blueprint, request, jsonify
import json
import time
from datetime import datetime
import logging

# 导入串口模块用于通信
# from serial_handler import SerialHandler

class LampControlHandler:
    """台灯控制处理器"""
    
    def __init__(self, serial_handler=None):
        """
        初始化台灯控制处理器
        
        Args:
            serial_handler: 串口处理器实例
        """
        self.serial_handler = serial_handler
        self.lamp_status = {
            'power': False,  # 台灯开关状态
            'brightness': 50,  # 亮度 (0-100)
            'color_temp': 4000,  # 色温 (2700K-6500K)
            'color_mode': 'warm',  # 颜色模式: warm, cool, daylight, rgb
            'rgb_color': {'r': 255, 'g': 255, 'b': 255},  # RGB颜色值
            'timer_enabled': False,  # 定时器是否启用
            'timer_duration': 0,  # 定时器时长(分钟)
            'scene_mode': 'normal',  # 场景模式: normal, reading, relax, work
            'auto_mode': False,  # 自动模式是否启用
            'last_update': datetime.now().isoformat()
        }
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_lamp_status(self):
        """获取台灯当前状态"""
        try:
            if self.serial_handler:
                data = self.serial_handler.request_data(0x40,[1]*8)
                if data is None:
                    self.logger.error("无法从台灯获取状态数据")
                    return None
                else:
                    if data['command'] == 0xBF:
                        self.logger.error("台灯未开机，不响应命令")
                        return None
                    if data['datatype'] != 0xB0:
                        self.logger.error(f"未知数据类型: {data['datatype']}")
                        return None
                    if data['command'] != 0x41:
                        self.logger.error(f"未知命令: {data['command']}")
                        return None
                    
                    # 使用已解析的字段
                    if 'is_light' in data:
                        self.lamp_status['power'] = data['is_light']
                    
                    if 'brightness' in data:
                        self.lamp_status['brightness'] = data['brightness']
                    
                    if 'color_temp' in data:
                        self.lamp_status['color_temp'] = data['color_temp']
                    
                    self.logger.info(f"成功获取台灯状态: 电源={self.lamp_status['power']}, 亮度={self.lamp_status['brightness']}, 色温={self.lamp_status['color_temp']}")
            
            self.lamp_status['last_update'] = datetime.now().isoformat()
            return self.lamp_status
        except Exception as e:
            self.logger.error(f"获取台灯状态失败: {e}")
            return None
    
    def set_power(self, power_on):
        """
        设置台灯开关
        
        Args:
            power_on (bool): True为开灯，False为关灯
        """
        try:
            # 使用serial_module中的send_command方法
            if power_on:
                success = self.serial_handler.send_command(0x14, [0] * 8)
                if success:
                    print("串口命令发送成功: 开灯")
                else:
                    print("串口命令发送失败: 开灯")
            else:
                success = self.serial_handler.send_command(0x15, [0] * 8)
                if success:
                    print("串口命令发送成功: 关灯")
                else:
                    print("串口命令发送失败: 关灯")
            
            self.lamp_status['power'] = power_on
            self.lamp_status['last_update'] = datetime.now().isoformat()
            self.logger.info(f"台灯{'开启' if power_on else '关闭'}")
            return True
        except Exception as e:
            self.logger.error(f"设置台灯开关失败: {e}")
            return False
    
    def set_brightness(self, brightness):
        """
        设置台灯亮度
        
        Args:
            brightness (int): 亮度值 (0-100)
        """
        try:
            # 限制亮度范围
            brightness = max(0, min(100, brightness))

            if self.serial_handler:
                self.serial_handler.send_command_setting_light(brightness, self.lamp_status['color_temp'])
            else:
                return False

            self.lamp_status['brightness'] = brightness
            self.lamp_status['last_update'] = datetime.now().isoformat()
            self.logger.info(f"设置台灯亮度为: {brightness}%")
            return True
        except Exception as e:
            self.logger.error(f"设置台灯亮度失败: {e}")
            return False
    
    def set_color_temperature(self, color_temp):
        """
        设置台灯色温
        
        Args:
            color_temp (int): 色温值 (2700K-6500K)
        """
        try:
            # 限制色温范围
            color_temp = max(2700, min(6500, color_temp))
            
            if self.serial_handler:
                self.serial_handler.send_command_setting_light(self.lamp_status['brightness'], color_temp)
            else:
                return False
            
            self.lamp_status['color_temp'] = color_temp
            self.lamp_status['last_update'] = datetime.now().isoformat()
            self.logger.info(f"设置台灯色温为: {color_temp}K")
            return True
        except Exception as e:
            self.logger.error(f"设置台灯色温失败: {e}")
            return False
    
    # 没办法调节RGB颜色，暂时注释掉
    # def set_rgb_color(self, r, g, b):
    #     """
    #     设置台灯RGB颜色
        
    #     Args:
    #         r (int): 红色值 (0-255)
    #         g (int): 绿色值 (0-255) 
    #         b (int): 蓝色值 (0-255)
    #     """
    #     try:
    #         # 限制RGB值范围
    #         r = max(0, min(255, r))
    #         g = max(0, min(255, g))
    #         b = max(0, min(255, b))
            
    #         # if self.serial_handler:
    #         #     cmd = f"RGB:{r},{g},{b}"
    #         #     self.serial_handler.send_command(cmd)
            
    #         self.lamp_status['rgb_color'] = {'r': r, 'g': g, 'b': b}
    #         self.lamp_status['color_mode'] = 'rgb'
    #         self.lamp_status['last_update'] = datetime.now().isoformat()
    #         self.logger.info(f"设置台灯RGB颜色为: R{r} G{g} B{b}")
    #         return True
    #     except Exception as e:
    #         self.logger.error(f"设置台灯RGB颜色失败: {e}")
    #         return False
    
    def set_color_mode(self, mode):
        """
        设置台灯颜色模式
        
        Args:
            mode (str): 颜色模式 warm, cool, daylight, rgb
        """
        try:
            valid_modes = ['warm', 'cool', 'daylight', 'rgb']
            if mode not in valid_modes:
                raise ValueError(f"无效的颜色模式: {mode}")
            
            # TODO: 通过串口发送颜色模式命令
            # if self.serial_handler:
            #     cmd = f"COLOR_MODE:{mode.upper()}"
            #     self.serial_handler.send_command(cmd)
            
            self.lamp_status['color_mode'] = mode
            self.lamp_status['last_update'] = datetime.now().isoformat()
            self.logger.info(f"设置台灯颜色模式为: {mode}")
            return True
        except Exception as e:
            self.logger.error(f"设置台灯颜色模式失败: {e}")
            return False
    
    def set_scene_mode(self, scene):
        """
        设置台灯场景模式
        
        Args:
            scene (str): 场景模式 normal, reading, relax, work
        """
        try:
            valid_scenes = ['normal', 'reading', 'relax', 'work']
            if scene not in valid_scenes:
                raise ValueError(f"无效的场景模式: {scene}")
            
            # TODO: 通过串口发送场景模式命令
            # if self.serial_handler:
            #     cmd = f"SCENE:{scene.upper()}"
            #     self.serial_handler.send_command(cmd)
            
            self.lamp_status['scene_mode'] = scene
            self.lamp_status['last_update'] = datetime.now().isoformat()
            self.logger.info(f"设置台灯场景模式为: {scene}")
            return True
        except Exception as e:
            self.logger.error(f"设置台灯场景模式失败: {e}")
            return False
    
    def set_timer(self, duration_minutes):
        """
        设置台灯定时器
        
        Args:
            duration_minutes (int): 定时器时长(分钟)，0为关闭定时器
        """
        try:
            if duration_minutes < 0:
                duration_minutes = 0
            
            # TODO: 通过串口发送定时器命令
            # if self.serial_handler:
            #     if duration_minutes > 0:
            #         cmd = f"TIMER:{duration_minutes}"
            #     else:
            #         cmd = "TIMER:OFF"
            #     self.serial_handler.send_command(cmd)
            
            self.lamp_status['timer_enabled'] = duration_minutes > 0
            self.lamp_status['timer_duration'] = duration_minutes
            self.lamp_status['last_update'] = datetime.now().isoformat()
            
            if duration_minutes > 0:
                self.logger.info(f"设置台灯定时器: {duration_minutes}分钟")
            else:
                self.logger.info("关闭台灯定时器")
            return True
        except Exception as e:
            self.logger.error(f"设置台灯定时器失败: {e}")
            return False
    
    def toggle_auto_mode(self, enabled):
        """
        切换自动模式
        
        Args:
            enabled (bool): True为启用自动模式，False为关闭
        """
        try:
            # TODO: 通过串口发送自动模式命令
            # if self.serial_handler:
            #     cmd = f"AUTO_MODE:{'ON' if enabled else 'OFF'}"
            #     self.serial_handler.send_command(cmd)
            
            self.lamp_status['auto_mode'] = enabled
            self.lamp_status['last_update'] = datetime.now().isoformat()
            self.logger.info(f"台灯自动模式{'启用' if enabled else '关闭'}")
            return True
        except Exception as e:
            self.logger.error(f"切换台灯自动模式失败: {e}")
            return False


def create_lamp_control_blueprint(serial_handler=None):
    """
    创建台灯控制蓝图
    
    Args:
        serial_handler: 串口处理器实例
    
    Returns:
        Flask Blueprint对象
    """
    lamp_control = Blueprint('lamp_control', __name__)
    handler = LampControlHandler(serial_handler)
    
    @lamp_control.route('/api/lamp/status', methods=['GET'])
    def get_lamp_status():
        """获取台灯状态API"""
        try:
            status = handler.get_lamp_status()
            if status:
                return jsonify({
                    'success': True,
                    'data': status,
                    'message': '获取台灯状态成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '获取台灯状态失败'
                }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'服务器错误: {str(e)}'
            }), 500
    
    @lamp_control.route('/api/lamp/power', methods=['POST'])
    def set_lamp_power():
        """设置台灯开关API"""
        try:
            data = request.get_json()
            if not data or 'power' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少power参数'
                }), 400
            
            power_on = bool(data['power'])
            success = handler.set_power(power_on)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {'power': power_on},
                    'message': f"台灯{'开启' if power_on else '关闭'}成功"
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '设置台灯开关失败'
                }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'服务器错误: {str(e)}'
            }), 500
    
    @lamp_control.route('/api/lamp/brightness', methods=['POST'])
    def set_lamp_brightness():
        """设置台灯亮度API"""
        try:
            data = request.get_json()
            if not data or 'brightness' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少brightness参数'
                }), 400
            
            brightness = int(data['brightness'])
            if brightness < 0 or brightness > 100:
                return jsonify({
                    'success': False,
                    'message': '亮度值必须在0-100之间'
                }), 400
            
            success = handler.set_brightness(brightness)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {'brightness': brightness},
                    'message': f'设置台灯亮度为{brightness}%成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '设置台灯亮度失败'
                }), 500
        except ValueError:
            return jsonify({
                'success': False,
                'message': '亮度值必须为数字'
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'服务器错误: {str(e)}'
            }), 500
    
    @lamp_control.route('/api/lamp/color_temp', methods=['POST'])
    def set_lamp_color_temp():
        """设置台灯色温API"""
        try:
            data = request.get_json()
            if not data or 'color_temp' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少color_temp参数'
                }), 400
            
            color_temp = int(data['color_temp'])
            if color_temp < 2700 or color_temp > 6500:
                return jsonify({
                    'success': False,
                    'message': '色温值必须在2700K-6500K之间'
                }), 400
            
            success = handler.set_color_temperature(color_temp)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {'color_temp': color_temp},
                    'message': f'设置台灯色温为{color_temp}K成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '设置台灯色温失败'
                }), 500
        except ValueError:
            return jsonify({
                'success': False,
                'message': '色温值必须为数字'
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'服务器错误: {str(e)}'
            }), 500
    
    @lamp_control.route('/api/lamp/rgb', methods=['POST'])
    def set_lamp_rgb():
        """设置台灯RGB颜色API"""
        try:
            data = request.get_json()
            if not data or not all(key in data for key in ['r', 'g', 'b']):
                return jsonify({
                    'success': False,
                    'message': '缺少r, g, b参数'
                }), 400
            
            r = int(data['r'])
            g = int(data['g'])
            b = int(data['b'])
            
            for val, name in [(r, 'r'), (g, 'g'), (b, 'b')]:
                if val < 0 or val > 255:
                    return jsonify({
                        'success': False,
                        'message': f'{name}值必须在0-255之间'
                    }), 400
            
            success = handler.set_rgb_color(r, g, b)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {'r': r, 'g': g, 'b': b},
                    'message': f'设置台灯RGB颜色为R{r} G{g} B{b}成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '设置台灯RGB颜色失败'
                }), 500
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'RGB值必须为数字'
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'服务器错误: {str(e)}'
            }), 500
    
    @lamp_control.route('/api/lamp/color_mode', methods=['POST'])
    def set_lamp_color_mode():
        """设置台灯颜色模式API"""
        try:
            data = request.get_json()
            if not data or 'mode' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少mode参数'
                }), 400
            
            mode = data['mode']
            valid_modes = ['warm', 'cool', 'daylight', 'rgb']
            if mode not in valid_modes:
                return jsonify({
                    'success': False,
                    'message': f'无效的颜色模式，支持的模式: {", ".join(valid_modes)}'
                }), 400
            
            success = handler.set_color_mode(mode)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {'color_mode': mode},
                    'message': f'设置台灯颜色模式为{mode}成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '设置台灯颜色模式失败'
                }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'服务器错误: {str(e)}'
            }), 500
    
    @lamp_control.route('/api/lamp/scene', methods=['POST'])
    def set_lamp_scene():
        """设置台灯场景模式API"""
        try:
            data = request.get_json()
            if not data or 'scene' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少scene参数'
                }), 400
            
            scene = data['scene']
            valid_scenes = ['normal', 'reading', 'relax', 'work']
            if scene not in valid_scenes:
                return jsonify({
                    'success': False,
                    'message': f'无效的场景模式，支持的场景: {", ".join(valid_scenes)}'
                }), 400
            
            success = handler.set_scene_mode(scene)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {'scene_mode': scene},
                    'message': f'设置台灯场景模式为{scene}成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '设置台灯场景模式失败'
                }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'服务器错误: {str(e)}'
            }), 500
    
    @lamp_control.route('/api/lamp/timer', methods=['POST'])
    def set_lamp_timer():
        """设置台灯定时器API"""
        try:
            data = request.get_json()
            if not data or 'duration' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少duration参数'
                }), 400
            
            duration = int(data['duration'])
            if duration < 0:
                return jsonify({
                    'success': False,
                    'message': '定时器时长不能为负数'
                }), 400
            
            success = handler.set_timer(duration)
            
            if success:
                if duration > 0:
                    message = f'设置台灯定时器{duration}分钟成功'
                else:
                    message = '关闭台灯定时器成功'
                
                return jsonify({
                    'success': True,
                    'data': {
                        'timer_enabled': duration > 0,
                        'timer_duration': duration
                    },
                    'message': message
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '设置台灯定时器失败'
                }), 500
        except ValueError:
            return jsonify({
                'success': False,
                'message': '定时器时长必须为数字'
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'服务器错误: {str(e)}'
            }), 500
    
    @lamp_control.route('/api/lamp/auto_mode', methods=['POST'])
    def toggle_lamp_auto_mode():
        """切换台灯自动模式API"""
        try:
            data = request.get_json()
            if not data or 'enabled' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少enabled参数'
                }), 400
            
            enabled = bool(data['enabled'])
            success = handler.toggle_auto_mode(enabled)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {'auto_mode': enabled},
                    'message': f"台灯自动模式{'启用' if enabled else '关闭'}成功"
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '切换台灯自动模式失败'
                }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'服务器错误: {str(e)}'
            }), 500
    
    @lamp_control.route('/api/lamp/preset', methods=['POST'])
    def set_lamp_preset():
        """设置台灯预设配置API"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'message': '缺少配置参数'
                }), 400
            
            results = []
            
            # 批量设置多个参数
            if 'power' in data:
                success = handler.set_power(bool(data['power']))
                results.append(('power', success))
            
            if 'brightness' in data:
                brightness = max(0, min(100, int(data['brightness'])))
                success = handler.set_brightness(brightness)
                results.append(('brightness', success))
            
            if 'color_temp' in data:
                color_temp = max(2700, min(6500, int(data['color_temp'])))
                success = handler.set_color_temperature(color_temp)
                results.append(('color_temp', success))
            
            if 'scene' in data:
                valid_scenes = ['normal', 'reading', 'relax', 'work']
                if data['scene'] in valid_scenes:
                    success = handler.set_scene_mode(data['scene'])
                    results.append(('scene', success))
            
            # 检查是否所有操作都成功
            all_success = all(result[1] for result in results)
            
            return jsonify({
                'success': all_success,
                'data': handler.get_lamp_status(),
                'message': '预设配置应用完成' if all_success else '部分配置应用失败',
                'details': {name: success for name, success in results}
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'服务器错误: {str(e)}'
            }), 500
    
    return lamp_control


def main():
    """
    主函数 - 用于直接运行模块测试串口通信
    """
    from flask import Flask
    import sys
    import os
    
    # 添加项目根目录到Python路径
    project_root = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, project_root)
    
    try:
        # 导入串口处理器
        from serial_handler import SerialHandler
        
        print("=== 台灯控制模块测试 ===")
        print("正在初始化串口处理器...")
        
        # 初始化串口处理器
        try:
            serial_handler = SerialHandler()
            print(f"✓ 串口处理器初始化成功，使用端口: {serial_handler.port}")
            serial_available = True
        except Exception as e:
            print(f"✗ 串口处理器初始化失败: {e}")
            print("  将在无串口模式下运行")
            serial_handler = None
            serial_available = False
        
        # 创建Flask应用
        app = Flask(__name__)
        app.config['DEBUG'] = True
        
        # 创建台灯控制蓝图
        lamp_control_bp = create_lamp_control_blueprint(serial_handler)
        app.register_blueprint(lamp_control_bp)
        
        # 创建测试页面
        @app.route('/')
        def index():
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>台灯控制模块测试</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .container { max-width: 800px; margin: 0 auto; }
                    .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
                    .success { background-color: #d4edda; color: #155724; }
                    .error { background-color: #f8d7da; color: #721c24; }
                    .warning { background-color: #fff3cd; color: #856404; }
                    button { padding: 10px 15px; margin: 5px; cursor: pointer; }
                    .test-section { border: 1px solid #ddd; padding: 15px; margin: 10px 0; }
                    input[type="number"], input[type="range"] { width: 100px; }
                    #status-display { background: #f8f9fa; padding: 15px; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>台灯控制模块测试</h1>
                    
                    <div class="status ''' + ('success' if serial_available else 'warning') + '''">
                        串口状态: ''' + ('已连接' if serial_available else '未连接（仿真模式）') + '''
                    </div>
                    
                    <div class="test-section">
                        <h3>台灯状态</h3>
                        <button onclick="getLampStatus()">获取状态</button>
                        <div id="status-display">点击"获取状态"查看当前台灯状态</div>
                    </div>
                    
                    <div class="test-section">
                        <h3>基本控制</h3>
                        <button onclick="setLampPower(true)">开灯</button>
                        <button onclick="setLampPower(false)">关灯</button>
                        <br>
                        亮度: <input type="range" id="brightness" min="0" max="100" value="50" onchange="setBrightness(this.value)">
                        <span id="brightness-value">50%</span>
                        <br>
                        色温: <input type="range" id="colortemp" min="2700" max="6500" value="4000" onchange="setColorTemp(this.value)">
                        <span id="colortemp-value">4000K</span>
                    </div>
                    
                    <div class="test-section">
                        <h3>颜色控制</h3>
                        <button onclick="setColorMode('warm')">暖光</button>
                        <button onclick="setColorMode('cool')">冷光</button>
                        <button onclick="setColorMode('daylight')">日光</button>
                        <button onclick="setColorMode('rgb')">RGB</button>
                        <br>
                        RGB: 
                        R:<input type="number" id="r" min="0" max="255" value="255">
                        G:<input type="number" id="g" min="0" max="255" value="255">
                        B:<input type="number" id="b" min="0" max="255" value="255">
                        <button onclick="setRGBColor()">设置RGB</button>
                    </div>
                    
                    <div class="test-section">
                        <h3>场景模式</h3>
                        <button onclick="setScene('normal')">普通</button>
                        <button onclick="setScene('reading')">阅读</button>
                        <button onclick="setScene('relax')">放松</button>
                        <button onclick="setScene('work')">工作</button>
                    </div>
                    
                    <div class="test-section">
                        <h3>定时器</h3>
                        <input type="number" id="timer" min="0" max="120" value="0" placeholder="分钟">
                        <button onclick="setTimer()">设置定时器</button>
                        <button onclick="setTimerValue(0)">关闭定时器</button>
                    </div>
                    
                    <div class="test-section">
                        <h3>自动模式</h3>
                        <button onclick="setAutoMode(true)">启用自动模式</button>
                        <button onclick="setAutoMode(false)">关闭自动模式</button>
                    </div>
                    
                    <div id="response-log" style="background: #f8f9fa; padding: 15px; margin-top: 20px; max-height: 200px; overflow-y: auto;">
                        <h4>响应日志</h4>
                    </div>
                </div>
                
                <script>
                function logResponse(message, isError = false) {
                    const log = document.getElementById('response-log');
                    const time = new Date().toLocaleTimeString();
                    const color = isError ? 'red' : 'green';
                    log.innerHTML += `<div style="color: ${color};">[${time}] ${message}</div>`;
                    log.scrollTop = log.scrollHeight;
                }
                
                async function apiCall(url, method = 'GET', data = null) {
                    try {
                        const options = {
                            method: method,
                            headers: {
                                'Content-Type': 'application/json',
                            }
                        };
                        if (data) {
                            options.body = JSON.stringify(data);
                        }
                        
                        const response = await fetch(url, options);
                        const result = await response.json();
                        
                        if (result.success) {
                            logResponse(`✓ ${result.message}`);
                        } else {
                            logResponse(`✗ ${result.message}`, true);
                        }
                        
                        return result;
                    } catch (error) {
                        logResponse(`✗ 请求失败: ${error.message}`, true);
                        return null;
                    }
                }
                
                async function getLampStatus() {
                    const result = await apiCall('/api/lamp/status');
                    if (result && result.success) {
                        document.getElementById('status-display').innerHTML = 
                            '<pre>' + JSON.stringify(result.data, null, 2) + '</pre>';
                    }
                }
                
                async function setLampPower(power) {
                    await apiCall('/api/lamp/power', 'POST', {power: power});
                }
                
                async function setBrightness(value) {
                    document.getElementById('brightness-value').textContent = value + '%';
                    await apiCall('/api/lamp/brightness', 'POST', {brightness: parseInt(value)});
                }
                
                async function setColorTemp(value) {
                    document.getElementById('colortemp-value').textContent = value + 'K';
                    await apiCall('/api/lamp/color_temp', 'POST', {color_temp: parseInt(value)});
                }
                
                async function setColorMode(mode) {
                    await apiCall('/api/lamp/color_mode', 'POST', {mode: mode});
                }
                
                async function setRGBColor() {
                    const r = parseInt(document.getElementById('r').value);
                    const g = parseInt(document.getElementById('g').value);  
                    const b = parseInt(document.getElementById('b').value);
                    await apiCall('/api/lamp/rgb', 'POST', {r: r, g: g, b: b});
                }
                
                async function setScene(scene) {
                    await apiCall('/api/lamp/scene', 'POST', {scene: scene});
                }
                
                async function setTimer() {
                    const duration = parseInt(document.getElementById('timer').value);
                    await apiCall('/api/lamp/timer', 'POST', {duration: duration});
                }
                
                async function setTimerValue(value) {
                    document.getElementById('timer').value = value;
                    await apiCall('/api/lamp/timer', 'POST', {duration: value});
                }
                
                async function setAutoMode(enabled) {
                    await apiCall('/api/lamp/auto_mode', 'POST', {enabled: enabled});
                }
                
                // 页面加载时获取状态
                window.onload = function() {
                    getLampStatus();
                };
                </script>
            </body>
            </html>
            '''
        
        print("\n=== 测试服务器启动 ===")
        print("访问 http://localhost:5003 进行测试")
        print("按 Ctrl+C 停止服务器")
        print("\n可用的API接口:")
        print("  GET  /api/lamp/status          - 获取台灯状态")
        print("  POST /api/lamp/power           - 设置开关")
        print("  POST /api/lamp/brightness      - 设置亮度")
        print("  POST /api/lamp/color_temp      - 设置色温")
        print("  POST /api/lamp/rgb             - 设置RGB颜色")
        print("  POST /api/lamp/color_mode      - 设置颜色模式")
        print("  POST /api/lamp/scene           - 设置场景模式")
        print("  POST /api/lamp/timer           - 设置定时器")
        print("  POST /api/lamp/auto_mode       - 设置自动模式")
        print("  POST /api/lamp/preset          - 批量设置")
        
        if serial_available:
            print(f"\n串口连接状态: ✓ 已连接到 {serial_handler.port}")
            print("串口命令将通过 serial_handler.send_command() 发送")
        else:
            print("\n串口连接状态: ✗ 未连接")
            print("运行在仿真模式，串口命令将被忽略")
        
        # 启动Flask应用
        app.run(host='0.0.0.0', port=5003, debug=False)
        
    except KeyboardInterrupt:
        print("\n程序已停止")
    except Exception as e:
        print(f"程序运行错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()