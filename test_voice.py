#!/usr/bin/env python3
"""
测试语音系统是否正常工作
"""
import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

print("=== 测试语音系统 ===")

# 首先检查基本依赖
print("1. 检查基本依赖...")
try:
    import pyaudio
    print("✅ pyaudio 可用")
except ImportError as e:
    print(f"❌ pyaudio 不可用: {e}")

try:
    import dashscope
    print("✅ dashscope 可用")
except ImportError as e:
    print(f"❌ dashscope 不可用: {e}")

# 检查配置文件
print("\n2. 检查配置文件...")
config_path = os.path.join(current_dir, "Audio", "config.json")
if os.path.exists(config_path):
    print(f"✅ 配置文件存在: {config_path}")
    try:
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✅ 配置文件读取成功，API Key: {config.get('api_key', 'N/A')[:10]}...")
    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
else:
    print(f"❌ 配置文件不存在: {config_path}")

# 测试模块导入
print("\n3. 测试模块导入...")
try:
    from modules.chatbot_module import get_chatbot_instance
    print("✅ chatbot_module 导入成功")
    
    print("4. 初始化语音助手...")
    chatbot = get_chatbot_instance()
    
    if chatbot:
        print("✅ 语音助手初始化成功")
        
        print("5. 测试语音合成...")
        test_text = "这是一个测试消息"
        result = chatbot.speak_text(test_text)
        
        if result:
            print("✅ 语音合成测试成功")
        else:
            print("❌ 语音合成测试失败")
    else:
        print("❌ 语音助手初始化失败，返回None")
        
except ImportError as e:
    print(f"❌ 模块导入失败: {str(e)}")
    
except Exception as e:
    print(f"❌ 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n=== 测试完成 ===")
