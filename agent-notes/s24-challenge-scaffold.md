# s24 challenge scaffold

站点挑战接口返回 33 条。`control_challenge`（控制流加强）和 `slide_sum2_challenge`（计算题验证码plus）的按钮文案是「开发中」，`main.js` 里没有对应 starter，这两道跳过。

其余 31 道的页面入口来自 starter 里的明文路径，或字符串表里的明文路径。目录在 `challenges/<slug>/`，清单是 `challenges/catalog.json`。合同是 `challenges/CONTRACT.md`。

共享运行时是 `modules/runtime.py`：登录后的 httpx 会话，以及 `collect_pages` 异步分页。验证码约定走本机 `ddddocr`。不使用浏览器自动化，不使用外部打码。

调度仍是 `compact_replay_done` / `blocked`。没有把交付改成浏览器采集器。
