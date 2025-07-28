// 工具详情页面JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('工具详情页面已加载');
    
    // 初始化页面
    initToolDetail();
    
    // 添加事件监听器
    addEventListeners();
});

function initToolDetail() {
    // 获取工具名称
    const toolName = getToolNameFromURL();
    
    // 显示对应的工具内容
    showToolContent(toolName);
    
    // 初始化图表
    initCharts();
    
    // 加载数据
    loadToolData(toolName);
}

function getToolNameFromURL() {
    // 从URL中获取工具名称
    const path = window.location.pathname;
    const match = path.match(/\/mobile\/tool\/(\w+)/);
    return match ? match[1] : 'posture';
}

function showToolContent(toolName) {
    // 隐藏所有工具内容
    document.querySelectorAll('.tool-content').forEach(content => {
        content.style.display = 'none';
    });
    
    // 显示对应的工具内容
    const targetContent = document.getElementById(toolName + '-content');
    if (targetContent) {
        targetContent.style.display = 'block';
    }
    
    // 更新标题
    const toolTitle = document.getElementById('toolTitle');
    if (toolTitle) {
        toolTitle.textContent = getToolDisplayName(toolName);
    }
}

function getToolDisplayName(toolName) {
    const toolNames = {
        'posture': '坐姿检测',
        'eye': '用眼监护',
        'emotion': '情绪识别'
    };
    return toolNames[toolName] || toolName;
}

function initCharts() {
    // 初始化图表
    // 这里可以根据需要添加图表初始化代码
    console.log('图表初始化完成');
}

function loadToolData(toolName) {
    // 加载工具数据
    fetch(`/api/tool/${toolName}/data`)
        .then(response => response.json())
        .then(data => {
            updateToolData(toolName, data);
        })
        .catch(error => {
            console.error('加载数据失败:', error);
        });
}

function updateToolData(toolName, data) {
    // 更新页面数据
    if (toolName === 'posture') {
        updatePostureData(data);
    } else if (toolName === 'eye') {
        updateEyeData(data);
    } else if (toolName === 'emotion') {
        updateEmotionData(data);
    }
}

function updatePostureData(data) {
    // 更新坐姿数据
    if (data.goodPostureTime) {
        document.getElementById('goodPostureTime').textContent = data.goodPostureTime;
    }
    if (data.mildBadPostureTime) {
        document.getElementById('mildBadPostureTime').textContent = data.mildBadPostureTime;
    }
    if (data.badPostureTime) {
        document.getElementById('badPostureTime').textContent = data.badPostureTime;
    }
    if (data.postureRate) {
        document.getElementById('postureRate').textContent = data.postureRate;
    }
}

function updateEyeData(data) {
    // 更新用眼数据
    // 根据实际需要实现
}

function updateEmotionData(data) {
    // 更新情绪数据
    // 根据实际需要实现
}

function addEventListeners() {
    // 添加时间范围选择器事件
    document.querySelectorAll('.time-range-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const range = this.dataset.range;
            changeTimeRange(range);
        });
    });
    
    // 添加图表指示器事件
    document.querySelectorAll('.indicator-dot').forEach(dot => {
        dot.addEventListener('click', function() {
            const chartIndex = this.dataset.chart;
            switchChart(chartIndex);
        });
    });
}

function changeTimeRange(range) {
    // 更新活跃状态
    document.querySelectorAll('.time-range-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // 重新加载数据
    const toolName = getToolNameFromURL();
    loadToolData(toolName);
}

function switchChart(chartIndex) {
    // 更新指示器状态
    document.querySelectorAll('.indicator-dot').forEach(dot => {
        dot.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // 切换图表显示
    document.querySelectorAll('.chart-slide').forEach(slide => {
        slide.classList.remove('active');
    });
    document.getElementById(`slide-${chartIndex}`).classList.add('active');
}

// 全局函数，供HTML调用
window.changeTimeRange = changeTimeRange;
window.switchChart = switchChart; 