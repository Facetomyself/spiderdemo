// 获取DOM元素 (内嵌模式)
const captchaImage = document.getElementById('captchaImage')
const info = document.querySelector('.info')
const btn = document.querySelector('.press-btn')
const fill = document.querySelector('.fill')
const overlay = document.querySelector('.overlay')
const prompt = document.getElementById('prompt')

let captchaId = ""
let state;
let pressing = false;
let rotating = false;
let startTime = 0;
let progressStartTime = 0;
let lastFrameTime = 0;
let rafRotate = 0;
let rafPress = 0;
let angle = 0;
let progress = 0;
const PRESS_DURATION = 2.0;

// RAF 动画旋转
function rotate(timestamp) {
  if (!rotating) return;

  if (!lastFrameTime) lastFrameTime = timestamp;
  const dt = (timestamp - lastFrameTime) / 1000; // 秒
  lastFrameTime = timestamp;

  angle = window.pressRotateState.tick(dt); // WASM 管理角度和速度
  captchaImage.style.transform = `rotate(${angle}deg)`;

  rafRotate = requestAnimationFrame(rotate);
}

function pressProgress() {
    if (!pressing) return;
    const now = Date.now();
    const elapsed = (now - progressStartTime) / 1000;
    progress = Math.min(elapsed / PRESS_DURATION, 1);
    updateFill();
    rafPress = requestAnimationFrame(pressProgress);
}

function startPress(e) {
    e.preventDefault();
    if (pressing) return;
    pressing = true;
    window.pressRotateState.pressStart()

    startTime = performance.now();
    progressStartTime = Date.now();
    window.pressRotateState.set_t(BigInt(progressStartTime))
    progress = 0;
    updateFill();

    rotating = true;
    lastFrameTime = startTime;
    requestAnimationFrame(rotate);
    requestAnimationFrame(pressProgress);
}

async function endPress(e) {
    e.preventDefault();
    if (!pressing) return;
    pressing = false;
    rotating = false;
    cancelAnimationFrame(rafRotate);
    cancelAnimationFrame(rafPress);

    window.pressRotateState.pressEnd(); // 立即停止角速度

    await pressRotateVerify()
    animateResetProgress();
}

function updateFill() {
    fill.style.width = Math.round(progress * 100) + '%';
}

function animateResetProgress() {
    const start = progress;
    const duration = 500;
    const startTime = performance.now();

    function step(ts) {
        const t = Math.min((ts - startTime) / duration, 1);
        const eased = 1 - (1 - t) * (1 - t);
        progress = start * (1 - eased);
        updateFill();

        if (t < 1) requestAnimationFrame(step);
        else progress = 0;
    }

    requestAnimationFrame(step);
}

/**
 * 获取挑战类型的显示名称
 * @param {string} type - 挑战类型ID
 * @returns {string} 显示名称
 */
function getChallengeDisplayName(type) {
    const names = {
        'header_check': '请求头检测挑战',
        'number_challenge': '动态数字求和挑战',
        'js_challenge': 'JS混淆解析挑战',
        "slide_puzzle_challenge": '滑动拼图',
        "slide_scratch_challenge": '滑动刮刮乐',
        "slide_cylinder_challenge": '滑动圆柱体',
        "click_stitch_challenge": '点击拼图',
        "press_rotate_challenge": '按压旋转',
    };
    return names[type] || type;
}

/**
 * 页面初始化
 */
function initializePage() {
    // 从URL获取挑战类型
    challengeType = getChallengeTypeFromUrl();
    console.log('当前挑战类型:', challengeType);

    // 更新页面标题
    updatePageTitle();

    // 加载第一页数据
    loadPageData(1);

}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function () {
    initializePage();
    btn.addEventListener('mousedown', startPress);
    document.addEventListener('mouseup', endPress);
    btn.addEventListener('touchstart', startPress, { passive: false });
    document.addEventListener('touchend', endPress);
});

/**
 * 更新页面标题显示当前题目类型
 */
function updatePageTitle() {
    const titleElement = document.querySelector('.challenge-title');
    if (titleElement) {
        const displayName = getChallengeDisplayName(challengeType);
        titleElement.innerHTML = `🎯 任务: 采集这100页的全部数字，计算加和并提交结果<br/><small>(${displayName})</small>`;
    }

    // 更新页面主标题
    const pageTitle = document.querySelector('.page-title');
    if (pageTitle) {
        pageTitle.innerHTML = `🔢 ${getChallengeDisplayName(challengeType)}`;
    }
}

// 显示验证码消息
function showCaptchaMessage(message, type) {
    if (captchaMessage) {
        captchaMessage.textContent = message;
        captchaMessage.className = `captcha-message ${type}`;
        captchaMessage.style.display = 'block';

        // 自动隐藏消息
        if (type !== 'loading') {
            const hideDelay = type === 'success' ? 800 : (type === 'error' ? 1500 : 3000); // 成功和错误消息都更快隐藏
            setTimeout(() => {
                captchaMessage.style.display = 'none';
            }, hideDelay);
        }
    }
}

// 隐藏验证码消息
function hideCaptchaMessage() {
    if (captchaMessage) {
        captchaMessage.style.display = 'none';
    }
}

// 保留原有的closeCaptcha函数名，用于兼容
function closeCaptcha() {
    hideCaptcha();
}

function hideCaptcha() {
    if (captchaImage) {
        captchaImage.style.display = 'none';
    }
    if (overlay) {
        overlay.style.display = 'none';
    }
}


async function pressRotateVerify() {
    try {
        angle = window.pressRotateState.angle; // 最终角度
        const timestamp = Date.now();
        let postData = {
            timestamp,
            angle,
            captchaId,
            data: window.pressRotateState.getResult(window.navigator.userAgent)
        }
        const response = await fetch('/captcha/api/press_rotate_challenge/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(postData)
        });

        const data = await response.json();

        // 检查后端返回的登录错误
        if (data.error && data.error.includes('请先登录')) {
            showLoginAlert();
            return data;
        }
        if (data.success) {
            window.press_rotate_token = data.data.token
            showCaptchaMessage('验证成功！', 'success');
            setTimeout(async () => {
                // 调用HTML中定义的成功回调函数
                if (typeof window.onPressRotateSuccess === 'function') {
                    window.onPressRotateSuccess();
                } else {
                    // 兼容原有逻辑
                    if (typeof hideCaptcha === 'function') {
                        hideCaptcha();
                    }
                    if (typeof loadPageData === 'function') {
                        await loadPageData(currentPage);
                    }
                }
            }, 500)
        } else {
            showCaptchaMessage('验证失败，请重试', 'error');
            setTimeout(async () => {
                showCaptchaMessage('正在加载验证码...', 'loading');
            }, 500)
            setTimeout(async () => {
                await fetchCaptcha()
            }, 1000)
        }
    } catch (error) {
        console.error('验证失败:', error);

        // 检查网络错误中的登录提示
        if (error.message && error.message.includes('请先登录')) {
            showLoginAlert();
        }

        throw error;
    }
}

async function fetchCaptcha() {
    captchaImage.style.backgroundImage = `url()`
    try {
        const response = await fetch('/captcha/api/press_rotate_challenge/captcha', {
            method: 'GET',
        });
        const data = await response.json();

        // 检查后端返回的登录错误
        if (data.error && data.error.includes('请先登录')) {
            showLoginAlert();
            return;
        }

        captchaId = data.data.captchaId
        if (data.success) {
            window.pressRotateState.check_data(data.data.data)
            captchaImage.style.backgroundImage = `url(${data.data.bg})`
            refresh()
        } else {
            showCaptchaMessage('获取验证码失败', 'error');
        }
    } catch (error) {
        console.error('获取验证码失败:', error);
        if (error.message && error.message.includes('请先登录')) {
            showLoginAlert();
        } else {
            showCaptchaMessage('获取验证码失败，请重试', 'error');
        }
    }
}

function refresh() {
    window.pressRotateState.reset()
    captchaImage.style.transform = `rotate(0deg)`;
    angle = 0;
}

// 刷新验证码（重新获取）
function refreshCaptcha() {

    // 先重置滑块位置
    refresh();

    // 清除验证码消息
    if (typeof hideCaptchaMessage === 'function') {
        hideCaptchaMessage();
    }

    // 重新获取验证码
    fetchCaptcha();
}

// 导出到全局
window.fetchCaptcha = fetchCaptcha;
window.refreshCaptcha = refreshCaptcha;

