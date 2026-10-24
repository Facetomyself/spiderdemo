# 第一代验证码

## 解题思路

这一题要采集 100 页、每页 10 个整数，求和后提交。第 1 页由初始化接口直接返回，不需要验证码。第 2 到 100 页先取一张 PNG，本地认出 4 个字符，再换这一页的数字。全部加总后交给提交接口，站点返回 `is_correct=true` 且消息含「答案正确」才算通过。

验证码是 PIL `ImageFont.load_default()` 的点阵字：大写和数字占 8 行，q、y、g、p、j 的下伸部分再占 2 行，背景上有彩色点和浅灰斜线。处理只在本机完成：用暗且低色度的像素抠出字形，和 62 个本地模板做错位比较。`I` 和 `l` 的点阵相同，两种都提交试一次。模板分数不为 0，或切分没有得到 4 个字时，再用 `ddddocr` 的 beta 模型（`common.onnx`）读清洗后的字带，作为下一条候选。不调用外部打码。

页数据属于同一次挑战，验证码存在各自的会话里。求解开 4 个 `SpiderSession`，用 `collect_pages` 以并发 4 拉取第 2–100 页。同一会话上连续取图会覆盖未提交的验证码，所以每个工人拿自己的会话。HTTP 429 时按 1、2、4、8 秒退避后再发。

## 请求链

1. `GET /captcha/api/cap1_challenge/init/?challenge_type=cap1_challenge`  
   返回 `page_data`（第 1 页的 10 个数）、`total_pages=100`、`success`。
2. `GET /captcha/api/cap1_challenge/captcha_image/?t=<页码-重试>`  
   返回 `image/png`。验证码跟当前会话走，换会话就是另一张图。
3. `POST /captcha/api/cap1_challenge/page/`  
   JSON：`captcha_input`、`page_num`、`challenge_type`。成功时 `page_data` 是 10 个整数。`验证码错误` 不会作废这张图，同一张图可以继续试候选；都不对再换图。
4. `POST /captcha/api/cap1_challenge/submit/`  
   JSON：`challenge_type`、`answer`（100 页全部整数之和）。判定看 `is_correct` 和 `message`，不看 HTTP 200 本身。

页面脚本在 `/static/js/captcha/cap1_challenge.js`，翻页请求在页面内联的 `apiGetPageData`。`anti_automation.js` 只计前端点击，协议请求不依赖它。

## 重点解决思路

裸跑 `ddddocr` 不够。这个环境里默认和 old 都会加载中文旧模型；beta 模型对带噪点的原图不稳定，清洗后也经常差一两个字符。点阵字和 `load_default()` 对齐之后，汉明距离能直接定字，站点接受的是这个字符串的原样大小写。

切分按整行做。先取墨水量最大的 10 行，丢掉孤立噪点，再按列切开。高度至少 6 的笔画都留下，这样 1 像素宽的 `I`/`l` 不会被宽噪声挤掉。斜线擦掉字中间的一列时，会多出一块碎片；多于 4 块才把只隔 1 列、合起来不超过 8 列的碎片粘回去。每个字保留与最优分差不超过 1 的候选，最多试 12 条组合。

并发不能共用一个验证码槽。4 个会话各自取图、各自提交页码，数字仍是同一次挑战的同一组数。单页失败会换图重试，不会带着缺页去提交。
