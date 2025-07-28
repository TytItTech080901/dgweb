// 家长监护页面功能
class GuardianPage {
    constructor() {
        this.isInitialized = false;
        this.videoStream = null;
        this.isVideoPaused = false;
        this.messageHistory = [];
        this.updateInterval = null;
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        this.setupEventListeners();
        this.loadInitialData();
        this.startVideoStream();
        this.startAutoUpdate();
        this.isInitialized = true;
        
        console.log('家长监护页面初始化完成');
    }
    
    setupEventListeners() {
        // 视频控制按钮
        const pauseBtn = document.getElementById('pauseVideo');
        const captureBtn = document.getElementById('captureBtn');
        const fullscreenBtn = document.getElementById('fullscreenBtn');
        
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => this.toggleVideoPause());
        }
        
        if (captureBtn) {
            captureBtn.addEventListener('click', () => this.capturePhoto());
        }
        
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        }
        
        // 消息发送
        const sendBtn = document.getElementById('sendMessage');
        const addMessageBtn = document.getElementById('addMessage');
        
        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }
        
        if (addMessageBtn) {
            addMessageBtn.addEventListener('click', () => this.showMessageInput());
        }
        
        // 消息输入框回车发送
        const messageInput = document.getElementById('messageContent');
        if (messageInput) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }
    }
    
    async loadInitialData() {
        try {
            // 加载消息历史
            await this.loadMessageHistory();
            
            // 更新UI
            this.updateMessageDisplay();
            
        } catch (error) {
            console.error('加载监护数据失败:', error);
            MobileUtils.showToast('数据加载失败', 'error');
        }
    }
    
    async loadMessageHistory() {
        try {
            const response = await MobileUtils.fetchData('/api/guardian/messages');
            this.messageHistory = response;
            
            // 保存到本地存储
            MobileUtils.setLocalStorage('guardianMessages', this.messageHistory);
            
        } catch (error) {
            console.warn('API请求失败，使用本地数据:', error);
            this.messageHistory = MobileUtils.getLocalStorage('guardianMessages', this.getDefaultMessages());
        }
    }
    
    getDefaultMessages() {
        return [
            {
                id: 1,
                sender: 'parent',
                content: '记得保持正确坐姿哦',
                type: 'sent',
                timestamp: new Date(Date.now() - 3600000).toISOString()
            },
            {
                id: 2,
                sender: 'scheduled',
                content: '该休息一下眼睛了',
                type: 'scheduled',
                timestamp: new Date(Date.now() + 1800000).toISOString()
            }
        ];
    }
    
    updateMessageDisplay() {
        const container = document.getElementById('messageHistory');
        if (!container) return;
        
        // 清空容器
        container.innerHTML = '';
        
        // 添加消息项
        this.messageHistory.forEach(message => {
            const messageEl = this.createMessageElement(message);
            container.appendChild(messageEl);
        });
        
        // 滚动到底部
        container.scrollTop = container.scrollHeight;
    }
    
    createMessageElement(message) {
        const messageEl = document.createElement('div');
        messageEl.className = `message-item ${message.type}`;
        
        const sender = message.sender === 'parent' ? '家长' : '定时消息';
        const icon = message.sender === 'parent' ? 'bi-person-check' : 'bi-clock';
        const time = MobileUtils.formatDate(message.timestamp);
        
        messageEl.innerHTML = `
            <div class="message-sender">
                <i class="bi ${icon}"></i>
                ${sender}
            </div>
            <div class="message-content">${message.content}</div>
            <div class="message-time">${time}</div>
        `;
        
        return messageEl;
    }
    
    startVideoStream() {
        const videoEl = document.getElementById('guardianVideo');
        if (!videoEl) return;
        
        // 模拟视频流
        this.videoStream = setInterval(() => {
            if (!this.isVideoPaused) {
                // 更新视频状态
                this.updateVideoStatus();
            }
        }, 1000);
    }
    
    updateVideoStatus() {
        const statusEl = document.querySelector('.monitor-status');
        if (statusEl) {
            const dot = statusEl.querySelector('.status-dot');
            if (dot) {
                dot.style.animation = this.isVideoPaused ? 'none' : 'pulse 1.5s infinite';
            }
        }
    }
    
    toggleVideoPause() {
        this.isVideoPaused = !this.isVideoPaused;
        
        const pauseBtn = document.getElementById('pauseVideo');
        if (pauseBtn) {
            const icon = pauseBtn.querySelector('i');
            if (icon) {
                icon.className = this.isVideoPaused ? 'bi bi-play' : 'bi bi-pause';
            }
        }
        
        const statusEl = document.querySelector('.monitor-status span:last-child');
        if (statusEl) {
            statusEl.textContent = this.isVideoPaused ? '已暂停' : '直播中';
        }
        
        this.updateVideoStatus();
        
        MobileUtils.showToast(
            this.isVideoPaused ? '视频已暂停' : '视频已恢复',
            'info'
        );
    }
    
    async capturePhoto() {
        try {
            const captureBtn = document.getElementById('captureBtn');
            if (captureBtn) {
                captureBtn.disabled = true;
                captureBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i>';
            }
            
            const response = await MobileUtils.fetchData('/api/guardian/capture', {
                method: 'POST'
            });
            
            if (response.success) {
                MobileUtils.showToast('拍照成功', 'success');
                
                // 模拟拍照效果
                const videoEl = document.getElementById('guardianVideo');
                if (videoEl) {
                    videoEl.style.filter = 'brightness(1.2)';
                    setTimeout(() => {
                        videoEl.style.filter = 'brightness(1)';
                    }, 200);
                }
            } else {
                throw new Error('拍照失败');
            }
            
        } catch (error) {
            console.error('拍照失败:', error);
            MobileUtils.showToast('拍照失败', 'error');
        } finally {
            const captureBtn = document.getElementById('captureBtn');
            if (captureBtn) {
                captureBtn.disabled = false;
                captureBtn.innerHTML = '<i class="bi bi-camera"></i>';
            }
        }
    }
    
    toggleFullscreen() {
        const videoContainer = document.querySelector('.video-container');
        if (!videoContainer) return;
        
        if (!document.fullscreenElement) {
            videoContainer.requestFullscreen().catch(err => {
                console.error('全屏失败:', err);
                MobileUtils.showToast('全屏失败', 'error');
            });
        } else {
            document.exitFullscreen();
        }
    }
    
    showMessageInput() {
        const messageInput = document.getElementById('messageContent');
        if (messageInput) {
            messageInput.focus();
            messageInput.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    async sendMessage() {
        const messageInput = document.getElementById('messageContent');
        const messageType = document.getElementById('messageType');
        
        if (!messageInput || !messageType) return;
        
        const content = messageInput.value.trim();
        const type = messageType.value;
        
        if (!content) {
            MobileUtils.showToast('请输入消息内容', 'warning');
            return;
        }
        
        try {
            const response = await MobileUtils.fetchData('/api/guardian/send_message', {
                method: 'POST',
                body: JSON.stringify({
                    content: content,
                    type: type
                })
            });
            
            if (response.success) {
                // 添加到消息历史
                this.messageHistory.unshift(response.message);
                
                // 更新显示
                this.updateMessageDisplay();
                
                // 清空输入框
                messageInput.value = '';
                
                MobileUtils.showToast('消息发送成功', 'success');
                
                // 保存到本地存储
                MobileUtils.setLocalStorage('guardianMessages', this.messageHistory);
                
            } else {
                throw new Error('发送失败');
            }
            
        } catch (error) {
            console.error('发送消息失败:', error);
            MobileUtils.showToast('发送失败', 'error');
        }
    }
    
    startAutoUpdate() {
        // 每10秒更新一次数据
        this.updateInterval = setInterval(() => {
            this.loadMessageHistory().then(() => {
                this.updateMessageDisplay();
            });
        }, 10000);
    }
    
    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        if (this.videoStream) {
            clearInterval(this.videoStream);
            this.videoStream = null;
        }
    }
    
    // 页面可见性变化处理
    onPageVisible() {
        console.log('监护页面变为可见');
        this.loadMessageHistory().then(() => {
            this.updateMessageDisplay();
        });
    }
    
    onPageHidden() {
        console.log('监护页面变为隐藏');
        this.stopAutoUpdate();
    }
    
    // 清理资源
    destroy() {
        this.stopAutoUpdate();
        this.isInitialized = false;
    }
}

// 初始化监护页面
document.addEventListener('DOMContentLoaded', () => {
    window.guardianPage = new GuardianPage();
    
    // 页面可见性变化监听
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            window.guardianPage.onPageHidden();
        } else {
            window.guardianPage.onPageVisible();
        }
    });
});

// 页面卸载时清理
window.addEventListener('beforeunload', () => {
    if (window.guardianPage) {
        window.guardianPage.destroy();
    }
}); 