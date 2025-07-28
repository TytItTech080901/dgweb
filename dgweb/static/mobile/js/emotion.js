// 情绪识别工具JavaScript - 柔和绿色调配色方案

// 全局变量
let currentEmotionView = 'radar';
let emotionRadarChart = null;
let emotionTrendChart = null;
let emotionDistributionChart = null;
let emotionHeatmapChart = null;
let emotionData = {
    dominantEmotion: '高兴',
    emotionScore: 4.2,
    stability: '良好',
    stabilityChange: 15
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('情绪识别工具初始化');
    
    // 初始化图表
    initEmotionCharts();
    
    // 加载情绪数据
    loadEmotionData();
    
    // 初始化事件监听器
    initEmotionEventListeners();
    
    // 开始实时监控
    startEmotionMonitoring();

    // 新增tab切换事件监听
    const tabBtns = document.querySelectorAll('.emotion-tab-btn');
    const tabPanels = document.querySelectorAll('.emotion-tab-panel');
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
        });
    });
});

// 初始化事件监听器
function initEmotionEventListeners() {
    // 情绪视图切换事件
    const viewSelect = document.getElementById('emotionViewSelect');
    if (viewSelect) {
        viewSelect.addEventListener('change', function() {
            switchEmotionView(this.value);
        });
    }
}

// 切换情绪视图
function switchEmotionView(viewType) {
    if (viewType === currentEmotionView) return;
    
    // 隐藏所有视图
    document.querySelectorAll('.emotion-chart-view').forEach(view => {
        view.classList.remove('active');
    });
    
    // 显示目标视图
    const targetView = document.getElementById(`emotion-${viewType}-view`);
    if (targetView) {
        targetView.classList.add('active');
    }
    
    currentEmotionView = viewType;
    
    // 重新渲染图表
    renderEmotionChart(viewType);
    
    // 显示提示
    const viewNames = {
        radar: '雷达图',
        trend: '趋势图',
        distribution: '分布图',
        heatmap: '热力图'
    };
    showToast(`已切换到${viewNames[viewType]}`);
}

// 初始化情绪图表
function initEmotionCharts() {
    // 初始化雷达图
    const radarCtx = document.getElementById('emotionRadarChart');
    if (radarCtx) {
        emotionRadarChart = new Chart(radarCtx, {
            type: 'radar',
            data: {
                labels: ['高兴', '平静', '焦虑', '愤怒', '悲伤', '兴奋'],
                datasets: [{
                    label: '情绪强度',
                    data: [4.2, 3.8, 1.5, 0.8, 1.2, 3.5],
                    backgroundColor: 'rgba(143, 180, 160, 0.2)',
                    borderColor: 'rgba(143, 180, 160, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(143, 180, 160, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(143, 180, 160, 1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 5,
                        ticks: {
                            stepSize: 1
                        }
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
    
    // 初始化趋势图
    const trendCtx = document.getElementById('emotionTrendChart');
    if (trendCtx) {
        emotionTrendChart = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: ['9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'],
                datasets: [{
                    label: '情绪值',
                    data: [3.2, 3.8, 4.1, 3.5, 2.8, 1.8, 2.5, 4.2],
                    borderColor: 'rgba(143, 180, 160, 1)',
                    backgroundColor: 'rgba(143, 180, 160, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 5
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
    
    // 初始化分布图（这里用简单的HTML代替）
    const distributionContainer = document.getElementById('emotionDistributionChart');
    if (distributionContainer) {
        renderDistributionChart(distributionContainer);
    }
    
    // 初始化热力图（这里用简单的HTML代替）
    const heatmapContainer = document.getElementById('emotionHeatmapChart');
    if (heatmapContainer) {
        renderHeatmapChart(heatmapContainer);
    }
}

// 渲染分布图
function renderDistributionChart(container) {
    const emotions = [
        { name: '高兴', count: 40, color: 'var(--success-color)' },
        { name: '平静', count: 40, color: 'var(--info-color)' },
        { name: '其他', count: 22, color: 'var(--danger-color)' }
    ];
    
    const total = emotions.reduce((sum, emotion) => sum + emotion.count, 0);
    
    const chartHTML = `
        <div style="display: flex; flex-direction: column; gap: 12px; padding: 20px;">
            ${emotions.map(emotion => {
                const percentage = ((emotion.count / total) * 100).toFixed(1);
                return `
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="width: 12px; height: 12px; background: ${emotion.color}; border-radius: 2px;"></div>
                        <span style="flex: 1; font-size: 14px; color: var(--text-color);">${emotion.name}</span>
                        <div style="flex: 2; height: 8px; background: var(--border-gray); border-radius: 4px; overflow: hidden;">
                            <div style="width: ${percentage}%; height: 100%; background: ${emotion.color};"></div>
                        </div>
                        <span style="font-size: 14px; font-weight: 600; color: var(--text-color);">${emotion.count}</span>
                    </div>
                `;
            }).join('')}
        </div>
    `;
    
    container.innerHTML = chartHTML;
}

// 渲染热力图
function renderHeatmapChart(container) {
    const hours = ['6-8', '8-10', '10-12', '12-14', '14-16', '16-18', '18-20'];
    const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
    
    const chartHTML = `
        <div style="display: flex; flex-direction: column; gap: 4px; padding: 20px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <div style="width: 60px;"></div>
                ${hours.map(hour => `<div style="flex: 1; text-align: center; font-size: 12px; color: var(--text-color);">${hour}</div>`).join('')}
            </div>
            ${days.map((day, dayIndex) => `
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 60px; font-size: 12px; color: var(--text-color);">${day}</div>
                    ${hours.map((hour, hourIndex) => {
                        const intensity = Math.floor(Math.random() * 3) + 1; // 1-3
                        const colors = ['var(--success-color)', 'var(--warning-color)', 'var(--danger-color)'];
                        return `<div style="flex: 1; height: 20px; background: ${colors[intensity - 1]}; border-radius: 2px; opacity: 0.6;"></div>`;
                    }).join('')}
                </div>
            `).join('')}
        </div>
    `;
    
    container.innerHTML = chartHTML;
}

// 渲染情绪图表
function renderEmotionChart(viewType) {
    switch(viewType) {
        case 'radar':
            updateRadarChart();
            break;
        case 'trend':
            updateTrendChart();
            break;
        case 'distribution':
            const distributionContainer = document.getElementById('emotionDistributionChart');
            if (distributionContainer) {
                renderDistributionChart(distributionContainer);
            }
            break;
        case 'heatmap':
            const heatmapContainer = document.getElementById('emotionHeatmapChart');
            if (heatmapContainer) {
                renderHeatmapChart(heatmapContainer);
            }
            break;
    }
}

// 更新雷达图
function updateRadarChart() {
    if (!emotionRadarChart) return;
    
    // 模拟数据更新
    const newData = [
        Math.random() * 2 + 3, // 高兴
        Math.random() * 2 + 3, // 平静
        Math.random() * 2 + 1, // 焦虑
        Math.random() * 1.5,   // 愤怒
        Math.random() * 1.5,   // 悲伤
        Math.random() * 2 + 3  // 兴奋
    ];
    
    emotionRadarChart.data.datasets[0].data = newData;
    emotionRadarChart.update();
}

// 更新趋势图
function updateTrendChart() {
    if (!emotionTrendChart) return;
    
    // 模拟数据更新
    const newData = Array.from({ length: 8 }, () => Math.random() * 3 + 2);
    
    emotionTrendChart.data.datasets[0].data = newData;
    emotionTrendChart.update();
}

// 加载情绪数据
function loadEmotionData() {
    // 尝试API调用
    fetch('/api/emotion/data')
        .then(response => {
            if (!response.ok) {
                throw new Error('API not available');
            }
            return response.json();
        })
        .then(data => {
            console.log('情绪数据加载成功:', data);
            updateEmotionData(data);
        })
        .catch(error => {
            console.log('使用模拟情绪数据:', error.message);
            loadMockEmotionData();
        });
}

// 加载模拟情绪数据
function loadMockEmotionData() {
    const mockData = {
        dominantEmotion: '高兴',
        emotionScore: 4.2,
        stability: '良好',
        stabilityChange: 15,
        timeline: [
            { time: '15:30', emotion: '高兴', emoji: '😊' },
            { time: '14:45', emotion: '平静', emoji: '😐' },
            { time: '14:20', emotion: '焦虑', emoji: '😟' },
            { time: '13:55', emotion: '高兴', emoji: '😊' }
        ]
    };
    
    updateEmotionData(mockData);
    updateEmotionTimeline(mockData.timeline);
}

// 更新情绪数据
function updateEmotionData(data) {
    emotionData = {
        dominantEmotion: data.dominantEmotion || '高兴',
        emotionScore: data.emotionScore || 4.2,
        stability: data.stability || '良好',
        stabilityChange: data.stabilityChange || 15
    };
    
    // 更新UI
    const dominantElement = document.querySelector('.emotion-value');
    if (dominantElement) {
        dominantElement.textContent = `${emotionData.dominantEmotion} 😊 (${emotionData.emotionScore}/5)`;
    }
    
    const stabilityElement = document.querySelector('.emotion-value.stable');
    if (stabilityElement) {
        stabilityElement.textContent = `${emotionData.stability} (比昨日${emotionData.stabilityChange > 0 ? '上升' : '下降'}${Math.abs(emotionData.stabilityChange)}%)`;
    }
}

// 更新情绪时间线
function updateEmotionTimeline(timelineData) {
    const timelineContainer = document.querySelector('.emotion-timeline');
    if (!timelineContainer) return;
    
    const timelineHTML = timelineData.map(item => `
        <div class="timeline-item">
            <div class="timeline-time">${item.time}</div>
            <div class="timeline-emotion">
                <div class="timeline-emoji">${item.emoji}</div>
                <div class="timeline-label">${item.emotion}</div>
            </div>
        </div>
    `).join('');
    
    timelineContainer.innerHTML = timelineHTML;
}

// 开始情绪监控
function startEmotionMonitoring() {
    // 模拟实时监控
    setInterval(() => {
        updateRealTimeEmotion();
    }, 10000);
}

// 更新实时情绪
function updateRealTimeEmotion() {
    // 模拟实时数据变化
    const emotions = ['高兴', '平静', '焦虑', '愤怒', '悲伤', '兴奋'];
    const emojis = ['😊', '😐', '😟', '😠', '😢', '🤩'];
    
    const randomIndex = Math.floor(Math.random() * emotions.length);
    const newEmotion = emotions[randomIndex];
    const newEmoji = emojis[randomIndex];
    
    // 更新情绪数据
    emotionData.dominantEmotion = newEmotion;
    emotionData.emotionScore = (Math.random() * 2 + 3).toFixed(1);
    
    // 更新UI
    const dominantElement = document.querySelector('.emotion-value');
    if (dominantElement) {
        dominantElement.textContent = `${emotionData.dominantEmotion} ${newEmoji} (${emotionData.emotionScore}/5)`;
    }
    
    // 检查情绪异常
    checkEmotionAnomaly();
}

// 检查情绪异常
function checkEmotionAnomaly() {
    const score = parseFloat(emotionData.emotionScore);
    
    if (score < 2.0) {
        showEmotionAlert('检测到情绪异常，建议及时关注');
    }
}

// 显示情绪警告
function showEmotionAlert(message) {
    console.log('情绪警告:', message);
    // 这里可以实现警告提示
}

// 发送关怀消息
function sendCareMessage() {
    showToast('正在发送关怀消息...');
    
    // 模拟发送消息
    setTimeout(() => {
        showToast('关怀消息已发送');
    }, 1000);
}

// 查看情绪详情
function viewEmotionDetail() {
    showToast('正在加载情绪详情...');
    
    // 模拟加载详情
    setTimeout(() => {
        showToast('情绪详情加载完成');
    }, 1000);
}

// 获取情绪建议
function getEmotionSuggestions() {
    const suggestions = [
        {
            title: '积极关注',
            text: '多关注孩子的积极情绪，给予正面反馈和鼓励',
            icon: 'bi-heart'
        },
        {
            title: '沟通交流',
            text: '当发现情绪异常时，及时与孩子沟通了解原因',
            icon: 'bi-chat-dots'
        },
        {
            title: '情绪调节',
            text: '引导孩子学习情绪调节技巧，如深呼吸、运动等',
            icon: 'bi-activity'
        }
    ];
    
    return suggestions;
}

// 导出情绪报告
function exportEmotionReport() {
    showToast('正在生成情绪报告...');
    
    // 模拟导出功能
    setTimeout(() => {
        const report = {
            date: new Date().toLocaleDateString(),
            data: emotionData,
            suggestions: getEmotionSuggestions()
        };
        
        console.log('情绪报告:', report);
        showToast('情绪报告导出成功');
    }, 2000);
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
    if (emotionRadarChart) {
        emotionRadarChart.destroy();
    }
    if (emotionTrendChart) {
        emotionTrendChart.destroy();
    }
    console.log('情绪识别工具卸载');
});

// 导出函数供其他模块使用
window.emotionModule = {
    switchEmotionView,
    loadEmotionData,
    updateEmotionData,
    sendCareMessage,
    viewEmotionDetail,
    exportEmotionReport,
    showToast
}; 