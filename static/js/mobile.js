// mobile.js - 移动端专用脚本文件

// 全局变量声明
let currentChartIndex = 0;

// 文档加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM加载完成，开始初始化移动端应用...');
    
    // 立即确保导航栏固定
    ensureNavFixed();
    
    // 初始化应用
    initMobileApp();
    
    // 显示首页
    showPage('home');
    
    // 延迟检查工具图标，确保Bootstrap Icons已加载
    setTimeout(() => {
        checkAndFixToolIcons();
    }, 500);
    
    // 确保 ECharts 库已加载
    if (typeof echarts === 'undefined') {
        console.warn('ECharts 库未加载，等待加载完成...');
        setTimeout(() => {
            if (typeof echarts !== 'undefined') {
                console.log('ECharts 库已加载');
                initCharts();
            } else {
                console.error('ECharts 库加载失败');
            }
        }, 2000);
    } else {
        console.log('ECharts 库已准备就绪');
    }
    
    // 再次确保导航栏固定（延迟执行）
    setTimeout(() => {
        ensureNavFixed();
    }, 1000);
    
    console.log('移动端应用初始化完成');
});

// 检查并修复工具图标显示
function checkAndFixToolIcons() {
    const toolItems = document.querySelectorAll('.tool-item');
    toolItems.forEach(item => {
        const toolImage = item.querySelector('.tool-image');
        const toolOverlay = item.querySelector('.tool-overlay');
        const toolIcon = item.querySelector('.tool-icon i');
        
        // 确保图标元素存在
        if (toolIcon) {
            console.log('工具图标存在:', toolIcon.className);
        } else {
            console.warn('工具图标缺失，正在修复...');
            const iconContainer = item.querySelector('.tool-icon');
            if (iconContainer) {
                const toolType = item.getAttribute('data-tool');
                let iconClass = 'bi bi-question-circle';
                
                switch(toolType) {
                    case 'posture':
                        iconClass = 'bi bi-person-standing';
                        break;
                    case 'eye':
                        iconClass = 'bi bi-eye';
                        break;
                    case 'emotion':
                        iconClass = 'bi bi-emoji-smile';
                        break;
                }
                
                iconContainer.innerHTML = `<i class="${iconClass}"></i>`;
            }
        }
        
        // 确保悬停效果正常工作
        item.addEventListener('mouseenter', function() {
            if (toolOverlay) {
                toolOverlay.style.opacity = '1';
            }
        });
        
        item.addEventListener('mouseleave', function() {
            if (toolOverlay) {
                toolOverlay.style.opacity = '0';
            }
        });
    });
}

// 确保导航栏固定定位
function ensureNavFixed() {
    const nav = document.querySelector('.mobile-nav');
    if (nav) {
        // 强制设置固定定位
        nav.style.position = 'fixed';
        nav.style.bottom = '0';
        nav.style.left = '0';
        nav.style.right = '0';
        nav.style.zIndex = '1000';
        
        // 监听滚动事件，确保导航栏保持固定
        window.addEventListener('scroll', function() {
            nav.style.position = 'fixed';
            nav.style.bottom = '0';
        });
        
        // 监听窗口大小变化
        window.addEventListener('resize', function() {
            nav.style.position = 'fixed';
            nav.style.bottom = '0';
        });
        
        console.log('导航栏固定定位已确保');
    }
}

// 初始化透明化渐变效果
function initTransparentGradientEffects() {
    // 确保导航栏固定
    ensureNavFixed();
    
    // 检查并修复工具图标
    checkAndFixToolIcons();
    
    // 为卡片添加渐变背景动画
    const cards = document.querySelectorAll('.mobile-card');
    cards.forEach((card, index) => {
        // 添加延迟动画效果
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in-up');
        
        // 添加鼠标悬停时的渐变效果
        card.addEventListener('mouseenter', function() {
            this.style.background = 'rgba(255, 255, 255, 0.3)';
            this.style.backdropFilter = 'blur(20px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.background = 'rgba(255, 255, 255, 0.2)';
            this.style.backdropFilter = 'blur(15px)';
        });
    });
    
    // 为工具项添加渐变效果
    const toolItems = document.querySelectorAll('.tool-item');
    toolItems.forEach((item, index) => {
        item.style.animationDelay = `${index * 0.15}s`;
        item.classList.add('fade-in-up');
        
        // 添加悬停时的渐变背景
        item.addEventListener('mouseenter', function() {
            this.style.background = 'rgba(255, 255, 255, 0.3)';
            this.style.border = '1px solid rgba(255, 255, 255, 0.4)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.background = 'rgba(255, 255, 255, 0.15)';
            this.style.border = '1px solid rgba(255, 255, 255, 0.2)';
        });
    });
    
    // 为统计项添加渐变效果
    const statItems = document.querySelectorAll('.stat-item');
    statItems.forEach((item, index) => {
        item.style.animationDelay = `${index * 0.1}s`;
        item.classList.add('fade-in-up');
    });
    
    // 为按钮添加渐变效果
    const buttons = document.querySelectorAll('.mobile-btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.background = 'rgba(143, 180, 160, 0.3)';
            this.style.border = '1px solid rgba(143, 180, 160, 0.5)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.background = 'rgba(143, 180, 160, 0.2)';
            this.style.border = '1px solid rgba(143, 180, 160, 0.3)';
        });
    });
}

// 添加CSS动画类
function addGradientAnimations() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .fade-in-up {
            animation: fadeInUp 0.6s ease-out forwards;
            opacity: 0;
        }
        
        .mobile-card {
            transition: all 0.3s ease;
        }
        
        .mobile-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(143, 180, 160, 0.12), 0 6px 20px rgba(143, 180, 160, 0.06);
        }
        
        .tool-item {
            transition: all 0.3s ease;
        }
        
        .tool-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(143, 180, 160, 0.15);
        }
        
        .stat-item {
            transition: all 0.3s ease;
        }
        
        .stat-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(143, 180, 160, 0.12);
        }
    `;
    document.head.appendChild(style);
}

// 初始化移动端应用
function initMobileApp() {
    console.log('初始化移动端应用...');
    
    // 添加渐变动画样式
    addGradientAnimations();
    
    // 初始化透明化渐变效果
    initTransparentGradientEffects();
    
    // 设置导航
    setupNavigation();
    
    // 设置工具事件
    setupToolEvents();
    
    // 设置控制事件
    setupControlEvents();
    
    // 初始化图表
    initCharts();
    
    // 更新模拟数据
    updateMockData();
    
    // 定期更新数据
    setInterval(updateMockData, 30000);
    
    // 定期获取系统状态
    setInterval(fetchAnalysisStatus, 10000);
    
    // 定期获取台灯状态
    setInterval(fetchLampStatus, 15000);
    
    console.log('移动端应用初始化完成');
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

// 显示指定页面
function showPage(pageId) {
    console.log('切换到页面:', pageId);
    
    // 隐藏所有页面
    const pages = document.querySelectorAll('.mobile-page');
    pages.forEach(page => {
        page.style.display = 'none';
        page.classList.remove('active');
    });
    
    // 移除所有导航项的激活状态
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.classList.remove('active');
    });
    
    // 显示目标页面
    const targetPage = document.getElementById(pageId);
    if (targetPage) {
        targetPage.style.display = 'block';
        // 添加延迟以显示动画效果
        setTimeout(() => {
            targetPage.classList.add('active');
        }, 50);
    }
    
    // 激活对应的导航项
    const activeNavItem = document.querySelector(`[data-page="${pageId}"]`);
    if (activeNavItem) {
        activeNavItem.classList.add('active');
    }
    
    // 根据页面类型执行特定初始化
    switch(pageId) {
        case 'home':
            // 重新初始化首页的透明化渐变效果
            setTimeout(() => {
                initTransparentGradientEffects();
                updateMockData();
            }, 100);
            break;
        case 'guardian':
            // 初始化监护页面的透明化效果
            setTimeout(() => {
                initTransparentGradientEffects();
                refreshGuardianData();
            }, 100);
            break;
        case 'remote':
            // 初始化远程控制页面的透明化效果
            setTimeout(() => {
                initTransparentGradientEffects();
                fetchLampStatus();
            }, 100);
            break;
        case 'settings':
            // 初始化设置页面的透明化效果
            setTimeout(() => {
                initTransparentGradientEffects();
            }, 100);
            break;
        case 'tool-detail':
            // 工具详情页面保持当前状态
            break;
    }
}

// 显示工具详情
function showToolDetail(tool) {
    const toolDetailPage = document.getElementById('tool-detail');
    const toolTitle = document.getElementById('toolTitle');

    document.querySelectorAll('.tool-content').forEach(content => {
        content.style.display = 'none';
    });
    
    // 显示对应的工具内容
    let title = '';
    switch(tool) {
        case 'posture':
            title = '坐姿检测';
            document.getElementById('posture-content').style.display = 'block';
            
            // 延迟初始化，确保容器完全显示
            setTimeout(() => {
                console.log('开始初始化坐姿检测图表...');
                
                // 重置图表切换状态
                currentChartIndex = 0;
                
                // 确保第一个幻灯片显示
                const slides = document.querySelectorAll('.chart-slide');
                const indicators = document.querySelectorAll('.indicator-dot');
                slides.forEach((slide, index) => {
                    if (index === 0) {
                        slide.classList.add('active');
                        slide.style.display = 'block';
                    } else {
                        slide.classList.remove('active');
                        slide.style.display = 'none';
                    }
                });
                indicators.forEach((dot, index) => {
                    dot.classList.toggle('active', index === 0);
                });
                
                // 再次延迟初始化饼图，确保容器布局完成
                setTimeout(() => {
                    initPosturePieChart();
                    
                    // 初始化图表切换功能
                    setupChartSwiper();
                    
                    console.log('坐姿检测图表初始化完成');
                }, 200);
                
                // 加载默认时间范围数据
                loadPostureData('day');
                loadPostureImages('day');
            }, 150);
            break;
        case 'eye':
            title = '用眼情况';
            document.getElementById('eye-content').style.display = 'block';
            
            // 延迟初始化，确保容器完全显示
            setTimeout(() => {
                console.log('开始初始化用眼情况模块...');
                
                // 确保用眼内容容器可见
                const eyeContent = document.getElementById('eye-content');
                if (eyeContent) {
                    eyeContent.style.display = 'block';
                    eyeContent.style.visibility = 'visible';
                }
                
                // 确保默认的用眼监控视图显示
                const eyeSlides = document.querySelectorAll('.eye-slide');
                const eyeIndicators = document.querySelectorAll('.indicator-btn');
                eyeSlides.forEach((slide, index) => {
                    if (index === 0) {
                        slide.classList.add('active');
                        slide.style.display = 'block';
                    } else {
                        slide.classList.remove('active');
                        slide.style.display = 'none';
                    }
                });
                eyeIndicators.forEach((indicator, index) => {
                    indicator.classList.toggle('active', index === 0);
                });
                
                // 延迟初始化热力图，确保容器布局完成
                setTimeout(() => {
                    // 强制显示热力图卡片
                    const heatmapCard = document.querySelector('#eye-content .mobile-card:last-child');
                    if (heatmapCard) {
                        heatmapCard.style.display = 'block';
                        heatmapCard.style.visibility = 'visible';
                    }
                    
                    // 初始化用眼热力图
                    initEyeHeatmapChart();
                    
                    // 更新用眼指标
                    updateEyeMetrics();
                    
                    console.log('用眼情况模块初始化完成');
                }, 200);
            }, 150);
            break;
        case 'emotion':
            title = '情绪反馈';
            document.getElementById('emotion-content').style.display = 'block';
            setTimeout(() => {
                // 初始化情绪图表
                initEmotionCharts();
                
                // 确保默认视图显示
                const defaultView = document.querySelector('.emotion-chart-view.active') || 
                                  document.getElementById('emotion-radar-view');
                if (defaultView) {
                    defaultView.classList.add('active');
                }
                
                // 刷新当前活跃的情绪图表
                setTimeout(() => {
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
                }, 200);
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
        
        // 更新新的亮度控件
        if (data.brightness !== undefined) {
            const brightnessSlider = document.getElementById('brightness-slider');
            const brightnessDisplay = document.getElementById('brightness-display');
            const currentBrightness = document.getElementById('currentBrightness');
            
            if (brightnessSlider) {
                brightnessSlider.value = data.brightness;
            }
            if (brightnessDisplay) {
                brightnessDisplay.textContent = data.brightness;
            }
            if (currentBrightness) {
                currentBrightness.textContent = data.brightness;
            }
        }
        
        // 更新新的色温控件
        if (data.temperature !== undefined) {
            const temperatureSlider = document.getElementById('temperature-slider');
            const temperatureDisplay = document.getElementById('temperature-display');
            const currentTemperature = document.getElementById('currentTemperature');
            
            const tempValue = data.temperature + 'K';
            if (temperatureSlider) {
                temperatureSlider.value = data.temperature;
            }
            if (temperatureDisplay) {
                temperatureDisplay.textContent = tempValue;
            }
            if (currentTemperature) {
                currentTemperature.textContent = tempValue;
            }
        }
        
        // 更新开关状态
        if (data.power_status !== undefined) {
            const powerSwitch = document.getElementById('power-switch');
            const powerSwitchText = document.getElementById('power-switch-text');
            if (powerSwitch) {
                powerSwitch.checked = data.power_status;
                if (powerSwitchText) {
                    powerSwitchText.textContent = data.power_status ? '已开启' : '已关闭';
                }
            }
        }
        
        if (data.light_status !== undefined) {
            const lightSwitch = document.getElementById('light-switch');
            const lightSwitchText = document.getElementById('light-switch-text');
            if (lightSwitch) {
                lightSwitch.checked = data.light_status;
                if (lightSwitchText) {
                    lightSwitchText.textContent = data.light_status ? '已开启' : '已关闭';
                }
            }
        }
        
        // 保留旧版本的兼容性
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
    const guardianVideo = document.getElementById('guardianVideo');
    if (guardianVideo) {
        // 注释掉原来的视频流，使用静态图片
        // guardianVideo.src = '/video_feed?t=' + new Date().getTime();
        guardianVideo.src = '/static/assert/WechatIMG69.jpg?t=' + new Date().getTime();
    }
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

// 更新概览数据
function updateMockData() {
    // 模拟数据更新首页概览
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

// 更新概览统计数据
function updateOverviewStats(stats) {
    const studyTime = document.getElementById('studyTime');
    const postureScore = document.getElementById('postureScore');
    const eyeRest = document.getElementById('eyeRest');
    
    if (studyTime && stats.study_time) {
        studyTime.textContent = stats.study_time;
    }
    
    if (postureScore && stats.posture_score) {
        postureScore.textContent = stats.posture_score;
    }
    
    if (eyeRest && stats.eye_rest_count) {
        eyeRest.textContent = stats.eye_rest_count;
    }
}

// 初始化图表
function initCharts() {
    initPostureChart();
    initEmotionCharts(); // 重新启用情绪图表初始化
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
                    '#90EE90',    // 正确姿势 - 薄荷绿
                    '#DDA15E',    // 低头 - 暖橙
                    '#8FBC8F',    // 前倾 - 抹茶绿
                    '#6B9DC7',    // 侧倾 - 浅蓝
                    '#E8EAE6'     // 其他 - 灰色
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
    
    // 如果已经初始化过，先销毁（ECharts使用dispose方法）
    if (window.emotionRadarChart && typeof window.emotionRadarChart.dispose === 'function') {
        try {
            window.emotionRadarChart.dispose();
        } catch (e) {
            console.warn('销毁雷达图失败:', e);
        }
        window.emotionRadarChart = null;
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
                    color: '#E8DDD6'
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
                    color: '#F4A261'
                },
                areaStyle: {
                    opacity: 0.3,
                    color: '#F4A261'
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
    
    // 如果已经初始化过，先销毁（Chart.js使用destroy方法）
    if (window.emotionTrendChart && typeof window.emotionTrendChart.destroy === 'function') {
        try {
            window.emotionTrendChart.destroy();
        } catch (e) {
            console.warn('销毁趋势图失败:', e);
        }
        window.emotionTrendChart = null;
    }
    
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'],
            datasets: [{
                label: '积极情绪',
                data: [75, 80, 70, 85, 60, 90, 65, 85],
                borderColor: '#90EE90',
                backgroundColor: 'rgba(144, 238, 144, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: '消极情绪', 
                data: [20, 15, 25, 10, 35, 8, 30, 12],
                borderColor: '#8FBC8F',
                backgroundColor: 'rgba(143, 188, 143, 0.1)',
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
    
    // 如果已经初始化过，先销毁（Chart.js使用destroy方法）
    if (window.emotionDistributionChart && typeof window.emotionDistributionChart.destroy === 'function') {
        try {
            window.emotionDistributionChart.destroy();
        } catch (e) {
            console.warn('销毁分布图失败:', e);
        }
        window.emotionDistributionChart = null;
    }
    
    const chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['积极情绪', '中性情绪', '消极情绪'],
            datasets: [{
                data: [65, 25, 10],
                backgroundColor: [
                    '#90EE90',   // 薄荷绿 - 积极情绪
                    '#DDA15E',   // 暖橙 - 中性情绪
                    '#8FBC8F'    // 抹茶绿 - 消极情绪
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
    
    // 如果已经初始化过，先销毁（ECharts使用dispose方法）
    if (window.emotionHeatmapChart && typeof window.emotionHeatmapChart.dispose === 'function') {
        try {
            window.emotionHeatmapChart.dispose();
        } catch (e) {
            console.warn('销毁情绪热力图失败:', e);
        }
        window.emotionHeatmapChart = null;
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
    console.log('开始初始化坐姿饼图...');
    
    const ctx = document.getElementById('posturePieChart');
    if (!ctx) {
        console.error('坐姿饼图容器元素未找到');
        return;
    }
    
    // 确保容器元素可见
    const chartContainer = ctx.closest('.chart-container');
    const chartSlide = ctx.closest('.chart-slide');
    
    if (chartContainer) {
        chartContainer.style.display = 'block';
        chartContainer.style.visibility = 'visible';
    }
    
    if (chartSlide && !chartSlide.classList.contains('active')) {
        chartSlide.classList.add('active');
        chartSlide.style.display = 'block';
    }
    
    console.log('坐姿饼图容器状态:', {
        element: ctx,
        offsetWidth: ctx.offsetWidth,
        offsetHeight: ctx.offsetHeight,
        clientWidth: ctx.clientWidth,
        clientHeight: ctx.clientHeight,
        containerVisible: chartContainer ? chartContainer.style.display : 'unknown',
        slideActive: chartSlide ? chartSlide.classList.contains('active') : 'unknown'
    });
    
    // 强制设置canvas尺寸
    ctx.style.width = '100%';
    ctx.style.height = '250px';
    
    // 如果已经初始化过，先销毁
    if (window.posturePieChart) {
        try {
            window.posturePieChart.destroy();
            console.log('已销毁旧的坐姿饼图实例');
        } catch (e) {
            console.warn('销毁坐姿饼图失败:', e);
        }
    }
    
    // 等待一帧后再初始化，确保DOM完全准备好
    requestAnimationFrame(() => {
        try {
            console.log('正在创建坐姿饼图...');
            window.posturePieChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['良好坐姿', '轻度不良坐姿', '不良坐姿'],
                    datasets: [{
                        data: [50, 30, 20],
                        backgroundColor: [
                            '#90EE90',   // 薄荷绿 - 良好坐姿
                            '#DDA15E',   // 暖橙 - 轻度不良坐姿
                            '#8FBC8F'    // 抹茶绿 - 不良坐姿
                        ],
                        borderWidth: 2,
                        borderColor: '#FFFFFF'
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
                
                console.log('坐姿时间占比饼图初始化完成', window.posturePieChart);
                
                // 强制更新图表
                setTimeout(() => {
                    if (window.posturePieChart) {
                        window.posturePieChart.resize();
                        window.posturePieChart.update();
                        console.log('坐姿饼图已更新');
                    }
                }, 100);
                
            } catch (error) {
                console.error('坐姿饼图初始化失败:', error);
            }
        });
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
                borderColor: '#8FBC8F',
                backgroundColor: 'rgba(143, 188, 143, 0.1)',
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#8FBC8F',
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
        },
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
                    if (value < 30) return 'rgba(168, 218, 220, 0.8)'; // 淡绿色
                    if (value < 60) return 'rgba(244, 162, 97, 0.8)';  // 柔和橙色
                    return 'rgba(231, 111, 81, 0.8)';                  // 暖红色
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
        console.warn('用眼热力图容器元素未找到');
        return;
    }
    
    // 确保容器及其父容器都可见
    const heatmapContainer = chartElement.closest('.heatmap-container');
    const eyeCard = chartElement.closest('.mobile-card');
    const eyeContent = chartElement.closest('#eye-content');
    
    if (eyeContent) {
        eyeContent.style.display = 'block';
        eyeContent.style.visibility = 'visible';
    }
    if (eyeCard) {
        eyeCard.style.display = 'block';
    }
    if (heatmapContainer) {
        heatmapContainer.style.display = 'block';
        heatmapContainer.style.height = '300px';
    }
    
    // 强制设置容器尺寸
    chartElement.style.width = '100%';
    chartElement.style.height = '280px';
    chartElement.style.display = 'block';
    chartElement.style.visibility = 'visible';
    
    // 等待容器布局完成
    setTimeout(() => {
        console.log('用眼热力图容器状态:', {
            offsetWidth: chartElement.offsetWidth,
            offsetHeight: chartElement.offsetHeight,
            clientWidth: chartElement.clientWidth,
            clientHeight: chartElement.clientHeight,
            display: chartElement.style.display,
            visibility: chartElement.style.visibility
        });
        
        // 如果容器仍然没有尺寸，强制设置
        if (chartElement.offsetWidth === 0 || chartElement.offsetHeight === 0) {
            chartElement.style.width = '100%';
            chartElement.style.height = '280px';
            chartElement.style.minHeight = '280px';
            chartElement.style.minWidth = '300px';
        }
        
        // 如果已经初始化过，先销毁
        if (window.eyeHeatmapChart && typeof window.eyeHeatmapChart.dispose === 'function') {
            try {
                window.eyeHeatmapChart.dispose();
                console.log('已销毁旧的用眼热力图实例');
            } catch (e) {
                console.warn('销毁用眼热力图失败:', e);
            }
            window.eyeHeatmapChart = null;
        }
        
        console.log('开始初始化用眼时间热力图...');
        
        try {
            // 检查 ECharts 是否可用
            if (typeof echarts === 'undefined') {
                console.error('ECharts 库未加载，无法初始化用眼热力图');
                return;
            }
            
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
                    bottom: '0',            inRange: {
                color: ['#F7F3EF', '#F4A261', '#E76F51']
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
            
            console.log('用眼时间热力图初始化完成');
            
            // 强制刷新图表尺寸
            setTimeout(() => {
                if (window.eyeHeatmapChart) {
                    window.eyeHeatmapChart.resize();
                    console.log('用眼热力图resize完成');
                }
            }, 100);
            
        } catch (error) {
            console.error('用眼时间热力图初始化失败:', error);
        }
    }, 100);
    
    // 响应式调整
    const resizeHandler = function () {
        if (window.eyeHeatmapChart) {
            window.eyeHeatmapChart.resize();
        }
    };
    
    window.removeEventListener('resize', resizeHandler);
    window.addEventListener('resize', resizeHandler);
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

// 全局函数 - 提供给HTML onclick事件调用

// 图表切换函数（全局函数）
window.switchChart = function(index) {
    if (typeof window.switchChartImpl === 'function') {
        window.switchChartImpl(index);
    }
};

// 时间范围切换事件（全局函数，可以被HTML onclick调用）
window.changeTimeRange = function(range) {
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
    if (typeof loadPostureData === 'function') {
        loadPostureData(range);
    }
    if (typeof updateChartsByTimeRange === 'function') {
        updateChartsByTimeRange(range);
    }
    if (typeof updatePostureStats === 'function') {
        updatePostureStats(range);
    }
    if (typeof loadPostureImages === 'function') {
        loadPostureImages(range);
    }
};

// 加载更多图像（全局函数）
window.loadMorePostureImages = function() {
    console.log('加载更多坐姿图像');
    // 这里可以实现分页加载逻辑
    window.location.href = '/posture-records';
};

// 导出坐姿图像（全局函数）
window.exportPostureImages = function() {
    console.log('导出坐姿图像记录');
    // 这里可以实现导出功能
    alert('导出功能开发中...');
};

// 显示图像详情（全局函数）
window.showImageDetail = function(src, time) {
    // 创建模态框显示图像详情
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.innerHTML = `
        <div class="modal-content" style="background: white; border-radius: 12px; max-width: 90%; max-height: 80%; overflow: hidden;">
            <div class="modal-header" style="padding: 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center;">
                <span class="modal-title" style="font-weight: 600;">坐姿记录 - ${time}</span>
                <button class="modal-close" onclick="this.parentElement.parentElement.parentElement.remove()" style="background: none; border: none; font-size: 24px; cursor: pointer;">
                    <i class="bi bi-x"></i>
                </button>
            </div>
            <div class="modal-body" style="padding: 15px; text-align: center;">
                <img src="${src}" alt="坐姿记录" style="max-width: 100%; height: auto; border-radius: 8px;">
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
};

// 控制台日志测试
console.log('移动端脚本已加载');

// 远程控制功能函数

// 电源开关控制
function togglePower() {
    const powerSwitch = document.getElementById('power-switch');
    const powerSwitchText = document.getElementById('power-switch-text');
    
    if (powerSwitch.checked) {
        sendLampCommand('power_on');
    } else {
        sendLampCommand('power_off');
    }
}

// 灯光开关控制
function toggleLight() {
    const lightSwitch = document.getElementById('light-switch');
    const lightSwitchText = document.getElementById('light-switch-text');
    
    if (lightSwitch.checked) {
        lightSwitchText.textContent = '已开启';
        sendLampCommand('light_on');
    } else {
        lightSwitchText.textContent = '已关闭';
        sendLampCommand('light_off');
    }
}

// 亮度调节
function adjustBrightness(value) {
    const brightnessDisplay = document.getElementById('brightness-display');
    const currentBrightness = document.getElementById('currentBrightness');
    
    if (brightnessDisplay) {
        brightnessDisplay.textContent = value;
    }
    if (currentBrightness) {
        currentBrightness.textContent = value;
    }
    
    // 实时发送亮度调节命令
    sendLampCommand('brightness', value);
}

// 色温调节
function adjustTemperature(value) {
    const temperatureDisplay = document.getElementById('temperature-display');
    const currentTemperature = document.getElementById('currentTemperature');
    
    const tempValue = value + 'K';
    if (temperatureDisplay) {
        temperatureDisplay.textContent = tempValue;
    }
    if (currentTemperature) {
        currentTemperature.textContent = tempValue;
    }
    
    // 实时发送色温调节命令
    sendLampCommand('temperature', value);
}

// 设置亮度快捷值
function setBrightness(value) {
    const brightnessSlider = document.getElementById('brightness-slider');
    if (brightnessSlider) {
        brightnessSlider.value = value;
        adjustBrightness(value);
    }
}

// 设置色温快捷值
function setTemperature(value) {
    const temperatureSlider = document.getElementById('temperature-slider');
    if (temperatureSlider) {
        temperatureSlider.value = value;
        adjustTemperature(value);
    }
}

// 应用灯光设置
function applyLightSettings() {
    const brightness = document.getElementById('brightness-slider')?.value;
    const temperature = document.getElementById('temperature-slider')?.value;
    
    const settings = {
        brightness: brightness,
        temperature: temperature
    };
    
    sendLampCommand('apply_settings', settings);
    showToast('设置已应用到台灯');
}

// 护眼模式切换
function toggleEyeCareMode() {
    const eyeCareMode = document.getElementById('eye-care-mode');
    const eyeCareModeText = document.getElementById('eye-care-mode-text');
    
    if (eyeCareMode.checked) {
        eyeCareModeText.textContent = '已开启';
        sendLampCommand('eye_care_on');
        showToast('护眼模式已开启');
    } else {
        eyeCareModeText.textContent = '已关闭';
        sendLampCommand('eye_care_off');
        showToast('护眼模式已关闭');
    }
}

// 设置远眺休息间隔
function setRestInterval(minutes) {
    const restIntervalInput = document.getElementById('rest-interval');
    if (restIntervalInput) {
        restIntervalInput.value = minutes;
    }
    
    // 更新按钮状态
    const restIntervalInputs = document.querySelectorAll('#rest-interval');
    restIntervalInputs.forEach(input => {
        const parentGroup = input.closest('.setting-group');
        if (parentGroup) {
            const presetButtons = parentGroup.querySelectorAll('.preset-btn');
            presetButtons.forEach(btn => {
                btn.classList.remove('active');
                if (btn.textContent.includes(minutes + '分钟')) {
                    btn.classList.add('active');
                }
            });
        }
    });
    
    sendLampCommand('set_rest_interval', minutes);
    showToast(`远眺休息间隔已设置为${minutes}分钟`);
}

// 设置连续用眼提醒时间
function setContinuousTime(minutes) {
    const continuousTimeInput = document.getElementById('continuous-time');
    if (continuousTimeInput) {
        continuousTimeInput.value = minutes;
    }
    
    // 更新按钮状态
    const parentGroup = document.querySelector('#continuous-time')?.closest('.setting-group');
    if (parentGroup) {
        const buttons = parentGroup.querySelectorAll('.preset-btn');
        buttons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.textContent.includes(minutes + '分钟')) {
                btn.classList.add('active');
            }
        });
    }
    
    sendLampCommand('set_continuous_time', minutes);
    showToast(`连续用眼提醒已设置为${minutes}分钟`);
}

// 发送台灯控制命令
function sendLampCommand(command, value = null) {
    let url = '';
    let data = {};
    
    switch(command) {
        case 'power_on':
            url = '/api/lamp/power';
            data = { power: true };
            break;
        case 'power_off':
            url = '/api/lamp/power';
            data = { power: false };
            break;
        case 'light_on':
            url = '/api/lamp/power';
            data = { power: true };
            break;
        case 'light_off':
            url = '/api/lamp/power';
            data = { power: false };
            break;
        case 'brightness':
            url = '/api/lamp/brightness';
            data = { brightness: value };
            break;
        case 'temperature':
            url = '/api/lamp/color_temp';
            data = { color_temp: value };
            break;
        case 'apply_settings':
            url = '/api/lamp/settings';
            data = value;
            break;
        case 'eye_care_on':
            url = '/api/lamp/scene';
            data = { scene: 'reading' };
            break;
        case 'eye_care_off':
            url = '/api/lamp/scene';
            data = { scene: 'normal' };
            break;
        case 'set_rest_interval':
            url = '/api/lamp/timer';
            data = { timer_enabled: true, timer_duration: value };
            break;
        case 'set_continuous_time':
            url = '/api/lamp/timer';
            data = { timer_enabled: true, timer_duration: value };
            break;
        default:
            console.warn('未知的台灯控制命令:', command);
            return;
    }
    
    const options = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (Object.keys(data).length > 0) {
        options.body = JSON.stringify(data);
    }
    
    fetch(url, options)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(result => {
            if (result.status === 'success') {
                console.log('台灯控制命令执行成功:', command, value);
                // 更新UI状态
                updateLampStatusUI(result);
                showToast(result.message || '操作成功');
            } else {
                console.error('台灯控制命令执行失败:', result.message);
                showToast('操作失败: ' + (result.message || '未知错误'));
            }
        })
        .catch(error => {
            console.error('发送台灯控制命令失败:', error);
            showToast('网络连接失败');
        });
}

// 更新台灯状态UI
function updateLampStatusUI(data) {
    // 处理电源状态
    if (data.data && data.data.power !== undefined) {
        const powerSwitch = document.getElementById('power-switch');
        const powerSwitchText = document.getElementById('power-switch-text');
        const lightSwitch = document.getElementById('light-switch');
        const lightSwitchText = document.getElementById('light-switch-text');
        
        if (powerSwitch) {
            powerSwitch.checked = data.data.power;
            if (powerSwitchText) {
                powerSwitchText.textContent = data.data.power ? '已开启' : '已关闭';
            }
        }
        
        // 同时更新灯光开关状态
        if (lightSwitch) {
            lightSwitch.checked = data.data.power;
            if (lightSwitchText) {
                lightSwitchText.textContent = data.data.power ? '已开启' : '已关闭';
            }
        }
    }
    
    // 处理亮度
    if (data.data && data.data.brightness !== undefined) {
        const brightnessSlider = document.getElementById('brightness-slider');
        const brightnessValue = document.getElementById('brightness-value');
        if (brightnessSlider) {
            brightnessSlider.value = data.data.brightness;
            if (brightnessValue) {
                brightnessValue.textContent = data.data.brightness + '%';
            }
        }
    }
    
    // 处理色温
    if (data.data && data.data.color_temp !== undefined) {
        const temperatureSlider = document.getElementById('temperature-slider');
        const temperatureValue = document.getElementById('temperature-value');
        if (temperatureSlider) {
            temperatureSlider.value = data.data.color_temp;
            if (temperatureValue) {
                temperatureValue.textContent = data.data.color_temp + 'K';
            }
        }
    }
    
    // 兼容旧格式（保持向后兼容）
    if (data.power_status !== undefined) {
        const powerSwitch = document.getElementById('power-switch');
        const powerSwitchText = document.getElementById('power-switch-text');
        if (powerSwitch) {
            powerSwitch.checked = data.power_status;
            if (powerSwitchText) {
                powerSwitchText.textContent = data.power_status ? '已开启' : '已关闭';
            }
        }
    }
    
    if (data.light_status !== undefined) {
        const lightSwitch = document.getElementById('light-switch');
        const lightSwitchText = document.getElementById('light-switch-text');
        if (lightSwitch) {
            lightSwitch.checked = data.light_status;
            if (lightSwitchText) {
                lightSwitchText.textContent = data.light_status ? '已开启' : '已关闭';
            }
        }
    }
    
    if (data.brightness !== undefined) {
        const brightnessSlider = document.getElementById('brightness-slider');
        const brightnessDisplay = document.getElementById('brightness-display');
        const currentBrightness = document.getElementById('currentBrightness');
        
        if (brightnessSlider) {
            brightnessSlider.value = data.brightness;
        }
        if (brightnessDisplay) {
            brightnessDisplay.textContent = data.brightness;
        }
        if (currentBrightness) {
            currentBrightness.textContent = data.brightness;
        }
    }
    
    // 兼容新的温度格式（color_temp）
    if (data.color_temp !== undefined) {
        const temperatureSlider = document.getElementById('temperature-slider');
        const temperatureDisplay = document.getElementById('temperature-display');
        const currentTemperature = document.getElementById('currentTemperature');
        
        const tempValue = data.color_temp + 'K';
        if (temperatureSlider) {
            temperatureSlider.value = data.color_temp;
        }
        if (temperatureDisplay) {
            temperatureDisplay.textContent = tempValue;
        }
        if (currentTemperature) {
            currentTemperature.textContent = tempValue;
        }
    }
    
    // 兼容旧的温度格式
    if (data.temperature !== undefined) {
        const temperatureSlider = document.getElementById('temperature-slider');
        const temperatureDisplay = document.getElementById('temperature-display');
        const currentTemperature = document.getElementById('currentTemperature');
        
        const tempValue = data.temperature + 'K';
        if (temperatureSlider) {
            temperatureSlider.value = data.temperature;
        }
        if (temperatureDisplay) {
            temperatureDisplay.textContent = tempValue;
        }
        if (currentTemperature) {
            currentTemperature.textContent = tempValue;
        }
    }
}

// 切换灯光控制和护眼设置内容
function switchLightEyeContent(type) {
    const lightBtn = document.querySelector('.light-eye-btn[onclick*="light"]');
    const eyeBtn = document.querySelector('.light-eye-btn[onclick*="eye"]');
    const lightContent = document.getElementById('light-content');
    const eyeContent = document.getElementById('eye-content');

    if (type === 'light') {
        lightBtn.classList.add('active');
        eyeBtn.classList.remove('active');
        lightContent.style.display = 'block';
        eyeContent.style.display = 'none';
    } else if (type === 'eye') {
        lightBtn.classList.remove('active');
        eyeBtn.classList.add('active');
        lightContent.style.display = 'none';
        eyeContent.style.display = 'block';
    }
}

// 图表切换实现函数
function switchChartImpl(index) {
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
            // 坐姿图像记录 - 刷新图像显示
            setTimeout(() => {
                loadPostureImages('day');
            }, 100);
        }
    }, 250);
}

// 将switchChartImpl函数暴露到全局
window.switchChartImpl = switchChartImpl;

// 全局图表切换函数，供 HTML onclick 调用
function switchChart(index) {
    console.log('切换到图表:', index);
    if (typeof switchChartImpl === 'function') {
        switchChartImpl(index);
    } else {
        console.error('switchChartImpl 函数未定义');
    }
}

// 将 switchChart 函数暴露到全局
window.switchChart = switchChart;

// 用眼情况视图切换函数
function switchEyeView(index) {
    console.log('切换用眼视图:', index);
    
    const eyeSlides = document.querySelectorAll('.eye-slide');
    const indicators = document.querySelectorAll('.indicator-btn');
    
    // 更新指示器状态
    indicators.forEach((indicator, i) => {
        indicator.classList.toggle('active', i === index);
    });
    
    // 切换视图显示
    eyeSlides.forEach((slide, i) => {
        if (i === index) {
            slide.classList.add('active');
            slide.style.display = 'block';
        } else {
            slide.classList.remove('active');
            slide.style.display = 'none';
        }
    });
    
    // 如果切换到用眼监控视图，更新指标数据
    if (index === 0) {
        updateEyeMetrics();
    }
}

// 将用眼视图切换函数暴露到全局
window.switchEyeView = switchEyeView;

/* 下面是原有代码的结束标志，确保不被覆盖 */
