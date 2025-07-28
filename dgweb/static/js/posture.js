// 坐姿检测工具JavaScript - 柔和绿色调配色方案

// 全局变量
let currentTimeRange = 'day';
let currentPostureTab = 'proportion';
let posturePieChart = null;
let heatmapChart = null;
let postureImages = [];
let isDataLoaded = {
    proportion: false,
    distribution: false,
    images: false
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('坐姿检测工具初始化');
    
    // 初始化事件监听器
    initEventListeners();
    
    // 默认加载坐姿分析数据
    loadTabData('proportion');
});

// 初始化事件监听器
function initEventListeners() {
    // 时间范围选择器事件
    const timeRangeBtns = document.querySelectorAll('.time-range-btn');
    timeRangeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const range = this.getAttribute('data-range');
            changeTimeRange(range);
        });
    });
    
    // 坐姿tab切换事件
    const tabBtns = document.querySelectorAll('.posture-tab-btn');
    const tabPanels = document.querySelectorAll('.posture-tab-panel');
    
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
            
            currentPostureTab = tab;
            
            // 按需加载数据
            loadTabData(tab);
        });
    });
}

// 按需加载tab数据
function loadTabData(tab) {
    if (isDataLoaded[tab]) {
        return; // 数据已加载，无需重复加载
    }
    
    switch(tab) {
        case 'proportion':
            loadPostureData();
            break;
        case 'distribution':
            loadDistributionData();
            break;
        case 'images':
            loadPostureImages();
            break;
    }
    
    isDataLoaded[tab] = true;
}

// 切换时间范围
function changeTimeRange(range) {
    currentTimeRange = range;
    
    // 更新按钮状态
    document.querySelectorAll('.time-range-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-range="${range}"]`).classList.add('active');
    
    // 重新加载当前tab的数据
    if (currentPostureTab === 'proportion') {
        loadPostureData();
    } else if (currentPostureTab === 'distribution') {
        loadDistributionData();
    }
    
    // 显示提示
    const rangeNames = {
        day: '今日',
        week: '本周',
        month: '本月'
    };
}

// 初始化图表
function initCharts() {
    // 初始化饼图
    const pieCtx = document.getElementById('posturePieChart');
    if (pieCtx && !posturePieChart) {
        posturePieChart = new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: ['良好坐姿', '轻度不良', '不良坐姿'],
                datasets: [{
                    data: [64, 24, 12],
                    backgroundColor: [
                        'rgba(143, 180, 160, 0.8)',
                        'rgba(255, 193, 7, 0.8)',
                        'rgba(220, 53, 69, 0.8)'
                    ],
                    borderColor: [
                        'rgba(143, 180, 160, 1)',
                        'rgba(255, 193, 7, 1)',
                        'rgba(220, 53, 69, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                cutout: '60%'
            }
        });
    }
    
    // 初始化热力图
    const heatmapCtx = document.getElementById('heatmapChart');
    if (heatmapCtx && !heatmapChart) {
        heatmapChart = new Chart(heatmapCtx, {
            type: 'bar',
            data: {
                labels: ['6-8', '8-10', '10-12', '12-14', '14-16', '16-18', '18-20', '20-22'],
                datasets: [{
                    label: '坐姿质量',
                    data: [85, 78, 72, 65, 58, 82, 90, 88],
                    backgroundColor: 'rgba(143, 180, 160, 0.6)',
                    borderColor: 'rgba(143, 180, 160, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
}

// 加载坐姿数据
function loadPostureData() {
    // 初始化图表
    initCharts();
    
    // 尝试API调用
    fetch(`/api/posture/data?range=${currentTimeRange}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('API not available');
            }
            return response.json();
        })
        .then(data => {
            console.log('坐姿数据加载成功:', data);
            updateStats(data);
            updateCharts(data);
        })
        .catch(error => {
            console.log('使用模拟数据:', error.message);
            const mockData = getMockPostureData();
            updateStats(mockData);
            updateCharts(mockData);
        });
}

// 加载分布数据
function loadDistributionData() {
    // 初始化图表
    initCharts();
    
    // 尝试API调用
    fetch(`/api/posture/distribution?range=${currentTimeRange}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('API not available');
            }
            return response.json();
        })
        .then(data => {
            console.log('分布数据加载成功:', data);
            updateDistributionChart(data);
        })
        .catch(error => {
            console.log('使用模拟分布数据:', error.message);
            const mockData = getMockDistributionData();
            updateDistributionChart(mockData);
        });
}

// 获取模拟坐姿数据
function getMockPostureData() {
    const mockData = {
        goodPostureTime: '3.2h',
        mildBadPostureTime: '1.2h',
        badPostureTime: '0.6h',
        postureRate: '64%',
        pieData: [64, 24, 12],
        heatmapData: [85, 78, 72, 65, 58, 82, 90, 88]
    };
    
    // 根据时间范围调整数据
    if (currentTimeRange === 'week') {
        mockData.goodPostureTime = '22.4h';
        mockData.mildBadPostureTime = '8.4h';
        mockData.badPostureTime = '4.2h';
        mockData.postureRate = '68%';
        mockData.pieData = [68, 22, 10];
    } else if (currentTimeRange === 'month') {
        mockData.goodPostureTime = '96.0h';
        mockData.mildBadPostureTime = '36.0h';
        mockData.badPostureTime = '18.0h';
        mockData.postureRate = '72%';
        mockData.pieData = [72, 20, 8];
    }
    
    return mockData;
}

// 获取模拟分布数据
function getMockDistributionData() {
    return {
        heatmapData: [85, 78, 72, 65, 58, 82, 90, 88]
    };
}

// 更新统计数据
function updateStats(data) {
    const elements = {
        goodPostureTime: document.getElementById('goodPostureTime'),
        mildBadPostureTime: document.getElementById('mildBadPostureTime'),
        badPostureTime: document.getElementById('badPostureTime'),
        postureRate: document.getElementById('postureRate')
    };
    
    if (elements.goodPostureTime) elements.goodPostureTime.textContent = data.goodPostureTime;
    if (elements.mildBadPostureTime) elements.mildBadPostureTime.textContent = data.mildBadPostureTime;
    if (elements.badPostureTime) elements.badPostureTime.textContent = data.badPostureTime;
    if (elements.postureRate) elements.postureRate.textContent = data.postureRate;
}

// 更新图表
function updateCharts(data) {
    // 更新饼图
    if (posturePieChart && data.pieData) {
        posturePieChart.data.datasets[0].data = data.pieData;
        posturePieChart.update();
    }
    
    // 更新热力图
    if (heatmapChart && data.heatmapData) {
        heatmapChart.data.datasets[0].data = data.heatmapData;
        heatmapChart.update();
    }
}

// 更新分布图表
function updateDistributionChart(data) {
    if (heatmapChart && data.heatmapData) {
        heatmapChart.data.datasets[0].data = data.heatmapData;
        heatmapChart.update();
    }
}

// 加载坐姿图像
function loadPostureImages() {
    // 尝试API调用
    fetch('/api/posture/images')
        .then(response => {
            if (!response.ok) {
                throw new Error('API not available');
            }
            return response.json();
        })
        .then(data => {
            console.log('坐姿图像加载成功:', data);
            postureImages = data.images || [];
            renderPostureImages();
        })
        .catch(error => {
            console.log('使用模拟图像数据:', error.message);
            loadMockPostureImages();
        });
}

// 加载模拟坐姿图像
function loadMockPostureImages() {
    postureImages = [
        { id: 1, url: '/static/placeholder.jpg', time: '2025-05-28 21:39:01', status: 'good' },
        { id: 2, url: '/static/placeholder.jpg', time: '2025-05-28 21:40:33', status: 'warning' },
        { id: 3, url: '/static/placeholder.jpg', time: '2025-05-28 21:41:21', status: 'good' },
        { id: 4, url: '/static/placeholder.jpg', time: '2025-05-28 21:42:32', status: 'bad' },
        { id: 5, url: '/static/placeholder.jpg', time: '2025-05-28 22:04:03', status: 'good' },
        { id: 6, url: '/static/placeholder.jpg', time: '2025-05-28 22:14:34', status: 'warning' }
    ];
    renderPostureImages();
}

// 渲染坐姿图像
function renderPostureImages() {
    const container = document.getElementById('posture-images-container');
    if (!container) return;
    
    if (postureImages.length === 0) {
        container.innerHTML = '<div class="loading-indicator">暂无坐姿图像记录</div>';
        return;
    }
    
    const imagesHTML = postureImages.map(image => `
        <div class="posture-image-item" onclick="showImageDetail(${image.id})">
            <img src="${image.url}" alt="坐姿记录" onerror="this.src='/static/placeholder.jpg'">
            <div class="posture-image-overlay">
                ${image.time}
            </div>
        </div>
    `).join('');
    
    container.innerHTML = imagesHTML;
}

// 显示图像详情
function showImageDetail(imageId) {
    const image = postureImages.find(img => img.id === imageId);
    if (image) {
        showToast(`查看坐姿记录: ${image.time}`);
        // 这里可以实现图像详情弹窗
    }
}

// 加载更多坐姿图像
function loadMorePostureImages() {
    showToast('正在加载更多记录...');
    
    // 模拟加载更多图像
    setTimeout(() => {
        const newImages = [
            { id: 7, url: '/static/placeholder.jpg', time: '2025-05-28 22:30:15', status: 'good' },
            { id: 8, url: '/static/placeholder.jpg', time: '2025-05-28 22:45:22', status: 'warning' }
        ];
        
        postureImages.push(...newImages);
        renderPostureImages();
        showToast('加载完成');
    }, 1000);
}

// 导出坐姿图像
function exportPostureImages() {
    showToast('正在导出坐姿记录...');
    
    // 模拟导出功能
    setTimeout(() => {
        const report = {
            date: new Date().toLocaleDateString(),
            totalImages: postureImages.length,
            images: postureImages
        };
        
        console.log('坐姿记录导出:', report);
        showToast('坐姿记录导出成功');
    }, 2000);
}

// 显示提示消息
function showToast(message) {
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

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
    if (posturePieChart) {
        posturePieChart.destroy();
    }
    if (heatmapChart) {
        heatmapChart.destroy();
    }
    console.log('坐姿检测工具卸载');
});

// 导出函数供其他模块使用
window.postureModule = {
    changeTimeRange,
    loadPostureData,
    loadPostureImages,
    exportPostureImages,
    showToast
}; 