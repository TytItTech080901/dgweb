import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 现在可以导入Audio模块了
from Audio.voice_assistant import Agent
import dashscope
from dashscope.audio.asr import *
from dashscope.audio.tts_v2 import *
from http import HTTPStatus
import json

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

    def chat_loop(self):
        sentence = self.my_agent.get_message()
        print(f"==>识别结果：{sentence}<==")
        self.my_agent.send_message(sentence)

def main():
    service = ChatbotService()
    service.initialize()
    while True:
        service.chat_loop()

if __name__ == "__main__":
    main()