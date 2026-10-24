# CSS偏移挑战

## 解题思路

题目要求采集 100 页、每页 10 个数字并提交总和。分页接口不返回明文，每条 `display_html` 把数字拆成普通文本和 `span`。带样式的字使用 `position: relative`，用 `left` 或 `right` 做视觉换位。`left` 为正时向右移，`right` 为正时向左移。样式值都落在 15px 的整数倍上（`3 * 5px`、`2 * 3 * 5px`、`3 * 3 * 5px`），15px 就是一个数字槽。每个字符的视觉槽位是「文档顺序下标 + 偏移像素 / 15」。按槽位从小到大拼回整数，再把 1000 个数相加。

`data-offset` 和 `data-calc` 与真实位移不一致，只当干扰，不参与计算。

## 请求链

1. `GET /css_anti/api/challenge/init/?challenge_type=CSS1_challenge`  
   初始化当前题。响应给出 `total_pages=100`，以及第 1 页的明文整数，用来核对本地还原。
2. `GET /css_anti/api/CSS1_challenge/page/{n}/?challenge_type=CSS1_challenge`  
   `n` 从 1 到 100。用 `modules.runtime.collect_pages` 异步采集，并发 4。遇到 HTTP 429 就指数退避后重试，不按页顺序串行等待。
3. 本地解析每条 `display_html`：先求 `:root` 里的 CSS 变量（`calc`、`min`、`max`、`var`），再读每个 `span` 的 `left` / `right`，还原数字并求和。
4. `POST /css_anti/api/challenge/submit/`  
   JSON 字段只有 `challenge_type` 和 `answer`。站点返回 `success=true`、`is_correct=true`，`message` 为「答案正确！🎉 恭喜首次通过！ (CSS1_challenge)」。

读页和提交都没有额外签名参数。`validatePageNavigation` 只在前端脚本里，接口本身不要求这个校验。

## 重点解决思路

偏移写在每条 HTML 自己的 `<style>` 里，变量名每次都变，负位移通常是 `--neg-* : calc(-1 * var(--offset-*))`，再交给 `left`。因此要在本地把变量求成像素，不能把 `var()` 当成固定类名。

还原时忽略 `<style>` 里的数字，只收集可见数字字符。槽位必须是整数且互不重叠，否则视为解析失败，不提交。第 1 页 10 个数先和 init 的明文逐项比对，一致后才把全量总和提交。没有偏移的片段（例如纯文本 `6444`）按原顺序读取。
