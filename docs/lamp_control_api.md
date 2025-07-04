# 台灯远程控制 API 文档

本文档描述了台灯远程控制系统的 API 接口。

## 基本信息

- 基础URL: `/api/lamp`
- 所有POST请求数据格式: `application/json`
- 所有响应数据格式: `application/json`

## API 端点

### 1. 获取台灯状态

获取台灯当前所有状态信息。

- URL: `/api/lamp/status`
- 方法: `GET`
- 响应:
  ```json
  {
    "status": "success",
    "data": {
      "power": false,
      "brightness": 50,
      "color_temp": 4000,
      "color_mode": "warm",
      "rgb_color": {
        "r": 255,
        "g": 255,
        "b": 255
      },
      "timer_enabled": false,
      "timer_duration": 0,
      "scene_mode": "normal",
      "auto_mode": false,
      "last_update": "2025-07-01T12:00:00.000000"
    }
  }
  ```

### 2. 控制台灯电源

开启或关闭台灯。

- URL: `/api/lamp/power`
- 方法: `POST`
- 请求体:
  ```json
  {
    "power": true  // true为开灯，false为关灯
  }
  ```
- 响应:
  ```json
  {
    "status": "success",
    "message": "台灯开启成功",
    "data": {
      "power": true
    }
  }
  ```

### 3. 调节台灯亮度

调整台灯亮度。

- URL: `/api/lamp/brightness`
- 方法: `POST`
- 请求体:
  ```json
  {
    "brightness": 80  // 0-100
  }
  ```
- 响应:
  ```json
  {
    "status": "success",
    "message": "设置台灯亮度为80%成功",
    "data": {
      "brightness": 80
    }
  }
  ```

### 4. 调节台灯色温

调整台灯色温。

- URL: `/api/lamp/color_temp`
- 方法: `POST`
- 请求体:
  ```json
  {
    "color_temp": 4500  // 2700-6500K
  }
  ```
- 响应:
  ```json
  {
    "status": "success",
    "message": "设置台灯色温为4500K成功",
    "data": {
      "color_temp": 4500
    }
  }
  ```

### 5. 设置RGB颜色

调整台灯RGB颜色（仅在RGB模式下有效）。

- URL: `/api/lamp/rgb`
- 方法: `POST`
- 请求体:
  ```json
  {
    "r": 255,  // 0-255
    "g": 128,  // 0-255
    "b": 0     // 0-255
  }
  ```
- 响应:
  ```json
  {
    "status": "success",
    "message": "设置台灯RGB颜色为R255G128B0成功",
    "data": {
      "r": 255,
      "g": 128,
      "b": 0
    }
  }
  ```

### 6. 设置颜色模式

设置台灯颜色模式。

- URL: `/api/lamp/color_mode`
- 方法: `POST`
- 请求体:
  ```json
  {
    "mode": "warm"  // 可选值: warm, cool, daylight, rgb
  }
  ```
- 响应:
  ```json
  {
    "status": "success",
    "message": "设置台灯颜色模式为warm成功",
    "data": {
      "color_mode": "warm"
    }
  }
  ```

### 7. 设置场景模式

设置台灯场景模式。

- URL: `/api/lamp/scene`
- 方法: `POST`
- 请求体:
  ```json
  {
    "scene": "reading"  // 可选值: normal, reading, relax, work
  }
  ```
- 响应:
  ```json
  {
    "status": "success",
    "message": "设置台灯场景模式为reading成功",
    "data": {
      "scene_mode": "reading"
    }
  }
  ```

### 8. 设置定时器

设置台灯自动关闭定时器。

- URL: `/api/lamp/timer`
- 方法: `POST`
- 请求体:
  ```json
  {
    "duration": 30  // 分钟，0表示关闭定时器
  }
  ```
- 响应:
  ```json
  {
    "status": "success",
    "message": "设置台灯定时器30分钟成功",
    "data": {
      "timer_enabled": true,
      "timer_duration": 30
    }
  }
  ```

### 9. 设置自动模式

启用或禁用台灯自动亮度调节模式。

- URL: `/api/lamp/auto_mode`
- 方法: `POST`
- 请求体:
  ```json
  {
    "enabled": true  // true启用，false禁用
  }
  ```
- 响应:
  ```json
  {
    "status": "success",
    "message": "启用台灯自动模式成功",
    "data": {
      "auto_mode": true
    }
  }
  ```

### 10. 应用预设配置

一次性应用多个台灯设置。

- URL: `/api/lamp/preset`
- 方法: `POST`
- 请求体:
  ```json
  {
    "power": true,
    "brightness": 80,
    "color_temp": 4000,
    "scene_mode": "reading"
  }
  ```
- 响应:
  ```json
  {
    "status": "success",
    "message": "应用台灯预设配置成功",
    "data": {
      // 返回完整的台灯状态...
    }
  }
  ```

## 错误响应

当请求失败时，API将返回以下格式的错误响应：

```json
{
  "status": "error",
  "message": "错误描述信息"
}
```

常见的错误情况：

- 400 Bad Request - 请求参数错误或缺失
- 500 Internal Server Error - 服务器内部错误

## 串口通信协议

台灯控制指令的串口通信协议说明：

1. 电源控制: `POWER:ON` 或 `POWER:OFF`
2. 亮度控制: `BRIGHTNESS:50` (值范围 0-100)
3. 色温控制: `COLOR_TEMP:4000` (值范围 2700-6500)
4. RGB控制: `RGB:255,128,0` (值范围 0-255)
5. 颜色模式: `COLOR_MODE:WARM` (值可为 WARM, COOL, DAYLIGHT, RGB)
6. 场景模式: `SCENE:READING` (值可为 NORMAL, READING, RELAX, WORK)
7. 定时控制: `TIMER:30` (分钟，0表示关闭定时器)
8. 自动模式: `AUTO_MODE:ON` 或 `AUTO_MODE:OFF`
9. 状态查询: `GET_STATUS`
