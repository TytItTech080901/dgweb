// 基础JavaScript功能
class MobileApp {
    constructor() {
        this.currentPage = 'home';
        this.isInitialized = false;
        this.toastQueue = [];
        this.isShowingToast = false;
        
        this.init();
    }
    
    init() {
        console.log('初始化移动端应用...');
        
        // 确保DOM加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupApp());
        } else {
            this.setupApp();
        }
    }
    
    setupApp() {
        if (this.isInitialized) return;
        
        this.setupEventListeners();
        this.setupBackgroundEffects();
        this.createToastContainer();
        this.isInitialized = true;
        
        console.log('移动端应用初始化完成');
    }
    
    setupEventListeners() {
        // 页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.onPageHidden();
            } else {
                this.onPageVisible();
            }
        });
        
        // 窗口大小变化
        window.addEventListener('resize', this.debounce(() => {
            this.onWindowResize();
        }, 250));
        
        // 触摸事件优化
        this.setupTouchOptimization();
    }
    
    setupTouchOptimization() {
        // 防止双击缩放
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (event) => {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
        
        // 防止滚动时的选择
        document.addEventListener('touchmove', (event) => {
            if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                return;
            }
            event.preventDefault();
        }, { passive: false });
    }
    
    setupBackgroundEffects() {
        // 添加视差滚动效果
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const parallax = document.querySelector('body::before');
            if (parallax) {
                const speed = scrolled * 0.5;
                parallax.style.transform = `translateY(${speed}px)`;
            }
        });
    }
    
    createToastContainer() {
        if (document.getElementById('toast-container')) return;
        
        const toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10000;
            pointer-events: none;
        `;
        document.body.appendChild(toastContainer);
    }
    
    // 工具函数
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    // Toast 消息系统
    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `mobile-toast ${type}`;
        toast.textContent = message;
        
        const container = document.getElementById('toast-container') || document.body;
        container.appendChild(toast);
        
        // 显示动画
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        // 自动隐藏
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, duration);
    }
    
    // 页面状态管理
    onPageHidden() {
        // console.log('页面隐藏');
        // 可以在这里暂停一些不必要的操作
    }
    
    onPageVisible() {
        // console.log('页面显示');
        // 可以在这里恢复一些操作
    }
    
    onWindowResize() {
        // console.log('窗口大小变化');
        // 处理响应式布局调整
    }
    
    // 数据获取工具
    async fetchData(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('数据获取失败:', error);
            this.showToast('网络请求失败', 'error');
            throw error;
        }
    }
    
    // 本地存储工具
    setLocalStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('本地存储失败:', error);
        }
    }
    
    getLocalStorage(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('本地存储读取失败:', error);
            return defaultValue;
        }
    }
    
    // 设备检测
    isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }
    
    isIOS() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent);
    }
    
    isAndroid() {
        return /Android/.test(navigator.userAgent);
    }
    
    // 网络状态检测
    isOnline() {
        return navigator.onLine;
    }
    
    // 格式化工具
    formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }
    
    formatDate(date) {
        const now = new Date();
        const target = new Date(date);
        const diff = now - target;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        
        if (days === 0) {
            return '今天';
        } else if (days === 1) {
            return '昨天';
        } else if (days < 7) {
            return `${days}天前`;
        } else {
            return target.toLocaleDateString();
        }
    }
    
    // 动画工具
    animate(element, keyframes, options = {}) {
        if (element.animate) {
            return element.animate(keyframes, {
                duration: 300,
                easing: 'ease-in-out',
                ...options
            });
        } else {
            // 降级处理
            element.style.transition = `all ${options.duration || 300}ms ease-in-out`;
            return Promise.resolve();
        }
    }
    
    // 滚动工具
    smoothScrollTo(element, offset = 0) {
        const targetPosition = element.offsetTop - offset;
        window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
        });
    }
    
    // 复制到剪贴板
    async copyToClipboard(text) {
        try {
            if (navigator.clipboard) {
                await navigator.clipboard.writeText(text);
                this.showToast('已复制到剪贴板', 'success');
            } else {
                // 降级处理
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                this.showToast('已复制到剪贴板', 'success');
            }
        } catch (error) {
            console.error('复制失败:', error);
            this.showToast('复制失败', 'error');
        }
    }
}

// 全局应用实例
window.mobileApp = new MobileApp();

// 导出工具函数供其他模块使用
window.MobileUtils = {
    debounce: window.mobileApp.debounce.bind(window.mobileApp),
    throttle: window.mobileApp.throttle.bind(window.mobileApp),
    showToast: window.mobileApp.showToast.bind(window.mobileApp),
    fetchData: window.mobileApp.fetchData.bind(window.mobileApp),
    setLocalStorage: window.mobileApp.setLocalStorage.bind(window.mobileApp),
    getLocalStorage: window.mobileApp.getLocalStorage.bind(window.mobileApp),
    formatTime: window.mobileApp.formatTime.bind(window.mobileApp),
    formatDate: window.mobileApp.formatDate.bind(window.mobileApp),
    animate: window.mobileApp.animate.bind(window.mobileApp),
    copyToClipboard: window.mobileApp.copyToClipboard.bind(window.mobileApp)
}; 