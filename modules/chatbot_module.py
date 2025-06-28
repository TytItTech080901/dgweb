import sys
import os
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append(os.path.join(parent_dir, 'Audio'))

# 导入必要的模块
import pyaudio
import dashscope
from dashscope.audio.asr import *
from dashscope.audio.tts_v2 import *
from http import HTTPStatus
import json

# 在文件开头添加串口模块导入
from .serial_module import SerialCommunicationHandler
from config import SERIAL_BAUDRATE


# 修改后的Agent类定义 (直接将声明代码复制过来)
class Agent:
    asr_model = "gummy-chat-v1"  # asr模型名称
    tts_model = "cosyvoice-v1"  # tts模型名称
    tts_voice = "longxiaochun"  # tts语音名称
    assistant_model = "qwen-turbo-2025-04-28"  # 大模型名称

    assistant = None  # 大模型助手
    thread = None  # 线程
    tools = None  # 工具列表

    class TTSCallback(ResultCallback):
        _player = None
        _stream = None

        def on_open(self):
            self._player = pyaudio.PyAudio()
            self._stream = self._player.open(
                format=pyaudio.paInt16, channels=1, rate=22050, output=True
            )

        def on_close(self):
            # stop player
            self._stream.stop_stream()
            self._stream.close()
            self._player.terminate()

        def on_data(self, data: bytes) -> None:
            self._stream.write(data)  # 往音频设备中写入数据,即播放音频

    class ASRCallback(TranslationRecognizerCallback):
        _mic = None
        _stream = None
        asr_result = None

        def on_open(self) -> None:
            self._mic = pyaudio.PyAudio()
            self._stream = self._mic.open(
                format=pyaudio.paInt16, channels=1, rate=16000, input=True
            )

        def on_close(self) -> None:
            self._stream.stop_stream()
            self._stream.close()
            self._mic.terminate()
            self._stream = None
            self._mic = None

        def on_event(
            self,
            request_id,
            transcription_result: TranscriptionResult,
            translation_result: TranslationResult,
            usage,
        ) -> None:
            if transcription_result is not None:
                if transcription_result.is_sentence_end:
                    self.asr_result = transcription_result.text

    def __init__(self, instructions: str, tools_json_path: str):
        # 从json中加载预设tools
        with open(tools_json_path, "r", encoding="utf-8") as tools_file:
            self.tools = json.load(tools_file)

        # 创建助手
        self.assistant = dashscope.Assistants.create(
            model=self.assistant_model,  # 大语言模型名，用于为智能体配置大模型
            name='"瞳灵"台灯智能体',  # 智能体名称，用于区别智能体的名称
            description='"瞳灵"台灯智能体,用于进行语音交互',  # 智能体的功能描述
            instructions=instructions,  # 由自然语言构成的指令，用于定义智能体的角色和任务
            tools=self.tools,  # 为智能体配置的工具列表
        )
        # 检测助手创建是否成功
        if not self.__check_status(self.assistant, "助手创建"):
            exit()
        # 创建助手的线程
        self.thread = dashscope.Threads.create()
        # 检测线程创建是否成功
        if not self.__check_status(self.thread, "线程创建"):
            exit()

    def __check_status(self, component, operation):
        if component.status_code == HTTPStatus.OK:
            print(f"{operation} 成功。")
            return True
        else:
            print(
                f"{operation} 失败。状态码：{component.status_code}，错误码：{component.code}，错误信息：{component.message}"
            )
            return False

    def get_message(self):
        # 创建语音识别回调函数
        asr_callback = self.ASRCallback()
        # 创建语音识别模型对象
        translator = TranslationRecognizerChat(
            model="gummy-chat-v1",
            format="pcm",
            sample_rate=16000,
            transcription_enabled=True,
            callback=asr_callback,
            max_end_silence=1000,  # 设置最大结束静音时长,单位为毫秒(ms),若语音结束后静音时长超过该预设值,系统将判定当前语句已结束
        )
        translator.start()
        message = ""
        while True:
            if asr_callback._stream:
                data = asr_callback._stream.read(3200, exception_on_overflow=False)
                if not translator.send_audio_frame(data):
                    message = asr_callback.asr_result
                    break
            else:
                break
        translator.stop()
        return message

    def send_message(self, messages: str):
        if messages == "":
            return
        # 向线程发送消息
        message = dashscope.Messages.create(self.thread.id, content=messages)
        # 检测消息创建是否成功
        if not self.__check_status(message, "消息创建"):
            exit()

        # 向助手发送消息
        run = dashscope.Runs.create(
            self.thread.id, assistant_id=self.assistant.id, stream=True  # 开启流式输出
        )

        # 创建tts合成器并启动
        tts_callback = self.TTSCallback()
        synthesizer = SpeechSynthesizer(
            model=self.tts_model,
            voice=self.tts_voice,
            format=AudioFormat.PCM_22050HZ_MONO_16BIT,
            callback=tts_callback,
        )
        
        # 启动语音合成器
        try:
            synthesizer.start()
        except Exception as e:
            print(f"启动语音合成器失败: {e}")
            # 如果TTS启动失败，仍然继续处理，只是不播放语音
            synthesizer = None

        while True:  # 添加外层循环
            for event, data in run:  # 事件流和事件数据的详细信息
                if event == "thread.run.requires_action":  # Assistant 调用了工具，正在等待函数输出
                    tool_outputs = []  # 提交输出的方法与第五步类似
                    for tool in data.required_action.submit_tool_outputs.tool_calls:
                        name = tool.function.name
                        args = json.loads(tool.function.arguments)
                        output = tools_map[name](**args)
                        tool_outputs.append(
                            {
                                "tool_call_id": tool.id,
                                "output": output,
                            }
                        )
                    run = dashscope.Runs.submit_tool_outputs(  # 提交函数输出
                        thread_id=self.thread.id,
                        run_id=data.id,
                        tool_outputs=tool_outputs,
                        stream=True,  # 此处也需要开启流式输出
                    )
                    break  # 跳出当前的 for 循环，下一次循环将轮询新的 Runs 对象。
                elif event == "thread.message.delta":
                    print(data.delta.content.text.value, end="", flush=True)
                    # 只有在synthesizer可用时才进行语音合成
                    if synthesizer:
                        try:
                            synthesizer.streaming_call(data.delta.content.text.value)
                        except Exception as e:
                            print(f"语音合成出错: {e}")
            else:
                break  # 如果首轮 for 循环正常结束（没有触发函数调用），就直接退出 while 循环

        # 完成语音合成
        if synthesizer:
            try:
                synthesizer.streaming_complete()
            except Exception as e:
                print(f"完成语音合成时出错: {e}")
        messages = dashscope.Messages.list(self.thread.id)
        if self.__check_status(messages, "消息检索"):
            if messages.data:
                # 显示最后一条消息的内容（助手的响应）
                last_message = messages.data[0]
                return last_message["content"][0]["text"]["value"]
                
    def reset(self):
        # 创建助手的线程
        self.thread = dashscope.Threads.create()
        # 检测线程创建是否成功
        if not self.__check_status(self.thread, "线程创建"):
            exit()
            
    def speak_text(self, text):
        """仅使用TTS朗读指定文本，不进行对话"""
        if not text:
            return False
            
        # 创建tts合成器
        tts_callback = self.TTSCallback()
        synthesizer = SpeechSynthesizer(
            model=self.tts_model,
            voice=self.tts_voice,
            format=AudioFormat.PCM_22050HZ_MONO_16BIT,
            callback=tts_callback,
        )
        
        try:
            # 启动语音合成器
            synthesizer.start()
            # 执行语音合成
            synthesizer.streaming_call(text)
            synthesizer.streaming_complete()
            return True
        except Exception as e:
            print(f"语音合成出错: {e}")
            return False

class ChatbotService:
    """语音助手服务，用于语音交互"""

    def __init__(self):
        try:
            with open("Audio/config.json", "r", encoding="utf-8") as config_file:
                self.config = json.load(config_file)
        except FileNotFoundError:
            # 尝试使用绝对路径
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            with open(os.path.join(base_path, "Audio/config.json"), "r", encoding="utf-8") as config_file:
                self.config = json.load(config_file)
                
        self.instructions = self.config["instructions"]
        dashscope.api_key = self.config["api_key"]
        
        # 构建绝对路径
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tools_path = os.path.join(base_path, "Audio/tools.json")
        
        # 初始化串口处理器
        try:
            self.serial_handler = SerialCommunicationHandler(baudrate=SERIAL_BAUDRATE)
            self.serial_available = (self.serial_handler is not None and 
                                   hasattr(self.serial_handler, 'initialized') and 
                                   self.serial_handler.initialized)
            print(f"串口通信初始化: {'成功' if self.serial_available else '失败'}")
        except Exception as e:
            print(f"串口通信初始化失败: {str(e)}")
            self.serial_handler = None
            self.serial_available = False
        
        self.my_agent = Agent(
            instructions=self.instructions,
            tools_json_path=tools_path,
        )

        # 关键词模型路径 - 使用绝对路径
        self.kws_models = [
            os.path.join(base_path, "Snowboy/resources/models/snowboy.umdl"),
            os.path.join(base_path, "Snowboy/resources/models/computer.umdl"),
        ]

    def initialize(self):
        """初始化语音助手"""
        print("语音助手初始化完成")
        return True

    def send_message(self, message):
        """发送消息并获取响应"""
        if not message:
            return "请提供有效的消息内容。"
        
        response = self.my_agent.send_message(message)
        if response:
            print(f"==>助手响应：{response}<==")
        else:
            print("==>助手未能生成响应<==")
        return response

    def chat_loop(self):
        """执行一轮语音交互"""
        sentence = self.my_agent.get_message()
        print(f"==>识别结果：{sentence}<==")
        response = self.my_agent.send_message(sentence)
        return response
        
    def reset(self):
        """重置对话上下文"""
        self.my_agent.reset()
        return True
        
    def speak_text(self, text):
        """朗读指定文本，无需进行对话"""
        return self.my_agent.speak_text(text)


# 全局变量用于存储聊天机器人实例
_chatbot_instance = None

def get_chatbot_instance():
    """获取聊天机器人实例"""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = ChatbotService()
    return _chatbot_instance

# 修改后的工具函数，支持串口通信
def light_on():
    """打开灯光"""
    print("==>打开灯光<==")
    chatbot = get_chatbot_instance()
    
    if chatbot.serial_available:
        try:
            # 使用serial_module中的send_command方法
            response, message = chatbot.serial_handler.send_command({
                'light_on': True
            })
            print(f"串口命令结果: {message}")
            return message
        except Exception as e:
            print(f"发送开灯命令时出错: {str(e)}")
            return "开灯命令执行出错，请检查串口连接"
    else:
        print("串口不可用，仅执行模拟开灯操作")
        return "串口不可用，已执行模拟开灯操作"

def light_off():
    """关闭灯光"""
    print("==>关闭灯光<==")
    chatbot = get_chatbot_instance()
    
    if chatbot.serial_available:
        try:
            # 使用serial_module中的send_command方法
            response, message = chatbot.serial_handler.send_command({
                'light_off': True
            })
            print(f"串口命令结果: {message}")
            return message
        except Exception as e:
            print(f"发送关灯命令时出错: {str(e)}")
            return "关灯命令执行出错，请检查串口连接"
    else:
        print("串口不可用，仅执行模拟关灯操作")
        return "串口不可用，已执行模拟关灯操作"

def light_brighter():
    """调高灯光亮度"""
    print("==>调高灯光亮度<==")
    chatbot = get_chatbot_instance()
    
    if chatbot.serial_available:
        try:
            # 使用serial_module中的send_command方法
            response, message = chatbot.serial_handler.send_command({
                'brightness_up': True
            })
            print(f"串口命令结果: {message}")
            return message
        except Exception as e:
            print(f"发送调高亮度命令时出错: {str(e)}")
            return "调高亮度命令执行出错，请检查串口连接"
    else:
        print("串口不可用，仅执行模拟调高亮度操作")
        return "串口不可用，已执行模拟调高亮度操作"

def light_dimmer():
    """调低灯光亮度"""
    print("==>调低灯光亮度<==")
    chatbot = get_chatbot_instance()
    
    if chatbot.serial_available:
        try:
            # 使用serial_module中的send_command方法
            response, message = chatbot.serial_handler.send_command({
                'brightness_down': True
            })
            print(f"串口命令结果: {message}")
            return message
        except Exception as e:
            print(f"发送调低亮度命令时出错: {str(e)}")
            return "调低亮度命令执行出错，请检查串口连接"
    else:
        print("串口不可用，仅执行模拟调低亮度操作")
        return "串口不可用，已执行模拟调低亮度操作"

def color_temperature_up():
    """提升光照色温"""
    print("==>提升光照色温<==")
    chatbot = get_chatbot_instance()
    
    if chatbot.serial_available:
        try:
            # 目前serial_module中没有色温控制，使用通用数据发送
            response, message = chatbot.serial_handler.send_data("COLOR_TEMP_UP")
            print(f"串口命令结果: {message}")
            return message if message else "已发送提升色温命令"
        except Exception as e:
            print(f"发送提升色温命令时出错: {str(e)}")
            return "提升色温命令执行出错，请检查串口连接"
    else:
        print("串口不可用，仅执行模拟提升色温操作")
        return "串口不可用，已执行模拟提升色温操作"

def color_temperature_down():
    """降低光照色温"""
    print("==>降低光照色温<==")
    chatbot = get_chatbot_instance()
    
    if chatbot.serial_available:
        try:
            # 目前serial_module中没有色温控制，使用通用数据发送
            response, message = chatbot.serial_handler.send_data("COLOR_TEMP_DOWN")
            print(f"串口命令结果: {message}")
            return message if message else "已发送降低色温命令"
        except Exception as e:
            print(f"发送降低色温命令时出错: {str(e)}")
            return "降低色温命令执行出错，请检查串口连接"
    else:
        print("串口不可用，仅执行模拟降低色温操作")
        return "串口不可用，已执行模拟降低色温操作"

def posture_reminder():
    """进行坐姿提醒"""
    print("==>进行坐姿提醒<==")
    chatbot = get_chatbot_instance()
    
    if chatbot.serial_available:
        try:
            # 使用serial_module中的send_command方法
            response, message = chatbot.serial_handler.send_command({
                'posture_reminder': True
            })
            print(f"串口命令结果: {message}")
            return message
        except Exception as e:
            print(f"发送坐姿提醒命令时出错: {str(e)}")
            return "坐姿提醒命令执行出错，请检查串口连接"
    else:
        print("串口不可用，仅执行模拟坐姿提醒操作")
        return "串口不可用，已执行模拟坐姿提醒操作"

def vision_reminder():
    """进行远眺提醒"""
    print("==>进行远眺提醒<==")
    chatbot = get_chatbot_instance()
    
    if chatbot.serial_available:
        try:
            # 使用serial_module中的send_command方法
            response, message = chatbot.serial_handler.send_command({
                'eye_rest_reminder': True
            })
            print(f"串口命令结果: {message}")
            return message
        except Exception as e:
            print(f"发送远眺提醒命令时出错: {str(e)}")
            return "远眺提醒命令执行出错，请检查串口连接"
    else:
        print("串口不可用，仅执行模拟远眺提醒操作")
        return "串口不可用，已执行模拟远眺提醒操作"

# 更新工具函数映射
tools_map = {
    "light_on": light_on,
    "light_off": light_off,
    "light_brighter": light_brighter,
    "light_dimmer": light_dimmer,
    "color_temperature_up": color_temperature_up,
    "color_temperature_down": color_temperature_down,
    "posture_reminder": posture_reminder,
    "vision_reminder": vision_reminder,
}


def main():
    chatbot = ChatbotService()
    chatbot.initialize()
    
    # # 朗读开场白
    # chatbot.speak_text("小可爱，你好！我是瞳灵智能台灯，我能开关灯光、调节亮度，让房间变亮或者变暗哦！还能控制机械臂把光照到你需要的地方呢，有什么需要就告诉我吧！")
    # time.sleep(2)

    # 随机生成的开场白
    msg = "你好，请简要介绍一下自己的功能，不要举例。"
    chatbot.send_message(msg)
    time.sleep(2)

    # 进入正常对话循环
    while True:
        chatbot.chat_loop()

if __name__ == "__main__":
    main()