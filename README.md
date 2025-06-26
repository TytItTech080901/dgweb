# 🏮 曈灵智能台灯家长端系统

一个集成了姿势检测、情绪分析、语音助手和设备控制的智能家庭教育辅助系统。基于Flask架构，提供实时视频分析、机械臂控制、数据可视化和家长监控等功能。

An integrated smart home education assistance system with posture detection, emotion analysis, voice assistant, and device control. Built on Flask architecture, providing real-time video analysis, robotic arm control, data visualization, and parental monitoring.

## ✨ 功能特点 | Features

### 🎯 核心功能
- 🤖 **AI姿势检测** | Real-time posture analysis with MediaPipe
- 😊 **情绪识别分析** | Emotion detection and analysis
- 🎤 **智能语音助手** | Voice assistant with Snowboy wake word detection
- 📹 **实时视频流** | Live video streaming and processing
- 🦾 **机械臂控制** | Robotic arm control via serial communication
- 📊 **数据可视化** | Interactive charts and analytics dashboard

### 🏠 家长监控功能
- 👨‍👩‍👧‍👦 **家长端面板** | Comprehensive parental monitoring dashboard
- 📈 **学习状态分析** | Learning behavior analysis and reports
- ⏰ **专注度监测** | Focus time tracking and statistics
- 📋 **日报/周报生成** | Automated daily and weekly reports
- 🚨 **不良姿势提醒** | Bad posture alerts and notifications
- 💡 **智能灯光控制** | Adaptive lighting control

### 🔧 技术功能
- 🌐 **Web界面控制** | Modern web-based control interface
- 💾 **MySQL数据存储** | Persistent data storage with MySQL
- 🔄 **实时数据推送** | Real-time data updates via Server-Sent Events
- 📱 **响应式设计** | Mobile-friendly responsive design
- 🎛️ **参数动态调节** | Real-time parameter adjustment
- 🔧 **调试模式支持** | Comprehensive debugging capabilities

## 🌟 项目亮点 | Project Highlights

### 🔥 技术亮点
- 🚀 **多AI模型融合**: MediaPipe + YOLO + 情绪识别多模型协同工作
- ⚡ **实时性能优化**: 支持多分辨率自适应，保证流畅体验
- 🔄 **模块化架构**: 松耦合设计，支持功能独立部署和扩展
- 🌐 **全栈Web应用**: 前后端分离，支持移动端访问
- 💾 **数据持久化**: 完整的数据采集、存储和分析链路

### 🎯 创新功能  
- 👨‍👩‍👧‍👦 **智能家庭教育**: 专为家庭教育场景设计的监控系统
- 🎭 **多维度分析**: 姿势 + 情绪 + 专注度的综合评估
- 🦾 **硬件联动**: 软硬件一体化的智能台灯控制
- 📊 **可视化报告**: 自动生成专业的学习分析报告
- 🎤 **语音交互**: 自然语言交互的智能助手

### 💡 应用价值
- 👶 **儿童健康**: 预防儿童近视和脊柱问题  
- 📚 **学习效率**: 通过数据分析优化学习环境
- 👪 **家庭和谐**: 帮助家长科学监督孩子学习
- 🏥 **预防医学**: 早期发现和预防健康问题
- 🤖 **AI普及**: 将AI技术带入普通家庭

## 🛠️ 系统要求 | Requirements

### 💻 硬件要求 | Hardware Requirements
- �️ **CPU**: Intel i5 / AMD Ryzen 5 或更高 | or higher
- 🧠 **内存**: 4GB RAM 最小，8GB 推荐 | minimum, 8GB recommended  
- � **存储**: 5GB 可用空间 | available storage
- 📷 **摄像头**: USB摄像头或内置摄像头 | USB or built-in camera
- 🎤 **麦克风**: 用于语音助手功能 | For voice assistant
- 🔌 **串口**: USB转串口设备 (可选) | USB-to-Serial (Optional)

### 🐍 软件要求 | Software Requirements  
- 🐍 **Python**: 3.9+ (推荐 3.9-3.11) | recommended 3.9-3.11
- �️ **MySQL**: 5.7+ 或 8.0+ | or 8.0+
- 🌐 **浏览器**: Chrome 90+, Firefox 88+, Safari 14+ | Modern browsers
- 🖥️ **操作系统**: Windows 10+, Ubuntu 18.04+, macOS 10.15+ | OS Support

### ⚡ 性能参数 | Performance Metrics
- 📹 **视频处理**: 15-30 FPS (取决于硬件) | depending on hardware
- 🤖 **AI检测延迟**: < 100ms (单帧处理) | single frame processing  
- 🌐 **Web响应**: < 50ms (API调用) | API calls
- 💾 **数据存储**: 支持10万+记录 | 100k+ records supported
- 🔄 **并发用户**: 支持10+同时访问 | concurrent users

## ⚡ 快速开始 | Quick Start

### 🚀 一键启动 | One-Click Start
```bash
# 克隆项目 | Clone project
git clone <repository-url>
cd Py-server

# 安装依赖 | Install dependencies  
pip install -r requirements.txt

# 配置数据库 | Setup database
mysql -u root -p < setup.sql

# 启动应用 | Start application
python app.py
```

### 🎯 快速体验 | Quick Experience
1. 🌐 打开浏览器访问: http://localhost:5000
2. 📹 确保摄像头正常工作
3. 🚀 点击"启动分析系统"开始体验
4. 👀 观察实时姿势和情绪检测结果
5. 📊 查看数据可视化图表

### 🔧 最小配置 | Minimal Configuration
如果只想体验核心功能，可以这样配置：
For core functionality only:
```python
# config.py 最小配置
DEBUG = True
DEBUG_BUTTON_VISIBLE = True  
ENABLE_CHATBOT = False  # 跳过语音功能
# 使用默认数据库配置
```

## 🚀 安装步骤 | Installation

### 1. 📥 克隆项目 | Clone the project
```bash
git clone <repository-url>
cd Py-server
```

### 2. 🐍 创建并激活虚拟环境 | Create and activate virtual environment
```bash
conda env create -f environment.yml
conda activate pyserver
```

或使用 pip | Or using pip:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 3. 🗄️ 配置数据库 | Configure Database

编辑 `config.py` 文件，设置数据库连接信息：
Edit `config.py` file to set database connection information:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'serial_data'
}

# 调试配置 | Debug Configuration
DEBUG = True  # 开启调试模式 | Enable debug mode
DEBUG_BUTTON_VISIBLE = True  # 显示调试按钮 | Show debug button

# 语音助手配置 | Voice Assistant Configuration
ENABLE_CHATBOT = True  # 启用语音助手 | Enable voice assistant
ENABLE_WELCOME_MESSAGE = False  # 启用欢迎消息 | Enable welcome message
AUTO_START_CHATBOT_LOOP = False  # 自动启动对话循环 | Auto start chat loop
```

### 4. 💾 创建数据库 | Create Database
```sql
CREATE DATABASE serial_data;
CREATE USER 'serial_user'@'localhost' IDENTIFIED BY 'Serial123!';
GRANT ALL PRIVILEGES ON serial_data.* TO 'serial_user'@'localhost';
FLUSH PRIVILEGES;
```

## 🏃‍♂️ 运行应用 | Running the Application

```bash
python app.py
```

🌐 服务器将在 http://0.0.0.0:5000 启动，支持所有网络接口访问

The server will start at http://0.0.0.0:5000 and accept connections from all network interfaces

### 🎮 访问界面 | Access Interfaces

- 🏠 **主页面**: http://localhost:5000 - 智能台灯家长端控制面板
- 🔧 **调试页面**: http://localhost:5000/debug - 系统调试和参数调整  
- 🎯 **检测页面**: http://localhost:5000/detection - 目标检测控制
- 📊 **坐姿记录**: http://localhost:5000/posture-records - 坐姿历史记录详情

## 📖 使用说明 | Usage

### 🏠 家长监控面板
1. 🖥️ 打开浏览器访问 http://localhost:5000
2. 📊 查看实时监控数据：
   - **坐姿检测**: 实时姿势分析和不良坐姿统计
   - **用眼情况**: 用眼距离和时长监测
   - **情绪反馈**: 学习情绪状态分析
3. 📈 数据可视化：
   - 坐姿质量趋势图
   - 用眼健康图表  
   - 情绪波动分析
4. 📋 报告生成：
   - 一键生成日报/周报
   - PDF格式导出
   - 数据统计分析

### 🎯 姿势与情绪分析
1. 🚀 启动分析系统：点击"启动分析系统"按钮
2. 📹 实时视频监控：查看姿势检测和情绪分析结果
3. 🔧 参数调整：
   - 情绪检测敏感度调节
   - 姿势判断阈值设置
   - 检测频率控制
4. 📊 数据查看：实时FPS、检测状态、分析结果

### 🦾 机械臂控制 (串口通信)
1. 🔌 连接设备：选择串口设备和波特率
2. 📡 数据通信：
   - **文本模式**: 发送自定义文本命令
   - **帧模式**: 发送结构化Yaw/Pitch数据
3. 📝 历史记录：查看通信历史和响应数据
4. 🔄 实时更新：自动接收设备反馈数据

### 🎤 语音助手
1. ⚙️ 在 `config.py` 中启用语音助手: `ENABLE_CHATBOT = True`
2. 🎙️ 语音唤醒：使用设定的唤醒词激活助手
3. 💬 语音交互：进行自然语言对话
4. 🔧 功能配置：
   - 欢迎消息开关
   - 自动对话循环
   - 语音识别参数

## 🔗 API接口文档 | API Documentation

### 🏠 页面路由 | Page Routes
- `GET /` - 家长监控主页面 | Main parental monitoring page
- `GET /debug` - 系统调试页面 | System debug page  
- `GET /detection` - 目标检测页面 | Object detection page
- `GET /posture-records` - 坐姿历史记录 | Posture history records

### 📊 数据API | Data APIs
- `GET /api/status` - 获取系统状态 | Get system status
- `POST /api/start_analysis` - 启动分析系统 | Start analysis system
- `POST /api/stop_analysis` - 停止分析系统 | Stop analysis system
- `GET /api/posture_data` - 获取坐姿数据 | Get posture data
- `GET /api/emotion_data` - 获取情绪数据 | Get emotion data
- `GET /api/fps_info` - 获取帧率信息 | Get FPS information

### 🔌 串口API | Serial APIs  
- `POST /api/connect_serial` - 连接串口设备 | Connect serial device
- `POST /api/disconnect_serial` - 断开串口连接 | Disconnect serial
- `POST /api/send_command` - 发送串口命令 | Send serial command
- `POST /api/send_frame` - 发送帧数据 | Send frame data
- `GET /api/serial_status` - 获取串口状态 | Get serial status

### 📹 视频流API | Video Stream APIs
- `GET /pose_video_feed` - 姿势分析视频流 | Posture analysis video stream
- `GET /emotion_video_feed` - 情绪分析视频流 | Emotion analysis video stream  
- `POST /api/set_resolution` - 设置视频分辨率 | Set video resolution
- `POST /api/toggle_video_stream` - 切换视频流状态 | Toggle video stream

### 🗄️ 数据库API | Database APIs
- `GET /api/history` - 获取历史记录 | Get history records
- `POST /api/clear_history` - 清空历史记录 | Clear history records
- `GET /api/posture_records` - 获取坐姿记录 | Get posture records
- `POST /api/export_data` - 导出数据 | Export data

### 🎤 语音助手API | Voice Assistant APIs
- `POST /api/start_chatbot` - 启动语音助手 | Start voice assistant
- `POST /api/stop_chatbot` - 停止语音助手 | Stop voice assistant  
- `GET /api/chatbot_status` - 获取助手状态 | Get assistant status

## 🏗️ 项目架构 | Project Architecture

### 📁 核心模块 | Core Modules
```
├── 📱 app.py                    # 应用入口主程序 | Main application entry
├── ⚙️ config.py                 # 系统配置文件 | System configuration  
├── 🗄️ db_handler.py             # 数据库操作处理 | Database operations
├── 🔌 serial_handler.py         # 串口通信处理 | Serial communication
├── 📂 modules/                  # 功能模块目录 | Function modules
│   ├── 🎯 detection_module.py   # YOLO目标检测 | YOLO object detection
│   ├── 🤖 posture_module.py     # MediaPipe姿势分析 | MediaPipe posture analysis  
│   ├── 😊 emotion_analyzer.py   # 情绪识别分析 | Emotion recognition
│   ├── 🎤 chatbot_module.py     # 语音助手模块 | Voice assistant module
│   ├── 📹 video_stream_module.py # 视频流处理 | Video stream processing
│   ├── 🔌 serial_module.py      # 串口通信模块 | Serial communication module
│   ├── 🗄️ database_module.py    # 数据库管理 | Database management
│   └── 🛣️ routes.py            # API路由定义 | API route definitions
├── 🎨 templates/               # HTML模板文件 | HTML templates
│   ├── 🏠 main.html            # 主页面模板 | Main page template
│   ├── 🔧 debug.html           # 调试页面模板 | Debug page template  
│   ├── 🎯 detection.html       # 检测页面模板 | Detection page template
│   └── 📊 posture_records.html # 坐姿记录模板 | Posture records template
├── 🎨 static/                  # 静态资源文件 | Static resources
│   ├── 🎨 css/                 # 样式表文件 | Stylesheets
│   ├── 🎮 js/                  # JavaScript脚本 | JavaScript files
│   └── 🖼️ posture_images/      # 坐姿图像存储 | Posture images storage
├── 🎤 Audio/                   # 语音助手模块 | Voice assistant
│   ├── ❄️ Snowboy/            # 语音唤醒引擎 | Voice wake-up engine
│   ├── 🎤 voice_assistant.py   # 语音助手核心 | Voice assistant core
│   └── 🛠️ tools.py            # 语音工具函数 | Voice utility functions
├── 🤖 Yolo/                    # YOLO检测模型 | YOLO detection models
│   ├── 🎯 detector.py          # 检测器实现 | Detector implementation
│   ├── 📷 camera.py            # 摄像头接口 | Camera interface
│   └── 🧠 best6_rknn_model/    # 训练好的模型 | Trained models
└── 📚 docs/                    # 项目文档 | Project documentation
    └── 📋 command_frame.md     # 命令帧格式说明 | Command frame format
```

### 🔗 系统流程 | System Workflow
1. 🎬 **视频采集**: 摄像头获取实时视频流
2. 🤖 **AI分析**: MediaPipe姿势检测 + 情绪识别
3. 📊 **数据处理**: 实时数据分析和状态判断  
4. 💾 **数据存储**: MySQL数据库持久化存储
5. 🌐 **Web展示**: 实时推送到前端界面
6. 🦾 **设备控制**: 串口通信控制机械臂设备
7. 👨‍👩‍👧‍👦 **家长监控**: 生成报告和可视化图表

## ⚙️ 配置选项 | Configuration Options

在 `config.py` 中可以配置以下选项：
The following options can be configured in `config.py`:

### 🔌 串口设置 | Serial Port Settings
```python
SERIAL_PORTS = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', '/dev/ttyACM1']
SERIAL_BAUDRATE = 115200
```

### 🗄️ 数据库设置 | Database Settings  
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'serial_user', 
    'password': 'Serial123!',
    'database': 'serial_data'
}
```

### 🌐 服务器设置 | Server Settings
```python
OPEN_HOST = '0.0.0.0'  # 监听所有网络接口 | Listen on all interfaces
OPEN_PORT = 5000       # 服务端口 | Service port
```

### 🔧 调试设置 | Debug Settings
```python
DEBUG = True                    # 调试模式 | Debug mode
DEBUG_BUTTON_VISIBLE = True     # 调试按钮显示 | Debug button visibility
```

### 🎤 语音助手设置 | Voice Assistant Settings
```python
ENABLE_CHATBOT = True           # 启用语音助手 | Enable voice assistant
ENABLE_WELCOME_MESSAGE = False  # 欢迎消息 | Welcome message
AUTO_START_CHATBOT_LOOP = False # 自动启动对话 | Auto start conversation
```

## 🔄 数据处理流程 | Data Processing Workflow

### 🎯 姿势检测流程 | Posture Detection Flow
1. 📹 **视频采集**: 摄像头实时捕获视频帧
2. 🤖 **MediaPipe处理**: 提取人体关键点坐标
3. 📐 **角度计算**: 计算头部倾斜角度和坐姿状态
4. ⚖️ **状态判断**: 根据阈值判断坐姿是否良好
5. 💾 **数据存储**: 保存检测结果到MySQL数据库
6. 📊 **实时展示**: 通过SSE推送到前端界面

### 😊 情绪识别流程 | Emotion Recognition Flow  
1. 👤 **面部检测**: 从视频帧中检测面部区域
2. 🔍 **特征提取**: 提取面部表情特征点
3. 🧠 **情绪分析**: AI模型分析当前情绪状态
4. 📈 **平滑处理**: 多帧平滑避免检测抖动
5. 📊 **状态更新**: 更新情绪状态到前端显示

### 🦾 机械臂控制流程 | Robotic Arm Control Flow
1. 📡 **数据发送**: 
   - 通过Web界面输入Yaw/Pitch控制参数
   - 按照特定帧格式打包数据: `start + type + find_bool + yaw + pitch + end`
   - 通过串口发送到下位机

2. 📡 **数据接收**:
   - 自动监听串口数据
   - 解析下位机返回的帧格式: `start + type + yaw + pitch + end`  
   - 实时显示接收到的位置反馈

3. 📝 **历史记录**:
   - 所有通信数据自动保存到数据库
   - 支持分页查看和历史记录清空
   - 通过SSE实时更新最新通信状态

### 🎤 语音助手流程 | Voice Assistant Flow
1. 👂 **语音监听**: Snowboy引擎监听唤醒词
2. 🎙️ **语音识别**: 将语音转换为文本
3. 🧠 **意图理解**: 分析用户意图和指令
4. 💬 **响应生成**: 生成合适的回复内容
5. 🔊 **语音合成**: 将回复转换为语音输出

## 🛠️ 故障排除 | Troubleshooting

### 📹 视频流问题 | Video Stream Issues
- 🔍 **摄像头无法访问**: 检查摄像头设备权限和驱动
- 📐 **分辨率不支持**: 调整config.py中的分辨率设置
- ⚡ **帧率过低**: 降低处理分辨率或关闭部分AI功能
- 🖥️ **显示黑屏**: 确认摄像头未被其他程序占用

### 🤖 AI检测问题 | AI Detection Issues  
- 📦 **MediaPipe安装失败**: `pip install mediapipe>=0.8.9`
- 🎯 **检测精度低**: 调整检测参数阈值
- 💡 **光线影响**: 确保充足均匀的面部光照
- 🔄 **检测抖动**: 增加平滑窗口大小

### 🔌 串口通信问题 | Serial Communication Issues
- 🔗 **设备连接失败**: 检查设备物理连接和驱动安装
- 🔐 **权限不足**: `sudo chmod 666 /dev/ttyUSB*`
- ⚡ **波特率不匹配**: 确认设备波特率设置正确
- 📡 **数据格式错误**: 检查帧格式和字节序

### 🗄️ 数据库问题 | Database Issues
- 🚀 **连接失败**: 运行 `python test_db.py` 测试连接
- 🔑 **权限不足**: 检查数据库用户权限设置
- 💾 **存储空间**: 确认数据库有足够存储空间
- 🔄 **表结构**: 重新运行数据库初始化

### 🎤 语音助手问题 | Voice Assistant Issues
- 🎙️ **麦克风无法访问**: 检查麦克风权限和设备
- 👂 **唤醒词不响应**: 调整Snowboy敏感度参数
- 🔊 **音频输出问题**: 检查扬声器设备和音量
- 🌐 **网络连接**: 确认语音服务网络连接正常

### 🌐 Web界面问题 | Web Interface Issues
- 🔄 **页面无法加载**: 检查Flask服务是否正常启动
- 📊 **图表不显示**: 确认Chart.js和ECharts库加载正常
- 🔧 **调试按钮不显示**: 确认config.py中DEBUG_BUTTON_VISIBLE=True
- 📱 **移动端适配**: 使用现代浏览器并启用JavaScript

## 🎯 帧格式说明 | Frame Format Documentation

### 📡 上位机发送帧格式 | Host Send Frame Format
```c
typedef struct {
    char start;     // 0: 帧头='s' | Frame header  
    char type;      // 1: 消息类型=0xA0 (上->下) | Message type (Host->Device)
    char find_bool; // 2: 是否追踪 | Tracking flag
    float yaw;      // 3-6: yaw角度数据 | Yaw angle data
    float pitch;    // 7-10: pitch角度数据 | Pitch angle data  
    char end;       // 11: 帧尾='e' | Frame footer
} usb_msg_t;
```

### 📡 下位机发送帧格式 | Device Send Frame Format  
```c
typedef struct {
    char start;     // 0: 帧头='s' | Frame header
    char type;      // 1: 消息类型=0xB0 (下->上) | Message type (Device->Host)
    float yaw;      // 2-5: yaw角度反馈 | Yaw angle feedback
    float pitch;    // 6-9: pitch角度反馈 | Pitch angle feedback
    char end;       // 10: 帧尾='e' | Frame footer  
} usb_msgRX_t;
```

### 📊 数据格式示例 | Data Format Examples
```python
# 发送示例 | Send Example
send_data = {
    "find_bool": True,
    "yaw": 15.5,
    "pitch": -10.2
}

# 接收示例 | Receive Example  
received_data = {
    "type": "frame_data",
    "yaw": 15.3,
    "pitch": -10.1,
    "timestamp": "2025-06-26 10:30:45"
}
```

## 🤝 贡献指南 | Contributing

欢迎贡献代码！请遵循以下步骤：
We welcome contributions! Please follow these steps:

1. 🍴 Fork 本项目 | Fork the repository
2. 🌿 创建特性分支 | Create a feature branch: `git checkout -b feature/amazing-feature`  
3. ✅ 提交更改 | Commit changes: `git commit -m '✨ Add amazing feature'`
4. 📤 推送分支 | Push to branch: `git push origin feature/amazing-feature`
5. 🔀 提交PR | Open a Pull Request

### 📝 提交规范 | Commit Convention
- ✨ `feat`: 新功能 | New feature
- 🐛 `fix`: 修复bug | Bug fix  
- 📚 `docs`: 文档更新 | Documentation
- 🎨 `style`: 代码格式 | Code style
- 🔧 `refactor`: 重构 | Refactoring
- ⚡ `perf`: 性能优化 | Performance
- ✅ `test`: 测试相关 | Testing
- 🚧 `chore`: 构建/工具 | Build/Tools

## 📄 许可证 | License

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## 🙏 致谢 | Acknowledgments

- 🤖 [MediaPipe](https://mediapipe.dev/) - 实时姿势检测
- 🎯 [YOLO](https://ultralytics.com/) - 目标检测模型  
- 📊 [Chart.js](https://www.chartjs.org/) - 数据可视化
- 🌐 [Flask](https://flask.palletsprojects.com/) - Web框架
- 🎤 [Snowboy](https://snowboy.kitt.ai/) - 语音唤醒
- 💾 [MySQL](https://www.mysql.com/) - 数据库支持

---

📧 **联系我们**: 如有问题或建议，请提交Issue或联系项目维护者

**Contact Us**: For questions or suggestions, please submit an Issue or contact the project maintainers