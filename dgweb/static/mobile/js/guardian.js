// 家长监护页面功能
class GuardianPage {
    constructor() {
        this.isInitialized = false;
        this.videoStream = null;
        this.isVideoPaused = false;
        this.messageHistory = [];
        this.scheduledMessages = [];
        this.currentTab = 'push';
        this.updateInterval = null;
        this.historyUpdateInterval = null;
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        this.setupEventListeners();
        this.loadInitialData();
        this.startVideoStream();
        this.startAutoUpdate();
        this.startHistoryUpdate();
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
        
        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
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
        
        // 家长监护tab切换事件
        const tabBtns = document.querySelectorAll('.guardian-tab-btn');
        const tabPanels = document.querySelectorAll('.guardian-tab-panel');
        
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
                
                window.guardianPage.currentTab = tab;
            });
        });
        
        // 网络状态监听
        window.addEventListener('online', () => {
            console.log('网络连接恢复');
            this.showToast('网络连接已恢复', 'success');
        });
        
        window.addEventListener('offline', () => {
            console.log('网络连接断开');
            this.showToast('网络连接已断开，使用本地数据', 'warning');
        });
    }
    
    async loadInitialData() {
        try {
            console.log('开始加载初始数据...');
            
            // 加载消息历史
            await this.loadMessageHistory();
            console.log('消息历史加载完成，数量:', this.messageHistory.length);
            
            // 加载定时消息
            await this.loadScheduledMessages();
            console.log('定时消息加载完成，数量:', this.scheduledMessages.length);
            
            // 更新UI
            this.updateMessageDisplay();
            this.updateScheduledMessagesDisplay();
            
            console.log('初始数据加载完成');
            
        } catch (error) {
            console.error('加载监护数据失败:', error);
            this.showToast('数据加载失败', 'error');
        }
    }
    
    async loadMessageHistory() {
        try {
            const response = await this.fetchData('/api/guardian/messages');
            if (response && Array.isArray(response)) {
                this.messageHistory = response;
                // 保存到本地存储
                this.setLocalStorage('guardianMessages', this.messageHistory);
            } else {
                throw new Error('Invalid response format');
            }
        } catch (error) {
            console.warn('API请求失败，使用本地数据:', error);
            const localData = this.getLocalStorage('guardianMessages', null);
            if (localData && Array.isArray(localData)) {
                this.messageHistory = localData;
            } else {
                this.messageHistory = this.getDefaultMessages();
                this.setLocalStorage('guardianMessages', this.messageHistory);
            }
        }
    }
    
    async loadScheduledMessages() {
        try {
            const response = await this.fetchData('/api/guardian/scheduled_messages');
            if (response && Array.isArray(response)) {
                this.scheduledMessages = response;
                // 保存到本地存储
                this.setLocalStorage('guardianScheduledMessages', this.scheduledMessages);
            } else {
                throw new Error('Invalid response format');
            }
        } catch (error) {
            console.warn('API请求失败，使用本地数据:', error);
            const localData = this.getLocalStorage('guardianScheduledMessages', null);
            if (localData && Array.isArray(localData)) {
                this.scheduledMessages = localData;
            } else {
                this.scheduledMessages = this.getDefaultScheduledMessages();
                this.setLocalStorage('guardianScheduledMessages', this.scheduledMessages);
            }
        }
    }
    
    getDefaultMessages() {
        return [
            {
                id: 1,
                sender: 'parent',
                content: '记得保持正确坐姿哦',
                type: 'immediate',
                timestamp: new Date(Date.now() - 3600000).toISOString()
            },
            {
                id: 2,
                sender: 'parent',
                content: '该休息一下眼睛了',
                type: 'immediate',
                timestamp: new Date(Date.now() - 1800000).toISOString()
            }
        ];
    }
    
    getDefaultScheduledMessages() {
        return [
            {
                id: 1,
                content: '记得保持正确坐姿哦',
                scheduledTime: new Date(Date.now() + 1800000).toISOString(),
                status: 'pending'
            },
            {
                id: 2,
                content: '该休息一下眼睛了',
                scheduledTime: new Date(Date.now() + 3600000).toISOString(),
                status: 'pending'
            }
        ];
    }
    
    updateMessageDisplay() {
        const container = document.getElementById('messageHistory');
        if (!container) return;
        
        console.log('更新消息显示，当前消息数量:', this.messageHistory.length);
        
        // 清空容器
        container.innerHTML = '';
        
        // 只显示最新的10条消息
        const recentMessages = this.messageHistory.slice(0, 10);
        
        if (recentMessages.length === 0) {
            container.innerHTML = '<div class="empty-state">暂无历史消息</div>';
            console.log('显示空状态');
            return;
        }
        
        // 添加消息项
        recentMessages.forEach(message => {
            const messageEl = this.createMessageElement(message);
            container.appendChild(messageEl);
        });
        
        console.log('显示消息数量:', recentMessages.length);
        
        // 滚动到底部
        container.scrollTop = container.scrollHeight;
    }
    
    updateScheduledMessagesDisplay() {
        const container = document.getElementById('scheduledMessages');
        if (!container) return;
        
        // 清空容器
        container.innerHTML = '';
        
        if (this.scheduledMessages.length === 0) {
            container.innerHTML = '<div class="empty-state">暂无定时消息</div>';
            return;
        }
        
        // 添加定时消息项
        this.scheduledMessages.forEach(message => {
            const messageEl = this.createScheduledMessageElement(message);
            container.appendChild(messageEl);
        });
    }
    
    createMessageElement(message) {
        const messageEl = document.createElement('div');
        messageEl.className = `message-item ${message.type}`;
        
        const sender = '家长';
        const icon = 'bi-person-check';
        const time = this.formatDate(message.timestamp);
        const typeText = message.type === 'immediate' ? '立即发送' : '定时发送';
        
        messageEl.innerHTML = `
            <div class="message-sender">
                <i class="bi ${icon}"></i>
                ${sender} (${typeText})
            </div>
            <div class="message-content">${message.content}</div>
            <div class="message-time">${time}</div>
        `;
        
        return messageEl;
    }
    
    createScheduledMessageElement(message) {
        const messageEl = document.createElement('div');
        messageEl.className = 'scheduled-message-item';
        
        const scheduledTime = this.formatDate(message.scheduledTime);
        const statusText = message.status === 'pending' ? '待发送' : '已发送';
        
        messageEl.innerHTML = `
            <div class="scheduled-message-time">${scheduledTime} (${statusText})</div>
            <div class="scheduled-message-content">${message.content}</div>
            <div class="scheduled-message-actions">
                <button class="edit-btn" onclick="window.guardianPage.editScheduledMessage(${message.id})">编辑</button>
                <button class="delete-btn" onclick="window.guardianPage.deleteScheduledMessage(${message.id})">删除</button>
            </div>
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
        
        this.showToast(
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
            
            const response = await this.fetchData('/api/guardian/capture', {
                method: 'POST'
            });
            
            if (response.success) {
                this.showToast('拍照成功', 'success');
                
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
            this.showToast('拍照失败', 'error');
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
                this.showToast('全屏失败', 'error');
            });
        } else {
            document.exitFullscreen();
        }
    }
    
    async sendMessage() {
        const messageInput = document.getElementById('messageContent');
        const messageType = document.getElementById('messageType');
        
        if (!messageInput || !messageType) return;
        
        const content = messageInput.value.trim();
        const type = messageType.value;
        
        if (!content) {
            this.showToast('请输入消息内容', 'warning');
            return;
        }
        
        // 创建新消息
        const newMessage = {
            id: Date.now(),
            sender: 'parent',
            content: content,
            type: type,
            timestamp: new Date().toISOString()
        };
        
        try {
            const response = await this.fetchData('/api/guardian/send_message', {
                method: 'POST',
                body: JSON.stringify({
                    content: content,
                    type: type
                })
            });
            
            if (response.success) {
                this.showToast('消息发送成功', 'success');
            } else {
                throw new Error('发送失败');
            }
            
        } catch (error) {
            console.error('发送消息失败:', error);
            this.showToast('消息已保存到本地', 'info');
        }
        
        // 无论API是否成功，都添加到本地历史记录
        this.messageHistory.unshift(newMessage);
        
        // 只保留最新的10条消息
        if (this.messageHistory.length > 10) {
            this.messageHistory = this.messageHistory.slice(0, 10);
        }
        
        // 更新显示
        this.updateMessageDisplay();
        
        // 清空输入框
        messageInput.value = '';
        
        // 保存到本地存储
        this.setLocalStorage('guardianMessages', this.messageHistory);
    }
    
    editScheduledMessage(messageId) {
        const message = this.scheduledMessages.find(m => m.id === messageId);
        if (message) {
            this.showToast('编辑定时消息功能开发中', 'info');
        }
    }
    
    deleteScheduledMessage(messageId) {
        const index = this.scheduledMessages.findIndex(m => m.id === messageId);
        if (index !== -1) {
            this.scheduledMessages.splice(index, 1);
            this.updateScheduledMessagesDisplay();
            this.setLocalStorage('guardianScheduledMessages', this.scheduledMessages);
            this.showToast('定时消息已删除', 'success');
        }
    }
    
    startAutoUpdate() {
        // 每30秒更新一次数据，减少频率避免频繁API请求
        this.updateInterval = setInterval(() => {
            // 只在有网络连接时才尝试更新
            if (navigator.onLine) {
                this.loadMessageHistory().then(() => {
                    this.updateMessageDisplay();
                }).catch(() => {
                    // 如果更新失败，保持当前显示
                    console.log('自动更新失败，保持当前数据');
                });
            }
        }, 30000);
    }
    
    startHistoryUpdate() {
        // 每2分钟更新一次历史留言板，减少频率
        this.historyUpdateInterval = setInterval(() => {
            // 只在有网络连接时才尝试更新
            if (navigator.onLine) {
                this.loadMessageHistory().then(() => {
                    this.updateMessageDisplay();
                }).catch(() => {
                    // 如果更新失败，保持当前显示
                    console.log('历史更新失败，保持当前数据');
                });
            }
        }, 120000);
    }
    
    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        if (this.historyUpdateInterval) {
            clearInterval(this.historyUpdateInterval);
            this.historyUpdateInterval = null;
        }
        
        if (this.videoStream) {
            clearInterval(this.videoStream);
            this.videoStream = null;
        }
    }
    
    // 页面可见性变化处理
    onPageVisible() {
        console.log('监护页面变为可见');
        // 只在有网络连接时才尝试更新
        if (navigator.onLine) {
            this.loadMessageHistory().then(() => {
                this.updateMessageDisplay();
            }).catch(() => {
                // 如果更新失败，保持当前显示
                console.log('页面可见性更新失败，保持当前数据');
            });
        }
    }
    
    onPageHidden() {
        console.log('监护页面变为隐藏');
        this.stopAutoUpdate();
    }
    
    // 工具方法
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
            console.log('API请求失败，使用本地数据:', error.message);
            throw error;
        }
    }
    
    setLocalStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('LocalStorage set error:', error);
        }
    }
    
    getLocalStorage(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('LocalStorage get error:', error);
            return defaultValue;
        }
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) { // 1分钟内
            return '刚刚';
        } else if (diff < 3600000) { // 1小时内
            return `${Math.floor(diff / 60000)}分钟前`;
        } else if (diff < 86400000) { // 1天内
            return `${Math.floor(diff / 3600000)}小时前`;
        } else {
            return date.toLocaleDateString();
        }
    }
    
    showToast(message) {
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