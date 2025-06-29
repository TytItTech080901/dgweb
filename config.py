# 串口配置
SERIAL_PORTS = [
    '/dev/ttyUSB0',
    '/dev/ttyUSB1',
    '/dev/ttyACM0',
    '/dev/ttyACM1'
]
SERIAL_BAUDRATE = 115200

# MySQL配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'serial_user',
    'password': 'Serial123!',  # 使用你设置的密码
    'database': 'serial_data'
}

# 调试配置
DEBUG = True  # 设置为True开启调试模式，False关闭调试模式
DEBUG_BUTTON_VISIBLE = True  # 控制main.html中调试按钮的显示

# 语音助手配置
ENABLE_CHATBOT = True  # 是否启用语音助手
ENABLE_WELCOME_MESSAGE = True  # 是否启用欢迎消息
AUTO_START_CHATBOT_LOOP = True  # 是否自动启动语音助手对话循环

# 开放端口配置
# 使用0.0.0.0表示监听所有可用网络接口，允许任何IP地址连接
OPEN_HOST = '0.0.0.0'
OPEN_PORT = 5002  # 修改为5002端口避免端口冲突
