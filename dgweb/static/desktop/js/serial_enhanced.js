/**
 * 增强版串口通信功能
 */

// 全局变量
let commandHistory = [];  // 存储命令历史
let historyIndex = -1;    // 当前历史命令索引

// 初始化增强版串口功能
document.addEventListener('DOMContentLoaded', function() {
    // 初始化历史命令导航按钮
    initCommandNavigation();
    
    // 初始化帧模式滑块
    initFrameSliders();
    
    // 初始化模式切换按钮
    initModeButtons();
});

// 初始化命令历史导航
function initCommandNavigation() {
    const commandInput = document.getElementById('commandInput');
    const dataInput = document.getElementById('dataInput');
    const arrowUpBtn = document.getElementById('arrowUpBtn');
    const arrowDownBtn = document.getElementById('arrowDownBtn');
    const clearCommandHistoryBtn = document.getElementById('clearCommandHistoryBtn');
    
    if (arrowUpBtn) {
        arrowUpBtn.addEventListener('click', function() {
            navigateCommandHistory('up', commandInput);
        });
    }
    
    if (arrowDownBtn) {
        arrowDownBtn.addEventListener('click', function() {
            navigateCommandHistory('down', commandInput);
        });
    }
    
    if (clearCommandHistoryBtn) {
        clearCommandHistoryBtn.addEventListener('click', function() {
            clearCommandHistory();
        });
    }
    
    // 为命令输入框添加上下键导航功能
    if (commandInput) {
        commandInput.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                navigateCommandHistory('up', commandInput);
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                navigateCommandHistory('down', commandInput);
            }
        });
    }
    
    // 为数据输入框添加上下键导航功能
    if (dataInput) {
        dataInput.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                navigateCommandHistory('up', dataInput);
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                navigateCommandHistory('down', dataInput);
            }
        });
    }
    
    // 加载保存在localStorage中的历史命令
    loadCommandHistory();
}

// 上下导航命令历史
function navigateCommandHistory(direction, inputElement) {
    if (!commandHistory.length) return;
    
    if (direction === 'up') {
        // 如果是第一次按上键，保存当前输入
        if (historyIndex === -1) {
            historyIndex = 0;
        } else if (historyIndex < commandHistory.length - 1) {
            historyIndex++;
        }
    } else if (direction === 'down') {
        if (historyIndex > 0) {
            historyIndex--;
        } else {
            // 达到最新的命令
            historyIndex = -1;
            inputElement.value = '';
            return;
        }
    }
    
    if (historyIndex >= 0 && historyIndex < commandHistory.length) {
        inputElement.value = commandHistory[commandHistory.length - 1 - historyIndex];
    }
}

// 添加命令到历史记录
function addToCommandHistory(command) {
    // 避免添加空命令或重复命令
    if (!command || (commandHistory.length > 0 && commandHistory[commandHistory.length - 1] === command)) {
        return;
    }
    
    // 添加到历史记录数组
    commandHistory.push(command);
    
    // 限制历史记录数量
    if (commandHistory.length > 50) {
        commandHistory.shift();
    }
    
    // 重置索引
    historyIndex = -1;
    
    // 更新UI显示
    updateCommandHistoryUI();
    
    // 保存到localStorage
    saveCommandHistory();
}

// 清空命令历史
function clearCommandHistory() {
    if (confirm('确定要清空命令历史记录吗？此操作不可恢复。')) {
        commandHistory = [];
        historyIndex = -1;
        updateCommandHistoryUI();
        localStorage.removeItem('serialCommandHistory');
    }
}

// 更新命令历史UI显示
function updateCommandHistoryUI() {
    const historyContainer = document.getElementById('commandHistory');
    if (!historyContainer) return;
    
    historyContainer.innerHTML = '';
    
    // 如果没有历史记录
    if (commandHistory.length === 0) {
        historyContainer.innerHTML = '<div class="no-history">无命令历史记录</div>';
        return;
    }
    
    // 显示最近的命令历史（倒序显示）
    for (let i = commandHistory.length - 1; i >= 0; i--) {
        const item = document.createElement('div');
        item.className = 'command-history-item';
        
        const commandText = document.createElement('div');
        commandText.className = 'command-text';
        commandText.textContent = commandHistory[i];
        
        const time = document.createElement('div');
        time.className = 'command-time';
        time.textContent = new Date().toLocaleString(); // 理想情况下应该存储每个命令的时间
        
        item.appendChild(commandText);
        item.appendChild(time);
        
        // 添加点击事件，点击可以填充命令
        item.addEventListener('click', function() {
            document.getElementById('commandInput').value = commandHistory[i];
            document.getElementById('dataInput').value = commandHistory[i];
        });
        
        historyContainer.appendChild(item);
    }
}

// 保存命令历史到localStorage
function saveCommandHistory() {
    try {
        localStorage.setItem('serialCommandHistory', JSON.stringify(commandHistory));
    } catch (e) {
        console.error('保存命令历史失败:', e);
    }
}

// 从localStorage加载命令历史
function loadCommandHistory() {
    try {
        const savedHistory = localStorage.getItem('serialCommandHistory');
        if (savedHistory) {
            commandHistory = JSON.parse(savedHistory);
            updateCommandHistoryUI();
        }
    } catch (e) {
        console.error('加载命令历史失败:', e);
    }
}

// 初始化帧模式滑块
function initFrameSliders() {
    // 创建并替换Yaw输入控件
    replaceWithSlider('yawInput', -180, 180, 0.1, '°');
    
    // 创建并替换Pitch输入控件
    replaceWithSlider('pitchInput', -90, 90, 0.1, '°');
}

// 将数字输入框替换为滑块
function replaceWithSlider(inputId, min, max, step, unit = '') {
    const inputElement = document.getElementById(inputId);
    if (!inputElement) return;
    
    // 获取原始值
    const originalValue = parseFloat(inputElement.value) || 0;
    
    // 创建滑块容器
    const sliderContainer = document.createElement('div');
    sliderContainer.className = 'slider-container';
    
    // 复制原始标签
    const labelForInput = document.querySelector(`label[for="${inputId}"]`);
    const label = document.createElement('label');
    label.textContent = labelForInput ? labelForInput.textContent : inputId;
    
    // 创建滑块
    const slider = document.createElement('input');
    slider.type = 'range';
    slider.id = `${inputId}Slider`;
    slider.min = min;
    slider.max = max;
    slider.step = step;
    slider.value = originalValue;
    
    // 创建数值显示
    const valueDisplay = document.createElement('div');
    valueDisplay.className = 'value-display';
    valueDisplay.textContent = originalValue + unit;
    
    // 添加事件监听器
    slider.addEventListener('input', function() {
        inputElement.value = this.value;
        valueDisplay.textContent = this.value + unit;
    });
    
    // 确保数字输入也能更新滑块
    inputElement.addEventListener('change', function() {
        slider.value = this.value;
        valueDisplay.textContent = this.value + unit;
    });
    
    // 组装UI
    sliderContainer.appendChild(label);
    sliderContainer.appendChild(slider);
    sliderContainer.appendChild(valueDisplay);
    
    // 隐藏原始数字输入框（但保留其功能）
    inputElement.style.display = 'none';
    
    // 在原始输入框的位置插入滑块容器
    inputElement.parentNode.insertBefore(sliderContainer, inputElement.nextSibling);
}

// 初始化模式切换按钮
function initModeButtons() {
    // 创建模式切换按钮
    const serialTab = document.getElementById('serialTab');
    if (!serialTab) return;
    
    const oldTabContainer = serialTab.querySelector('.tab-container');
    if (!oldTabContainer) return;
    
    // 创建新的模式切换按钮
    const modeButtons = document.createElement('div');
    modeButtons.className = 'mode-buttons';
    
    const textModeBtn = document.createElement('div');
    textModeBtn.className = 'mode-button active';
    textModeBtn.textContent = '文本模式';
    textModeBtn.dataset.mode = 'textMode';
    
    const frameModeBtn = document.createElement('div');
    frameModeBtn.className = 'mode-button';
    frameModeBtn.textContent = '帧模式';
    frameModeBtn.dataset.mode = 'frameMode';
    
    modeButtons.appendChild(textModeBtn);
    modeButtons.appendChild(frameModeBtn);
    
    // 添加点击事件
    modeButtons.addEventListener('click', function(event) {
        if (event.target.classList.contains('mode-button')) {
            // 切换活动按钮
            const buttons = modeButtons.querySelectorAll('.mode-button');
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            // 切换内容
            const modeName = event.target.dataset.mode;
            openSubTab(event, modeName);
        }
    });
    
    // 替换旧的标签容器
    oldTabContainer.parentNode.replaceChild(modeButtons, oldTabContainer);
}

// 增强发送命令函数，增加历史记录
const originalSendSerialCommand = window.sendSerialCommand;

window.sendSerialCommand = function() {
    const commandInput = document.getElementById('commandInput');
    if (commandInput && commandInput.value.trim()) {
        addToCommandHistory(commandInput.value.trim());
    }
    
    // 调用原始函数
    if (typeof originalSendSerialCommand === 'function') {
        return originalSendSerialCommand.apply(this, arguments);
    }
};

// 增强发送数据函数，增加历史记录
const originalSendData = window.sendData;

window.sendData = function() {
    const dataInput = document.getElementById('dataInput');
    if (dataInput && dataInput.value.trim()) {
        addToCommandHistory(dataInput.value.trim());
    }
    
    // 调用原始函数
    if (typeof originalSendData === 'function') {
        return originalSendData.apply(this, arguments);
    }
};

// 增强历史记录显示
const originalUpdateHistory = window.updateHistory;

window.updateHistory = function(page) {
    // 调用原始函数
    if (typeof originalUpdateHistory === 'function') {
        originalUpdateHistory.apply(this, arguments);
        
        // 增强历史记录显示
        setTimeout(enhanceHistoryDisplay, 100);
    }
};

// 增强历史记录显示
function enhanceHistoryDisplay() {
    const historyRecords = document.querySelectorAll('.history-record');
    
    historyRecords.forEach(record => {
        // 如果已经增强过，跳过
        if (record.classList.contains('enhanced')) return;
        
        // 标记为已增强
        record.classList.add('enhanced');
        
        // 获取原始内容并解析
        const html = record.innerHTML;
        const recordNumberMatch = html.match(/<span class="record-number">#(\d+)<\/span>/);
        const recordNumber = recordNumberMatch ? recordNumberMatch[1] : '';
        
        // 提取各部分内容
        const sentData = extractContent(html, '发送:');
        const receivedData = extractContent(html, '接收:');
        const status = extractContent(html, '状态:');
        const message = extractContent(html, '消息:');
        const time = extractContent(html, '时间:');
        
        // 创建新的增强显示
        record.innerHTML = `
            <div class="record-header">
                <span class="record-number">#${recordNumber}</span>
                <span class="record-time">${time}</span>
            </div>
            <div class="record-data">
                <div class="record-data-label">发送:</div>
                <div class="record-data-content">${sentData || '无数据'}</div>
            </div>
            <div class="record-data">
                <div class="record-data-label">接收:</div>
                <div class="record-data-content">${receivedData || '无响应'}</div>
            </div>
            <div class="record-footer">
                <span class="record-status ${status === 'success' ? 'record-status-success' : 'record-status-error'}">
                    ${status || '未知'}
                </span>
                <span class="record-message">${message || '无消息'}</span>
            </div>
        `;
    });
}

// 辅助函数：从HTML中提取内容
function extractContent(html, prefix) {
    const regex = new RegExp(prefix + '\\s*([^<]+)<br>');
    const match = html.match(regex);
    return match ? match[1].trim() : '';
}
