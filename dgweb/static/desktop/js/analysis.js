// analysis.js - 姿势情绪分析功能

// 情绪分析参数
let emotionParams = {
    happiness_threshold: 0.5,
    sadness_threshold: 0.5,
    anger_threshold: 0.5,
    surprise_threshold: 0.5,
    fear_threshold: 0.5,
    disgust_threshold: 0.5,
    neutral_threshold: 0.5
};

document.addEventListener('DOMContentLoaded', function() {
    // 获取情绪分析参数
    fetchEmotionParams();
    
    // 初始化时间范围切换按钮
    initTimeRangeButtons();
    
    // 初始化阈值设置按钮 - 检查元素是否存在
    const applyThresholdsBtn = document.getElementById('applyThresholdsBtn');
    if (applyThresholdsBtn) {
        applyThresholdsBtn.addEventListener('click', applyPostureThresholds);
    } else {
        console.log('警告: 未找到应用阈值按钮元素');
    }
    
    // 初始化视频流控制按钮
    initVideoStreamControl();
    
    // 从后端获取坐姿统计数据
    updatePostureStats();
    
    // 每60秒自动更新一次坐姿统计数据
    setInterval(updatePostureStats, 60000);
});

// 获取情绪分析参数
function fetchEmotionParams() {
    fetch('/api/get_emotion_params')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateEmotionParamsUI(data.emotion_params);
                emotionParams = data.emotion_params;
            }
        })
        .catch(error => {
            console.error('获取情绪分析参数失败:', error);
        });
}

// 更新情绪参数UI
function updateEmotionParamsUI(params) {
    // 确保参数UI元素存在
    const emotionParamsForm = document.getElementById('emotionParamsForm');
    if (!emotionParamsForm) return;

    // 遍历参数，更新对应的输入框
    for (const key in params) {
        const input = document.getElementById(key + '_input');
        if (input) {
            input.value = params[key];
        }
    }
}

// 保存情绪分析参数
function saveEmotionParams() {
    // 收集表单数据
    const form = document.getElementById('emotionParamsForm');
    if (!form) return;

    const formData = new FormData(form);
    const params = {};
    
    // 转换为JSON对象
    for (const [key, value] of formData.entries()) {
        params[key] = parseFloat(value);
    }
    
    // 发送请求 - 使用正确的API路径
    fetch('/api/update_emotion_params', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('情绪分析参数已保存', 'success');
            emotionParams = params;
        } else {
            showNotification('保存失败: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('保存情绪分析参数失败:', error);
        showNotification('保存请求失败', 'error');
    });
}

// 更新姿势和情绪状态
function updatePostureEmotionStatus(data) {
    // 更新姿势状态信息
    if (data.posture_data) {
        const { head_angle, posture_status, detection_status } = data.posture_data;
        
        if (document.getElementById('headAngle')) {
            document.getElementById('headAngle').textContent = head_angle ? `${head_angle.toFixed(1)} °` : '-- °';
        }
        
        if (document.getElementById('postureStatus')) {
            document.getElementById('postureStatus').textContent = posture_status || '--';
        }
        
        if (document.getElementById('detectionStatus')) {
            document.getElementById('detectionStatus').textContent = detection_status || '--';
        }
    }
    
    // 更新情绪状态信息
    if (data.emotion_data) {
        const { current_emotion } = data.emotion_data;
        
        if (document.getElementById('emotionStatus')) {
            document.getElementById('emotionStatus').textContent = current_emotion || '--';
        }
    }
}

// 坐姿统计相关功能
let currentTimeRange = 'day'; // 默认显示今日数据

// 初始化时间范围切换按钮
function initTimeRangeButtons() {
    const buttons = document.querySelectorAll('.time-range-btn');
    
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            // 移除所有按钮的active类
            buttons.forEach(btn => btn.classList.remove('active'));
            
            // 为当前按钮添加active类
            this.classList.add('active');
            
            // 更新当前时间范围
            currentTimeRange = this.dataset.range;
            
            // 更新坐姿统计数据
            updatePostureStats();
        });
    });
}

// 更新坐姿统计数据
function updatePostureStats() {
    // 发送请求获取坐姿统计数据
    fetch(`/api/get_posture_stats?time_range=${currentTimeRange}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayPostureStats(data.posture_stats);
            } else {
                console.error('获取坐姿统计数据失败:', data.message);
            }
        })
        .catch(error => {
            console.error('请求坐姿统计数据出错:', error);
        });
}

// 显示坐姿统计数据
function displayPostureStats(stats) {
    // 更新总时长 - 添加元素存在性检查
    const totalPostureTimeElement = document.getElementById('totalPostureTime');
    if (totalPostureTimeElement) {
        totalPostureTimeElement.textContent = stats.total_time.formatted_time;
    }
    
    // 更新良好坐姿占比 - 添加元素存在性检查
    const goodPosturePercentageElement = document.getElementById('goodPosturePercentage');
    if (goodPosturePercentageElement) {
        goodPosturePercentageElement.textContent = `${stats.good_posture_percentage}%`;
    }
    
    // 更新各类型坐姿数据
    const types = ['good', 'mild', 'moderate', 'severe'];
    
    types.forEach(type => {
        // 确保stats中有对应的类型数据
        const typeData = stats[type] || {seconds: 0, percentage: 0, formatted_time: '0h 0m'};
        
        // 更新百分比
        const percentageElement = document.getElementById(`${type}Percentage`);
        if (percentageElement) {
            percentageElement.textContent = `${typeData.percentage}%`;
        }
        
        // 更新时长
        const timeElement = document.getElementById(`${type}Time`);
        if (timeElement) {
            timeElement.textContent = typeData.formatted_time;
        }
        
        // 更新描述文本 - 根据当前阈值动态更新
        const goodThresholdElement = document.getElementById('goodThreshold');
        const mildThresholdElement = document.getElementById('mildThreshold');
        const moderateThresholdElement = document.getElementById('moderateThreshold');
        
        if (goodThresholdElement && mildThresholdElement && moderateThresholdElement) {
            const typeDescElement = document.querySelector(`.posture-type-card.${type} .posture-type-desc`);
            if (typeDescElement) {
                if (type === 'good') {
                    typeDescElement.textContent = `0-${goodThresholdElement.value}°`;
                } else if (type === 'mild') {
                    typeDescElement.textContent = `${goodThresholdElement.value}-${mildThresholdElement.value}°`;
                } else if (type === 'moderate') {
                    typeDescElement.textContent = `${mildThresholdElement.value}-${moderateThresholdElement.value}°`;
                } else if (type === 'severe') {
                    typeDescElement.textContent = `${moderateThresholdElement.value}°以上`;
                }
            }
        }
    });

    // 计算并更新不良坐姿总时间（mild + moderate + severe）
    const badTimeElement = document.querySelector('.stat-item:nth-child(2) .stat-value');
    if (badTimeElement) {
        // 计算不良坐姿总秒数
        const badSeconds = (stats.mild ? stats.mild.seconds : 0) + 
                          (stats.moderate ? stats.moderate.seconds : 0) + 
                          (stats.severe ? stats.severe.seconds : 0);
        
        // 格式化不良坐姿总时间
        let badTimeFormatted = '';
        const hours = Math.floor(badSeconds / 3600);
        const minutes = Math.floor((badSeconds % 3600) / 60);
        
        if (hours > 0) {
            badTimeFormatted = `${hours}h ${minutes}m`;
        } else {
            badTimeFormatted = `${minutes}m`;
        }
        
        badTimeElement.textContent = badTimeFormatted;
    }
    
    // 更新主页面上的不良坐姿时间（如果存在）
    updateMainPagePostureStats(stats);
}

// 更新主页面上的坐姿统计数据
function updateMainPagePostureStats(stats) {
    // 首先检查Chart对象是否存在
    if (typeof Chart === 'undefined') {
        console.log('Chart.js未加载，跳过饼图更新');
        // 继续执行其他不依赖Chart.js的统计更新
    } else {
        // 获取主页面上的坐姿饼图
        const posturePieChart = Chart.getChart('posturePieChart');
        
        if (posturePieChart) {
            // 更新饼图数据
            posturePieChart.data.datasets[0].data = [
                stats.good.percentage,
                stats.mild.percentage,
                stats.moderate.percentage,
                stats.severe.percentage
            ];
            posturePieChart.update();
        }
        
        // 更新不良坐姿时段分布图
        updatePostureDistributionChart();
    }
    
    // 查找主页面上的统计卡片
    const mainPageStatItems = document.querySelectorAll('.dashboard .stat-item');
    if (mainPageStatItems && mainPageStatItems.length >= 3) {
        // 更新良好坐姿时间
        const goodTimeElement = mainPageStatItems[0].querySelector('.stat-value');
        if (goodTimeElement) {
            goodTimeElement.textContent = stats.good.formatted_time;
        }
        
        // 更新不良坐姿时间
        const badTimeElement = mainPageStatItems[1].querySelector('.stat-value');
        if (badTimeElement) {
            // 计算不良坐姿总秒数（mild + moderate + severe）
            const badSeconds = (stats.mild ? stats.mild.seconds : 0) + 
                              (stats.moderate ? stats.moderate.seconds : 0) + 
                              (stats.severe ? stats.severe.seconds : 0);
            
            // 格式化不良坐姿总时间
            let badTimeFormatted = '';
            const hours = Math.floor(badSeconds / 3600);
            const minutes = Math.floor((badSeconds % 3600) / 60);
            
            if (hours > 0) {
                badTimeFormatted = `${hours}h ${minutes}m`;
            } else {
                badTimeFormatted = `${minutes}m`;
            }
            
            badTimeElement.textContent = badTimeFormatted;
        }
        
        // 更新良好率
        const goodRateElement = mainPageStatItems[2].querySelector('.stat-value');
        if (goodRateElement) {
            goodRateElement.textContent = `${stats.good_posture_percentage}%`;
        }
    }
}

// 更新不良坐姿时段分布图
function updatePostureDistributionChart() {
    // 获取不良坐姿时段分布图实例
    const heatmapChart = Chart.getChart('heatmapChart');
    if (!heatmapChart) {
        console.log('找不到不良坐姿时段分布图表实例');
        return;
    }
    
    // 发送请求获取不良坐姿时段分布数据
    fetch(`/api/get_posture_distribution?time_range=${currentTimeRange}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // 更新图表数据
                const distribution = data.distribution;
                
                // 过滤掉不良次数为0的时段
                const filteredLabels = [];
                const filteredData = [];
                
                distribution.labels.forEach((label, index) => {
                    if (distribution.data[index] > 0) {
                        filteredLabels.push(label);
                        filteredData.push(distribution.data[index]);
                    }
                });
                
                // 如果过滤后没有数据，显示提示信息
                if (filteredData.length === 0) {
                    // 清空图表并显示无数据提示
                    heatmapChart.data.labels = [];
                    heatmapChart.data.datasets[0].data = [];
                    
                    // 获取图表容器
                    const chartContainer = heatmapChart.canvas.parentNode;
                    
                    // 移除旧的图例（如果存在）
                    const oldLegend = chartContainer.querySelector('.custom-legend');
                    if (oldLegend) {
                        oldLegend.remove();
                    }
                    
                    // 创建无数据提示
                    const noDataMessage = document.createElement('div');
                    noDataMessage.className = 'custom-legend';
                    noDataMessage.style.marginTop = '15px';
                    noDataMessage.style.fontSize = '14px';
                    noDataMessage.style.textAlign = 'center';
                    noDataMessage.style.color = '#666';
                    noDataMessage.textContent = '当前时段无不良坐姿记录数据';
                    
                    // 添加到图表容器
                    chartContainer.appendChild(noDataMessage);
                } else {
                    // 更新图表数据集
                    heatmapChart.data.labels = filteredLabels;
                    heatmapChart.data.datasets[0].data = filteredData;
                }
                
                // 重新渲染图表
                heatmapChart.update();
            } else {
                console.error('获取不良坐姿时段分布数据失败:', data.message);
            }
        })
        .catch(error => {
            console.error('请求不良坐姿时段分布数据出错:', error);
        });
}

// 应用坐姿阈值设置
function applyPostureThresholds() {
    const goodThreshold = parseFloat(document.getElementById('goodThreshold').value);
    const mildThreshold = parseFloat(document.getElementById('mildThreshold').value);
    const moderateThreshold = parseFloat(document.getElementById('moderateThreshold').value);
    
    // 验证阈值是否有效
    if (goodThreshold >= mildThreshold || mildThreshold >= moderateThreshold) {
        alert('请确保阈值设置递增：良好坐姿 < 轻度不良 < 中度不良');
        return;
    }
    
    // 发送请求更新阈值设置
    fetch('/api/set_posture_thresholds', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            enabled: true,
            thresholds: {
                good: goodThreshold,
                mild: mildThreshold,
                moderate: moderateThreshold
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // 更新成功后刷新统计数据
            updatePostureStats();
            
            // 显示成功通知
            showNotification('阈值设置已更新', 'success');
        } else {
            showNotification('更新阈值设置失败: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('请求更新阈值设置出错:', error);
        showNotification('更新阈值设置出错', 'error');
    });
}

// 显示通知
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 5秒后自动移除
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// 初始化视频流控制
function initVideoStreamControl() {
    const toggleStreamingBtn = document.getElementById('toggleStreamingBtn');
    const streamingStatusText = document.getElementById('streamingStatusText');
    
    if (!toggleStreamingBtn || !streamingStatusText) {
        console.log('警告: 未找到视频流控制按钮或状态文本元素');
        return;
    }
    
    // 在页面加载时确保视频元素的src是初始黑屏
    initializeVideoElements();
    
    // 获取当前视频流状态
    getVideoStreamStatus();
    
    // 添加按钮点击事件
    toggleStreamingBtn.addEventListener('click', function() {
        const isCurrentlyEnabled = toggleStreamingBtn.textContent === '禁用视频流';
        toggleVideoStream(!isCurrentlyEnabled);
    });
}

// 初始化视频元素函数
function initializeVideoElements() {
    const blackImage = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=';
    const poseVideo = document.getElementById('poseVideo');
    const emotionVideo = document.getElementById('emotionVideo');
    
    // 确保页面加载时初始显示黑屏
    if (poseVideo) {
        poseVideo.src = blackImage;
    }
    
    if (emotionVideo) {
        emotionVideo.src = blackImage;
    }
    
    console.log('初始化视频元素为黑屏');
}

// 获取视频流状态
function getVideoStreamStatus() {
    fetch('/api/get_video_stream_status')
        .then(response => response.json())
        .then(data => {
            updateVideoStreamUI(data.is_streaming);
            
            // 如果流已启用，则设置视频元素的src
            if (data.is_streaming) {
                // 获取视频元素
                const poseVideo = document.getElementById('poseVideo');
                const emotionVideo = document.getElementById('emotionVideo');
                
                if (poseVideo && poseVideo.hasAttribute('data-src')) {
                    poseVideo.src = poseVideo.getAttribute('data-src') + '?' + new Date().getTime();
                }
                
                if (emotionVideo && emotionVideo.hasAttribute('data-src')) {
                    emotionVideo.src = emotionVideo.getAttribute('data-src') + '?' + new Date().getTime();
                }
            }
        })
        .catch(error => {
            console.error('获取视频流状态失败:', error);
        });
}

// 切换视频流状态
function toggleVideoStream(enable) {
    fetch('/api/toggle_video_stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            enable: enable
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateVideoStreamUI(data.is_streaming);
            
            // 获取视频元素
            const poseVideo = document.getElementById('poseVideo');
            const emotionVideo = document.getElementById('emotionVideo');
            
            if (data.is_streaming) {
                // 启用视频流 - 从data-src属性获取源URL，并添加时间戳防止缓存
                if (poseVideo) {
                    const poseVideoSrc = poseVideo.getAttribute('data-src') || '/pose_video_feed';
                    poseVideo.src = poseVideoSrc + '?' + new Date().getTime();
                }
                
                if (emotionVideo) {
                    const emotionVideoSrc = emotionVideo.getAttribute('data-src') || '/emotion_video_feed';
                    emotionVideo.src = emotionVideoSrc + '?' + new Date().getTime();
                }
            } else {
                // 禁用视频流 - 设置为空黑色图像
                const blackImage = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=';
                
                if (poseVideo) {
                    poseVideo.src = blackImage;
                }
                
                if (emotionVideo) {
                    emotionVideo.src = blackImage;
                }
            }
            
            showNotification(`视频流已${data.is_streaming ? '启用' : '禁用'}`, 'success');
        } else {
            showNotification('操作失败: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('切换视频流状态失败:', error);
        showNotification('请求失败', 'error');
    });
}

// 更新视频流UI
function updateVideoStreamUI(isStreaming) {
    const toggleStreamingBtn = document.getElementById('toggleStreamingBtn');
    const streamingStatusText = document.getElementById('streamingStatusText');
    
    if (toggleStreamingBtn) {
        toggleStreamingBtn.textContent = isStreaming ? '禁用视频流' : '启用视频流';
        toggleStreamingBtn.className = isStreaming ? 'red' : 'btn-primary';
    }
    
    if (streamingStatusText) {
        streamingStatusText.textContent = isStreaming ? '已启用' : '已禁用';
        streamingStatusText.className = isStreaming ? 'status-running' : 'status-stopped';
    }
}

// 暴露公共函数
window.fetchEmotionParams = fetchEmotionParams;
window.saveEmotionParams = saveEmotionParams;
window.updatePostureEmotionStatus = updatePostureEmotionStatus;