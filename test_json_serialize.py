#!/usr/bin/env python3
"""测试JSON序列化修复是否成功"""
import json
import numpy as np

def test_json_serialization():
    """测试检测位置数据的JSON序列化"""
    # 模拟检测位置数据，包括numpy的float32类型
    original_data = {
        "detected": True,
        "x": np.float32(-0.229),  # 故意使用numpy float32类型
        "y": np.float32(-0.240),  # 故意使用numpy float32类型
        "confidence": np.float32(0.65),
        "fps": np.float32(19.9),
        "width": np.float32(0.2),
        "height": np.float32(0.3)
    }
    
    print("原始数据 (包含numpy类型):")
    for key, value in original_data.items():
        print(f"{key}: {value} (类型: {type(value).__name__})")
    
    # 尝试直接序列化，应该会失败
    print("\n尝试直接序列化原始数据...")
    try:
        json_data = json.dumps(original_data)
        print("意外成功 - 这不应该发生!")
    except TypeError as e:
        print(f"预期的错误: {e}")
    
    # 应用我们的修复 - 转换所有值为Python内置类型
    fixed_data = {
        "detected": bool(original_data["detected"]),
        "x": float(original_data["x"]),
        "y": float(original_data["y"]),
        "confidence": float(original_data["confidence"]),
        "fps": float(original_data["fps"]),
        "width": float(original_data["width"]),
        "height": float(original_data["height"])
    }
    
    print("\n修复后的数据 (Python内置类型):")
    for key, value in fixed_data.items():
        print(f"{key}: {value} (类型: {type(value).__name__})")
    
    # 尝试序列化修复后的数据，应该成功
    print("\n尝试序列化修复后的数据...")
    try:
        json_data = json.dumps(fixed_data)
        print("序列化成功!")
        print(f"JSON数据: {json_data}")
        return True
    except TypeError as e:
        print(f"序列化失败: {e}")
        return False
        
if __name__ == "__main__":
    test_json_serialization()
