# 挑战解题合同

这是 spiderdemo 开放题的协议解题合同。每题只写自己的文件夹。

## 通过标准

站点自己的提交接口返回“答案正确”或等价的完成字段，才算通过。HTTP 200、页面能打开、本地算出一个数，都不算通过。把公开结果字段写入本文件夹的 `result.json`。不要写 Cookie、token、密码、验证码原图字节。

## 允许

- 用 `modules.runtime.SpiderSession` 带登录态发 HTTP。
- 读题目页和它引用的 JS/WASM/CSS/字体，在本地把算法或验证码还原出来。
- 多页数字采集必须异步：用 `modules.runtime.collect_pages` 或 `httpx.AsyncClient` 加 `asyncio.gather`。禁止按页顺序一个一个等。
- 验证码只用本机库。当前虚拟环境已有 `ddddocr`、`PIL`、`onnxruntime`。滑块可用 `ddddocr` 的 `slide_match` / `slide_comparison`。
- 静态分析不够时，可以做一次 RuyiTrace interactive 取证，或对本地脚本下断点。取证不是交卷方式。

## 禁止

- 浏览器自动化取巧：Playwright、Selenium、Puppeteer、ruyipage、比特浏览器、CloakBrowser，以及任何“打开页面让脚本自己点完”的做法。
- 外部打码平台、在线 OCR、把验证码图片发给第三方。
- 把密码、Cookie、token 写进笔记、`result.json`、日志或回复。
- 改别的题目文件夹、`modules/login`、调度戳、`workspace.json`。
- 运行 `web_case.py next`。当前调度停在登录回放，不是这道题的任务。

## 本文件夹产物

- `solve.py`：可重复执行的入口。从项目根运行时 `PYTHONPATH` 是 `D:\reverse_ENV\workspace\spiderdemo`，解释器是 `D:\reverse_ENV\.venv\Scripts\python.exe`。
- `ANALYSIS.md`：中文，三节。`解题思路`、`请求链`、`重点解决思路`。写清分页、签名、字体、验证码或加密各自怎么落地。
- `result.json`：只保留站点对提交的公开判定字段。

数字采集题默认先看页面自己的 init / page / submit。请求头检测那一题的共享脚本使用 `GET /sec1/api/challenge/init/?challenge_type=` 和 `POST /sec1/api/challenge/submit/`，body 字段是 `challenge_type` 与 `answer`。其它题以自己的页面脚本为准，不要照搬这条路径。
