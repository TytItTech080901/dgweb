// tabs.js - 标签页切换功能

document.addEventListener('DOMContentLoaded', function() {
    // 获取所有标签和标签内容
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // 为每个标签添加点击事件
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // 获取目标标签内容的ID
            const targetId = this.getAttribute('data-tab');
            
            // 移除所有标签的active类
            tabs.forEach(t => t.classList.remove('active'));
            
            // 添加active类到当前标签
            this.classList.add('active');
            
            // 隐藏所有标签内容
            tabContents.forEach(content => content.classList.remove('active'));
            
            // 显示目标标签内容
            document.getElementById(targetId).classList.add('active');
        });
    });
});