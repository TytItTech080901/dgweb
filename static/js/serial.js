// serial.js - 串口通信功能

document.addEventListener('DOMContentLoaded', function() {
    // 初始化串口界面
    initSerialInterface();
    
    // 获取串口状态
    fetchSerialStatus();
    
    // 每5秒自动更新一次串口状态
    setInterval(fetchSerialStatus, 5000);
});

// 初始化串口界面
function initSerialInterface() {
    // 为串口相关按钮添加事件监听器
    const connectBtn = document.getElementById('connectBtn');
    if (connectBtn) {
        connectBtn.addEventListener('click', connectSerial);
    }
    
    const disconnectBtn = document.getElementById('disconnectBtn');
    if (disconnectBtn) {
        disconnectBtn.addEventListener('click', disconnectSerial);
    }
    
    const sendCommandBtn = document.getElementById('sendCommandBtn');
    if (sendCommandBtn) {
        sendCommandBtn.addEventListener('click', sendSerialCommand);
    }
    
    // 设置键盘事件，按Enter键发送命令
    const commandInput = document.getElementById('commandInput');
    if (commandInput) {
        commandInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendSerialCommand();
            }
        });
    }
}

// 获取串口状态
function fetchSerialStatus() {
    fetch('/api/get_serial_status')
        .then(response => response.json())
        .then(data => {
            updateSerialStatusUI(data);
        })
        .catch(error => {
            console.error('获取串口状态失败:', error);
            // 显示错误状态
            const statusText = document.getElementById('serialStatusText');
            if (statusText) {
                statusText.textContent = '状态获取失败';
                statusText.className = 'status-error';
            }
        });
}

// 更新串口状态UI
function updateSerialStatusUI(data) {
    const statusText = document.getElementById('serialStatusText');
    if (!statusText) return;
    
    console.log('串口状态:', data);  // 调试日志
    
    if (data.connected) {
        statusText.textContent = `已连接 (${data.port || '未知设备'}, ${data.baudrate || '未知波特率'})`;
        statusText.className = 'status-connected';
        
        // 更新按钮状态
        if (document.getElementById('connectBtn')) {
            document.getElementById('connectBtn').disabled = true;
        }
        if (document.getElementById('disconnectBtn')) {
            document.getElementById('disconnectBtn').disabled = false;
        }
        if (document.getElementById('sendCommandBtn')) {
            document.getElementById('sendCommandBtn').disabled = false;
        }
        
        // 保存当前串口设置到输入框
        if (data.port && document.getElementById('portInput')) {
            document.getElementById('portInput').value = data.port;
        }
        if (data.baudrate && document.getElementById('baudrateSelect')) {
            const baudrateSelect = document.getElementById('baudrateSelect');
            for (let i = 0; i < baudrateSelect.options.length; i++) {
                if (parseInt(baudrateSelect.options[i].value) === data.baudrate) {
                    baudrateSelect.selectedIndex = i;
                    break;
                }
            }
        }
    } else {
        statusText.textContent = '未连接';
        statusText.className = 'status-disconnected';
        
        // 更新按钮状态
        if (document.getElementById('connectBtn')) {
            document.getElementById('connectBtn').disabled = false;
        }
        if (document.getElementById('disconnectBtn')) {
            document.getElementById('disconnectBtn').disabled = true;
        }
        if (document.getElementById('sendCommandBtn')) {
            document.getElementById('sendCommandBtn').disabled = false;  // 允许发送但会提示错误
        }
    }
}

// 连接串口
function connectSerial() {
    const portInput = document.getElementById('portInput');
    const baudrateSelect = document.getElementById('baudrateSelect');
    
    if (!portInput || !baudrateSelect) {
        showNotification('找不到串口设置控件', 'error');
        return;
    }
    
    const port = portInput.value.trim();
    const baudrate = parseInt(baudrateSelect.value);
    
    if (!port) {
        showNotification('请输入串口设备路径', 'error');
        return;
    }
    
    // 更新状态为"正在连接"
    const statusText = document.getElementById('serialStatusText');
    if (statusText) {
        statusText.textContent = '正在连接...';
        statusText.className = 'status-connecting';
    }
    
    // 禁用连接按钮，避免重复点击
    if (document.getElementById('connectBtn')) {
        document.getElementById('connectBtn').disabled = true;
    }
    
    fetch('/api/connect_serial', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            port: port,
            baudrate: baudrate
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('串口已连接', 'success');
            fetchSerialStatus();  // 刷新状态
        } else {
            showNotification('连接失败: ' + data.message, 'error');
            // 恢复连接按钮状态
            if (document.getElementById('connectBtn')) {
                document.getElementById('connectBtn').disabled = false;
            }
            // 更新状态为"连接失败"
            if (statusText) {
                statusText.textContent = '连接失败';
                statusText.className = 'status-error';
            }
        }
    })
    .catch(error => {
        console.error('连接串口失败:', error);
        showNotification('连接请求失败', 'error');
        // 恢复连接按钮状态
        if (document.getElementById('connectBtn')) {
            document.getElementById('connectBtn').disabled = false;
        }
        // 更新状态为"连接失败"
        if (statusText) {
            statusText.textContent = '连接失败';
            statusText.className = 'status-error';
        }
    });
}

// 断开串口
function disconnectSerial() {
    // 更新状态为"正在断开"
    const statusText = document.getElementById('serialStatusText');
    if (statusText) {
        statusText.textContent = '正在断开...';
        statusText.className = 'status-disconnecting';
    }
    
    fetch('/api/disconnect_serial', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('串口已断开', 'success');
            fetchSerialStatus();  // 刷新状态
        } else {
            showNotification('断开失败: ' + data.message, 'error');
            fetchSerialStatus();  // 刷新状态以显示实际情况
        }
    })
    .catch(error => {
        console.error('断开串口失败:', error);
        showNotification('断开请求失败', 'error');
        fetchSerialStatus();  // 刷新状态以显示实际情况
    });
}

// 发送串口命令
function sendSerialCommand() {
    const commandInput = document.getElementById('commandInput');
    if (!commandInput) {
        showNotification('找不到命令输入框', 'error');
        return;
    }
    
    const command = commandInput.value.trim();
    if (!command) {
        showNotification('请输入命令', 'error');
        return;
    }
    
    // 获取串口状态
    fetch('/api/get_serial_status')
        .then(response => response.json())
        .then(statusData => {
            if (!statusData.connected) {
                showNotification('串口未连接，请先连接串口', 'error');
                return;
            }
            
            // 串口已连接，发送命令
            fetch('/api/send_serial_command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    command: command
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // 清空输入框并聚焦以准备下一次输入
                    commandInput.value = '';
                    commandInput.focus();
                    
                    // 添加命令到历史记录
                    addCommandToHistory(command);
                    
                    // 更新响应区域
                    const responseElement = document.getElementById('response');
                    if (responseElement) {
                        responseElement.innerText = data.response || '命令已发送，无响应';
                    }
                } else {
                    showNotification('发送失败: ' + data.message, 'error');
                }
            })
            .catch(error => {
                console.error('发送命令失败:', error);
                showNotification('发送请求失败', 'error');
            });
        })
        .catch(error => {
            console.error('获取串口状态失败:', error);
            showNotification('无法确认串口状态，请检查连接', 'error');
        });
}

// 添加命令到历史记录
function addCommandToHistory(command) {
    const historyList = document.getElementById('commandHistory');
    if (!historyList) return;
    
    const item = document.createElement('div');
    item.className = 'command-history-item';
    item.textContent = command;
    
    // 添加点击事件，点击可以填充命令
    item.addEventListener('click', function() {
        const commandInput = document.getElementById('commandInput');
        if (commandInput) {
            commandInput.value = command;
            commandInput.focus();
        }
    });
    
    // 添加到顶部
    if (historyList.firstChild) {
        historyList.insertBefore(item, historyList.firstChild);
    } else {
        historyList.appendChild(item);
    }
    
    // 限制历史记录数量
    const maxHistory = 10;
    while (historyList.childElementCount > maxHistory) {
        historyList.removeChild(historyList.lastChild);
    }
}

// 显示通知
function showNotification(message, type = 'info') {
    // 如果页面中存在更高级的通知系统（如toast），则使用它
    if (typeof window.toast === 'function') {
        window.toast(message, type);
        return;
    }
    
    // 创建一个新的通知元素
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 3秒后自动移除
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 导出公共函数
window.connectSerial = connectSerial;
window.disconnectSerial = disconnectSerial;
window.sendSerialCommand = sendSerialCommand;