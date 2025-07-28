// 设置页面JavaScript - 柔和绿色调配色方案

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('设置页面初始化');
    
    // 初始化设置项
    initSettings();
    
    // 初始化事件监听器
    initSettingsEvents();
    
    // 加载用户信息
    loadUserInfo();
    
    // 加载系统信息
    loadSystemInfo();
});

// 初始化设置项
function initSettings() {
    // 从本地存储加载设置
    const settings = loadSettingsFromStorage();
    
    // 应用设置到UI
    applySettingsToUI(settings);
}

// 初始化设置事件
function initSettingsEvents() {
    // 绑定设置开关事件
    const settingToggles = document.querySelectorAll('.setting-toggle');
    settingToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const setting = this.getAttribute('data-setting');
            toggleSetting(setting, this);
        });
    });
    
    // 绑定设置选择器事件
    const settingSelects = document.querySelectorAll('.setting-select');
    settingSelects.forEach(select => {
        select.addEventListener('change', function() {
            const setting = this.getAttribute('data-setting') || this.name;
            updateSetting(setting, this.value);
        });
    });
    
    // 绑定账户操作事件
    const actionItems = document.querySelectorAll('.action-item');
    actionItems.forEach(item => {
        item.addEventListener('click', function() {
            const action = this.textContent.trim();
            handleAccountAction(action, this);
        });
    });
}

// 切换设置开关
function toggleSetting(setting, element) {
    const isActive = element.classList.contains('active');
    
    // 添加加载状态
    element.classList.add('loading');
    
    // 模拟API调用
    setTimeout(() => {
        if (isActive) {
            element.classList.remove('active');
            element.innerHTML = '<i class="bi bi-toggle-off"></i>';
        } else {
            element.classList.add('active');
            element.innerHTML = '<i class="bi bi-toggle-on"></i>';
        }
        
        // 移除加载状态
        element.classList.remove('loading');
        
        // 保存设置
        saveSetting(setting, !isActive);
        
        // 显示提示
        showToast(`${getSettingName(setting)}已${!isActive ? '开启' : '关闭'}`);
    }, 500);
}

// 更新设置值
function updateSetting(setting, value) {
    // 添加加载状态
    const select = document.querySelector(`[data-setting="${setting}"]`) || 
                   document.querySelector(`[name="${setting}"]`);
    if (select) {
        select.classList.add('loading');
    }
    
    // 模拟API调用
    setTimeout(() => {
        // 移除加载状态
        if (select) {
            select.classList.remove('loading');
        }
        
        // 保存设置
        saveSetting(setting, value);
        
        // 显示提示
        showToast(`${getSettingName(setting)}已更新为${value}`);
    }, 300);
}

// 处理账户操作
function handleAccountAction(action, element) {
    // 添加加载状态
    element.classList.add('loading');
    
    switch(action) {
        case '修改个人信息':
            showPersonalInfoModal();
            break;
        case '修改密码':
            showPasswordModal();
            break;
        case '网络设置':
            showNetworkSettings();
            break;
        case '数据导出':
            exportData();
            break;
        case '帮助与反馈':
            showHelpFeedback();
            break;
        case '退出登录':
            confirmLogout();
            break;
        default:
            console.log('未知操作:', action);
    }
    
    // 移除加载状态
    setTimeout(() => {
        element.classList.remove('loading');
    }, 1000);
}

// 显示个人信息模态框
function showPersonalInfoModal() {
    showToast('个人信息修改功能开发中...');
}

// 显示密码修改模态框
function showPasswordModal() {
    showToast('密码修改功能开发中...');
}

// 显示网络设置
function showNetworkSettings() {
    showToast('网络设置功能开发中...');
}

// 导出数据
function exportData() {
    showToast('数据导出功能开发中...');
}

// 显示帮助与反馈
function showHelpFeedback() {
    showToast('帮助与反馈功能开发中...');
}

// 确认退出登录
function confirmLogout() {
    if (confirm('确定要退出登录吗？')) {
        logout();
    }
}

// 退出登录
function logout() {
    showToast('正在退出登录...');
    
    // 模拟退出登录
    setTimeout(() => {
        // 清除本地存储
        localStorage.clear();
        sessionStorage.clear();
        
        // 跳转到登录页面
        window.location.href = '/login';
    }, 1000);
}

// 加载用户信息
function loadUserInfo() {
    // 模拟从API获取用户信息
    const userInfo = {
        username: '家长用户',
        role: '管理员',
        avatar: null
    };
    
    // 更新UI
    const usernameElement = document.querySelector('.username');
    const userRoleElement = document.querySelector('.user-role');
    
    if (usernameElement) {
        usernameElement.textContent = userInfo.username;
    }
    
    if (userRoleElement) {
        userRoleElement.textContent = userInfo.role;
    }
}

// 加载系统信息
function loadSystemInfo() {
    // 模拟从API获取系统信息
    const systemInfo = {
        version: 'v2.1.0',
        lastUpdate: '2025-07-20',
        deviceId: 'TL-001-2025'
    };
    
    // 更新UI
    const versionElement = document.querySelector('.info-item:nth-child(1) .info-value');
    const updateElement = document.querySelector('.info-item:nth-child(2) .info-value');
    const deviceElement = document.querySelector('.info-item:nth-child(3) .info-value');
    
    if (versionElement) {
        versionElement.textContent = systemInfo.version;
    }
    
    if (updateElement) {
        updateElement.textContent = systemInfo.lastUpdate;
    }
    
    if (deviceElement) {
        deviceElement.textContent = systemInfo.deviceId;
    }
}

// 从本地存储加载设置
function loadSettingsFromStorage() {
    const defaultSettings = {
        posture: true,
        eye: true,
        emotion: false,
        report: true,
        sensitivity: 'medium',
        photoFrequency: '10',
        dataRetention: '30'
    };
    
    try {
        const stored = localStorage.getItem('appSettings');
        return stored ? { ...defaultSettings, ...JSON.parse(stored) } : defaultSettings;
    } catch (error) {
        console.error('加载设置失败:', error);
        return defaultSettings;
    }
}

// 保存设置到本地存储
function saveSetting(key, value) {
    try {
        const settings = loadSettingsFromStorage();
        settings[key] = value;
        localStorage.setItem('appSettings', JSON.stringify(settings));
        
        // 发送设置到服务器
        sendSettingsToServer(key, value);
    } catch (error) {
        console.error('保存设置失败:', error);
    }
}

// 发送设置到服务器
function sendSettingsToServer(key, value) {
    const data = {
        setting: key,
        value: value
    };
    
    fetch('/api/settings/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(result => {
        console.log('设置更新成功:', result);
    })
    .catch(error => {
        console.error('设置更新失败:', error);
        // 可以在这里显示错误提示
    });
}

// 应用设置到UI
function applySettingsToUI(settings) {
    // 应用开关设置
    Object.keys(settings).forEach(key => {
        const toggle = document.querySelector(`[data-setting="${key}"]`);
        if (toggle) {
            if (settings[key] === true) {
                toggle.classList.add('active');
                toggle.innerHTML = '<i class="bi bi-toggle-on"></i>';
            } else if (settings[key] === false) {
                toggle.classList.remove('active');
                toggle.innerHTML = '<i class="bi bi-toggle-off"></i>';
            }
        }
        
        // 应用选择器设置
        const select = document.querySelector(`[data-setting="${key}"]`) || 
                      document.querySelector(`[name="${key}"]`);
        if (select && typeof settings[key] === 'string') {
            select.value = settings[key];
        }
    });
}

// 获取设置名称
function getSettingName(setting) {
    const settingNames = {
        posture: '姿势提醒',
        eye: '用眼提醒',
        emotion: '情绪异常',
        report: '学习报告',
        sensitivity: '检测灵敏度',
        photoFrequency: '拍照频率',
        dataRetention: '数据保存'
    };
    
    return settingNames[setting] || setting;
}

// 显示提示消息
function showToast(message) {
    // 创建toast元素
    const toast = document.createElement('div');
    toast.className = 'mobile-toast';
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
    
    // 显示动画
    setTimeout(() => {
        toast.style.opacity = '1';
    }, 100);
    
    // 自动隐藏
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
    // 清理定时器等资源
    console.log('设置页面卸载');
});

// 导出函数供其他模块使用
window.settingsModule = {
    toggleSetting,
    updateSetting,
    saveSetting,
    loadSettingsFromStorage,
    showToast
}; 