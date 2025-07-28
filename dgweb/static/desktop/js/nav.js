// 导航栏功能
class NavigationManager {
    constructor() {
        this.currentPage = null;
        this.navItems = [];
        this.isInitialized = false;
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        this.setupNavigation();
        this.setupActiveState();
        this.setupAnimations();
        this.isInitialized = true;
        
        console.log('导航栏初始化完成');
    }
    
    setupNavigation() {
        this.navItems = document.querySelectorAll('.nav-item');
        
        this.navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleNavigation(item);
            });
            
            // 添加触摸反馈
            item.addEventListener('touchstart', () => {
                this.addTouchFeedback(item);
            });
            
            item.addEventListener('touchend', () => {
                this.removeTouchFeedback(item);
            });
        });
    }
    
    setupActiveState() {
        // 根据当前URL设置活动状态
        const currentPath = window.location.pathname;
        this.navItems.forEach(item => {
            const href = item.getAttribute('href');
            if (href && currentPath.includes(href.split('/').pop())) {
                this.setActiveItem(item);
            }
        });
    }
    
    setupAnimations() {
        // 添加导航项的进入动画
        this.navItems.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                item.style.transition = 'all 0.3s ease-out';
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }
    
    handleNavigation(item) {
        const href = item.getAttribute('href');
        if (!href) return;
        
        // 添加点击动画
        this.addClickAnimation(item);
        
        // 更新活动状态
        this.setActiveItem(item);
        
        // 导航到新页面
        setTimeout(() => {
            window.location.href = href;
        }, 150);
    }
    
    setActiveItem(item) {
        // 移除所有活动状态
        this.navItems.forEach(navItem => {
            navItem.classList.remove('active');
        });
        
        // 设置当前项为活动状态
        item.classList.add('active');
        this.currentPage = item;
        
        // 触发活动动画
        this.triggerActiveAnimation(item);
    }
    
    addTouchFeedback(item) {
        item.style.transform = 'scale(0.95)';
        item.style.transition = 'transform 0.1s ease-out';
    }
    
    removeTouchFeedback(item) {
        item.style.transform = 'scale(1)';
    }
    
    addClickAnimation(item) {
        // 创建涟漪效果
        const ripple = document.createElement('div');
        ripple.className = 'nav-ripple';
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
            z-index: 1;
        `;
        
        item.appendChild(ripple);
        
        // 动画
        requestAnimationFrame(() => {
            ripple.style.transition = 'all 0.3s ease-out';
            ripple.style.width = '60px';
            ripple.style.height = '60px';
            ripple.style.opacity = '0';
        });
        
        // 清理
        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 300);
    }
    
    triggerActiveAnimation(item) {
        const icon = item.querySelector('.nav-icon');
        const text = item.querySelector('span');
        
        if (icon) {
            icon.style.transform = 'scale(1.2)';
            setTimeout(() => {
                icon.style.transform = 'scale(1.1)';
            }, 150);
        }
        
        if (text) {
            text.style.transform = 'scale(1.1)';
            setTimeout(() => {
                text.style.transform = 'scale(1)';
            }, 150);
        }
    }
    
    // 获取当前页面
    getCurrentPage() {
        return this.currentPage;
    }
    
    // 检查是否在指定页面
    isOnPage(pageName) {
        return this.currentPage && this.currentPage.getAttribute('href').includes(pageName);
    }
    
    // 导航到指定页面
    navigateTo(pageName) {
        const targetItem = Array.from(this.navItems).find(item => 
            item.getAttribute('href').includes(pageName)
        );
        
        if (targetItem) {
            this.handleNavigation(targetItem);
        }
    }
}

// 初始化导航管理器
window.navigationManager = new NavigationManager();

// 添加导航栏样式
const navStyles = `
    .nav-ripple {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        background: rgba(74, 144, 226, 0.3);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        pointer-events: none;
        z-index: 1;
        transition: all 0.3s ease-out;
    }
    
    .nav-item:active {
        transform: scale(0.95);
    }
    
    .nav-item:active .nav-icon {
        transform: scale(1.1);
    }
    
    .nav-item:active span {
        transform: scale(1.05);
    }
`;

// 注入样式
if (!document.getElementById('nav-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'nav-styles';
    styleSheet.textContent = navStyles;
    document.head.appendChild(styleSheet);
} 