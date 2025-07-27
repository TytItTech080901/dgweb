// mobile.js - 移动端专用脚本文件
document.addEventListener('DOMContentLoaded', function() {
    // 初始化移动端应用
    initMobileApp();
    
    // 注册导航切换事件
    setupNavigation();
    
    // 注册工具点击事件
    setupToolEvents();
    
    // 注册控制按钮事件
    setupControlEvents();
    
    // 图表切换器将在显示坐姿检测工具时初始化
});

// 移动端应用初始化
function initMobileApp() {
    console.log('移动端应用初始化...');
    
    // 显示默认的首页
    showPage('home');
    
    // 获取分析系统状态并更新UI
    fetchAnalysisStatus();
    
    // 定时更新状态
    setInterval(function() {
        fetchAnalysisStatus();
        updateMockData();
    }, 3000);
    
    // 初始化模拟数据
    updateMockData();
    
    // 初始化首页图表
    setTimeout(() => {
        initCharts();
    }, 1000);
}

// 设置导航切换
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 获取目标页面ID
            const targetPage = this.getAttribute('data-page');
            
            // 切换页面显示
            showPage(targetPage);
            
            // 更新导航激活状态
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

// 设置工具事件
function setupToolEvents() {
    // 工具项点击事件
    document.querySelectorAll('.tool-item').forEach(item => {
        item.addEventListener('click', function() {
            const tool = this.getAttribute('data-tool');
            showToolDetail(tool);
        });
    });
    
    // 返回按钮事件
    const backBtn = document.querySelector('.back-btn');
    if (backBtn) {
        backBtn.addEventListener('click', function() {
            showPage('home');
            // 重新激活首页导航
            document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
            document.querySelector('[data-page="home"]').classList.add('active');
        });
    }
}

// 设置控制事件
function setupControlEvents() {
    // 快速操作按钮
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            handleQuickAction(action);
        });
    });
    
    // 台灯控制按钮
    document.querySelectorAll('.control-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            handleLampControl(action);
        });
    });
    
    // 模式按钮
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const mode = this.getAttribute('data-mode');
            handleModeChange(mode);
            
            // 更新按钮状态
            document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // 滑块事件
    const brightnessSlider = document.getElementById('brightnessSlider');
    const brightnessValue = document.getElementById('brightnessValue');
    if (brightnessSlider && brightnessValue) {
        brightnessSlider.addEventListener('input', function() {
            brightnessValue.textContent = this.value;
            // 实时调节亮度
            handleLampControl('brightness', this.value);
        });
    }
    
    // 色温滑块
    const temperatureSlider = document.getElementById('temperatureSlider');
    if (temperatureSlider) {
        temperatureSlider.addEventListener('input', function() {
            handleLampControl('temperature', this.value);
        });
    }
    
    // 定时器开关
    document.querySelectorAll('.timer-toggle').forEach(toggle => {
        toggle.addEventListener('click', function() {
            const timer = this.getAttribute('data-timer');
            const isActive = this.classList.contains('active');
            
            this.classList.toggle('active');
            const icon = this.querySelector('i');
            
            if (this.classList.contains('active')) {
                icon.className = 'bi bi-toggle-on';
                showToast(`${timer}定时已开启`);
            } else {
                icon.className = 'bi bi-toggle-off';
                showToast(`${timer}定时已关闭`);
            }
        });
    });
    
    // 设置开关
    document.querySelectorAll('.setting-toggle').forEach(toggle => {
        toggle.addEventListener('click', function() {
            const setting = this.getAttribute('data-setting');
            
            this.classList.toggle('active');
            const icon = this.querySelector('i');
            
            if (this.classList.contains('active')) {
                icon.className = 'bi bi-toggle-on';
                showToast(`${setting}通知已开启`);
            } else {
                icon.className = 'bi bi-toggle-off';
                showToast(`${setting}通知已关闭`);
            }
        });
    });
    
    // 消息发送
    const sendMessageBtn = document.getElementById('sendMessage');
    if (sendMessageBtn) {
        sendMessageBtn.addEventListener('click', function() {
            const messageContent = document.getElementById('messageContent').value;
            const messageType = document.getElementById('messageType').value;
            
            if (messageContent.trim()) {
                sendMessage(messageContent, messageType);
                document.getElementById('messageContent').value = '';
            } else {
                showToast('请输入消息内容');
            }
        });
    }
    
    // 视频控制按钮
    const pauseVideoBtn = document.getElementById('pauseVideo');
    if (pauseVideoBtn) {
        pauseVideoBtn.addEventListener('click', function() {
            const icon = this.querySelector('i');
            if (icon.classList.contains('bi-pause')) {
                icon.className = 'bi bi-play';
                showToast('视频已暂停');
            } else {
                icon.className = 'bi bi-pause';
                showToast('视频已恢复');
            }
        });
    }
    
    // 拍照按钮
    const captureBtn = document.getElementById('captureBtn');
    if (captureBtn) {
        captureBtn.addEventListener('click', function() {
            showToast('照片已保存');
        });
    }
    
    // 全屏按钮
    const fullscreenBtn = document.getElementById('fullscreenBtn');
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', function() {
            showToast('已进入全屏模式');
        });
    }
}

// 显示指定页面，隐藏其他页面
function showPage(pageId) {
    const pages = document.querySelectorAll('.mobile-page');
    const header = document.querySelector('header');
    
    pages.forEach(page => {
        if (page.id === pageId) {
            page.style.display = 'block';
        } else {
            page.style.display = 'none';
        }
    });
    
    // 控制header显示：只有工具详情页隐藏header
    if (header) {
        if (pageId === 'tool-detail') {
            header.style.display = 'none';
        } else {
            header.style.display = 'block';
        }
    }
    
    // 页面切换后的特殊处理
    switch(pageId) {
        case 'home':
            fetchLatestData();
            break;
        case 'guardian':
            refreshGuardianData();
            break;
        case 'remote':
            fetchLampStatus();
            break;
        case 'settings':
            // 设置页面无需特殊处理
            break;
    }
}

// 显示工具详情
function showToolDetail(tool) {
    const toolDetailPage = document.getElementById('tool-detail');
    const toolTitle = document.getElementById('toolTitle');
    
    // 隐藏所有工具内容
    document.querySelectorAll('.tool-content').forEach(content => {
        content.style.display = 'none';
    });
    
    // 显示对应的工具内容
    let title = '';
    switch(tool) {
        case 'posture':
            title = '坐姿检测';
            document.getElementById('posture-content').style.display = 'block';
            // 图表已在HTML中直接初始化，只需要刷新显示
            setTimeout(() => {
                // 重置图表切换状态
                currentChartIndex = 0;
                
                // 初始化图表切换功能
                setupChartSwiper();
                
                // 确保第一个幻灯片显示
                const slides = document.querySelectorAll('.chart-slide');
                const indicators = document.querySelectorAll('.indicator-dot');
                slides.forEach((slide, index) => {
                    slide.classList.toggle('active', index === 0);
                });
                indicators.forEach((dot, index) => {
                    dot.classList.toggle('active', index === 0);
                });
                
                // 刷新图表显示
                if (window.posturePieChart) {
                    console.log('刷新坐姿饼图显示...');
                    window.posturePieChart.resize();
                    window.posturePieChart.update();
                }
                
                // 加载默认时间范围数据
                loadPostureData('day');
                loadPostureImages('day');
            }, 100);
            break;
        case 'eye':
            title = '用眼情况';
            document.getElementById('eye-content').style.display = 'block';
            // 图表已在HTML中直接初始化，只需要刷新显示
            setTimeout(() => {
                updateEyeMetrics();
                
                // 刷新热力图显示
                if (window.eyeHeatmapChart) {
                    console.log('刷新用眼热力图显示...');
                    window.eyeHeatmapChart.resize();
                }
            }, 100);
            break;
        case 'emotion':
            title = '情绪反馈';
            document.getElementById('emotion-content').style.display = 'block';
            // 图表已在HTML中直接初始化，只需要刷新显示
            setTimeout(() => {
                // 刷新当前活跃的情绪图表
                const activeView = document.querySelector('.emotion-chart-view.active');
                if (activeView) {
                    const viewId = activeView.id;
                    if (viewId.includes('radar') && window.emotionRadarChart) {
                        window.emotionRadarChart.resize();
                    } else if (viewId.includes('trend') && window.emotionTrendChart) {
                        window.emotionTrendChart.resize();
                    } else if (viewId.includes('distribution') && window.emotionDistributionChart) {
                        window.emotionDistributionChart.resize();
                    } else if (viewId.includes('heatmap') && window.emotionHeatmapChart) {
                        window.emotionHeatmapChart.resize();
                    }
                }
            }, 100);
            break;
    }
    
    toolTitle.textContent = title;
    showPage('tool-detail');
}

// 处理快速操作
function handleQuickAction(action) {
    switch(action) {
        case 'lamp_on':
            handleLampControl('on');
            break;
        case 'lamp_off':
            handleLampControl('off');
            break;
        case 'start_analysis':
            togglePostureAnalysis();
            break;
        case 'take_photo':
            takePhoto();
            break;
    }
}

// 处理台灯控制
function handleLampControl(action, value = null) {
    let endpoint = '';
    let message = '';
    
    switch(action) {
        case 'lamp_on':
        case 'on':
            endpoint = '/lamp_control/on';
            message = '台灯已开启';
            break;
        case 'lamp_off':
        case 'off':
            endpoint = '/lamp_control/off';
            message = '台灯已关闭';
            break;
        case 'brightness_up':
            endpoint = '/lamp_control/brighter';
            message = '亮度已调高';
            break;
        case 'brightness_down':
            endpoint = '/lamp_control/dimmer';
            message = '亮度已调低';
            break;
        case 'brightness':
            endpoint = `/lamp_control/brightness/${value}`;
            message = `亮度已调至${value}%`;
            break;
        case 'temperature':
            endpoint = `/lamp_control/temperature/${value}`;
            message = '色温已调节';
            break;
        default:
            endpoint = `/lamp_control/${action}`;
            message = '操作完成';
    }
    
    fetch(endpoint)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showToast(message);
                // 更新台灯状态显示
                setTimeout(fetchLampStatus, 500);
            } else {
                showToast('操作失败: ' + (data.message || '未知错误'));
            }
        })
        .catch(error => {
            console.error('台灯控制失败:', error);
            showToast('网络连接失败');
        });
}

// 处理模式切换
function handleModeChange(mode) {
    const modeNames = {
        'reading': '阅读模式',
        'study': '学习模式',
        'rest': '休息模式',
        'night': '夜灯模式'
    };
    
    fetch(`/lamp_control/mode/${mode}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showToast(`已切换至${modeNames[mode]}`);
            } else {
                showToast('模式切换失败');
            }
        })
        .catch(error => {
            console.error('模式切换失败:', error);
            showToast('网络连接失败');
        });
}

// 切换姿势分析
function togglePostureAnalysis() {
    const btn = document.querySelector('[data-action="start_analysis"]');
    const isRunning = btn.textContent.includes('停止');
    
    const endpoint = isRunning ? '/stop_pose_analysis' : '/start_pose_analysis';
    
    fetch(endpoint)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                btn.innerHTML = isRunning ? 
                    '<i class="bi bi-play-circle"></i><span>开始分析</span>' : 
                    '<i class="bi bi-stop-circle"></i><span>停止分析</span>';
                
                showToast(isRunning ? '分析已停止' : '分析已开始');
                
                // 刷新状态显示
                setTimeout(fetchAnalysisStatus, 500);
            }
        })
        .catch(error => {
            console.error('控制操作失败:', error);
            showToast('操作失败，请重试');
        });
}

// 拍照功能
function takePhoto() {
    fetch('/capture_photo')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showToast('照片已保存');
            } else {
                showToast('拍照失败');
            }
        })
        .catch(error => {
            console.error('拍照失败:', error);
            showToast('拍照失败');
        });
}

// 发送消息
function sendMessage(content, type) {
    const messageData = {
        content: content,
        type: type,
        timestamp: Date.now()
    };
    
    fetch('/send_message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(messageData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showToast(type === 'immediate' ? '消息已发送' : '定时消息已设置');
                addMessageToHistory(content, type);
            } else {
                showToast('发送失败');
            }
        })
        .catch(error => {
            console.error('发送消息失败:', error);
            showToast('网络连接失败');
        });
}

// 添加消息到历史记录
function addMessageToHistory(content, type) {
    const messageHistory = document.getElementById('messageHistory');
    if (!messageHistory) return;
    
    const messageItem = document.createElement('div');
    messageItem.className = `message-item ${type === 'scheduled' ? 'scheduled' : 'sent'}`;
    
    const now = new Date();
    const timeStr = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    
    messageItem.innerHTML = `
        <div class="message-sender">
            <i class="bi bi-${type === 'scheduled' ? 'clock' : 'person-check'}"></i>
            ${type === 'scheduled' ? '定时消息' : '家长'}
        </div>
        <div class="message-content">${content}</div>
        <div class="message-time">${timeStr}${type === 'scheduled' ? ' (预定)' : ''}</div>
    `;
    
    messageHistory.insertBefore(messageItem, messageHistory.firstChild);
}

// 获取分析系统状态
function fetchAnalysisStatus() {
    fetch('/get_pose_status')
        .then(response => response.json())
        .then(data => {
            updateSystemStatus(data);
        })
        .catch(error => {
            console.error('获取系统状态失败:', error);
            updateSystemStatusError();
        });
}

// 更新系统状态显示
function updateSystemStatus(data) {
    const statusIndicator = document.querySelector('.status-indicator');
    if (!statusIndicator) return;
    
    const statusText = statusIndicator.querySelector('.status-text');
    
    // 根据状态更新UI
    if (data.status === 'success') {
        if (data.is_running) {
            statusIndicator.className = 'status-indicator status-running';
            statusText.textContent = '运行中';
        } else {
            statusIndicator.className = 'status-indicator status-paused';
            statusText.textContent = '已暂停';
        }
    } else {
        updateSystemStatusError();
    }
}

// 更新系统状态为错误
function updateSystemStatusError() {
    const statusIndicator = document.querySelector('.status-indicator');
    if (statusIndicator) {
        statusIndicator.className = 'status-indicator status-error';
        const statusText = statusIndicator.querySelector('.status-text');
        if (statusText) {
            statusText.textContent = '连接错误';
        }
    }
}

// 获取台灯状态
function fetchLampStatus() {
    fetch('/lamp_status')
        .then(response => response.json())
        .then(data => {
            updateLampStatus(data);
        })
        .catch(error => {
            console.error('获取台灯状态失败:', error);
        });
}

// 更新台灯状态显示
function updateLampStatus(data) {
    if (data.status === 'success') {
        const lampStatus = document.getElementById('lampStatus');
        if (lampStatus) {
            lampStatus.textContent = data.is_on ? '已开启' : '已关闭';
            lampStatus.parentElement.className = data.is_on ? 
                'status-indicator status-running' : 
                'status-indicator status-paused';
        }
        
        // 更新亮度滑块
        const brightnessSlider = document.getElementById('brightnessSlider');
        const brightnessValue = document.getElementById('brightnessValue');
        if (brightnessSlider && data.brightness !== undefined) {
            brightnessSlider.value = data.brightness;
            if (brightnessValue) {
                brightnessValue.textContent = data.brightness;
            }
        }
    }
}

// 刷新监护数据
function refreshGuardianData() {
    // 刷新视频流
    const guardianVideo = document.getElementById('guardianVideo');
    if (guardianVideo) {
        guardianVideo.src = '/video_feed?t=' + new Date().getTime();
    }
    
    // 可以在这里添加其他监护数据的刷新逻辑
}

// 获取最新数据
function fetchLatestData() {
    // 获取姿势统计数据
    fetch('/get_posture_stats')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updatePostureStats(data.stats);
            }
        })
        .catch(error => {
            console.error('获取姿势统计失败:', error);
        });
}

// 更新姿势统计
function updatePostureStats(stats) {
    // 更新图表数据
    if (window.postureChart && stats) {
        window.postureChart.data.datasets[0].data = [
            stats.correct || 0,
            stats.head_down || 0,
            stats.leaning_forward || 0,
            stats.leaning_side || 0,
            stats.other || 0
        ];
        window.postureChart.update();
    }
}

// 更新模拟数据
function updateMockData() {
    // 更新首页概览数据
    const studyTime = document.getElementById('studyTime');
    const postureScore = document.getElementById('postureScore');
    const eyeRest = document.getElementById('eyeRest');
    
    if (studyTime) {
        const hours = (Math.random() * 3 + 3).toFixed(1);
        studyTime.textContent = hours + 'h';
    }
    
    if (postureScore) {
        const score = Math.floor(Math.random() * 25 + 70);
        postureScore.textContent = score + '%';
    }
    
    if (eyeRest) {
        const rest = Math.floor(Math.random() * 8 + 10);
        eyeRest.textContent = rest;
    }
}

// 初始化图表
function initCharts() {
    initPostureChart();
    initEmotionCharts();
    // 注意：其他图表（posturePieChart, scoreTrendChart, heatmapChart）
    // 将在显示坐姿检测工具时按需初始化
}

// 初始化姿势检测图表
function initPostureChart() {
    const postureCtx = document.getElementById('postureChart');
    if (!postureCtx) return;
    
    const ctx = postureCtx.getContext('2d');
    window.postureChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['正确姿势', '低头', '前倾', '侧倾', '其他'],
            datasets: [{
                data: [75, 15, 8, 2, 0],
                backgroundColor: [
                    '#34a853',
                    '#fbbc05',
                    '#ea4335',
                    '#4285f4',
                    '#9aa0a6'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 15,
                        font: {
                            size: 11
                        }
                    }
                }
            }
        }
    });
}

// 初始化情绪图表（多视图）
function initEmotionCharts() {
    initEmotionRadarChart();
    initEmotionTrendChart();
    initEmotionDistributionChart();
    initEmotionHeatmapChart();
    
    // 绑定视图切换事件
    const viewSelect = document.getElementById('emotionViewSelect');
    if (viewSelect) {
        viewSelect.addEventListener('change', function() {
            switchEmotionView(this.value);
        });
    }
}

// 初始化情绪雷达图
function initEmotionRadarChart() {
    const emotionCtx = document.getElementById('emotionRadarChart');
    if (!emotionCtx) return;
    
    // 如果已经初始化过，先销毁
    if (window.emotionRadarChart) {
        window.emotionRadarChart.dispose();
    }
    
    const chart = echarts.init(emotionCtx);
    window.emotionRadarChart = chart; // 保存到全局变量
    
    const option = {
        radar: {
            indicator: [
                { name: '开心', max: 100 },
                { name: '专注', max: 100 },
                { name: '平静', max: 100 },
                { name: '焦虑', max: 100 },
                { name: '疲惫', max: 100 },
                { name: '兴奋', max: 100 }
            ],
            radius: 80,
            splitNumber: 4,
            axisLine: {
                lineStyle: {
                    color: '#ddd'
                }
            },
            splitLine: {
                lineStyle: {
                    color: '#ddd'
                }
            }
        },
        series: [{
            name: '情绪状态',
            type: 'radar',
            data: [{
                value: [85, 70, 75, 15, 25, 60],
                name: '当前状态',
                itemStyle: {
                    color: '#2196f3'
                },
                areaStyle: {
                    opacity: 0.3,
                    color: '#2196f3'
                }
            }]
        }]
    };
    chart.setOption(option);
    
    console.log('情绪雷达图初始化完成');
}

// 初始化情绪趋势图
function initEmotionTrendChart() {
    const ctx = document.getElementById('emotionTrendChart');
    if (!ctx) return;
    
    // 如果已经初始化过，先销毁
    if (window.emotionTrendChart) {
        window.emotionTrendChart.destroy();
    }
    
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'],
            datasets: [{
                label: '积极情绪',
                data: [75, 80, 70, 85, 60, 90, 65, 85],
                borderColor: '#4caf50',
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: '消极情绪', 
                data: [20, 15, 25, 10, 35, 8, 30, 12],
                borderColor: '#f44336',
                backgroundColor: 'rgba(244, 67, 54, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 25
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top'
                }
            }
        }
    });
    
    window.emotionTrendChart = chart;
    console.log('情绪趋势图初始化完成');
}

// 初始化情绪分布图
function initEmotionDistributionChart() {
    const ctx = document.getElementById('emotionDistributionChart');
    if (!ctx) return;
    
    // 如果已经初始化过，先销毁
    if (window.emotionDistributionChart) {
        window.emotionDistributionChart.destroy();
    }
    
    const chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['积极情绪', '中性情绪', '消极情绪'],
            datasets: [{
                data: [65, 25, 10],
                backgroundColor: [
                    '#4caf50',
                    '#ff9800', 
                    '#f44336'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
    
    window.emotionDistributionChart = chart;
    console.log('情绪分布图初始化完成');
}

// 初始化情绪热力图
function initEmotionHeatmapChart() {
    const container = document.getElementById('emotionHeatmapChart');
    if (!container) return;
    
    // 如果已经初始化过，先销毁
    if (window.emotionHeatmapChart) {
        window.emotionHeatmapChart.dispose();
    }
    
    const chart = echarts.init(container);
    window.emotionHeatmapChart = chart;
    
    // 生成模拟数据
    const hours = ['9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'];
    const emotions = ['开心', '专注', '平静', '焦虑', '疲惫'];
    const data = [];
    
    for (let i = 0; i < hours.length; i++) {
        for (let j = 0; j < emotions.length; j++) {
            data.push([i, j, Math.round(Math.random() * 100)]);
        }
    }
    
    const option = {
        tooltip: {
            position: 'top',
            formatter: function(params) {
                return `${hours[params.data[0]]} - ${emotions[params.data[1]]}: ${params.data[2]}%`;
            }
        },
        grid: {
            height: '60%',
            top: '10%',
            left: '20%'
        },
        xAxis: {
            type: 'category',
            data: hours,
            splitArea: {
                show: true
            }
        },
        yAxis: {
            type: 'category',
            data: emotions,
            splitArea: {
                show: true
            }
        },
        visualMap: {
            min: 0,
            max: 100,
            calculable: true,
            orient: 'horizontal',
            left: 'center',
            bottom: '5%',
            inRange: {
                color: ['#e8f5e8', '#ffeb3b', '#ff5722']
            }
        },
        series: [{
            name: '情绪强度',
            type: 'heatmap',
            data: data,
            label: {
                show: false
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    };
    
    chart.setOption(option);
    console.log('情绪热力图初始化完成');
}

// 切换情绪视图
function switchEmotionView(viewType) {
    // 隐藏所有视图
    const allViews = document.querySelectorAll('.emotion-chart-view');
    allViews.forEach(view => {
        view.classList.remove('active');
    });
    
    // 显示选定的视图
    const targetView = document.getElementById(`emotion-${viewType}-view`);
    if (targetView) {
        targetView.classList.add('active');
        
        // 根据视图类型触发图表重绘
        setTimeout(() => {
            switch(viewType) {
                case 'radar':
                    if (window.emotionRadarChart) {
                        window.emotionRadarChart.resize();
                    }
                    break;
                case 'trend':
                    if (window.emotionTrendChart) {
                        window.emotionTrendChart.resize();
                    }
                    break;
                case 'distribution':
                    if (window.emotionDistributionChart) {
                        window.emotionDistributionChart.resize();
                    }
                    break;
                case 'heatmap':
                    if (window.emotionHeatmapChart) {
                        window.emotionHeatmapChart.resize();
                    }
                    break;
            }
        }, 100);
    }
}

// 初始化坐姿时间占比饼图
function initPosturePieChart() {
    const ctx = document.getElementById('posturePieChart');
    if (!ctx) {
        console.warn('坐姿饼图容器元素未找到');
        return;
    }
    
    console.log('坐姿饼图容器状态:', {
        offsetWidth: ctx.offsetWidth,
        offsetHeight: ctx.offsetHeight,
        clientWidth: ctx.clientWidth,
        clientHeight: ctx.clientHeight
    });
    
    // 强制设置canvas尺寸
    ctx.style.width = '100%';
    ctx.style.height = '250px';
    ctx.width = ctx.offsetWidth || 300;
    ctx.height = 250;
    
    // 如果已经初始化过，先销毁
    if (window.posturePieChart) {
        window.posturePieChart.destroy();
    }
    
    console.log('开始初始化坐姿饼图...');
    window.posturePieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['良好坐姿', '轻度不良坐姿', '不良坐姿'],
            datasets: [{
                data: [50, 30, 20],
                backgroundColor: [
                    '#34a853',   // 绿色 - 良好坐姿
                    '#fbbc05',   // 黄色 - 轻度不良坐姿
                    '#ea4335'    // 红色 - 不良坐姿
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                }
            }
        }
    });
    
    console.log('坐姿时间占比饼图初始化完成');
}

// 初始化坐姿评分趋势图
function initScoreTrendChart() {
    const ctx = document.getElementById('scoreTrendChart');
    if (!ctx) return;
    
    window.scoreTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
            datasets: [{
                label: '坐姿评分',
                data: [70, 72, 68, 75, 73, 76, 64],
                borderColor: '#4285f4',
                backgroundColor: 'rgba(66, 133, 244, 0.1)',
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#4285f4',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        font: {
                            size: 10
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 10
                        }
                    }
                }
            }
        }
    });
}

// 初始化不良姿态时段分布热力图
function initHeatmapChart() {
    const ctx = document.getElementById('heatmapChart');
    if (!ctx) return;
    
    // 生成热力图数据
    const data = [];
    const hours = ['6', '8', '10', '12', '14', '16', '18', '20', '22'];
    const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
    
    days.forEach((day, dayIndex) => {
        hours.forEach((hour, hourIndex) => {
            const value = Math.random() * 100;
            data.push({
                x: hourIndex,
                y: dayIndex,
                v: value
            });
        });
    });
    
    window.heatmapChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: '不良坐姿率',
                data: data,
                backgroundColor: function(context) {
                    const value = context.parsed.v;
                    if (value < 30) return 'rgba(52, 168, 83, 0.8)';
                    if (value < 60) return 'rgba(251, 188, 5, 0.8)';
                    return 'rgba(234, 67, 53, 0.8)';
                },
                pointRadius: function(context) {
                    return Math.max(4, context.parsed.v / 10);
                }
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const dayIndex = context[0].parsed.y;
                            const hourIndex = context[0].parsed.x;
                            return `${days[dayIndex]} ${hours[hourIndex]}:00`;
                        },
                        label: function(context) {
                            return `不良坐姿率: ${Math.round(context.parsed.v)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    min: 0,
                    max: hours.length - 1,
                    ticks: {
                        stepSize: 1,
                        callback: function(value, index, values) {
                            return hours[value] || '';
                        },
                        font: {
                            size: 10
                        }
                    },
                    title: {
                        display: true,
                        text: '时间',
                        font: {
                            size: 11
                        }
                    }
                },
                y: {
                    type: 'linear',
                    min: 0,
                    max: days.length - 1,
                    ticks: {
                        stepSize: 1,
                        callback: function(value, index, values) {
                            return days[value] || '';
                        },
                        font: {
                            size: 10
                        }
                    },
                    title: {
                        display: true,
                        text: '日期',
                        font: {
                            size: 11
                        }
                    }
                }
            }
        }
    });
}

// 初始化用眼时间热力图（使用ECharts，与网页端保持一致）
function initEyeHeatmapChart() {
    const chartElement = document.getElementById('eyeHeatmapChart');
    if (!chartElement) {
        console.warn('热力图容器元素未找到');
        return;
    }
    
    console.log('热力图容器状态:', {
        offsetWidth: chartElement.offsetWidth,
        offsetHeight: chartElement.offsetHeight,
        clientWidth: chartElement.clientWidth,
        clientHeight: chartElement.clientHeight
    });
    
    // 强制设置容器尺寸
    chartElement.style.width = '100%';
    chartElement.style.height = '300px';
    
    // 如果已经初始化过，先销毁
    if (window.eyeHeatmapChart) {
        window.eyeHeatmapChart.dispose();
    }
    
    console.log('开始初始化用眼时间热力图...');
    
    // 初始化ECharts实例
    const heatmapChart = echarts.init(chartElement);
    window.eyeHeatmapChart = heatmapChart;
    
    // 生成热力图数据 - 与网页端一致
    const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`);
    const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
    const data = [];
    
    for (let i = 0; i < days.length; i++) {
        for (let j = 0; j < hours.length; j++) {
            // 模拟用眼强度数据，与网页端逻辑保持一致
            let value;
            if (j >= 8 && j <= 11) {
                value = Math.floor(Math.random() * 2) + 1; // 上午学习时间
            } else if (j >= 14 && j <= 17) {
                value = Math.floor(Math.random() * 2) + 1; // 下午学习时间
            } else if (j >= 19 && j <= 21) {
                value = Math.floor(Math.random() * 2) + 1; // 晚上学习时间
            } else {
                value = Math.floor(Math.random() * 1); // 其他时间
            }
            data.push([j, i, value]); // x, y, value
        }
    }
    
    // 设置ECharts配置，与网页端保持一致
    heatmapChart.setOption({
        tooltip: {
            position: 'top',
            formatter: function (params) {
                return days[params.data[1]] + ' ' + hours[params.data[0]] + '<br/>用眼强度: ' + params.data[2];
            }
        },
        grid: {
            height: '70%',
            top: '10%',
            left: '10%',
            right: '10%'
        },
        xAxis: {
            type: 'category',
            data: hours,
            splitArea: { show: true },
            axisLabel: { 
                rotate: 45,
                fontSize: 10
            }
        },
        yAxis: {
            type: 'category',
            data: days,
            splitArea: { show: true },
            axisLabel: {
                fontSize: 10
            }
        },
        visualMap: {
            min: 0,
            max: 2,
            calculable: true,
            orient: 'horizontal',
            left: 'center',
            bottom: '0',
            inRange: {
                color: ['#e0f7fa', '#ffecb3', '#ff8a65']
            },
            textStyle: {
                fontSize: 10
            }
        },
        series: [{
            name: '用眼强度',
            type: 'heatmap',
            data: data,
            label: {
                show: false
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    });
    
    // 强制刷新图表尺寸
    setTimeout(() => {
        heatmapChart.resize();
        console.log('热力图resize完成');
    }, 100);
    
    // 响应式调整
    const resizeHandler = function () {
        if (window.eyeHeatmapChart) {
            window.eyeHeatmapChart.resize();
        }
    };
    
    window.removeEventListener('resize', resizeHandler);
    window.addEventListener('resize', resizeHandler);
    
    console.log('用眼时间热力图初始化完成');
}

// 更新用眼指标数据
function updateEyeMetrics() {
    // 模拟动态更新用眼指标
    const metrics = [
        { id: 'continuous-time', value: (Math.random() * 2 + 1.5).toFixed(1) + '小时' },
        { id: 'blink-rate', value: Math.floor(Math.random() * 10 + 12) + '次/分钟' },
        { id: 'eye-distance', value: Math.floor(Math.random() * 15 + 40) + 'cm' }
    ];
    
    // 更新页面显示的数据
    const continuousTimeElement = document.querySelector('#eye-content .metric-value');
    if (continuousTimeElement) {
        continuousTimeElement.textContent = metrics[0].value;
    }
    
    const blinkRateElement = document.querySelectorAll('#eye-content .metric-value')[1];
    if (blinkRateElement) {
        blinkRateElement.textContent = metrics[1].value;
    }
    
    const eyeDistanceElement = document.querySelectorAll('#eye-content .metric-value')[2];
    if (eyeDistanceElement) {
        eyeDistanceElement.textContent = metrics[2].value;
    }
    
    console.log('用眼指标已更新:', metrics);
}

// 显示提示消息
function showToast(message) {
    // 检查是否已存在toast元素
    let toast = document.getElementById('mobile-toast');
    
    if (!toast) {
        // 创建toast元素
        toast = document.createElement('div');
        toast.id = 'mobile-toast';
        toast.className = 'mobile-toast';
        document.body.appendChild(toast);
    }
    
    // 设置消息并显示
    toast.textContent = message;
    toast.classList.add('show');
    
    // 2.5秒后隐藏
    setTimeout(() => {
        toast.classList.remove('show');
    }, 2500);
}

// 时间范围切换函数
function changeTimeRange(range) {
    console.log('切换时间范围:', range);
    
    // 更新按钮状态
    const buttons = document.querySelectorAll('.time-range-btn');
    buttons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-range') === range) {
            btn.classList.add('active');
        }
    });
    
    // 重新加载数据和图表
    loadPostureData(range);
    updateChartsByTimeRange(range);
    updatePostureStats(range);
    loadPostureImages(range);
}

// 根据时间范围加载坐姿数据
function loadPostureData(range = 'day') {
    console.log('加载坐姿数据，时间范围:', range);
    
    // 这里可以添加实际的API调用
    // 模拟不同时间范围的数据
    let mockData = getMockDataByRange(range);
    
    // 更新统计数据
    document.getElementById('goodPostureTime').textContent = mockData.goodTime;
    const mildBadElement = document.getElementById('mildBadPostureTime');
    if (mildBadElement) {
        mildBadElement.textContent = mockData.mildBadTime;
    }
    document.getElementById('badPostureTime').textContent = mockData.badTime;
    document.getElementById('postureRate').textContent = mockData.rate;
}

// 根据时间范围获取模拟数据
function getMockDataByRange(range) {
    const mockData = {
        'day': {
            goodTime: '3.2h',
            mildBadTime: '1.2h',
            badTime: '0.6h',
            rate: '64%',
            chartData: [50, 30, 20],  // [良好, 轻度不良, 不良]
            trendData: [70, 72, 68, 75, 73, 76, 64]
        },
        'week': {
            goodTime: '22.4h', 
            mildBadTime: '8.4h',
            badTime: '4.2h',
            rate: '64%',
            chartData: [52, 28, 20],
            trendData: [62, 65, 68, 70, 72, 69, 64]
        },
        'month': {
            goodTime: '96h',
            mildBadTime: '36h',
            badTime: '18h', 
            rate: '64%',
            chartData: [55, 25, 20],
            trendData: [58, 60, 62, 65, 68, 66, 64]
        }
    };
    
    return mockData[range] || mockData['day'];
}

// 根据时间范围更新图表
function updateChartsByTimeRange(range) {
    const mockData = getMockDataByRange(range);
    
    // 更新饼图
    if (window.posturePieChart) {
        window.posturePieChart.data.datasets[0].data = mockData.chartData;
        window.posturePieChart.update();
    }
    
    // 更新趋势图
    if (window.scoreTrendChart) {
        window.scoreTrendChart.data.datasets[0].data = mockData.trendData;
        window.scoreTrendChart.update();
    }
    
    // 更新热力图
    if (window.heatmapChart) {
        updateHeatmapData(range);
    }
}

// 更新热力图数据
function updateHeatmapData(range) {
    // 模拟不同时间范围的热力图数据
    const heatmapData = generateHeatmapData(range);
    
    if (window.heatmapChart) {
        window.heatmapChart.data.datasets[0].data = heatmapData;
        window.heatmapChart.update();
    }
}

// 生成热力图数据
function generateHeatmapData(range) {
    const data = [];
    const hours = range === 'day' ? 24 : (range === 'week' ? 7 * 24 : 30 * 24);
    
    for (let i = 0; i < hours; i++) {
        data.push({
            x: i % 24,
            y: Math.floor(i / 24),
            v: Math.random() * 100
        });
    }
    
    return data;
}

// 更新坐姿统计信息
function updatePostureStats(range) {
    // 根据时间范围更新改善建议
    const suggestions = {
        'day': '今日下午3-5点时段坐姿不良率较高，建议适当休息。',
        'week': '本周坐姿改善效果明显，请继续保持良好习惯。',
        'month': '本月整体表现良好，建议加强下午时段的监督。'
    };
    
    const suggestionText = document.querySelector('.suggestion-text');
    if (suggestionText) {
        suggestionText.textContent = suggestions[range] || suggestions['day'];
    }
}

// 加载坐姿图像记录
function loadPostureImages(range = 'day') {
    console.log('加载坐姿图像记录，时间范围:', range);
    
    const container = document.getElementById('posture-images-container');
    if (!container) return;
    
    // 显示加载状态
    container.innerHTML = `
        <div class="loading-indicator">
            <i class="bi bi-arrow-clockwise"></i>
            <span>加载中...</span>
        </div>
    `;
    
    // 模拟异步加载
    setTimeout(() => {
        const mockImages = generateMockImages(range);
        displayPostureImages(container, mockImages);
    }, 1000);
}

// 生成模拟图像数据
function generateMockImages(range) {
    const imageCount = range === 'day' ? 6 : (range === 'week' ? 12 : 18);
    const images = [];
    
    for (let i = 0; i < imageCount; i++) {
        images.push({
            src: '/static/placeholder.jpg',
            time: `${14 + Math.floor(i / 3)}:${(i % 3) * 20}`,
            status: Math.random() > 0.7 ? 'bad' : 'good'
        });
    }
    
    return images;
}

// 显示坐姿图像
function displayPostureImages(container, images) {
    if (images.length === 0) {
        container.innerHTML = `
            <div class="loading-indicator">
                <i class="bi bi-image"></i>
                <span>暂无图像记录</span>
            </div>
        `;
        return;
    }
    
    const imageGrid = images.map(image => `
        <div class="posture-image-item" onclick="showImageDetail('${image.src}', '${image.time}')">
            <img src="${image.src}" alt="坐姿记录">
            <div class="posture-image-overlay">
                <span>${image.time}</span>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = imageGrid;
}

// 显示图像详情
function showImageDetail(src, time) {
    // 创建模态框显示图像详情
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <span class="modal-title">坐姿记录 - ${time}</span>
                <button class="modal-close" onclick="this.parentElement.parentElement.parentElement.remove()">
                    <i class="bi bi-x"></i>
                </button>
            </div>
            <div class="modal-body">
                <img src="${src}" alt="坐姿记录">
            </div>
        </div>
    `;
    
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    `;
    
    document.body.appendChild(modal);
    
    // 点击背景关闭
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });
}

// 加载更多坐姿图像
function loadMorePostureImages() {
    console.log('加载更多坐姿图像');
    // 这里可以实现分页加载逻辑
    window.location.href = '/posture-records';
}

// 导出坐姿图像
function exportPostureImages() {
    console.log('导出坐姿图像记录');
    // 这里可以实现导出功能
    alert('导出功能开发中...');
}

// 图表切换相关变量
let currentChartIndex = 0;
const chartConfig = [
    {
        title: '坐姿时间占比',
        icon: 'bi bi-pie-chart'
    },
    {
        title: '不良姿态时段分布', 
        icon: 'bi bi-clock'
    },
    {
        title: '坐姿图像记录',
        icon: 'bi bi-images'
    }
];

// 切换图表函数
function switchChart(index) {
    if (index === currentChartIndex) return;
    
    const slides = document.querySelectorAll('.chart-slide');
    const indicators = document.querySelectorAll('.indicator-dot');
    const chartTitle = document.getElementById('chartTitle');
    const chartIcon = document.getElementById('chartIcon');
    
    // 更新指示器
    indicators.forEach((dot, i) => {
        dot.classList.toggle('active', i === index);
    });
    
    // 切换动画
    const currentSlide = slides[currentChartIndex];
    const nextSlide = slides[index];
    
    if (currentSlide && nextSlide) {
        // 淡出当前幻灯片
        currentSlide.style.opacity = '0';
        currentSlide.style.transform = index > currentChartIndex ? 'translateX(-20px)' : 'translateX(20px)';
        
        setTimeout(() => {
            currentSlide.classList.remove('active');
            
            // 淡入新幻灯片
            nextSlide.classList.add('active');
            nextSlide.style.opacity = '0';
            nextSlide.style.transform = index > currentChartIndex ? 'translateX(20px)' : 'translateX(-20px)';
            
            setTimeout(() => {
                nextSlide.style.opacity = '1';
                nextSlide.style.transform = 'translateX(0)';
            }, 50);
        }, 200);
    }
    
    // 更新标题和图标
    if (chartTitle && chartIcon && chartConfig[index]) {
        chartTitle.textContent = chartConfig[index].title;
        chartIcon.innerHTML = `<i class="${chartConfig[index].icon}"></i>`;
    }
    
    currentChartIndex = index;
    
    // 根据切换的图表重新初始化相应的组件
    setTimeout(() => {
        if (index === 0) {
            // 坐姿时间占比图表 - 确保容器完全显示后再初始化
            setTimeout(() => {
                initPosturePieChart();
            }, 100);
        } else if (index === 1) {
            // 不良姿态时段分布图表  
            setTimeout(() => {
                initHeatmapChart();
            }, 100);
        } else if (index === 2) {
            // 坐姿图像记录
            const activeRange = document.querySelector('.time-range-btn.active')?.getAttribute('data-range') || 'day';
            loadPostureImages(activeRange);
        }
    }, 250);
}

// 将switchChart函数暴露到全局
window.switchChart = switchChart;
window.switchChartImpl = switchChart;

// 添加触摸滑动支持
function setupChartSwiper() {
    const swiper = document.getElementById('chartSwiper');
    if (!swiper) return;
    
    let startX = 0;
    let startY = 0;
    let isSwipping = false;
    
    swiper.addEventListener('touchstart', function(e) {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
        isSwipping = true;
    });
    
    swiper.addEventListener('touchmove', function(e) {
        if (!isSwipping) return;
        
        const currentX = e.touches[0].clientX;
        const currentY = e.touches[0].clientY;
        const diffX = startX - currentX;
        const diffY = startY - currentY;
        
        // 如果垂直滑动幅度大于水平滑动，不处理
        if (Math.abs(diffY) > Math.abs(diffX)) {
            return;
        }
        
        e.preventDefault();
    });
    
    swiper.addEventListener('touchend', function(e) {
        if (!isSwipping) return;
        
        const endX = e.changedTouches[0].clientX;
        const diffX = startX - endX;
        
        // 滑动距离阈值
        const threshold = 50;
        
        if (Math.abs(diffX) > threshold) {
            if (diffX > 0) {
                // 向左滑，显示下一个图表
                const nextIndex = (currentChartIndex + 1) % chartConfig.length;
                switchChart(nextIndex);
            } else {
                // 向右滑，显示上一个图表
                const prevIndex = (currentChartIndex - 1 + chartConfig.length) % chartConfig.length;
                switchChart(prevIndex);
            }
        }
        
        isSwipping = false;
    });
}

// 切换用眼情况视图
let currentEyeView = 0;

function switchEyeView(index) {
    console.log('切换用眼视图到:', index);
    currentEyeView = index;
    
    // 更新指示器状态
    const indicators = document.querySelectorAll('.indicator-btn');
    indicators.forEach((btn, i) => {
        btn.classList.toggle('active', i === index);
    });
    
    // 更新滑动视图
    const slides = document.querySelectorAll('.eye-slide');
    slides.forEach((slide, i) => {
        slide.classList.toggle('active', i === index);
    });
    
    // 更新卡片标题
    const titleElement = document.getElementById('eyeCardTitle');
    if (titleElement) {
        titleElement.textContent = index === 0 ? '用眼监控' : '每日反馈';
    }
}

// 全局函数声明，供HTML onclick调用
window.showPage = showPage;
window.changeTimeRange = changeTimeRange;
window.switchChart = switchChart;
window.loadMorePostureImages = loadMorePostureImages;
window.exportPostureImages = exportPostureImages;
window.switchEyeView = switchEyeView;
