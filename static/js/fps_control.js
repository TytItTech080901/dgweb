// fps_control.js - 帧率控制和分辨率管理功能

// 帧率阈值常量
const TARGET_FPS = 25.0;  // 目标帧率
const FPS_THRESHOLD_LOW = 15.0;  // 低帧率阈值
const FPS_THRESHOLD_HIGH = 28.0;  // 高帧率阈值

// 在页面加载时初始化帧率控制模块
document.addEventListener('DOMContentLoaded', function() {
    // 设置事件监听器
    setupResolutionControls();
});

// 获取帧率信息
function fetchFPSInfo() {
    fetch('/get_fps_info')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateFPSDisplay(data);
            }
        })
        .catch(error => {
            console.error('获取帧率信息失败:', error);
        });
}

// 更新帧率显示
function updateFPSDisplay(data) {
    // 更新图像接收帧率
    const captureFPS = document.getElementById('captureFPS');
    captureFPS.textContent = data.capture_fps.toFixed(1);
    updateFPSIndicator(captureFPS, data.capture_fps);
    
    // 更新图像处理帧率 (平均姿势和情绪处理帧率)
    const processFPS = document.getElementById('processFPS');
    const avgProcessFPS = (data.pose_process_fps + data.emotion_process_fps) / 2;
    processFPS.textContent = avgProcessFPS.toFixed(1);
    updateFPSIndicator(processFPS, avgProcessFPS);
    
    // 更新视频流帧率 (平均姿势和情绪视频流帧率)
    const streamFPS = document.getElementById('streamFPS');
    const avgStreamFPS = (data.pose_stream_fps + data.emotion_stream_fps) / 2;
    streamFPS.textContent = avgStreamFPS.toFixed(1);
    updateFPSIndicator(streamFPS, avgStreamFPS);
}

// 根据帧率值更新指示器颜色
function updateFPSIndicator(element, fps) {
    // 移除所有现有类
    element.classList.remove('fps-low', 'fps-medium', 'fps-good');
    
    // 添加适当的类
    if (fps < FPS_THRESHOLD_LOW) {
        element.classList.add('fps-low');
    } else if (fps < TARGET_FPS) {
        element.classList.add('fps-medium');
    } else {
        element.classList.add('fps-good');
    }
}

// 设置分辨率控制事件监听器
function setupResolutionControls() {
    // 自适应分辨率复选框事件
    const adaptiveCheckbox = document.getElementById('adaptiveResolution');
    const resolutionSelector = document.getElementById('resolutionSelector');
    
    if (adaptiveCheckbox && resolutionSelector) {
        adaptiveCheckbox.addEventListener('change', function() {
            resolutionSelector.disabled = this.checked;
        });
    }
    
    // 质量滑块值更新
    const qualitySlider = document.getElementById('qualitySlider');
    const qualityValue = document.getElementById('qualityValue');
    
    if (qualitySlider && qualityValue) {
        qualitySlider.addEventListener('input', function() {
            qualityValue.textContent = this.value;
        });
    }
    
    // 应用按钮事件
    const applyButton = document.getElementById('applyResolutionBtn');
    if (applyButton) {
        applyButton.addEventListener('click', applyResolutionSettings);
    }
}

// 应用分辨率设置
function applyResolutionSettings() {
    const adaptiveCheckbox = document.getElementById('adaptiveResolution');
    const resolutionSelector = document.getElementById('resolutionSelector');
    const targetSelector = document.getElementById('targetSelector');
    const qualitySlider = document.getElementById('qualitySlider');
    
    if (!adaptiveCheckbox || !resolutionSelector || !targetSelector || !qualitySlider) {
        console.error('找不到分辨率控制元素');
        return;
    }
    
    const adaptive = adaptiveCheckbox.checked;
    const resolutionIndex = adaptive ? null : parseInt(resolutionSelector.value);
    const target = targetSelector.value;
    const quality = parseInt(qualitySlider.value);
    
    // 构建请求数据
    const requestData = {
        adaptive: adaptive,
        resolution_index: resolutionIndex,
        target: target,
        quality: quality
    };
    
    // 发送请求
    fetch('/set_resolution_mode', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showModalMessage('设置已应用', '分辨率控制设置已成功应用。');
        } else {
            showModalMessage('设置失败', `应用设置时发生错误: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('应用分辨率设置失败:', error);
        showModalMessage('请求失败', '无法连接到服务器，请检查网络连接。', 'error');
    });
}

// 显示模态消息
function showModalMessage(title, message, type = 'success') {
    // 简易实现，实际项目中可以使用更好的UI组件
    alert(`${title}\n${message}`);
}

// 导出公共函数
window.fetchFPSInfo = fetchFPSInfo;
window.applyResolutionSettings = applyResolutionSettings;