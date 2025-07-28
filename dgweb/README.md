# 曈灵智能台灯家长端 - 移动端

这是一个基于Flask的移动端Web应用，为智能台灯提供家长监护功能。

## 项目结构

```
dgweb/
├── app.py                 # Flask主应用文件
├── requirements.txt       # Python依赖
├── README.md             # 项目说明
├── templates/            # HTML模板
│   ├── base.html         # 基础模板
│   ├── home.html         # 首页
│   ├── guardian.html     # 家长监护
│   ├── remote.html       # 远程控制
│   ├── settings.html     # 设置页面
│   └── tool_detail.html  # 工具详情页
└── static/               # 静态资源
    ├── css/              # 样式文件
    │   ├── base.css      # 基础样式
    │   ├── nav.css       # 导航样式
    │   ├── home.css      # 首页样式
    │   ├── guardian.css  # 监护页面样式
    │   ├── remote.css    # 远程控制样式
    │   ├── settings.css  # 设置页面样式
    │   └── tool_detail.css # 工具详情样式
    ├── js/               # JavaScript文件
    │   ├── base.js       # 基础功能
    │   ├── nav.js        # 导航功能
    │   ├── home.js       # 首页功能
    │   ├── guardian.js   # 监护功能
    │   ├── remote.js     # 远程控制功能
    │   ├── settings.js   # 设置功能
    │   └── tool_detail.js # 工具详情功能
    ├── asserts/          # 图片等资源
    └── uploads/          # 上传文件目录
```

## 功能特性

### 首页
- 工具快速访问（坐姿检测、用眼监护、情绪识别）
- 今日概览统计
- 实时数据更新

### 家长监护
- 实时监控画面
- 视频控制（暂停、拍照、全屏）
- 消息推送功能
- 消息历史记录

### 远程控制
- 台灯状态显示
- 灯光控制（电源、亮度、色温）
- 护眼设置
- 一键应用设置

### 设置
- 通知设置
- 监控设置
- 账户管理
- 系统信息

### 工具详情
- 坐姿检测数据分析
- 用眼情况监控
- 情绪识别反馈
- 图表可视化

## 安装和运行

### 1. 安装依赖

```bash
cd dgweb
pip install -r requirements.txt
```

### 2. 运行应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动

### 3. 访问应用

- 首页：`http://localhost:5000/`
- 家长监护：`http://localhost:5000/mobile/guardian`
- 远程控制：`http://localhost:5000/mobile/remote`
- 设置：`http://localhost:5000/mobile/settings`

## API接口

### 首页相关
- `GET /api/home/stats` - 获取首页统计数据

### 监护相关
- `GET /api/guardian/video_status` - 获取视频状态
- `POST /api/guardian/capture` - 拍照功能
- `POST /api/guardian/send_message` - 发送消息
- `GET /api/guardian/messages` - 获取消息历史

### 台灯控制
- `GET /api/lamp/status` - 获取台灯状态
- `POST /api/lamp/control/<action>` - 台灯控制

### 设置相关
- `GET /api/settings/notifications` - 获取通知设置
- `POST /api/settings/notifications` - 更新通知设置

### 工具数据
- `GET /api/tool/<tool_name>/data` - 获取工具数据
- `GET /api/tool/<tool_name>/images` - 获取工具相关图片

## 技术栈

- **后端**: Flask
- **前端**: HTML5, CSS3, JavaScript (ES6+)
- **图表**: Chart.js, ECharts
- **图标**: Bootstrap Icons
- **样式**: CSS Grid, Flexbox, CSS Variables

## 开发说明

### 添加新页面

1. 在 `templates/` 目录下创建HTML模板
2. 在 `static/css/` 目录下创建对应的CSS文件
3. 在 `static/js/` 目录下创建对应的JS文件
4. 在 `app.py` 中添加路由

### 样式规范

- 使用CSS变量定义主题色彩
- 响应式设计，支持移动端
- 统一的动画和过渡效果
- 模块化的CSS结构

### JavaScript规范

- 使用ES6+语法
- 模块化的代码结构
- 统一的错误处理
- 本地存储支持

## 部署

### 生产环境部署

1. 使用Gunicorn作为WSGI服务器
2. 配置Nginx作为反向代理
3. 设置环境变量
4. 配置SSL证书

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
```

## 贡献

欢迎提交Issue和Pull Request来改进项目。

## 许可证

MIT License 