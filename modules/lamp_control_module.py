"""
台灯远程控制模块 - 提供台灯控制的所有功能和API接口
"""
from flask import Blueprint, request, jsonify, render_template
import json
import time
from datetime import datetime
import logging
import threading

# 导入串口模块用于通信
from serial_handler import SerialHandler

class LampControlHandler:
    """台灯控制处理器类"""
    
    def __init__(self, serial_handler=None):
        """
        初始化台灯控制处理器
        
        Args:
            serial_handler: 串口处理器实例，如果为None则不会发送实际命令
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
        
        # 定时器线程
        self.timer_thread = None
        self.timer_running = False
    
    def get_lamp_status(self):
        """获取台灯当前状态"""
        try:
            # 通过串口查询台灯实际状态
            if self.serial_handler and self.serial_handler.is_connected():
                # 发送查询状态命令
                # TODO: 这里留空，实现串口状态查询命令
                # status_cmd = "GET_STATUS"
                # response = self.serial_handler.send_command(status_cmd)
                # if response:
                #     # 解析返回的状态数据并更新lamp_status
                #     pass
                pass
            
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
            # 通过串口发送开关命令
            if self.serial_handler and self.serial_handler.is_connected():
                # TODO: 这里留空，实现串口开关控制命令发送
                # cmd = f"POWER:{'ON' if power_on else 'OFF'}"
                # self.serial_handler.send_command(cmd)
                pass
            
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
            
            # 通过串口发送亮度命令
            if self.serial_handler and self.serial_handler.is_connected():
                # TODO: 这里留空，实现串口亮度控制命令发送
                # cmd = f"BRIGHTNESS:{brightness}"
                # self.serial_handler.send_command(cmd)
                pass
            
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
            
            # 通过串口发送色温命令
            if self.serial_handler and self.serial_handler.is_connected():
                # TODO: 这里留空，实现串口色温控制命令发送
                # cmd = f"COLOR_TEMP:{color_temp}"
                # self.serial_handler.send_command(cmd)
                pass
            
            self.lamp_status['color_temp'] = color_temp
            self.lamp_status['last_update'] = datetime.now().isoformat()
            self.logger.info(f"设置台灯色温为: {color_temp}K")
            return True
        except Exception as e:
            self.logger.error(f"设置台灯色温失败: {e}")
            return False
    
    def set_rgb_color(self, r, g, b):
        """
        设置台灯RGB颜色
        
        Args:
            r (int): 红色值 (0-255)
            g (int): 绿色值 (0-255) 
            b (int): 蓝色值 (0-255)
        """
        try:
            # 限制RGB值范围
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            # 通过串口发送RGB颜色命令
            if self.serial_handler and self.serial_handler.is_connected():
                # TODO: 这里留空，实现串口RGB颜色控制命令发送
                # cmd = f"RGB:{r},{g},{b}"
                # self.serial_handler.send_command(cmd)
                pass
            
            self.lamp_status['rgb_color'] = {'r': r, 'g': g, 'b': b}
            self.lamp_status['color_mode'] = 'rgb'
            self.lamp_status['last_update'] = datetime.now().isoformat()
            self.logger.info(f"设置台灯RGB颜色为: R{r} G{g} B{b}")
            return True
        except Exception as e:
            self.logger.error(f"设置台灯RGB颜色失败: {e}")
            return False
    
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
            
            # 通过串口发送颜色模式命令
            if self.serial_handler and self.serial_handler.is_connected():
                # TODO: 这里留空，实现串口颜色模式控制命令发送
                # cmd = f"COLOR_MODE:{mode.upper()}"
                # self.serial_handler.send_command(cmd)
                pass
            
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
            
            # 通过串口发送场景模式命令
            if self.serial_handler and self.serial_handler.is_connected():
                # TODO: 这里留空，实现串口场景模式控制命令发送
                # cmd = f"SCENE:{scene.upper()}"
                # self.serial_handler.send_command(cmd)
                pass
            
            self.lamp_status['scene_mode'] = scene
            self.lamp_status['last_update'] = datetime.now().isoformat()
            self.logger.info(f"设置台灯场景模式为: {scene}")
            return True
        except Exception as e:
            self.logger.error(f"设置台灯场景模式失败: {e}")
            return False
    
    def set_timer(self, duration):
        """
        设置台灯定时器
        
        Args:
            duration (int): 定时时长(分钟)，0表示关闭定时器
        """
        try:
            # 限制定时器时长范围
            duration = max(0, min(180, duration))  # 最大180分钟
            
            # 如果有正在运行的定时器，停止它
            if self.timer_thread and self.timer_running:
                self.timer_running = False
                self.timer_thread.join(1)  # 等待线程结束，最多等待1秒
            
            # 更新状态
            self.lamp_status['timer_enabled'] = duration > 0
            self.lamp_status['timer_duration'] = duration
            self.lamp_status['last_update'] = datetime.now().isoformat()
            
            # 如果设置了有效的定时时长，启动定时器线程
            if duration > 0:
                self.timer_running = True
                self.timer_thread = threading.Thread(target=self._timer_countdown, args=(duration,))
                self.timer_thread.daemon = True
                self.timer_thread.start()
                
                # 通过串口发送定时器命令
                if self.serial_handler and self.serial_handler.is_connected():
                    # TODO: 这里留空，实现串口定时器控制命令发送
                    # cmd = f"TIMER:{duration}"
                    # self.serial_handler.send_command(cmd)
                    pass
                
                self.logger.info(f"设置台灯定时器: {duration}分钟")
            else:
                # 关闭定时器
                if self.serial_handler and self.serial_handler.is_connected():
                    # TODO: 这里留空，实现串口关闭定时器命令发送
                    # cmd = "TIMER:0"
                    # self.serial_handler.send_command(cmd)
                    pass
                
                self.logger.info("关闭台灯定时器")
            
            return True
        except Exception as e:
            self.logger.error(f"设置台灯定时器失败: {e}")
            return False
    
    def _timer_countdown(self, duration):
        """
        定时器倒计时线程函数
        
        Args:
            duration (int): 定时时长(分钟)
        """
        try:
            # 将分钟转换为秒
            seconds = duration * 60
            
            # 倒计时
            while seconds > 0 and self.timer_running:
                time.sleep(1)
                seconds -= 1
            
            # 如果定时器正常结束（不是被中途取消）
            if self.timer_running:
                # 关闭台灯
                self.set_power(False)
                
                # 重置定时器状态
                self.lamp_status['timer_enabled'] = False
                self.lamp_status['timer_duration'] = 0
                self.lamp_status['last_update'] = datetime.now().isoformat()
                
                self.logger.info("定时器时间到，已关闭台灯")
            
            # 标记定时器线程已结束
            self.timer_running = False
        except Exception as e:
            self.logger.error(f"定时器线程出错: {e}")
            self.timer_running = False
    
    def set_auto_mode(self, enabled):
        """
        设置台灯自动模式
        
        Args:
            enabled (bool): True为启用自动模式，False为关闭自动模式
        """
        try:
            # 通过串口发送自动模式命令
            if self.serial_handler and self.serial_handler.is_connected():
                # TODO: 这里留空，实现串口自动模式控制命令发送
                # cmd = f"AUTO_MODE:{'ON' if enabled else 'OFF'}"
                # self.serial_handler.send_command(cmd)
                pass
            
            self.lamp_status['auto_mode'] = enabled
            self.lamp_status['last_update'] = datetime.now().isoformat()
            self.logger.info(f"{'启用' if enabled else '关闭'}台灯自动模式")
            return True
        except Exception as e:
            self.logger.error(f"设置台灯自动模式失败: {e}")
            return False
    
    def set_preset(self, preset_data):
        """
        应用预设配置
        
        Args:
            preset_data (dict): 预设配置数据
        """
        try:
            # 预设中可能包含的配置项
            if 'power' in preset_data:
                self.set_power(preset_data['power'])
            
            if 'brightness' in preset_data:
                self.set_brightness(preset_data['brightness'])
            
            if 'color_temp' in preset_data:
                self.set_color_temperature(preset_data['color_temp'])
            
            if 'rgb_color' in preset_data:
                rgb = preset_data['rgb_color']
                self.set_rgb_color(rgb['r'], rgb['g'], rgb['b'])
            
            if 'color_mode' in preset_data:
                self.set_color_mode(preset_data['color_mode'])
            
            if 'scene_mode' in preset_data:
                self.set_scene_mode(preset_data['scene_mode'])
            
            if 'timer_duration' in preset_data:
                self.set_timer(preset_data['timer_duration'])
            
            if 'auto_mode' in preset_data:
                self.set_auto_mode(preset_data['auto_mode'])
            
            self.logger.info("已应用台灯预设配置")
            return True
        except Exception as e:
            self.logger.error(f"应用台灯预设配置失败: {e}")
            return False

def create_lamp_control_blueprint(serial_handler=None):
    """
    创建台灯控制蓝图
    
    Args:
        serial_handler: 串口处理器实例
    
    Returns:
        Blueprint: 台灯控制蓝图
    """
    lamp_bp = Blueprint('lamp', __name__)
    
    # 创建台灯控制处理器实例
    lamp_handler = LampControlHandler(serial_handler)
    
    # 台灯控制界面
    @lamp_bp.route('/lamp_control')
    def lamp_control_page():
        return render_template('lamp_control.html')
    
    # 获取台灯状态API
    @lamp_bp.route('/api/lamp/status', methods=['GET'])
    def get_lamp_status():
        """获取台灯当前状态"""
        status = lamp_handler.get_lamp_status()
        if status:
            return jsonify({
                'status': 'success',
                'data': status
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '获取台灯状态失败'
            }), 500
    
    # 设置台灯开关API
    @lamp_bp.route('/api/lamp/power', methods=['POST'])
    def set_lamp_power():
        """设置台灯开关"""
        try:
            data = request.get_json()
            if 'power' not in data:
                return jsonify({
                    'status': 'error',
                    'message': '缺少power参数'
                }), 400
            
            power_on = bool(data['power'])
            if lamp_handler.set_power(power_on):
                return jsonify({
                    'status': 'success',
                    'message': f"台灯{'开启' if power_on else '关闭'}成功",
                    'data': {'power': power_on}
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f"台灯{'开启' if power_on else '关闭'}失败"
                }), 500
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f"设置台灯开关出错: {str(e)}"
            }), 500
    
    # 设置台灯亮度API
    @lamp_bp.route('/api/lamp/brightness', methods=['POST'])
    def set_lamp_brightness():
        """设置台灯亮度"""
        try:
            data = request.get_json()
            if 'brightness' not in data:
                return jsonify({
                    'status': 'error',
                    'message': '缺少brightness参数'
                }), 400
            
            brightness = int(data['brightness'])
            if lamp_handler.set_brightness(brightness):
                return jsonify({
                    'status': 'success',
                    'message': f"设置台灯亮度为{brightness}%成功",
                    'data': {'brightness': brightness}
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': "设置台灯亮度失败"
                }), 500
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f"设置台灯亮度出错: {str(e)}"
            }), 500
    
    # 设置台灯色温API
    @lamp_bp.route('/api/lamp/color_temp', methods=['POST'])
    def set_lamp_color_temp():
        """设置台灯色温"""
        try:
            data = request.get_json()
            if 'color_temp' not in data:
                return jsonify({
                    'status': 'error',
                    'message': '缺少color_temp参数'
                }), 400
            
            color_temp = int(data['color_temp'])
            if lamp_handler.set_color_temperature(color_temp):
                return jsonify({
                    'status': 'success',
                    'message': f"设置台灯色温为{color_temp}K成功",
                    'data': {'color_temp': color_temp}
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': "设置台灯色温失败"
                }), 500
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f"设置台灯色温出错: {str(e)}"
            }), 500
    
    # 设置台灯RGB颜色API
    @lamp_bp.route('/api/lamp/rgb', methods=['POST'])
    def set_lamp_rgb():
        """设置台灯RGB颜色"""
        try:
            data = request.get_json()
            if not all(key in data for key in ['r', 'g', 'b']):
                return jsonify({
                    'status': 'error',
                    'message': '缺少r, g, b参数'
                }), 400
            
            r = int(data['r'])
            g = int(data['g'])
            b = int(data['b'])
            
            if lamp_handler.set_rgb_color(r, g, b):
                return jsonify({
                    'status': 'success',
                    'message': f"设置台灯RGB颜色为R{r}G{g}B{b}成功",
                    'data': {'r': r, 'g': g, 'b': b}
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': "设置台灯RGB颜色失败"
                }), 500
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f"设置台灯RGB颜色出错: {str(e)}"
            }), 500
    
    # 设置台灯颜色模式API
    @lamp_bp.route('/api/lamp/color_mode', methods=['POST'])
    def set_lamp_color_mode():
        """设置台灯颜色模式"""
        try:
            data = request.get_json()
            if 'mode' not in data:
                return jsonify({
                    'status': 'error',
                    'message': '缺少mode参数'
                }), 400
            
            mode = data['mode']
            if lamp_handler.set_color_mode(mode):
                return jsonify({
                    'status': 'success',
                    'message': f"设置台灯颜色模式为{mode}成功",
                    'data': {'color_mode': mode}
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': "设置台灯颜色模式失败"
                }), 500
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f"设置台灯颜色模式出错: {str(e)}"
            }), 500
    
    # 设置台灯场景模式API
    @lamp_bp.route('/api/lamp/scene', methods=['POST'])
    def set_lamp_scene():
        """设置台灯场景模式"""
        try:
            data = request.get_json()
            if 'scene' not in data:
                return jsonify({
                    'status': 'error',
                    'message': '缺少scene参数'
                }), 400
            
            scene = data['scene']
            if lamp_handler.set_scene_mode(scene):
                return jsonify({
                    'status': 'success',
                    'message': f"设置台灯场景模式为{scene}成功",
                    'data': {'scene_mode': scene}
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': "设置台灯场景模式失败"
                }), 500
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f"设置台灯场景模式出错: {str(e)}"
            }), 500
    
    # 设置台灯定时器API
    @lamp_bp.route('/api/lamp/timer', methods=['POST'])
    def set_lamp_timer():
        """设置台灯定时器"""
        try:
            data = request.get_json()
            if 'duration' not in data:
                return jsonify({
                    'status': 'error',
                    'message': '缺少duration参数'
                }), 400
            
            duration = int(data['duration'])
            if lamp_handler.set_timer(duration):
                return jsonify({
                    'status': 'success',
                    'message': f"设置台灯定时器{duration}分钟成功" if duration > 0 else "关闭台灯定时器成功",
                    'data': {
                        'timer_enabled': duration > 0,
                        'timer_duration': duration
                    }
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': "设置台灯定时器失败"
                }), 500
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f"设置台灯定时器出错: {str(e)}"
            }), 500
    
    # 设置台灯自动模式API
    @lamp_bp.route('/api/lamp/auto_mode', methods=['POST'])
    def set_lamp_auto_mode():
        """设置台灯自动模式"""
        try:
            data = request.get_json()
            if 'enabled' not in data:
                return jsonify({
                    'status': 'error',
                    'message': '缺少enabled参数'
                }), 400
            
            enabled = bool(data['enabled'])
            if lamp_handler.set_auto_mode(enabled):
                return jsonify({
                    'status': 'success',
                    'message': f"{'启用' if enabled else '关闭'}台灯自动模式成功",
                    'data': {'auto_mode': enabled}
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f"{'启用' if enabled else '关闭'}台灯自动模式失败"
                }), 500
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f"设置台灯自动模式出错: {str(e)}"
            }), 500
    
    # 设置台灯预设配置API
    @lamp_bp.route('/api/lamp/preset', methods=['POST'])
    def set_lamp_preset():
        """设置台灯预设配置"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': '预设配置数据为空'
                }), 400
            
            if lamp_handler.set_preset(data):
                return jsonify({
                    'status': 'success',
                    'message': "应用台灯预设配置成功",
                    'data': lamp_handler.get_lamp_status()
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': "应用台灯预设配置失败"
                }), 500
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f"应用台灯预设配置出错: {str(e)}"
            }), 500
    
    return lamp_bp
