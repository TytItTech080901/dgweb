// analysis.js - 姿势情绪分析功能

// 情绪分析参数
let emotionParams = {
    happiness_threshold: 0.5,
    sadness_threshold: 0.5,
    anger_threshold: 0.5,
    surprise_threshold: 0.5,
    fear_threshold: 0.5,
    disgust_threshold: 0.5,
    neutral_threshold: 0.5
};

document.addEventListener('DOMContentLoaded', function() {
    // 获取情绪分析参数
    fetchEmotionParams();
    
    // 初始化时间范围切换按钮
    initTimeRangeButtons();
    
    // 初始化阈值设置按钮
    document.getElementById('applyThresholdsBtn').addEventListener('click', applyPostureThresholds);
    
    // 从后端获取坐姿统计数据
    updatePostureStats();
    
    // 每60秒自动更新一次坐姿统计数据
    setInterval(updatePostureStats, 60000);
});

// 获取情绪分析参数
function fetchEmotionParams() {
    fetch('/api/get_emotion_params')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateEmotionParamsUI(data.emotion_params);
                emotionParams = data.emotion_params;
            }
        })
        .catch(error => {
            console.error('获取情绪分析参数失败:', error);
        });
}

// 更新情绪参数UI
function updateEmotionParamsUI(params) {
    // 确保参数UI元素存在
    const emotionParamsForm = document.getElementById('emotionParamsForm');
    if (!emotionParamsForm) return;

    // 遍历参数，更新对应的输入框
    for (const key in params) {
        const input = document.getElementById(key + '_input');
        if (input) {
            input.value = params[key];
        }
    }
}

// 保存情绪分析参数
function saveEmotionParams() {
    // 收集表单数据
    const form = document.getElementById('emotionParamsForm');
    if (!form) return;

    const formData = new FormData(form);
    const params = {};
    
    // 转换为JSON对象
    for (const [key, value] of formData.entries()) {
        params[key] = parseFloat(value);
    }
    
    // 发送请求 - 使用正确的API路径
    fetch('/api/update_emotion_params', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('情绪分析参数已保存', 'success');
            emotionParams = params;
        } else {
            showNotification('保存失败: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('保存情绪分析参数失败:', error);
        showNotification('保存请求失败', 'error');
    });
}

// 更新姿势和情绪状态
function updatePostureEmotionStatus(data) {
    // 更新姿势状态信息
    if (data.posture_data) {
        const { head_angle, posture_status, detection_status } = data.posture_data;
        
        if (document.getElementById('headAngle')) {
            document.getElementById('headAngle').textContent = head_angle ? `${head_angle.toFixed(1)} °` : '-- °';
        }
        
        if (document.getElementById('postureStatus')) {
            document.getElementById('postureStatus').textContent = posture_status || '--';
        }
        
        if (document.getElementById('detectionStatus')) {
            document.getElementById('detectionStatus').textContent = detection_status || '--';
        }
    }
    
    // 更新情绪状态信息
    if (data.emotion_data) {
        const { current_emotion } = data.emotion_data;
        
        if (document.getElementById('emotionStatus')) {
            document.getElementById('emotionStatus').textContent = current_emotion || '--';
        }
    }
}

// 坐姿统计相关功能
let currentTimeRange = 'day'; // 默认显示今日数据

// 初始化时间范围切换按钮
function initTimeRangeButtons() {
    const buttons = document.querySelectorAll('.time-range-btn');
    
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            // 移除所有按钮的active类
            buttons.forEach(btn => btn.classList.remove('active'));
            
            // 为当前按钮添加active类
            this.classList.add('active');
            
            // 更新当前时间范围
            currentTimeRange = this.dataset.range;
            
            // 更新坐姿统计数据
            updatePostureStats();
        });
    });
}

// 更新坐姿统计数据
function updatePostureStats() {
    // 发送请求获取坐姿统计数据
    fetch(`/api/get_posture_stats?time_range=${currentTimeRange}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayPostureStats(data.posture_stats);
            } else {
                console.error('获取坐姿统计数据失败:', data.message);
            }
        })
        .catch(error => {
            console.error('请求坐姿统计数据出错:', error);
        });
}

// 显示坐姿统计数据
function displayPostureStats(stats) {
    // 更新总时长
    document.getElementById('totalPostureTime').textContent = stats.total_time.formatted_time;
    
    // 更新良好坐姿占比
    document.getElementById('goodPosturePercentage').textContent = `${stats.good_posture_percentage}%`;
    
    // 更新各类型坐姿数据
    const types = ['good', 'mild', 'moderate', 'severe'];
    
    types.forEach(type => {
        // 确保stats中有对应的类型数据
        const typeData = stats[type] || {seconds: 0, percentage: 0, formatted_time: '0h 0m'};
        
        // 更新百分比
        document.getElementById(`${type}Percentage`).textContent = `${typeData.percentage}%`;
        
        // 更新时长
        document.getElementById(`${type}Time`).textContent = typeData.formatted_time;
        
        // 更新描述文本 - 根据当前阈值动态更新
        const typeDescElement = document.querySelector(`.posture-type-card.${type} .posture-type-desc`);
        
        if (type === 'good') {
            typeDescElement.textContent = `0-${document.getElementById('goodThreshold').value}°`;
        } else if (type === 'mild') {
            typeDescElement.textContent = `${document.getElementById('goodThreshold').value}-${document.getElementById('mildThreshold').value}°`;
        } else if (type === 'moderate') {
            typeDescElement.textContent = `${document.getElementById('mildThreshold').value}-${document.getElementById('moderateThreshold').value}°`;
        } else if (type === 'severe') {
            typeDescElement.textContent = `${document.getElementById('moderateThreshold').value}°以上`;
        }
    });
}

// 应用坐姿阈值设置
function applyPostureThresholds() {
    const goodThreshold = parseFloat(document.getElementById('goodThreshold').value);
    const mildThreshold = parseFloat(document.getElementById('mildThreshold').value);
    const moderateThreshold = parseFloat(document.getElementById('moderateThreshold').value);
    
    // 验证阈值是否有效
    if (goodThreshold >= mildThreshold || mildThreshold >= moderateThreshold) {
        alert('请确保阈值设置递增：良好坐姿 < 轻度不良 < 中度不良');
        return;
    }
    
    // 发送请求更新阈值设置
    fetch('/api/set_posture_thresholds', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            enabled: true,
            thresholds: {
                good: goodThreshold,
                mild: mildThreshold,
                moderate: moderateThreshold
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // 更新成功后刷新统计数据
            updatePostureStats();
            
            // 显示成功通知
            showNotification('阈值设置已更新', 'success');
        } else {
            showNotification('更新阈值设置失败: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('请求更新阈值设置出错:', error);
        showNotification('更新阈值设置出错', 'error');
    });
}

// 显示通知
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 5秒后自动移除
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// 暴露公共函数
window.fetchEmotionParams = fetchEmotionParams;
window.saveEmotionParams = saveEmotionParams;
window.updatePostureEmotionStatus = updatePostureEmotionStatus;