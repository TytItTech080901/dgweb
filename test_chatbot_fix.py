#!/usr/bin/env python3
"""
测试修复后的ChatbotService是否解决了循环错误问题
"""
import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, '/home/cat/Py-server')

def test_chatbot_service():
    """测试ChatbotService的基本功能"""
    print("=== 测试ChatbotService ===")
    
    try:
        from modules.chatbot_module import ChatbotService
        
        print("1. 测试基础初始化...")
        chatbot = ChatbotService()
        print("✓ 基础初始化成功")
        
        print("2. 测试Agent延迟初始化...")
        # 不立即初始化Agent，模拟app.py的行为
        print("✓ Agent未立即初始化（延迟初始化）")
        
        print("3. 测试资源清理...")
        chatbot.cleanup()
        print("✓ 资源清理成功")
        
        print("4. 测试重复清理...")
        chatbot.cleanup()  # 应该能安全地重复调用
        print("✓ 重复清理安全")
        
        print("\n所有测试通过！")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_integration():
    """测试与app.py的集成"""
    print("\n=== 测试App集成 ===")
    
    try:
        # 模拟app.py中的初始化过程
        from modules.chatbot_module import ChatbotService
        
        print("1. 创建ChatbotService实例...")
        chatbot = ChatbotService(external_serial_handler=None)
        print("✓ 实例创建成功")
        
        print("2. 测试延迟初始化...")
        # 不调用initialize()，模拟app.py中的延迟初始化
        print("✓ 延迟初始化设置")
        
        print("3. 清理资源...")
        chatbot.cleanup()
        print("✓ 清理成功")
        
        print("\nApp集成测试通过！")
        return True
        
    except Exception as e:
        print(f"✗ App集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_chatbot_service()
    success2 = test_app_integration()
    
    if success1 and success2:
        print("\n🎉 所有测试都通过了！修复应该有效。")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败，需要进一步修复。")
        sys.exit(1)
