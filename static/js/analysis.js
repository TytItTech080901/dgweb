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
});

// 获取情绪分析参数
function fetchEmotionParams() {
    fetch('/get_emotion_params')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateEmotionParamsUI(data.params);
                emotionParams = data.params;
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
    
    // 发送请求
    fetch('/set_emotion_params', {
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

// 暴露公共函数
window.fetchEmotionParams = fetchEmotionParams;
window.saveEmotionParams = saveEmotionParams;
window.updatePostureEmotionStatus = updatePostureEmotionStatus;