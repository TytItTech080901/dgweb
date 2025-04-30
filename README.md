# Serial Communication Web Server

一个基于 Flask 的串口通信 Web 服务器，支持串口数据收发和历史记录管理，添加了对特定帧格式的支持。

A Flask-based web server for serial communication that supports sending/receiving serial data, managing historical records, and handling specific frame formats.

## 功能特点 | Features

- 自动检测和连接串口设备 | Auto-detect and connect to serial devices
- Web 界面支持数据发送和接收 | Web interface for sending and receiving data
- 支持特定帧格式的通信 | Support for specific frame format communication
- 自动解析并显示接收到的帧数据 | Auto-parse and display received frame data
- 历史记录管理和分页显示 | Historical record management with pagination
- MySQL 数据存储 | MySQL data storage
- 实时响应显示 | Real-time response display
- 支持清空历史记录 | Support clearing history records
- 基于Server-Sent Events的实时数据推送 | Real-time data push based on Server-Sent Events

## 系统要求 | Requirements

- Python 3.9+
- MySQL 数据库 | MySQL Database
- 串口设备 | Serial Device

## 安装步骤 | Installation

1. 克隆项目 | Clone the project
```bash
git clone <repository-url>
cd Py-server
```

2. 创建并激活虚拟环境 | Create and activate virtual environment
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

3. 配置数据库 | Configure Database

编辑 `config.py` 文件，设置数据库连接信息：
Edit `config.py` file to set database connection information:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'serial_data'
}
```

4. 创建数据库 | Create Database
```sql
CREATE DATABASE serial_data;
CREATE USER 'serial_user'@'localhost' IDENTIFIED BY 'Serial123!';
GRANT ALL PRIVILEGES ON serial_data.* TO 'serial_user'@'localhost';
FLUSH PRIVILEGES;
```

## 运行应用 | Running the Application

```bash
python server.py
```

服务器将在 http://127.0.0.1:5000 启动

The server will start at http://127.0.0.1:5000

## 使用说明 | Usage

1. 打开浏览器访问 http://127.0.0.1:5000
2. 选择操作模式：
   - 文本模式：在输入框中输入要发送的文本数据
   - 帧模式：输入 Yaw 和 Pitch 值，设置是否追踪
3. 点击相应按钮发送数据：
   - 文本模式：点击"发送"按钮
   - 帧模式：点击"发送帧数据"按钮
4. 自动接收数据：
   - 系统将自动接收并解析串口发送的帧数据
   - 最新接收的数据会实时显示在界面上
5. 查看接收到的响应和历史记录
6. 可以使用分页按钮浏览历史记录
7. 使用"清空历史记录"按钮清除所有记录

## 帧格式说明 | Frame Format

### 上位机发送帧格式 | Host Send Frame Format
```
typedef struct {
    char start;     //0 帧头取 's'
    char type;      //1 消息类型：上->下：0xA0
    char find_bool; //2 是否追踪
    float yaw;      //3-6 yaw数据
    float pitch;    //7-10 pitch数据
    char end;       //31 帧尾取'e'
} usb_msg_t;
```

### 下位机发送帧格式 | Device Send Frame Format
```
typedef struct {
    char start;     //0 帧头取 's'
    char type;      //1 消息类型：下->上：0xB0
    float yaw;      //2-5 yaw数据
    float pitch;    //6-9 pitch数据
    char end;       //31 帧尾取'e'
} usb_msgRX_t;
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

## 故障排除 | Troubleshooting

1. 串口连接问题 | Serial Connection Issues
   - 检查设备是否正确连接 | Check if the device is properly connected
   - 确认串口权限 | Verify serial port permissions
   - 检查波特率设置 | Check baud rate settings

2. 数据库问题 | Database Issues
   - 运行 `test_db.py` 测试数据库连接 | Run `test_db.py` to test database connection
   - 检查数据库配置 | Check database configuration
   - 确认数据库服务是否运行 | Verify if database service is running

3. 帧数据问题 | Frame Data Issues
   - 检查帧格式是否匹配 | Check if frame format matches
   - 确认字节序是否正确 | Verify byte order is correct
   - 调试发送/接收的原始数据 | Debug raw data sent/received

## 许可证 | License

[MIT License](LICENSE)