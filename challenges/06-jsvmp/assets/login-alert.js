/**
 * 登录提示通用JavaScript函数
 * 可以被所有挑战页面引入使用
 */

/**
 * 显示登录提示
 */
function showLoginAlert() {
    const loginAlert = document.getElementById('loginAlert');
    if (loginAlert) {
        loginAlert.style.display = 'block';
        // 添加滚动到顶部的效果
        loginAlert.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

/**
 * 隐藏登录提示
 */
function hideLoginAlert() {
    const loginAlert = document.getElementById('loginAlert');
    if (loginAlert) {
        loginAlert.style.display = 'none';
    }
}

// 如果页面已加载完成，自动绑定相关事件
document.addEventListener('DOMContentLoaded', function() {
    // 可以在这里添加一些通用的初始化逻辑
    console.log('登录提示组件已加载');
});