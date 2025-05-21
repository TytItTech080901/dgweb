#!/usr/bin/env python3
"""测试检测位置API"""
import requests
import json
import time

def test_detection_position_api():
    """测试 /api/detection/position API 端点"""
    print("测试/api/detection/position API端点...")
    url = "http://localhost:5002/api/detection/position"
    
    # 尝试获取检测位置数据
    try:
        response = requests.get(url)
        
        # 检查HTTP状态码
        if response.status_code == 200:
            print(f"API请求成功: 状态码 {response.status_code}")
            data = response.json()
            print(f"API响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"API请求失败: 状态码 {response.status_code}")
            print(f"错误响应: {response.text}")
            return False
    except Exception as e:
        print(f"API请求出错: {str(e)}")
        return False

if __name__ == "__main__":
    # 等待服务器启动
    print("等待5秒让服务器完全启动...")
    time.sleep(5)
    test_detection_position_api()
