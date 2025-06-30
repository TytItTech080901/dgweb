# 瞳灵智能台灯系统 | Tongling Smart Lamp System

一个集成了智能台灯控制、坐姿监测、用眼健康管理、串口通信和AI语音交互的综合性Web系统。

An integrated web system featuring smart lamp control, posture monitoring, eye healt# 开放端口配置 | Server Configuration  
OPEN_HOST = '0.0.0.0'
OPEN_PORT = 5002  # 默认端口5002，避免冲突anagement, serial communication, and AI voice interaction.

## 🎯 核心功能 | Core Features

### 🔊 AI语音助手 | AI Voice Assistant
- **智能对话系统** | Intelligent conversation system
  - 基于通义千问大语言模型 | Based on Qwen LLM
  - 儿童友好的交互方式 | Child-friendly interaction
  - 多轮对话上下文保持 | Multi-turn conversation context
- **语音识别与合成** | Speech recognition and synthesis
  - 实时语音识别(ASR) | Real-time Automatic Speech Recognition
  - 高质量语音合成(TTS) | High-quality Text-to-Speech
  - 自适应采样率支持 | Adaptive sample rate support
- **台灯智能控制** | Smart lamp control
  - 自然语言命令解析 | Natural language command parsing
  - 亮度和色温智能调节 | Intelligent brightness and color temperature adjustment
  - 语音反馈确认 | Voice feedback confirmation
- **音频设备适配** | Audio device adaptation
  - 多采样率自动检测 | Multi-sample rate auto-detection
  - PyAudio兼容性优化 | PyAudio compatibility optimization
  - 设备状态实时监控 | Real-time device status monitoring

### 👨‍👩‍👧‍👦 家长监护系统 | Parental Guardian System
- **定时留言功能** | Scheduled messaging
  - 支持立即发送和定时发送 | Support immediate and scheduled sending
  - 智能状态管理（pending/sent/failed）| Intelligent status management
  - 实际发送时间记录 | Actual sending time recording
- **语音朗读留言** | Voice message playback
  - 自动TTS语音合成 | Automatic TTS voice synthesis
  - 多采样率音频适配 | Multi-sample rate audio adaptation
  - 智能音频设备检测 | Intelligent audio device detection
- **留言状态跟踪** | Message status tracking
  - 实时状态更新 | Real-time status updates
  - 历史记录查询 | Historical record queries
  - 发送失败重试机制 | Retry mechanism for failed sends
- **远程关怀功能** | Remote care features
  - 实时视频监控 | Real-time video monitoring
  - 家长留言管理界面 | Parental message management interface
  - 儿童使用情况报告 | Children usage reports

### 💡 智能台灯控制 | Smart Lamp Control
- 台灯开关控制 | Lamp on/off control
- 亮度调节 | Brightness adjustment
- 色温调节 | Color temperature adjustment
- 串口协议通信 | Serial protocol communication
- 实时状态反馈 | Real-time status feedback

### 👁️ 坐姿与用眼监测 | Posture & Eye Health Monitoring
- 实时坐姿检测 | Real-time posture detection
- 用眼习惯分析 | Eye usage pattern analysis
- 健康提醒系统 | Health reminder system
- 数据统计与报告 | Data statistics and reports
- PDF报告导出 | PDF report export

### 🔌 串口通信系统 | Serial Communication System
- 自动设备检测 | Automatic device detection
- 新协议支持 | New protocol support
- 实时数据监控 | Real-time data monitoring
- 协议调试界面 | Protocol debugging interface
- 历史数据管理 | Historical data management

### 📱 Web管理界面 | Web Management Interface
- 响应式设计 | Responsive design
- 实时数据推送 | Real-time data streaming
- 多模块集成 | Multi-module integration
- 调试工具集成 | Debug tools integration

## 🏗️ 系统架构 | System Architecture

### 📁 项目结构 | Project Structure
```
Py-server/
├── app.py                 # 主应用入口 | Main application entry
├── config.py             # 系统配置 | System configuration
├── routes.py             # 主路由模块 | Main routing module
├── serial_handler.py     # 串口处理器 | Serial handler
├── db_handler.py         # 数据库处理器 | Database handler
├── guardian_scheduler.py # 家长监护定时处理器 | Guardian scheduler
├── test_voice.py         # 语音系统测试 | Voice system test
├── detect_audio.sh       # 音频设备检测脚本 | Audio device detection
├── modules/              # 功能模块 | Function modules
│   ├── chatbot_module.py     # AI语音助手 | AI voice assistant
│   ├── serial_module.py      # 串口通信 | Serial communication
│   ├── posture_module.py     # 坐姿监测 | Posture monitoring
│   ├── detection_module.py   # 目标检测 | Object detection
│   ├── database_module.py    # 数据库操作 | Database operations
│   ├── video_stream_module.py # 视频流处理 | Video stream processing
│   └── routes.py            # 模块路由 | Module routes
├── templates/            # 网页模板 | Web templates
│   ├── main.html             # 主页面 | Main page
│   ├── debug.html            # 调试页面 | Debug page
│   ├── protocol_debug.html   # 协议调试 | Protocol debug
│   └── detection.html        # 检测页面 | Detection page
├── static/               # 静态资源 | Static resources
├── Audio/                # 语音模块 | Audio module
│   ├── config.json           # 语音配置 | Voice configuration
│   ├── tools.json            # 工具配置 | Tools configuration
│   └── voice_assistant.py    # 语音助手 | Voice assistant
├── Yolo/                 # 目标检测模型 | Object detection models
└── docs/                 # 文档 | Documentation
    ├── serial_comm.md        # 串口协议文档 | Serial protocol docs
    └── command_frame.md      # 命令帧文档 | Command frame docs
```

### 🔄 数据流 | Data Flow
```
用户语音 → 语音识别 → AI对话 → 命令解析 → 串口发送 → 台灯控制
Camera → 姿态检测 → 数据分析 → 健康提醒 → 报告生成
串口设备 ↔ 协议解析 ↔ 数据库存储 ↔ Web界面显示
家长留言 → 定时调度 → 语音合成 → 音频播放 → 状态更新
视频流 → 处理优化 → 实时传输 → 家长监护 → 远程关怀
```

## 🚀 快速开始 | Quick Start

### 1. 环境准备 | Environment Setup

```bash
# 克隆项目 | Clone the project
git clone <repository-url>
cd Py-server

# 创建conda环境 | Create conda environment
conda env create -f environment.yml
conda activate pyserver

# 或使用pip | Or using pip
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 安装语音相关依赖 | Install voice-related dependencies
pip install dashscope pyaudio

# 安装RKNN工具包（如果需要）| Install RKNN toolkit (if needed)
pip install rknn_toolkit_lite2-2.3.2-cp39-cp39-manylinux_2_17_aarch64.manylinux2014_aarch64.whl
```

### 2. 配置系统 | System Configuration

#### 数据库配置 | Database Configuration
```sql
-- 创建数据库和用户 | Create database and user
CREATE DATABASE serial_data;
CREATE USER 'serial_user'@'localhost' IDENTIFIED BY 'Serial123!';
GRANT ALL PRIVILEGES ON serial_data.* TO 'serial_user'@'localhost';
FLUSH PRIVILEGES;
```

#### 语音助手配置 | Voice Assistant Configuration
在 `Audio/config.json` 中配置API密钥：
Configure API key in `Audio/config.json`:
```json
{
    "api_key": "your_dashscope_api_key",
    "instructions": "你是瞳灵智能台灯的语音助手..."
}
```

#### 音频设备配置 | Audio Device Configuration
检测音频设备支持的采样率：
Check audio device supported sample rates:
```bash
# 运行音频设备检测脚本 | Run audio device detection script
./detect_audio.sh

# 或手动检测 | Or manually detect
arecord -l  # 列出录音设备 | List recording devices
aplay -l   # 列出播放设备 | List playback devices

# 测试语音系统 | Test voice system
python test_voice.py
```

#### 家长监护配置 | Guardian System Configuration
系统会自动创建以下数据库表：
The system will automatically create the following database tables:
- `guardian_messages`: 存储家长留言 | Store parental messages
- `serial_history`: 存储串口通信历史 | Store serial communication history
- `posture_records`: 存储坐姿记录 | Store posture records

#### 系统配置 | System Configuration
编辑 `config.py` 根据需要调整设置：
Edit `config.py` to adjust settings as needed:
```python
# 串口配置 | Serial Configuration
SERIAL_BAUDRATE = 115200

# 功能开关 | Feature Switches
ENABLE_CHATBOT = True
ENABLE_WELCOME_MESSAGE = False
DEBUG_BUTTON_VISIBLE = True

# 服务器配置 | Server Configuration
OPEN_HOST = '0.0.0.0'
OPEN_PORT = 5000
```

### 3. 启动应用 | Launch Application

```bash
# 启动主应用 | Start main application
python app.py

# 访问系统 | Access system
# 浏览器打开 | Open in browser: http://localhost:5002
```

### 4. 功能验证 | Feature Verification

1. **语音助手测试** | Voice Assistant Test
   - 主页面点击"开始语音交互" | Click "Start Voice Interaction" on main page
   - 说话测试语音识别和合成 | Speak to test voice recognition and synthesis
   - 运行测试脚本：`python test_voice.py` | Run test script: `python test_voice.py`

2. **台灯控制测试** | Lamp Control Test
   - 连接STM串口设备 | Connect STM serial device
   - 使用语音命令："打开台灯" | Voice command: "Turn on the lamp"

3. **坐姿监测测试** | Posture Monitoring Test
   - 确保摄像头正常工作 | Ensure camera is working
   - 查看实时姿态检测结果 | View real-time posture detection results

4. **家长监护测试** | Guardian System Test
   - 在主页面填写家长留言 | Fill in parental message on main page
   - 测试立即发送和定时发送功能 | Test immediate and scheduled sending
   - 验证语音朗读功能 | Verify voice reading functionality
   - 查看留言历史和状态 | Check message history and status

5. **音频设备测试** | Audio Device Test
   ```bash
   # 一键检测音频设备和采样率 | One-click audio device and sample rate detection
   ./detect_audio.sh
   
   # 手动检测录音设备 | Manual recording device detection
   arecord -l
   
   # 手动检测播放设备 | Manual playback device detection  
   aplay -l
   
   # 测试特定采样率 | Test specific sample rate
   arecord -f S16_LE -c 1 -r 16000 -d 1 test.wav
   aplay test.wav
   
   # 综合语音系统测试 | Comprehensive voice system test
   python test_voice.py
   ```
   
   **测试输出示例** | Test Output Example:
   ```
   === 检测音频设备信息 ===
   1. 录音设备列表:
   card 1: USB [USB Audio], device 0: USB Audio [USB Audio]
   
   2. 播放设备列表:
   card 0: PCH [HDA Intel PCH], device 0: ALC287 Analog [ALC287 Analog]
   
   3. 测试常用采样率支持情况:
   测试采样率 16000Hz: 录音✅ 播放✅
   测试采样率 44100Hz: 录音✅ 播放✅
   ```

## 📖 使用指南 | User Guide

### 🎙️ AI语音交互 | AI Voice Interaction

1. **启动语音助手** | Start Voice Assistant
   - 点击主页面"开始语音交互"按钮 | Click "Start Voice Interaction" button
   - 系统会进行初始化并播放欢迎语音 | System will initialize and play welcome message

2. **语音命令示例** | Voice Command Examples
   ```
   "打开台灯" / "Turn on the lamp"
   "关闭台灯" / "Turn off the lamp"
   "调亮一点" / "Make it brighter"
   "调暗一点" / "Make it dimmer"
   "调高色温" / "Increase color temperature"
   "降低色温" / "Decrease color temperature"
   ```

3. **对话管理** | Conversation Management
   - 点击"重置对话"清空上下文 | Click "Reset Conversation" to clear context
   - 支持多轮对话和上下文理解 | Supports multi-turn conversations and context understanding

### 💡 台灯控制面板 | Lamp Control Panel

1. **手动控制** | Manual Control
   - 使用网页按钮直接控制台灯 | Use web buttons to directly control lamp
   - 实时查看台灯状态反馈 | View real-time lamp status feedback

2. **状态监控** | Status Monitoring
   - 查看当前亮度和色温数值 | View current brightness and color temperature values
   - 监控串口连接状态 | Monitor serial connection status

### 👁️ 健康监测系统 | Health Monitoring System

1. **坐姿监测** | Posture Monitoring
   - 自动检测坐姿状态 | Automatically detect posture status
   - 提供实时纠正建议 | Provide real-time correction suggestions
   - 生成每日坐姿报告 | Generate daily posture reports

2. **用眼健康** | Eye Health
   - 监测用眼时长 | Monitor eye usage duration
   - 智能休息提醒 | Intelligent rest reminders
   - 导出PDF健康报告 | Export PDF health reports

### �‍👩‍👧‍👦 家长监护功能 | Guardian Features

1. **发送定时留言** | Send Scheduled Messages
   ```
   1. 在主页面找到"家长留言"区域
   2. 填写留言内容
   3. 选择发送时间（立即发送或指定时间）
   4. 点击"发送留言"按钮
   5. 系统会显示留言状态和发送时间
   ```

2. **留言状态说明** | Message Status Description
   - **pending**: 定时待发 - 等待指定时间发送
   - **sent**: 已发送 - 显示实际发送的时间
   - **failed**: 发送失败 - 需要重新发送

3. **语音朗读功能** | Voice Reading Feature
   - 留言发送时自动进行语音朗读
   - 支持多种采样率自适应
   - 兼容不同音频设备
   - 朗读完成后记录发送时间

4. **留言历史管理** | Message History Management
   - 查看所有历史留言
   - 按时间排序显示
   - 支持留言状态筛选
   - 可重新发送失败的留言

### 🔧 调试与开发 | Debug & Development

1. **协议调试界面** | Protocol Debug Interface
   - 访问 `/protocol_debug` 进入协议调试 | Access `/protocol_debug` for protocol debugging
   - 支持标准协议、新协议和原始数据发送 | Support standard protocol, new protocol, and raw data sending
   - 实时监控串口数据收发 | Real-time monitoring of serial data transmission

2. **系统调试** | System Debug
   - 访问 `/debug` 查看系统状态 | Access `/debug` to view system status
   - 查看各模块运行状态和日志 | View module running status and logs
   - 测试各功能模块连接性 | Test connectivity of function modules

## 📡 串口协议说明 | Serial Protocol Documentation

### 🔄 新协议格式 | New Protocol Format (推荐使用 | Recommended)

**帧结构 | Frame Structure (32字节 | 32 bytes)**
```
字节位置 | 内容              | 说明
0       | 0x73 ('s')       | 帧头 | Frame header
1       | 数据类型          | 0xA0: 上位机→下位机 | Host→Device
        |                  | 0xB0: 下位机→上位机 | Device→Host
2       | 命令字            | 具体命令 | Specific command
3-30    | 数据域 (28字节)   | 8个uint32数据 | 8 uint32 data
31      | 0x65 ('e')       | 帧尾 | Frame tail
```

**命令字定义 | Command Definitions**
```
0x00: 开机 | Power on
0x01: 关机 | Power off  
0x02: 复位 | Reset
0x10: 提高光照亮度 | Increase brightness
0x11: 降低光照亮度 | Decrease brightness
0x12: 提升光照色温 | Increase color temperature
0x13: 降低光照色温 | Decrease color temperature
0x14: 开灯 | Turn on light
0x15: 关灯 | Turn off light
0x20: 坐姿提醒 | Posture reminder
0x21: 远眺提醒 | Vision reminder
```

**数据域说明 | Data Field Description**
```
设备状态上报 (命令字0xFF):
data[0]: 设备电源状态 (0/1)
data[1]: 灯光开关状态 (0/1)  
data[2]: 光照亮度 (0-1000)
data[3]: 光照色温 (3000-6500K)
data[4-7]: 保留字段
```

### 🔧 协议调试工具 | Protocol Debug Tools

1. **Web调试界面** | Web Debug Interface
   ```
   访问地址: http://localhost:5002/protocol_debug
   功能: 发送/接收协议帧，实时监控数据
   ```

2. **命令行调试** | Command Line Debug
   ```bash
   # 使用Python直接测试串口
   python -c "
   from serial_handler import SerialHandler
   handler = SerialHandler()
   handler.send_command(0x14, [0]*8)  # 发送开灯命令
   "
   ```

## 项目结构 | Project Structure

- `server.py`: 主服务器程序 | Main server program
- `serial_handler.py`: 串口通信处理类 | Serial communication handler class
- `config.py`: 配置文件 | Configuration file
- `test_db.py`: 数据库连接测试 | Database connection test
- `requirements.txt`: Python 依赖包列表 | Python dependencies list
- `environment.yml`: Conda 环境配置 | Conda environment configuration
- `templates/`: HTML 模板文件 | HTML template files
  - `index.html`: 主页面模板 | Main page template

## 配置选项 | Configuration Options

在 `config.py` 中可以配置以下选项：
The following options can be configured in `config.py`:

- 串口设置 | Serial Port Settings
  - `SERIAL_PORTS`: 可用串口列表 | List of available serial ports
  - `SERIAL_BAUDRATE`: 波特率 | Baud rate

- 数据库设置 | Database Settings
  - `DB_CONFIG`: MySQL 连接配置 | MySQL connection configuration

- 服务器设置 | Server Settings
  - `OPEN_HOST`: 服务器监听地址 | Server listening address

## 💻 系统要求 | System Requirements

### 硬件要求 | Hardware Requirements
- 摄像头设备 | Camera device
- USB串口设备 (STM Virtual COM Port) | USB serial device
- 支持的操作系统：Linux (推荐)、Windows、macOS | Supported OS: Linux (recommended), Windows, macOS

### 软件要求 | Software Requirements
- **Python 3.9+** | Python 3.9 or higher
- **MySQL 5.7+** | MySQL Database 5.7 or higher
- **conda 或 pip** | conda or pip environment management
- **现代浏览器** | Modern browser (Chrome, Firefox, Safari)
- **系统音频支持** | System audio support (ALSA/PulseAudio)

### 依赖服务 | Dependencies
- **阿里云通义千问API** | Alibaba Cloud Qwen API
  - dashscope SDK
  - 语音识别与合成服务 | Speech recognition and synthesis services
- **计算机视觉库** | Computer Vision Libraries
  - OpenCV 4.5+
  - MediaPipe 0.8.9+
- **深度学习框架** | Deep Learning Framework
  - PyTorch (可选) | PyTorch (optional)
  - RKNN Toolkit Lite (ARM设备) | RKNN Toolkit Lite (for ARM devices)
- **音频处理库** | Audio Processing Libraries
  - PyAudio
  - 系统音频驱动 | System audio drivers

## 串口帧数据处理 | Serial Frame Data Processing

系统支持以下串口帧数据操作：

1. 发送帧数据：
   - 通过 `send_yaw_pitch(find_bool, yaw, pitch)` 方法发送特定格式的帧数据
   - 自动按照上位机帧格式打包数据

2. 接收帧数据：
   - 系统自动监控串口，接收并解析下位机发送的帧数据
   - 接收到的数据自动保存到数据库并推送到前端界面

3. 实时更新：
   - 通过 Server-Sent Events (SSE) 技术实现前端数据实时更新
   - 可以通过界面上的"自动更新"按钮控制是否接收实时更新

## ❗ 故障排除 | Troubleshooting

### 🔊 语音助手问题 | Voice Assistant Issues

#### 问题：语音识别不工作
**解决方案：**
```bash
# 1. 检查麦克风权限
sudo usermod -a -G audio $USER
# 重新登录生效

# 2. 检查API配置
cat Audio/config.json
# 确保api_key正确配置

# 3. 检查依赖安装
pip install dashscope pyaudio

# 4. 测试麦克风
arecord -f S16_LE -c 1 -r 16000 -d 3 test_mic.wav
aplay test_mic.wav

# 5. 检查音频设备权限
ls -la /dev/snd/
```

#### 问题：TTS合成失败或无声音
**解决方案：**
```bash
# 1. 检查音频输出设备
aplay -l

# 2. 测试音频播放
speaker-test -t wav -c 1

# 3. 检查采样率支持
./detect_audio.sh

# 4. 测试TTS功能
python -c "
from modules.chatbot_module import get_chatbot_instance
chatbot = get_chatbot_instance()
chatbot.speak_text('测试语音合成')
"

# 5. 检查PulseAudio（如果使用）
pulseaudio --check
pulseaudio --start
```

#### 问题：采样率不支持错误
**解决方案：**
```bash
# 1. 运行采样率检测
python test_voice.py

# 2. 修改chatbot_module.py中的采样率设置
# 在TTSCallback和ASRCallback类中调整采样率参数

# 3. 手动测试不同采样率
for rate in 8000 16000 22050 44100 48000; do
    echo "测试 ${rate}Hz"
    timeout 2 arecord -f S16_LE -c 1 -r $rate test_${rate}.wav 2>/dev/null
    [ $? -eq 0 ] && echo "✅ ${rate}Hz 录音支持" || echo "❌ ${rate}Hz 录音不支持"
done
```

#### 问题：家长留言语音朗读失败
**解决方案：**
```bash
# 1. 检查guardian_scheduler.py是否运行
ps aux | grep guardian_scheduler

# 2. 检查数据库连接
python -c "
from db_handler import DBHandler
from config import DB_CONFIG
db = DBHandler(DB_CONFIG)
print('数据库连接:', db.test_connection())
"

# 3. 手动测试留言朗读
python -c "
from modules.chatbot_module import get_chatbot_instance
chatbot = get_chatbot_instance()
result = chatbot.speak_text('这是一条测试留言')
print('朗读结果:', result)
"

# 4. 检查留言状态更新
mysql -u serial_user -p serial_data -e "SELECT * FROM guardian_messages ORDER BY created_at DESC LIMIT 5;"
```

### 💡 台灯控制问题 | Lamp Control Issues

#### 问题：串口连接失败
**解决方案：**
```bash
# 检查串口设备
ls -la /dev/tty*

# 修复权限
sudo chmod 666 /dev/ttyACM0

# 检查驱动
lsusb | grep -i stm
```

#### 问题：命令发送无响应
**解决方案：**
```bash
# 启用调试模式查看详细日志
DEBUG=True python app.py

# 使用协议调试界面测试
# 访问: http://localhost:5000/protocol_debug
```

### 👁️ 监测系统问题 | Monitoring System Issues

#### 问题：摄像头无法启动
**解决方案：**
```bash
# 检查摄像头设备
ls /dev/video*

# 测试摄像头
python -c "
import cv2
cap = cv2.VideoCapture(0)
print('Camera available:', cap.isOpened())
cap.release()
"
```

#### 问题：姿态检测不准确
**解决方案：**
- 确保光线充足
- 调整摄像头角度
- 检查YOLO模型文件完整性

### 🗄️ 数据库问题 | Database Issues

#### 问题：数据库连接失败
**解决方案：**
```bash
# 测试数据库连接
python test_db.py

# 检查MySQL服务
sudo systemctl status mysql

# 重置数据库配置
mysql -u root -p < init_database.sql
```

### 🌐 Web界面问题 | Web Interface Issues

#### 问题：页面加载缓慢
**解决方案：**
- 检查网络连接
- 清除浏览器缓存
- 检查服务器资源使用情况

#### 问题：实时数据不更新
**解决方案：**
```bash
# 检查SSE连接
curl -N http://localhost:5002/api/frame_events

# 重启服务
sudo systemctl restart flask_server
```

### 📞 技术支持 | Technical Support

遇到问题时，请提供以下信息：
When encountering issues, please provide:

1. 系统版本和硬件信息 | System version and hardware info
2. 完整错误日志 | Complete error logs  
3. 复现步骤 | Steps to reproduce
4. 配置文件内容 | Configuration file contents

**联系方式 | Contact Information:**
- 📧 Email: support@example.com
- 🐛 Issues: GitHub Issues页面
- 📚 文档: 查看 `docs/` 目录

## 📋 更新日志 | Changelog

### v2.0.0 (2025-06-30)
- ✨ **新增家长监护系统** | Added parental guardian system
  - 定时留言功能 | Scheduled messaging
  - 语音朗读留言 | Voice message reading
  - 留言状态跟踪 | Message status tracking
  - 实时发送时间记录 | Real-time sending time recording

- 🔊 **语音系统优化** | Voice system optimization
  - 多采样率自适应支持 | Multi-sample rate adaptive support
  - 音频设备兼容性提升 | Improved audio device compatibility
  - TTS/ASR稳定性增强 | Enhanced TTS/ASR stability
  - 新增语音测试脚本 | Added voice testing scripts

- 🛠️ **系统工具增强** | System tools enhancement
  - 新增 `detect_audio.sh` 音频检测脚本 | Added audio detection script
  - 新增 `test_voice.py` 语音测试工具 | Added voice testing tool
  - 改进调试和故障排除功能 | Improved debugging and troubleshooting

- 📚 **文档完善** | Documentation improvement
  - 详细的安装配置指南 | Detailed installation and configuration guide
  - 完整的功能使用说明 | Complete feature usage instructions
  - 丰富的故障排除方案 | Comprehensive troubleshooting solutions

### v1.0.0 (2025-06-01)
- 🎉 **项目初始版本** | Initial project version
- 💡 智能台灯控制 | Smart lamp control
- 👁️ 坐姿监测系统 | Posture monitoring system
- 🔌 串口通信协议 | Serial communication protocol
- 🌐 Web管理界面 | Web management interface

## 🔮 未来计划 | Future Plans

### v2.1.0 (计划中 | Planned)
- 🤖 增强AI对话能力 | Enhanced AI conversation capabilities
- 📱 移动端应用支持 | Mobile app support
- 🌙 智能睡眠模式 | Intelligent sleep mode
- 🎨 个性化主题设置 | Personalized theme settings

### v2.2.0 (计划中 | Planned)
- 🌐 多语言支持 | Multi-language support
- 🔐 用户账户系统 | User account system
- 📊 高级数据分析 | Advanced data analytics
- 🏠 智能家居集成 | Smart home integration

## 🤝 贡献指南 | Contributing Guide

### 🌟 如何贡献 | How to Contribute

1. **Fork项目** | Fork the project
2. **创建功能分支** | Create a feature branch
   ```bash
   git checkout -b feature/new-feature
   ```
3. **提交更改** | Commit changes
   ```bash
   git commit -m "✨ Add new feature"
   ```
4. **推送分支** | Push branch
   ```bash
   git push origin feature/new-feature
   ```
5. **创建Pull Request** | Create Pull Request

### 📝 提交规范 | Commit Convention

使用语义化提交信息 | Use semantic commit messages:

- `✨ feat: 新功能 | new feature`
- `🐛 fix: 修复问题 | bug fix`
- `📚 docs: 文档更新 | documentation`
- `🎨 style: 代码格式 | code style`
- `♻️ refactor: 重构代码 | refactoring`
- `⚡ perf: 性能优化 | performance`
- `✅ test: 测试相关 | testing`
- `🔧 chore: 构建/工具 | build/tools`

### 🏗️ 开发环境设置 | Development Environment

```bash
# 1. 克隆开发分支
git clone -b dev_comm <repository-url>

# 2. 安装开发依赖
pip install -r requirements-dev.txt

# 3. 安装pre-commit hooks
pre-commit install

# 4. 运行测试套件
pytest tests/
```

## 📄 许可证 | License

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 联系我们 | Contact Us

- 🌟 **Star** 本项目如果它对你有帮助！
- 🐛 **Issues** 报告问题或请求功能
- 📧 **Email** 技术支持邮箱
- 📖 **Wiki** 查看详细文档

---

<div align="center">
<h3>🎉 感谢使用瞳灵智能台灯系统！</h3>
<h3>🎉 Thank you for using Tongling Smart Lamp System!</h3>

**让智能照明改变您的生活方式** | **Let smart lighting change your lifestyle**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![AI Powered](https://img.shields.io/badge/AI-Powered-purple.svg)](https://dashscope.aliyun.com/)

</div>