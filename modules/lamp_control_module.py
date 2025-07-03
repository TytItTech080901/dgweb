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
                data = self.serial_handler.request_data(0x40, [1]*8)
                if data is None:
                    self.logger.error("无法从台灯获取状态数据")
                else:
                    if data['command'] == 0xBF:
                        self.logger.error("台灯未开机，不响应命令")
                    elif data['datatype'] != 0xB0:
                        self.logger.error(f"未知数据类型: {data['datatype']}")
                    elif data['command'] != 0x41:
                        self.logger.error(f"未知命令: {data['command']}")
                    else:
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
            # 通过串口发送开关命令
            if self.serial_handler and self.serial_handler.is_connected():
                # 使用正确的串口协议发送开关命令
                if power_on:
                    success = self.serial_handler.send_command(0x14, [0] * 8)
                    if success:
                        self.logger.info("串口命令发送成功: 开灯")
                    else:
                        self.logger.error("串口命令发送失败: 开灯")
                        return False
                else:
                    success = self.serial_handler.send_command(0x15, [0] * 8)
                    if success:
                        self.logger.info("串口命令发送成功: 关灯")
                    else:
                        self.logger.error("串口命令发送失败: 关灯")
                        return False
            
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
                # 使用正确的串口协议发送亮度命令
                # 获取当前色温值
                color_temp = self.lamp_status['color_temp']
                # 将色温从2700K-6500K范围映射到0-100
                color_temp_percent = int((color_temp - 2700) / 38)  # (6500-2700)/100=38
                # 发送亮度和色温命令
                if not self.serial_handler.send_command_setting_light(brightness, color_temp_percent):
                    self.logger.error("串口发送亮度命令失败")
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
            
            # 通过串口发送色温命令
            if self.serial_handler and self.serial_handler.is_connected():
                # 将色温从2700K-6500K范围映射到0-100
                color_temp_percent = int((color_temp - 2700) / 38)  # (6500-2700)/100=38
                # 获取当前亮度值
                brightness = self.lamp_status['brightness']
                # 发送亮度和色温命令
                if not self.serial_handler.send_command_setting_light(brightness, color_temp_percent):
                    self.logger.error("串口发送色温命令失败")
                    return False
            
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
            
            # 注意：当前台灯硬件不支持RGB颜色调节
            # 仅更新状态，不实际发送命令
            self.logger.warning("当前台灯硬件不支持RGB颜色调节，仅更新状态")
            
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
            
            # 根据颜色模式设置相应的色温
            if self.serial_handler and self.serial_handler.is_connected():
                # 根据模式设置对应的色温
                color_temps = {
                    'warm': 2700,     # 暖光 (2700K)
                    'cool': 4500,     # 冷光 (4500K)
                    'daylight': 6500, # 日光 (6500K)
                    'rgb': 4000       # RGB模式下默认中性色温
                }
                
                if mode in color_temps:
                    # 设置对应的色温
                    self.set_color_temperature(color_temps[mode])
            
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
            
            # 场景模式对应的参数配置
            scene_configs = {
                'normal': {'brightness': 70, 'color_temp': 4000},  # 普通模式
                'reading': {'brightness': 85, 'color_temp': 5000},  # 阅读模式
                'relax': {'brightness': 40, 'color_temp': 3000},    # 放松模式
                'work': {'brightness': 100, 'color_temp': 5500}     # 工作模式
            }
            
            # 应用场景配置
            if scene in scene_configs:
                config = scene_configs[scene]
                # 设置亮度
                if 'brightness' in config:
                    self.set_brightness(config['brightness'])
                # 设置色温
                if 'color_temp' in config:
                    self.set_color_temperature(config['color_temp'])
            
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
            # 自动模式在下位机未实现，使用软件模拟
            self.logger.info("自动模式在下位机未实现，使用软件模拟")
            
            # 如果启用自动模式，可以在这里添加自动调节逻辑
            # 例如根据时间自动调整亮度和色温
            if enabled:
                # 获取当前小时
                current_hour = datetime.now().hour
                
                # 根据时间设置不同的亮度和色温
                if 6 <= current_hour < 9:  # 早晨
                    self.set_brightness(70)
                    self.set_color_temperature(5000)  # 偏冷色调
                elif 9 <= current_hour < 17:  # 白天
                    self.set_brightness(85)
                    self.set_color_temperature(6000)  # 日光色
                elif 17 <= current_hour < 20:  # 傍晚
                    self.set_brightness(75)
                    self.set_color_temperature(4500)  # 中性色
                else:  # 夜晚
                    self.set_brightness(50)
                    self.set_color_temperature(3000)  # 暖色调
            
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
            
    def set_settings(self, settings_data):
        """
        设置台灯的多个参数
        
        Args:
            settings_data (dict): 包含多个台灯设置参数的字典
        
        Returns:
            bool: 设置是否成功
        """
        try:
            # 验证参数格式
            if not isinstance(settings_data, dict):
                raise ValueError("设置数据必须是字典类型")
            
            # 应用设置，与预设类似但可能有不同的参数名称或结构
            result = True
            updated_settings = {}
            
            # 处理电源设置
            if 'power' in settings_data:
                power = bool(settings_data['power'])
                if self.set_power(power):
                    updated_settings['power'] = power
                else:
                    result = False
            
            # 处理亮度设置
            if 'brightness' in settings_data:
                brightness = int(settings_data['brightness'])
                if self.set_brightness(brightness):
                    updated_settings['brightness'] = brightness
                else:
                    result = False
            
            # 处理色温设置
            if 'color_temp' in settings_data or 'temperature' in settings_data:
                color_temp = int(settings_data.get('color_temp', settings_data.get('temperature', 4000)))
                if self.set_color_temperature(color_temp):
                    updated_settings['color_temp'] = color_temp
                else:
                    result = False
                    
            # 处理直接命令（如前端传来的command参数）
            # 忽略命令参数，我们使用更高级的接口处理
            if 'command' in settings_data:
                # 记录命令但不直接使用，因为我们使用更高级的函数接口
                self.logger.info(f"收到命令参数: {settings_data['command']}，使用高级接口处理")
                updated_settings['command_received'] = settings_data['command']
            
            # 处理RGB颜色设置
            if 'rgb' in settings_data or 'rgb_color' in settings_data:
                rgb_data = settings_data.get('rgb', settings_data.get('rgb_color'))
                if isinstance(rgb_data, dict) and all(k in rgb_data for k in ['r', 'g', 'b']):
                    r, g, b = rgb_data['r'], rgb_data['g'], rgb_data['b']
                    if self.set_rgb_color(r, g, b):
                        updated_settings['rgb_color'] = {'r': r, 'g': g, 'b': b}
                    else:
                        result = False
            
            # 处理颜色模式设置
            if 'color_mode' in settings_data:
                mode = settings_data['color_mode']
                if self.set_color_mode(mode):
                    updated_settings['color_mode'] = mode
                else:
                    result = False
            
            # 处理场景模式设置
            if 'scene_mode' in settings_data or 'scene' in settings_data:
                scene = settings_data.get('scene_mode', settings_data.get('scene'))
                if self.set_scene_mode(scene):
                    updated_settings['scene_mode'] = scene
                else:
                    result = False
            
            # 处理定时器设置
            if 'timer_duration' in settings_data or 'timer' in settings_data:
                duration = settings_data.get('timer_duration', settings_data.get('timer', 0))
                if self.set_timer(duration):
                    updated_settings['timer_duration'] = duration
                    updated_settings['timer_enabled'] = duration > 0
                else:
                    result = False
            
            # 处理自动模式设置
            if 'auto_mode' in settings_data or 'auto' in settings_data:
                enabled = settings_data.get('auto_mode', settings_data.get('auto', False))
                if self.set_auto_mode(enabled):
                    updated_settings['auto_mode'] = enabled
                else:
                    result = False
            
            if result:
                self.logger.info(f"成功应用台灯设置: {updated_settings}")
            else:
                self.logger.warning(f"部分台灯设置应用失败: {updated_settings}")
            
            return result, updated_settings
        except Exception as e:
            self.logger.error(f"设置台灯参数失败: {e}")
            return False, {}

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
    
    # 协议调试界面
    @lamp_bp.route('/protocol_debug')
    def protocol_debug_page():
        """协议调试界面"""
        return render_template('protocol_debug.html')
    
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
            # 安全处理JSON解析
            if not request.is_json:
                return jsonify({
                    'status': 'error', 
                    'message': '请求必须是JSON格式'
                }), 400
                
            try:
                data = request.get_json()
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'无法解析JSON数据: {str(e)}'
                }), 400
                
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
            # 安全处理JSON解析
            if not request.is_json:
                return jsonify({
                    'status': 'error', 
                    'message': '请求必须是JSON格式'
                }), 400
                
            try:
                data = request.get_json()
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'无法解析JSON数据: {str(e)}'
                }), 400
                
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
    
    # 设置台灯多个参数API
    @lamp_bp.route('/api/lamp/settings', methods=['POST'])
    def set_lamp_settings():
        """设置台灯多个参数"""
        try:
            # 安全处理JSON解析
            if not request.is_json:
                return jsonify({
                    'status': 'error', 
                    'message': '请求必须是JSON格式'
                }), 400
                
            try:
                data = request.get_json()
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'无法解析JSON数据: {str(e)}'
                }), 400
                
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': '设置数据为空'
                }), 400
            
            # 记录收到的请求数据
            logging.info(f"收到设置请求: {data}")
            
            success, updated_settings = lamp_handler.set_settings(data)
            if success:
                return jsonify({
                    'status': 'success',
                    'message': "设置台灯参数成功",
                    'data': lamp_handler.get_lamp_status()
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': "部分或全部台灯参数设置失败",
                    'data': updated_settings
                }), 500
        except ValueError as e:
            # 参数验证错误
            return jsonify({
                'status': 'error',
                'message': f"参数无效: {str(e)}"
            }), 400
        except Exception as e:
            # 记录详细错误信息
            logging.exception(f"设置台灯参数出错: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f"设置台灯参数出错: {str(e)}"
            }), 500
    
    # 直接发送串口命令API
    @lamp_bp.route('/api/serial/command', methods=['POST'])
    def send_serial_command():
        """
        直接发送串口命令
        
        这个API允许直接发送任意串口命令
        """
        try:
            # 安全处理JSON解析
            if not request.is_json:
                return jsonify({
                    'status': 'error', 
                    'message': '请求必须是JSON格式'
                }), 400
                
            try:
                data = request.get_json()
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'无法解析JSON数据: {str(e)}'
                }), 400
            
            if 'command' not in data:
                return jsonify({
                    'status': 'error',
                    'message': '缺少command参数'
                }), 400
            
            command = data['command']
            # 记录收到的命令
            logging.info(f"收到串口命令请求: {command}")
            
            # 根据命令格式处理
            if isinstance(command, int) or (isinstance(command, str) and command.startswith('0x')):
                # 处理十六进制命令
                cmd_value = int(command, 16) if isinstance(command, str) else command
                data_bytes = data.get('data', [0] * 8)  # 默认数据
                
                # 发送命令
                if lamp_handler.serial_handler and lamp_handler.serial_handler.is_connected():
                    success = lamp_handler.serial_handler.send_command(cmd_value, data_bytes)
                    if success:
                        return jsonify({
                            'status': 'success',
                            'message': f"命令 {hex(cmd_value) if isinstance(cmd_value, int) else command} 发送成功"
                        })
                    else:
                        return jsonify({
                            'status': 'error',
                            'message': f"命令 {hex(cmd_value) if isinstance(cmd_value, int) else command} 发送失败"
                        }), 500
                else:
                    return jsonify({
                        'status': 'error',
                        'message': "串口未连接"
                    }), 500
            else:
                # 其他格式的命令（如自定义命令字符串）
                return jsonify({
                    'status': 'error',
                    'message': f"不支持的命令格式: {command}"
                }), 400
        except Exception as e:
            # 记录详细错误信息
            logging.exception(f"发送串口命令出错: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f"发送串口命令出错: {str(e)}"
            }), 500
    
    # 串口调试接口
    @lamp_bp.route('/api/serial/debug', methods=['GET', 'POST'])
    def serial_debug():
        """串口调试接口"""
        if request.method == 'GET':
            # 返回串口状态
            if lamp_handler.serial_handler:
                connected = lamp_handler.serial_handler.is_connected()
                port = lamp_handler.serial_handler.port if connected else "未连接"
                baudrate = lamp_handler.serial_handler.baudrate if connected else 0
                
                return jsonify({
                    'status': 'success',
                    'data': {
                        'connected': connected,
                        'port': port,
                        'baudrate': baudrate
                    }
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': "串口处理器未初始化"
                }), 500
        elif request.method == 'POST':
            # 发送调试命令
            try:
                # 安全处理JSON解析
                if not request.is_json:
                    return jsonify({
                        'status': 'error', 
                        'message': '请求必须是JSON格式'
                    }), 400
                    
                try:
                    data = request.get_json()
                except Exception as e:
                    return jsonify({
                        'status': 'error',
                        'message': f'无法解析JSON数据: {str(e)}'
                    }), 400
                
                # 验证参数
                if 'action' not in data:
                    return jsonify({
                        'status': 'error',
                        'message': '缺少action参数'
                    }), 400
                
                action = data['action']
                
                # 处理不同的调试动作
                if action == 'query_status':
                    # 查询台灯状态
                    status = lamp_handler.get_lamp_status()
                    return jsonify({
                        'status': 'success',
                        'data': status
                    })
                elif action == 'reconnect':
                    # 重新连接串口
                    if lamp_handler.serial_handler:
                        success = lamp_handler.serial_handler.reconnect()
                        if success:
                            return jsonify({
                                'status': 'success',
                                'message': "串口重新连接成功"
                            })
                        else:
                            return jsonify({
                                'status': 'error',
                                'message': "串口重新连接失败"
                            }), 500
                    else:
                        return jsonify({
                            'status': 'error',
                            'message': "串口处理器未初始化"
                        }), 500
                else:
                    return jsonify({
                        'status': 'error',
                        'message': f"不支持的调试动作: {action}"
                    }), 400
            except Exception as e:
                # 记录详细错误信息
                logging.exception(f"串口调试出错: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': f"串口调试出错: {str(e)}"
                }), 500
    
    return lamp_bp
