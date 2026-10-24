# 字体反爬（雪碧图）

## 解题思路

题目要求把 100 页、每页 10 个数字加总后提交。初始化接口直接给出第 1 页的明文数字；第 2 页起（以及再次请求第 1 页时）每个数字被拆成 4 个 `sprite` 标签，真实字形在一张 500×50 的 PNG 雪碧图里。样式把可视窗口定成 25×45，`background-position` 的横坐标是 `-8, -58, …, -458`，对应 10 个 50px 宽的格子，每格恰好一个 0–9。

雪碧图每页都会换排列，但 10 个字形本身不变。初始化给出的第 1 页明文用来给这 10 个字形建模板，后面各页只做像素匹配，不再依赖 OCR 投票。格子宽 50px，第一格从 x=8 开始，所以下标是 `abs(background-position) // 50`。不能用当页最小偏移当原点：这一页如果没用到最左边那一格，最小偏移会变成 58，所有下标都会错一位。拼回 4 位数字后，第 1 页必须和初始化明文一致才提交。

## 请求链

1. `GET /font_anti/api/font_sprites_challenge/init/?challenge_type=font_sprites_challenge`  
   建立或继续本次挑战，返回 `total_pages=100` 和第 1 页明文 `page_data`。
2. `GET /font_anti/api/font_sprites_challenge/page/{1..100}/?challenge_type=font_sprites_challenge`  
   每页返回 10 段 sprite HTML、`css_code` 和 base64 `sprite`。100 页用 `collect_pages` 并发拉取，并发度为 4；遇到 429 或连接错误则指数退避。
3. `POST /font_anti/api/font_sprites_challenge/submit/`  
   JSON 体只有 `challenge_type` 和整数 `answer`。以响应里的 `is_correct` / `message` 判断是否答对。

## 重点解决思路

类名每页都变，不能跨页缓存。稳定的是字形像素和第 1 页明文的对应关系。`background-position` 取值是 `-8, -58, …, -458`，用整除 50 得到 0–9，和 500px 宽的雪碧图一一对应。某页 CSS 可以缺掉其中一格；这时若改用最小偏移做原点，原来的 `-58` 会被当成第 0 格，整页数字都会读错。模板匹配要求 10 格正好是 0–9 各一次，对不上就重新拉这一页。
