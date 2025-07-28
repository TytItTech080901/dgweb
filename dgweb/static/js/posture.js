// 坐姿检测工具JavaScript - 柔和绿色调配色方案

// 全局变量
let currentTimeRange = 'day';
let currentChartIndex = 0;
let posturePieChart = null;
let heatmapChart = null;
let postureImages = [];

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('坐姿检测工具初始化');
    
    // 初始化图表
    initCharts();
    
    // 加载数据
    loadPostureData();
    
    // 加载坐姿图像
    loadPostureImages();
    
    // 初始化事件监听器
    initEventListeners();
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
    
    // 图表指示器事件
    const indicatorDots = document.querySelectorAll('.indicator-dot');
    indicatorDots.forEach(dot => {
        dot.addEventListener('click', function() {
            const chartIndex = parseInt(this.getAttribute('data-chart'));
            switchChart(chartIndex);
        });
    });
}

// 切换时间范围
function changeTimeRange(range) {
    currentTimeRange = range;
    
    // 更新按钮状态
    document.querySelectorAll('.time-range-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-range="${range}"]`).classList.add('active');
    
    // 重新加载数据
    loadPostureData();
    
    // 显示提示
    const rangeNames = {
        day: '今日',
        week: '本周',
        month: '本月'
    };
    showToast(`已切换到${rangeNames[range]}数据`);
}

// 切换图表
function switchChart(chartIndex) {
    if (chartIndex === currentChartIndex) return;
    
    // 更新指示器状态
    document.querySelectorAll('.indicator-dot').forEach(dot => {
        dot.classList.remove('active');
    });
    document.querySelector(`[data-chart="${chartIndex}"]`).classList.add('active');
    
    // 更新图表显示
    const slides = document.querySelectorAll('.chart-slide');
    slides.forEach(slide => {
        slide.classList.remove('active');
    });
    
    const currentSlide = slides[currentChartIndex];
    const targetSlide = slides[chartIndex];
    
    // 添加切换动画
    currentSlide.classList.add('slide-out-left');
    setTimeout(() => {
        currentSlide.classList.remove('active', 'slide-out-left');
        targetSlide.classList.add('active', 'slide-in-right');
        setTimeout(() => {
            targetSlide.classList.remove('slide-in-right');
        }, 300);
    }, 150);
    
    currentChartIndex = chartIndex;
    
    // 更新图表标题和图标
    updateChartHeader(chartIndex);
    
    // 重新渲染图表
    renderChart(chartIndex);
}

// 更新图表头部
function updateChartHeader(chartIndex) {
    const titles = ['坐姿时间占比', '不良姿态时段分布', '坐姿图像记录'];
    const icons = ['bi-pie-chart', 'bi-calendar-week', 'bi-images'];
    
    const titleElement = document.getElementById('chartTitle');
    const iconElement = document.getElementById('chartIcon');
    
    if (titleElement) {
        titleElement.textContent = titles[chartIndex];
    }
    
    if (iconElement) {
        iconElement.innerHTML = `<i class="bi ${icons[chartIndex]}"></i>`;
    }
}

// 初始化图表
function initCharts() {
    // 初始化饼图
    const pieCtx = document.getElementById('posturePieChart');
    if (pieCtx) {
        posturePieChart = new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: ['良好坐姿', '轻度不良', '不良坐姿'],
                datasets: [{
                    data: [64, 24, 12],
                    backgroundColor: [
                        'rgba(143, 180, 160, 0.8)',
                        'rgba(230, 184, 148, 0.8)',
                        'rgba(209, 139, 122, 0.8)'
                    ],
                    borderColor: [
                        'rgba(143, 180, 160, 1)',
                        'rgba(230, 184, 148, 1)',
                        'rgba(209, 139, 122, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: {
                                size: 12
                            }
                        }
                    }
                }
            }
        });
    }
    
    // 初始化热力图
    const heatmapCtx = document.getElementById('heatmapChart');
    if (heatmapCtx) {
        // 这里可以集成热力图库，暂时用简单的柱状图代替
        heatmapChart = new Chart(heatmapCtx, {
            type: 'bar',
            data: {
                labels: ['6-8', '8-10', '10-12', '12-14', '14-16', '16-18', '18-20'],
                datasets: [{
                    label: '坐姿质量',
                    data: [85, 78, 72, 65, 58, 82, 90],
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

// 渲染图表
function renderChart(chartIndex) {
    switch(chartIndex) {
        case 0:
            updatePieChart();
            break;
        case 1:
            updateHeatmapChart();
            break;
        case 2:
            // 图像记录不需要重新渲染
            break;
    }
}

// 更新饼图数据
function updatePieChart() {
    if (!posturePieChart) return;
    
    // 模拟不同时间范围的数据
    const dataMap = {
        day: [64, 24, 12],
        week: [58, 28, 14],
        month: [52, 32, 16]
    };
    
    const newData = dataMap[currentTimeRange] || dataMap.day;
    
    posturePieChart.data.datasets[0].data = newData;
    posturePieChart.update();
    
    // 更新统计数值
    updateStats(newData);
}

// 更新热力图数据
function updateHeatmapChart() {
    if (!heatmapChart) return;
    
    // 模拟不同时间范围的数据
    const dataMap = {
        day: [85, 78, 72, 65, 58, 82, 90],
        week: [82, 75, 68, 62, 55, 79, 87],
        month: [79, 72, 65, 58, 52, 76, 84]
    };
    
    const newData = dataMap[currentTimeRange] || dataMap.day;
    
    heatmapChart.data.datasets[0].data = newData;
    heatmapChart.update();
}

// 更新统计数值
function updateStats(data) {
    const total = data.reduce((sum, val) => sum + val, 0);
    const goodTime = (data[0] / total * 5).toFixed(1);
    const mildTime = (data[1] / total * 5).toFixed(1);
    const badTime = (data[2] / total * 5).toFixed(1);
    const rate = data[0];
    
    document.getElementById('goodPostureTime').textContent = goodTime + 'h';
    document.getElementById('mildBadPostureTime').textContent = mildTime + 'h';
    document.getElementById('badPostureTime').textContent = badTime + 'h';
    document.getElementById('postureRate').textContent = rate + '%';
}

// 加载坐姿数据
function loadPostureData() {
    // 模拟API调用
    fetch(`/api/posture/data?range=${currentTimeRange}`)
        .then(response => response.json())
        .then(data => {
            console.log('坐姿数据加载成功:', data);
            // 这里可以处理真实的数据
        })
        .catch(error => {
            console.error('加载坐姿数据失败:', error);
            // 使用模拟数据
            updatePieChart();
            updateHeatmapChart();
        });
}

// 加载坐姿图像
function loadPostureImages() {
    const container = document.getElementById('posture-images-container');
    if (!container) return;
    
    // 清空容器
    container.innerHTML = '<div class="loading-indicator"><i class="bi bi-arrow-clockwise"></i><span>加载中...</span></div>';
    
    // 模拟API调用
    fetch('/api/posture/images')
        .then(response => response.json())
        .then(data => {
            postureImages = data.images || [];
            renderPostureImages();
        })
        .catch(error => {
            console.error('加载坐姿图像失败:', error);
            // 使用模拟数据
            loadMockPostureImages();
        });
}

// 加载模拟坐姿图像
function loadMockPostureImages() {
    const mockImages = [
        { id: 1, url: '/static/posture_images/posture_20250528_213901_8c748294.jpg', time: '2025-05-28 21:39:01', quality: 'good' },
        { id: 2, url: '/static/posture_images/posture_20250528_214033_8d2c9369.jpg', time: '2025-05-28 21:40:33', quality: 'warning' },
        { id: 3, url: '/static/posture_images/posture_20250528_214121_70930925.jpg', time: '2025-05-28 21:41:21', quality: 'good' },
        { id: 4, url: '/static/posture_images/posture_20250528_214232_a147a01a.jpg', time: '2025-05-28 21:42:32', quality: 'danger' },
        { id: 5, url: '/static/posture_images/posture_20250528_220403_6e4d79db.jpg', time: '2025-05-28 22:04:03', quality: 'good' },
        { id: 6, url: '/static/posture_images/posture_20250528_221434_ef659455.jpg', time: '2025-05-28 22:14:34', quality: 'warning' }
    ];
    
    postureImages = mockImages;
    renderPostureImages();
}

// 渲染坐姿图像
function renderPostureImages() {
    const container = document.getElementById('posture-images-container');
    if (!container) return;
    
    if (postureImages.length === 0) {
        container.innerHTML = '<div class="loading-indicator"><i class="bi bi-images"></i><span>暂无图像记录</span></div>';
        return;
    }
    
    const imageHTML = postureImages.map(image => `
        <div class="posture-image-item" data-id="${image.id}">
            <img src="${image.url}" alt="坐姿记录" onerror="this.src='/static/asserts/WechatIMG69.jpg'">
            <div class="posture-image-overlay">
                <span style="color: white; font-size: 10px;">${image.time}</span>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = imageHTML;
    
    // 添加图像点击事件
    container.querySelectorAll('.posture-image-item').forEach(item => {
        item.addEventListener('click', function() {
            const imageId = this.getAttribute('data-id');
            showImageDetail(imageId);
        });
    });
}

// 显示图像详情
function showImageDetail(imageId) {
    const image = postureImages.find(img => img.id == imageId);
    if (!image) return;
    
    // 这里可以实现图像详情弹窗
    showToast(`查看图像详情: ${image.time}`);
}

// 加载更多坐姿图像
function loadMorePostureImages() {
    showToast('正在加载更多图像...');
    
    // 模拟加载更多数据
    setTimeout(() => {
        const newImages = [
            { id: 7, url: '/static/posture_images/posture_20250528_222435_e4206c3e.jpg', time: '2025-05-28 22:24:35', quality: 'good' },
            { id: 8, url: '/static/posture_images/posture_20250528_223456_f1234567.jpg', time: '2025-05-28 22:34:56', quality: 'warning' }
        ];
        
        postureImages = [...postureImages, ...newImages];
        renderPostureImages();
        showToast('已加载更多图像');
    }, 1000);
}

// 导出坐姿图像
function exportPostureImages() {
    showToast('正在导出图像记录...');
    
    // 模拟导出功能
    setTimeout(() => {
        showToast('图像记录导出成功');
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
    switchChart,
    loadPostureData,
    loadPostureImages,
    showToast
}; 