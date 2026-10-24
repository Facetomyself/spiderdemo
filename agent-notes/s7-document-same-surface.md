# s7-document-same-surface

## 面

存在性：首页 document 的安装方式。同一对象，不换宿主字段。

## 改前 / 改后

- 改前：`RuyiDOM.main` 里再嵌套 `new RuyiDOM(html, { url })`。第二个 RuyiDOM 会把父会话通道打掉。`r656200b927284d80866d` 在 `print(JSON)` 前退出，stderr 结尾是 `Exiting due to channel error.`
- 改后：不再 `new RuyiDOM(...)`。已经读到的首页 HTML 写进当前 main 文档，用的是该文档的 `document.open`、`document.write`、`document.close`。写入前仍安装原来的请求边界钩子。`readHomepage` 以及禁止调用 `login` / `showRegister` / `toRegister` 都保持。xpcshell 的 `RuyiDOM.main` 没有现成 `window`，所以只在没有当前 window 时为这一份 main 文档建一个 docShell，不建第二个 RuyiDOM，也不 `browser.close()`。

## 未重跑

未调用 ruyidom，未重跑 runner。未改 `next`、`turnGate`、`goal`、`dispatcher`、`hostProbe`。未提交注册或登录。未新增 navigator、screen、指纹、descriptor、`toString`、原型。
