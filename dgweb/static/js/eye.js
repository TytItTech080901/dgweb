// 用眼情况工具JavaScript - 柔和绿色调配色方案

// 全局变量
let currentEyeTab = 'monitor';
let eyeHeatmapChart = null;
let eyeMetrics = {
    continuousTime: '2.5小时',
    blinkRate: '15次/分钟',
    screenDistance: '45cm'
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('用眼情况工具初始化');
    
    // 初始化图表
    initEyeCharts();
    
    // 加载用眼数据
    loadEyeData();
    
    // 初始化事件监听器
    initEyeEventListeners();
    
    // 开始实时监控
    startEyeMonitoring();
});

// 初始化事件监听器
function initEyeEventListeners() {
    // 用眼tab切换事件
    const tabBtns = document.querySelectorAll('.eye-tab-btn');
    const tabPanels = document.querySelectorAll('.eye-tab-panel');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // 切换按钮激活状态
            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // 切换内容面板显示
            const tab = this.getAttribute('data-tab');
            tabPanels.forEach(panel => {
                if (panel.id === 'tab-' + tab) {
                    panel.classList.add('active');
                } else {
                    panel.classList.remove('active');
                }
            });
            
            currentEyeTab = tab;
            
            // 显示提示
            const tabNames = {
                monitor: '用眼监控',
                feedback: '每日反馈',
                weekly: '本周情况'
            };
            showToast(`已切换到${tabNames[tab]}`);
        });
    });
}

// 初始化用眼图表
function initEyeCharts() {
    // 初始化热力图
    const heatmapContainer = document.getElementById('eyeHeatmapChart');
    if (heatmapContainer) {
        // 这里可以集成热力图库，暂时用简单的柱状图代替
        const canvas = document.createElement('canvas');
        heatmapContainer.appendChild(canvas);
        
        eyeHeatmapChart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
                datasets: [{
                    label: '用眼强度',
                    data: [65, 72, 68, 75, 82, 58, 45],
                    backgroundColor: 'rgba(143, 180, 160, 0.6)',
                    borderColor: 'rgba(143, 180, 160, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
}

// 加载用眼数据
function loadEyeData() {
    // 模拟API调用
    fetch('/api/eye/data')
        .then(response => response.json())
        .then(data => {
            console.log('用眼数据加载成功:', data);
            updateEyeMetrics(data);
        })
        .catch(error => {
            console.error('加载用眼数据失败:', error);
            // 使用模拟数据
            loadMockEyeData();
        });
}

// 加载模拟用眼数据
function loadMockEyeData() {
    const mockData = {
        continuousTime: '2.5小时',
        blinkRate: '15次/分钟',
        screenDistance: '45cm',
        weeklyData: [65, 72, 68, 75, 82, 58, 45],
        feedback: [
            { type: 'positive', text: '本周平均远眺次数：4.3 次/天', icon: 'bi-check-circle-fill' },
            { type: 'positive', text: '当前环境光照：良好', icon: 'bi-brightness-high-fill' },
            { type: 'positive', text: '色温状态：柔和', icon: 'bi-thermometer-sun' },
            { type: 'warning', text: '昨日连续用眼超时：72 分钟', icon: 'bi-exclamation-triangle-fill' }
        ]
    };
    
    updateEyeMetrics(mockData);
    updateFeedbackList(mockData.feedback);
}

// 更新用眼指标
function updateEyeMetrics(data) {
    eyeMetrics = {
        continuousTime: data.continuousTime || '2.5小时',
        blinkRate: data.blinkRate || '15次/分钟',
        screenDistance: data.screenDistance || '45cm'
    };
    
    // 更新UI - 更新所有metric-value元素
    const metricElements = document.querySelectorAll('.metric-value');
    if (metricElements.length >= 3) {
        metricElements[0].textContent = eyeMetrics.continuousTime;
        metricElements[1].textContent = eyeMetrics.blinkRate;
        metricElements[2].textContent = eyeMetrics.screenDistance;
    }
    
    // 更新热力图数据
    if (eyeHeatmapChart && data.weeklyData) {
        eyeHeatmapChart.data.datasets[0].data = data.weeklyData;
        eyeHeatmapChart.update();
    }
}

// 更新反馈列表
function updateFeedbackList(feedbackData) {
    const feedbackList = document.querySelector('.feedback-list');
    if (!feedbackList) return;
    
    const feedbackHTML = feedbackData.map(item => `
        <div class="feedback-item ${item.type}">
            <div class="feedback-badge">
                <i class="bi ${item.icon}"></i>
            </div>
            <div class="feedback-content">
                <div class="feedback-text">${item.text}</div>
            </div>
        </div>
    `).join('');
    
    feedbackList.innerHTML = feedbackHTML;
}

// 开始用眼监控
function startEyeMonitoring() {
    // 模拟实时监控
    setInterval(() => {
        updateRealTimeMetrics();
    }, 5000);
}

// 更新实时指标
function updateRealTimeMetrics() {
    // 模拟实时数据变化
    const randomChange = (base, range) => {
        const change = (Math.random() - 0.5) * range;
        return Math.max(0, base + change);
    };
    
    // 更新连续用眼时间
    const currentTime = parseFloat(eyeMetrics.continuousTime);
    const newTime = randomChange(currentTime, 0.1);
    eyeMetrics.continuousTime = newTime.toFixed(1) + '小时';
    
    // 更新眨眼频率
    const currentBlink = parseInt(eyeMetrics.blinkRate);
    const newBlink = Math.round(randomChange(currentBlink, 2));
    eyeMetrics.blinkRate = newBlink + '次/分钟';
    
    // 更新眼屏距离
    const currentDistance = parseInt(eyeMetrics.screenDistance);
    const newDistance = Math.round(randomChange(currentDistance, 5));
    eyeMetrics.screenDistance = newDistance + 'cm';
    
    // 更新UI - 更新所有metric-value元素
    const metricElements = document.querySelectorAll('.metric-value');
    if (metricElements.length >= 3) {
        metricElements[0].textContent = eyeMetrics.continuousTime;
        metricElements[1].textContent = eyeMetrics.blinkRate;
        metricElements[2].textContent = eyeMetrics.screenDistance;
    }
    
    // 检查用眼健康状态
    checkEyeHealth();
}

// 检查用眼健康状态
function checkEyeHealth() {
    const continuousTime = parseFloat(eyeMetrics.continuousTime);
    const blinkRate = parseInt(eyeMetrics.blinkRate);
    const screenDistance = parseInt(eyeMetrics.screenDistance);
    
    // 检查连续用眼时间
    if (continuousTime > 2.0) {
        showEyeWarning('连续用眼时间过长，建议休息');
    }
    
    // 检查眨眼频率
    if (blinkRate < 12) {
        showEyeWarning('眨眼频率偏低，注意眼部保湿');
    }
    
    // 检查眼屏距离
    if (screenDistance < 40) {
        showEyeWarning('眼屏距离过近，请保持适当距离');
    }
}

// 显示用眼警告
function showEyeWarning(message) {
    // 这里可以实现警告提示
    console.log('用眼警告:', message);
}

// 获取用眼建议
function getEyeSuggestions() {
    const suggestions = [
        {
            title: '20-20-20法则',
            text: '每20分钟看20英尺外的物体20秒，缓解眼部疲劳',
            icon: 'bi-clock-history'
        },
        {
            title: '调整屏幕亮度',
            text: '保持屏幕亮度与周围环境光线协调',
            icon: 'bi-brightness-high'
        },
        {
            title: '保持适当距离',
            text: '眼睛与屏幕保持50-60厘米的距离',
            icon: 'bi-arrows-angle-expand'
        }
    ];
    
    return suggestions;
}

// 导出用眼报告
function exportEyeReport() {
    showToast('正在生成用眼报告...');
    
    // 模拟导出功能
    setTimeout(() => {
        const report = {
            date: new Date().toLocaleDateString(),
            metrics: eyeMetrics,
            suggestions: getEyeSuggestions()
        };
        
        console.log('用眼报告:', report);
        showToast('用眼报告导出成功');
    }, 2000);
}

// 设置用眼提醒
function setEyeReminder(interval) {
    showToast(`已设置${interval}分钟用眼提醒`);
    
    // 这里可以实现提醒功能
    setInterval(() => {
        showEyeReminder();
    }, interval * 60 * 1000);
}

// 显示用眼提醒
function showEyeReminder() {
    showToast('用眼时间提醒：请休息一下，远眺放松眼睛');
}

// 显示提示消息
function showToast(message) {
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: var(--primary-color);
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(143, 180, 160, 0.3);
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '1';
    }, 100);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
    if (eyeHeatmapChart) {
        eyeHeatmapChart.destroy();
    }
    console.log('用眼情况工具卸载');
});

// 导出函数供其他模块使用
window.eyeModule = {
    loadEyeData,
    updateEyeMetrics,
    exportEyeReport,
    setEyeReminder,
    showToast
}; 