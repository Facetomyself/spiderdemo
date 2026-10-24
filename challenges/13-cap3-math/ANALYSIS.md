# cap3_challenge 计算题验证码

## 解题思路

这一题要采集 100 页、每页 10 个数字，求和后提交。第 1 页由初始化接口直接给出，不需要验证码。第 2 页到第 100 页每次都要先取一张计算题图，本地算出结果，再把结果当作 `captcha_input` 换这一页的数字。

验证码图被切成 50 张 3×50 的 PNG，按数组顺序从左到右拼回 150×50。图上有彩色噪点和灰色斜线。数字用暗色像素留下，再和本机 PIL 默认字体做重合度匹配。加号和减号的横杠比较浅，只看暗色像素会把加号认成乘号、把减号丢掉，所以在两个数字的空隙里再看浅灰色笔画：又横又竖是加号，只有横杠是减号，其余有笔画像乘号。

`ddddocr` 会先读整张拼好的图。这种点阵上它经常缺运算符，所以只有字体匹配读不出合法算式时才采用它的结果。算式只允许非负整数和 `+ - * /`，除法必须整除。100 页全部到齐后把总和交给提交接口。

## 请求链

1. `GET /captcha/cap3_challenge/?challenge_type=cap3_challenge` 取页面。页面脚本是 `/static/js/captcha/cap3_challenge.js`，页内还有 `apiGetPageData`。
2. `GET /captcha/api/cap3_challenge/init/?challenge_type=cap3_challenge`。成功时字段有 `success`、`page_data`、`total_pages`、`current_page`、`message`。`page_data` 就是第 1 页的 10 个整数。
3. 对其余页：`GET /captcha/api/cap3_challenge/captcha_image/?t=`。JSON 的 `data` 是 50 段 base64 PNG。
4. `POST /captcha/api/cap3_challenge/page/`，JSON 字段是 `captcha_input`、`page_num`、`challenge_type`。通过时 `success=true` 且带 `page_data`。失败时常见 `验证码错误` 或 `验证码已过期，请刷新`。
5. `POST /captcha/api/cap3_challenge/submit/`，JSON 字段是 `challenge_type` 和 `answer`。通过时 `is_correct=true`，`message` 含「答案正确」。

多页用 `collect_pages`，并发上限 4。验证码答案存在当前会话的一个槽里，第二次取图会让上一张过期，所以取图、识别、提交这三步共用一把锁。HTTP 429 按 1 秒起指数退避，上限 8 秒。单页最多重试 12 次。

## 重点解决思路

难点不在分页签名，而在算式图。切片顺序就是阅读顺序，不需要再打乱还原。彩色点用通道差滤掉，接近 200 的灰线不计入笔画。

数字高度大约 8 像素，和 PIL `ImageFont.load_default` 在 10 到 20 号的字形做缩放后的交并比，取得分最高的数字。两个数字之间的空隙窄于 3 列时视为同一个数，例如 `30`。空隙更宽时，用亮度不超过 188 的灰像素判断运算符，避免只剩加号竖笔时被认成 `*`。

`ddddocr` 限制在数字和 `+ - * x X =`。它能读到个别数字，但整条算式不可靠，因此不能单独交卷。识别失败或站点拒绝就换一张新图，不把空结果提交上去。
