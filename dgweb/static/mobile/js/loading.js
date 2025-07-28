// 欢迎界面JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('欢迎界面已准备就绪');
    
    // 添加触摸事件支持
    addTouchSupport();
    
    // 添加按钮点击事件
    const startButton = document.getElementById('startButton');
    if (startButton) {
        startButton.addEventListener('click', startApp);
    }
});

function startApp() {
    // 添加点击效果
    const button = document.querySelector('.start-button');
    if (button) {
        button.style.transform = 'scale(0.95)';
        
        // 添加过渡动画
        setTimeout(() => {
            button.style.transform = 'scale(1)';
        }, 100);
        
        setTimeout(() => {
            // 跳转到主页
            window.location.href = '/mobile/home';
        }, 150);
    }
}

function addTouchSupport() {
    // 防止页面滚动
    document.addEventListener('touchmove', function(e) {
        e.preventDefault();
    }, { passive: false });
    
    // 添加触摸反馈
    const button = document.querySelector('.start-button');
    if (button) {
        button.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.95)';
        });
        
        button.addEventListener('touchend', function() {
            this.style.transform = 'scale(1)';
        });
    }
}

// 页面可见性变化处理
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        console.log('页面隐藏');
    } else {
        console.log('页面显示');
    }
});

// 错误处理
window.addEventListener('error', function(e) {
    console.error('页面加载错误:', e.error);
});

// 网络状态检测
window.addEventListener('online', function() {
    console.log('网络连接已恢复');
});

window.addEventListener('offline', function() {
    console.log('网络连接已断开');
}); 