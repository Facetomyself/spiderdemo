# s10 document same-surface flush

## 面

仍是首页 document。安装方式保持 `document.open` / `document.write` / `document.close`。没有新增 navigator、screen、指纹、descriptor 或 toString。没有调用 `login()` / `showRegister()` / `toRegister()`。

## 改动

`r7429e6a582b7404ea200` 里页面脚本已经执行，随后 `Exiting due to channel error.`，stdout 没有 JSON。通道观察只留在内存里，进程退出后请求边界丢失。

同一条 runner 现在在每条站内通道响应上立刻追加 `landing/env-patch/ruyidom/channel-log.jsonl`。`auth/check` 和 `auth/captcha` 都出现时再立刻 `print` 一行 JSON。未重跑。

## 协议模块

注册和登录协议模块还不能标完成。浏览器事实里只有未登录的两个 GET。登录 POST 的 URL 仍未观察。
