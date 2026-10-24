# s4-environment-patch

## 面

存在性：首页 `document` 没有离开 `about:blank`。不是外观、descriptor、`toString`、原型或指纹。

## 双条件

- 浏览器 `rt_20261010022224_c1437434d7`：首页文档存在，页面脚本发出 `GET /admin_I/api/auth/check` 和 `GET /admin_I/api/auth/captcha`。
- 本地 `r56175f00023947f4985b`：通道 `GET https://www.spiderdemo.cn/` 200，但 `location` 仍是 `about:blank`，navigation timing 的 `responseStatus` / `decodedBodySize` / `transferSize` 都是 0，`login` / `showRegister` / `toRegister` 不存在。

## 改前 / 改后

- 改前：`RuyiDOM.fromURL` 走 `loadURI`。通道能看到 200，响应没有装进 document。stderr 是 xpcshell 内部模块 `SessionStoreFunctions.sys.mjs` 加载失败，没有把它伪装成页面 API，也没有造 stub。
- 改后：同一条 runner 先用独立通道读首页响应体，再用 `new RuyiDOM(html, { url })` 把该 HTML 装进 document。`code.base.js` 是改前副本。未改 navigator、screen、指纹、descriptor、`toString`、原型。

## 未重跑

未调用 ruyidom，未重跑 runner。未改 `next`、`turnGate`、`goal`、`dispatcher`、`hostProbe`。未提交注册或登录。未写 Cookie、token、密码。未降级 patched Node。
