# 控制命令帧 (Command Frame) 文档

## 概述

为控制和监测设备功能，我们在现有的串行通信协议中添加了新的帧类型：
- 命令帧 (0xA3)：用于发送控制指令
- 响应帧 (0xB3)：设备返回的命令执行状态

这些帧可以控制灯光（开/关/亮度调节）和发送提醒（姿势/眼睛休息）。

## 帧格式

### 命令帧 (0xA3)

| 字节位置 | 数据类型 | 说明 |
|---------|---------|------|
| 0       | char    | 帧头，固定为's' |
| 1       | char    | 消息类型，固定为0xA3 |
| 2       | char    | 开灯控制位 (1=开灯, 0=无操作) |
| 3       | char    | 关灯控制位 (1=关灯, 0=无操作) |
| 4       | char    | 增加亮度控制位 (1=增加, 0=无操作) |
| 5       | char    | 减少亮度控制位 (1=减少, 0=无操作) |
| 6       | char    | 姿势提醒控制位 (1=发送提醒, 0=无操作) |
| 7       | char    | 眼睛休息提醒控制位 (1=发送提醒, 0=无操作) |
| 8-30    | char    | 保留位 (全为0) |
| 31      | char    | 帧尾，固定为'e' |

### 响应帧 (0xB3)

| 字节位置 | 数据类型 | 说明 |
|---------|---------|------|
| 0       | char    | 帧头，固定为's' |
| 1       | char    | 消息类型，固定为0xB3 |
| 2       | char    | 开灯命令确认 (1=已执行, 0=未执行) |
| 3       | char    | 关灯命令确认 (1=已执行, 0=未执行) |
| 4       | char    | 增加亮度命令确认 (1=已执行, 0=未执行) |
| 5       | char    | 减少亮度命令确认 (1=已执行, 0=未执行) |
| 6       | char    | 姿势提醒命令确认 (1=已执行, 0=未执行) |
| 7       | char    | 眼睛休息提醒命令确认 (1=已执行, 0=未执行) |
| 8-30    | char    | 保留位 (全为0) |
| 31      | char    | 帧尾，固定为'e' |

## 使用方法

### SerialHandler 类 (低级接口)

```python
# 导入类
from serial_handler import SerialHandler

# 创建实例
handler = SerialHandler()

# 发送单个命令
response = handler.send_command(light_on=True)
response = handler.send_command(light_off=True)
response = handler.send_command(brightness_up=True)
response = handler.send_command(brightness_down=True)
response = handler.send_command(posture_reminder=True)
response = handler.send_command(eye_rest_reminder=True)

# 发送多个命令
response = handler.send_command(light_on=True, brightness_up=True)

# 检查响应
if response:
    if response.get('light_on_ack'):
        print("开灯命令已执行")
```

### SerialCommunicationHandler 类 (高级接口)

```python
# 导入类
from modules.serial_module import SerialCommunicationHandler

# 创建实例
handler = SerialCommunicationHandler()

# 发送单个命令
response, message = handler.send_command({'light_on': True})
response, message = handler.send_command({'light_off': True})
response, message = handler.send_command({'brightness_up': True})
response, message = handler.send_command({'brightness_down': True})
response, message = handler.send_command({'posture_reminder': True})
response, message = handler.send_command({'eye_rest_reminder': True})

# 发送多个命令
response, message = handler.send_command({
    'light_on': True,
    'brightness_up': True
})

# 输出消息
print(message)  # 例如: "命令(开灯、增加亮度)发送成功，成功执行：开灯、增加亮度"
```

## 测试

使用提供的测试脚本测试功能:

```bash
python command_test.py
```

或者：

```bash
./command_test.py
```
