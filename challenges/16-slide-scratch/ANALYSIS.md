# 滑动刮刮乐

## 解题思路

这一题要采集 100 页、每页 10 个整数，求和后提交。`init` 直接返回第 1 页。第 2 页起每次都要先解开一张滑动刮刮乐，通过后才能取该页数字。

刮刮乐接口给出题目（例如 `2个芒果`）和一张 750×460 的底图。页面上盖着一块从左向右拉开的遮罩，遮罩容器最大宽度是 350px。提交的 `distance` 是遮罩左边缘的 CSS 像素；服务端按 `distance * 750 / 350` 还原成原图像素，再和「从左数第 N 个目标图标刚好完全露出」的位置比较。差 1 个像素也会失败，并且失败后这张验证码立刻作废，不能在同一张图上修正。

图标是 16 种固定精灵（飞机、篮球、轮船、火箭、月亮、手机、奶瓶、草莓、书包、羽毛球、芒果、太阳、葡萄、风扇、菠萝、足球）。用蒙版模板匹配找出目标，按右边界从左到右排序，取第 N 个。右边界用匹配横坐标加上模板宽度（图标右侧第一个像素，而不是图标内部的最后一个像素）。再换算成 CSS 距离提交。

页数据用 `collect_pages` 并发拉取，并发度 4。全部 100 页齐了才求和提交。站点返回 `is_correct: true`，消息为答案正确。

## 请求链

1. `GET /captcha/api/slide_scratch_challenge/init/?challenge_type=slide_scratch_challenge`  
   初始化，并带第 1 页 `page_data`。
2. `GET /captcha/api/slide_scratch_challenge/captcha`  
   返回 `question`、`captchaId` 和底图 data URL。只在内存里解码，不落盘。
3. `POST /captcha/api/slide_scratch_challenge/verify`  
   JSON：`distance`（浮点 CSS 像素）、`captchaId`。成功才有一次性通行凭证。
4. `GET /captcha/api/slide_scratch_challenge/page/{n}/?challenge_type=slide_scratch_challenge&token=...`  
   第 2–100 页。凭证只用于这一次取页，不写入文件或日志。
5. `POST /captcha/api/slide_scratch_challenge/submit/`  
   JSON：`challenge_type`、`answer`（100 页全部数字之和）。

没有验证码时直接请求第 2 页会返回「缺少验证 token」。`429` 时按 1s、2s、4s… 退避，上限 16s。

## 重点解决思路

遮罩位移不能靠外部打码，也不能靠浏览器去拖。底图上的图标和题面名词一一对应，所以事先从多张样本里抽出每种图标的透明蒙版，解题时只对题目点名的那一种做 `matchTemplate`（`TM_CCORR_NORMED` + alpha 蒙版）。得分阈值 0.96：真图标通常在 0.98 以上，轮船、月亮、奶瓶的背景误峰大约在 0.91–0.95，放低阈值会把左侧误峰当成第 N 个。

坐标有两步，缺一不可：

- 完全露出的原图位置是匹配点 `x + 模板宽度`，不是图标色块的最右列。已知芒果样本的服务端目标是 640，色块右沿是 639，加 1 后重合。
- 浏览器实际提交的是 350px 容器里的位移。`distance = 原图x * 350 / 图宽`。用 `1个太阳`、原图 x=480 时得到 224，验证接口直接返回成功，说明比例就是样式里的 `max-width: 350px`，不是滑块按钮宽度。

同一会话可以并行持有多张未验证的验证码，所以 4 路并发各自完成「拉图 → 本地测距 → 验证 → 取页」，不必按页串行。
