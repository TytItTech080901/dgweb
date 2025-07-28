// 远程控制页面JavaScript - 柔和绿色调配色方案

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('远程控制页面初始化');
    
    // 初始化台灯状态
    fetchLampStatus();
    
    // 设置定时器定期更新状态
    setInterval(fetchLampStatus, 5000);
    
    // 初始化事件监听器
    initRemoteControlEvents();
});

// 初始化远程控制事件
function initRemoteControlEvents() {
    // 绑定按钮事件
    const powerBtn = document.getElementById('power-btn');
    const lightBtn = document.getElementById('light-btn');
    
    if (powerBtn) {
        powerBtn.addEventListener('click', togglePower);
    }
    
    if (lightBtn) {
        lightBtn.addEventListener('click', toggleLight);
    }
    
    // 绑定滑块事件
    const brightnessSlider = document.getElementById('brightness-slider');
    const temperatureSlider = document.getElementById('temperature-slider');
    
    if (brightnessSlider) {
        brightnessSlider.addEventListener('input', function() {
            adjustBrightness(this.value);
        });
    }
    
    if (temperatureSlider) {
        temperatureSlider.addEventListener('input', function() {
            adjustTemperature(this.value);
        });
    }
    
    // 绑定护眼模式开关事件
    const eyeCareMode = document.getElementById('eye-care-mode');
    if (eyeCareMode) {
        eyeCareMode.addEventListener('change', toggleEyeCareMode);
    }
}

// 电源开关控制
function togglePower() {
    const powerBtn = document.getElementById('power-btn');
    const lampStatus = document.getElementById('lampStatus');
    
    if (powerBtn.classList.contains('on')) {
        // 关闭电源
        powerBtn.classList.remove('on');
        powerBtn.innerHTML = '<i class="bi bi-power"></i>台灯电源';
        if (lampStatus) {
            lampStatus.textContent = '已关闭';
        }
        sendLampCommand('power_off');
    } else {
        // 开启电源
        powerBtn.classList.add('on');
        powerBtn.innerHTML = '<i class="bi bi-power"></i>台灯电源';
        if (lampStatus) {
            lampStatus.textContent = '已开启';
        }
        sendLampCommand('power_on');
    }
}

// 灯光开关控制
function toggleLight() {
    const lightBtn = document.getElementById('light-btn');
    const lampStatus = document.getElementById('lampStatus');
    
    if (lightBtn.classList.contains('on')) {
        // 关闭灯光
        lightBtn.classList.remove('on');
        lightBtn.innerHTML = '<i class="bi bi-lightbulb"></i>灯光开关';
        if (lampStatus) {
            lampStatus.textContent = '已关闭';
        }
        sendLampCommand('light_off');
    } else {
        // 开启灯光
        lightBtn.classList.add('on');
        lightBtn.innerHTML = '<i class="bi bi-lightbulb"></i>灯光开关';
        if (lampStatus) {
            lampStatus.textContent = '已开启';
        }
        sendLampCommand('light_on');
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

// 获取台灯状态
function fetchLampStatus() {
    fetch('/api/lamp/status')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            updateLampStatusUI(data);
        })
        .catch(error => {
            console.error('获取台灯状态失败:', error);
            // 使用模拟数据作为备用
            updateLampStatusUI({
                status: 'success',
                data: {
                    power: true,
                    brightness: 500,
                    color_temp: 5300
                }
            });
        });
}

// 更新台灯状态UI
function updateLampStatusUI(data) {
    // 处理电源状态
    if (data.data && data.data.power !== undefined) {
        const powerBtn = document.getElementById('power-btn');
        const lightBtn = document.getElementById('light-btn');
        const lampStatus = document.getElementById('lampStatus');
        
        if (powerBtn) {
            if (data.data.power) {
                powerBtn.classList.add('on');
                powerBtn.innerHTML = '<i class="bi bi-power"></i>台灯电源';
            } else {
                powerBtn.classList.remove('on');
                powerBtn.innerHTML = '<i class="bi bi-power"></i>台灯电源';
            }
        }
        
        if (lightBtn) {
            if (data.data.power) {
                lightBtn.classList.add('on');
                lightBtn.innerHTML = '<i class="bi bi-lightbulb"></i>灯光开关';
            } else {
                lightBtn.classList.remove('on');
                lightBtn.innerHTML = '<i class="bi bi-lightbulb"></i>灯光开关';
            }
        }
        
        if (lampStatus) {
            lampStatus.textContent = data.data.power ? '已开启' : '已关闭';
        }
    }
    
    // 处理亮度
    if (data.data && data.data.brightness !== undefined) {
        const brightnessSlider = document.getElementById('brightness-slider');
        const brightnessDisplay = document.getElementById('brightness-display');
        const currentBrightness = document.getElementById('currentBrightness');
        
        if (brightnessSlider) {
            brightnessSlider.value = data.data.brightness;
        }
        if (brightnessDisplay) {
            brightnessDisplay.textContent = data.data.brightness;
        }
        if (currentBrightness) {
            currentBrightness.textContent = data.data.brightness;
        }
    }
    
    // 处理色温
    if (data.data && data.data.color_temp !== undefined) {
        const temperatureSlider = document.getElementById('temperature-slider');
        const temperatureDisplay = document.getElementById('temperature-display');
        const currentTemperature = document.getElementById('currentTemperature');
        
        const tempValue = data.data.color_temp + 'K';
        if (temperatureSlider) {
            temperatureSlider.value = data.data.color_temp;
        }
        if (temperatureDisplay) {
            temperatureDisplay.textContent = tempValue;
        }
        if (currentTemperature) {
            currentTemperature.textContent = tempValue;
        }
    }
    
    // 兼容旧格式（保持向后兼容）
    if (data.power_status !== undefined) {
        const powerBtn = document.getElementById('power-btn');
        const lightBtn = document.getElementById('light-btn');
        const lampStatus = document.getElementById('lampStatus');
        
        if (powerBtn) {
            if (data.power_status) {
                powerBtn.classList.add('on');
                powerBtn.innerHTML = '<i class="bi bi-power"></i>台灯电源';
            } else {
                powerBtn.classList.remove('on');
                powerBtn.innerHTML = '<i class="bi bi-power"></i>台灯电源';
            }
        }
        
        if (lightBtn) {
            if (data.power_status) {
                lightBtn.classList.add('on');
                lightBtn.innerHTML = '<i class="bi bi-lightbulb"></i>灯光开关';
            } else {
                lightBtn.classList.remove('on');
                lightBtn.innerHTML = '<i class="bi bi-lightbulb"></i>灯光开关';
            }
        }
        
        if (lampStatus) {
            lampStatus.textContent = data.power_status ? '已开启' : '已关闭';
        }
    }
    
    if (data.light_status !== undefined) {
        const lightBtn = document.getElementById('light-btn');
        const lampStatus = document.getElementById('lampStatus');
        
        if (lightBtn) {
            if (data.light_status) {
                lightBtn.classList.add('on');
                lightBtn.innerHTML = '<i class="bi bi-lightbulb"></i>灯光开关';
            } else {
                lightBtn.classList.remove('on');
                lightBtn.innerHTML = '<i class="bi bi-lightbulb"></i>灯光开关';
            }
        }
        
        if (lampStatus) {
            lampStatus.textContent = data.light_status ? '已开启' : '已关闭';
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
    console.log('远程控制页面卸载');
}); 