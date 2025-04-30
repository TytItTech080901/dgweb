# Serial Communication Web Server

一个基于 Flask 的串口通信 Web 服务器，支持串口数据收发和历史记录管理。

A Flask-based web server for serial communication that supports sending/receiving serial data and managing historical records.

## 功能特点 | Features

- 自动检测和连接串口设备 | Auto-detect and connect to serial devices
- Web 界面支持数据发送和接收 | Web interface for sending and receiving data
- 历史记录管理和分页显示 | Historical record management with pagination
- MySQL 数据存储 | MySQL data storage
- 实时响应显示 | Real-time response display
- 支持清空历史记录 | Support clearing history records

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
2. 在输入框中输入要发送的数据
3. 点击"Send"按钮发送数据
4. 查看接收到的响应和历史记录
5. 可以使用分页按钮浏览历史记录
6. 使用"清空历史记录"按钮清除所有记录

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

## 故障排除 | Troubleshooting

1. 串口连接问题 | Serial Connection Issues
   - 检查设备是否正确连接 | Check if the device is properly connected
   - 确认串口权限 | Verify serial port permissions
   - 检查波特率设置 | Check baud rate settings

2. 数据库问题 | Database Issues
   - 运行 `test_db.py` 测试数据库连接 | Run `test_db.py` to test database connection
   - 检查数据库配置 | Check database configuration
   - 确认数据库服务是否运行 | Verify if database service is running

## 许可证 | License

[MIT License](LICENSE)