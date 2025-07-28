// 首页功能
class HomePage {
    constructor() {
        this.isInitialized = false;
        this.statsData = null;
        this.updateInterval = null;
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        this.setupEventListeners();
        this.loadInitialData();
        this.startAutoUpdate();
        this.isInitialized = true;
        
        console.log('首页初始化完成');
    }
    
    setupEventListeners() {
        // 工具项点击事件
        document.querySelectorAll('.feature-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const tool = item.getAttribute('data-tool');
                this.handleToolClick(tool, item);
            });
            
            // 添加触摸反馈
            item.addEventListener('touchstart', () => {
                this.addTouchFeedback(item);
            });
            
            item.addEventListener('touchend', () => {
                this.removeTouchFeedback(item);
            });
        });
        
        // 统计项点击事件
        document.querySelectorAll('.overview-stats .stat-item').forEach(item => {
            item.addEventListener('click', () => {
                this.handleStatClick(item);
            });
        });
    }
    
    async loadInitialData() {
        try {
            // 加载统计数据
            await this.loadStatsData();
            
            // 更新UI
            this.updateStatsDisplay();
            
        } catch (error) {
            console.error('加载首页数据失败:', error);
            MobileUtils.showToast('数据加载失败', 'error');
        }
    }
    
    async loadStatsData() {
        try {
            // 从API获取数据
            const response = await MobileUtils.fetchData('/api/home/stats');
            this.statsData = response;
            
            // 保存到本地存储
            MobileUtils.setLocalStorage('homeStats', this.statsData);
            
        } catch (error) {
            console.warn('API请求失败，使用本地数据:', error);
            // 使用本地存储的数据或默认数据
            this.statsData = MobileUtils.getLocalStorage('homeStats', this.getDefaultStats());
        }
    }
    
    getDefaultStats() {
        return {
            studyTime: '4.5h',
            postureScore: '85%',
            eyeRest: '12',
            lastUpdate: new Date().toISOString()
        };
    }
    
    updateStatsDisplay() {
        if (!this.statsData) return;
        
        // 更新学习时长
        const studyTimeEl = document.getElementById('studyTime');
        if (studyTimeEl) {
            studyTimeEl.textContent = this.statsData.studyTime;
            this.animateValue(studyTimeEl, this.statsData.studyTime);
        }
        
        // 更新姿势正确率
        const postureScoreEl = document.getElementById('postureScore');
        if (postureScoreEl) {
            postureScoreEl.textContent = this.statsData.postureScore;
            this.animateValue(postureScoreEl, this.statsData.postureScore);
        }
        
        // 更新眼部休息次数
        const eyeRestEl = document.getElementById('eyeRest');
        if (eyeRestEl) {
            eyeRestEl.textContent = this.statsData.eyeRest;
            this.animateValue(eyeRestEl, this.statsData.eyeRest);
        }
    }
    
    animateValue(element, targetValue) {
        const currentValue = element.textContent;
        if (currentValue === targetValue) return;
        
        // 简单的数字动画
        if (this.isNumeric(targetValue)) {
            const startValue = parseFloat(currentValue) || 0;
            const endValue = parseFloat(targetValue);
            const duration = 1000;
            const startTime = Date.now();
            
            const animate = () => {
                const elapsed = Date.now() - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                const current = startValue + (endValue - startValue) * this.easeOutQuart(progress);
                element.textContent = Math.round(current);
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    element.textContent = targetValue;
                }
            };
            
            animate();
        } else {
            // 非数字值直接更新
            element.textContent = targetValue;
        }
    }
    
    isNumeric(value) {
        return !isNaN(parseFloat(value)) && isFinite(value);
    }
    
    easeOutQuart(t) {
        return 1 - Math.pow(1 - t, 4);
    }
    
    startAutoUpdate() {
        // 每30秒更新一次数据
        this.updateInterval = setInterval(() => {
            this.loadStatsData().then(() => {
                this.updateStatsDisplay();
            });
        }, 30000);
    }
    
    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    
    handleToolClick(tool, element) {
        // 添加点击动画
        this.addClickAnimation(element);
        
        setTimeout(() => {
            // 跳转到独立的工具页面
            const toolRoutes = {
                'posture': '/posture',
                'eye': '/eye',
                'emotion': '/emotion'
            };
            
            const route = toolRoutes[tool];
            if (route) {
                window.location.href = route;
            } else {
                // 如果没有独立页面，使用原来的路由
                window.location.href = `/mobile/tool/${tool}`;
            }
        }, 300);
    }
    
    getToolName(tool) {
        const toolNames = {
            'posture': '坐姿检测',
            'eye': '用眼监护',
            'emotion': '情绪识别'
        };
        return toolNames[tool] || tool;
    }
    
    handleStatClick(element) {
        // 添加点击反馈
        this.addClickAnimation(element);
    }
    
    addTouchFeedback(element) {
        element.style.transform = 'scale(0.95)';
        element.style.transition = 'transform 0.1s ease-out';
    }
    
    removeTouchFeedback(element) {
        element.style.transform = 'scale(1)';
    }
    
    addClickAnimation(element) {
        // 创建涟漪效果
        const ripple = document.createElement('div');
        ripple.className = 'click-ripple';
        ripple.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            background: rgba(74, 144, 226, 0.3);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            pointer-events: none;
            z-index: 10;
        `;
        
        element.appendChild(ripple);
        
        // 动画
        requestAnimationFrame(() => {
            ripple.style.transition = 'all 0.3s ease-out';
            ripple.style.width = '100px';
            ripple.style.height = '100px';
            ripple.style.opacity = '0';
        });
        
        // 清理
        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 300);
    }
    
    // 页面可见性变化处理
    onPageVisible() {
        // console.log('首页变为可见');
        this.loadStatsData().then(() => {
            this.updateStatsDisplay();
        });
    }
    
    onPageHidden() {
        // console.log('首页变为隐藏');
        this.stopAutoUpdate();
    }
    
    // 清理资源
    destroy() {
        this.stopAutoUpdate();
        this.isInitialized = false;
    }
}

// 全局函数
function showToolDetail(tool) {
    console.log('showToolDetail called with tool:', tool);
    console.log('window.homePage:', window.homePage);
    
    if (window.homePage) {
        const element = document.querySelector(`[data-tool="${tool}"]`);
        console.log('Found element:', element);
        if (element) {
            window.homePage.handleToolClick(tool, element);
        } else {
            console.error('Element not found for tool:', tool);
        }
    } else {
        console.error('window.homePage is not available');
        // 备用方案：直接跳转
        const toolRoutes = {
            'posture': '/posture',
            'eye': '/eye',
            'emotion': '/emotion'
        };
        const route = toolRoutes[tool];
        if (route) {
            console.log('Direct navigation to:', route);
            window.location.href = route;
        }
    }
}

// 初始化首页
document.addEventListener('DOMContentLoaded', () => {
    window.homePage = new HomePage();
    
    // 页面可见性变化监听
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            window.homePage.onPageHidden();
        } else {
            window.homePage.onPageVisible();
        }
    });
});

// 页面卸载时清理
window.addEventListener('beforeunload', () => {
    if (window.homePage) {
        window.homePage.destroy();
    }
}); 