## 解题思路

本题要采集 100 页、每页 10 个整数，求和后交给站点提交接口。第 1 页直接请求 init。第 2 页起，页面脚本 `initWlzShieldCaptcha` 创建 `WlzShield.CheckboxCaptcha`（siteKey 固定写在页面里），成功回调只读取 `wsToken`，再用本地可还原的 magic sign 调用 verify 换 `page_data`。100 页齐了才 POST submit。

签名在页面脚本 `generateMagicSign` 里，盐是 `wlz_shield_magic_2024`。错误签名会被站点以 403 拒绝；签名正确才会进入 token 校验。token 不是页面脚本算出来的。补环境跑通控件后，挑战请求的字段是 `timestamp`、`wlzData`、`siteKey`、`type`。把挑战接口应答换成带 `wsToken` 的 JSON 时，`onSuccess` 拿到的就是应答里的原值，控件不另签一份。

## 请求链

1. `GET /captcha/api/wlzshield_captcha_challenge/init/?challenge_type=wlzshield_captcha_challenge`  
   返回第 1 页 `page_data`、`total_pages=100`。
2. `POST https://captcha.wangluozhe.com/api/challenge`  
   正文含 `timestamp`、`wlzData`、`siteKey`、`type`。成功时应返回 `wsToken`。
3. `POST /captcha/api/wlzshield_captcha_challenge/verify/?page_num=&timestamp=&sign=`  
   正文 `wlz_token`、`page_num`、`challenge_type`。`sign` 为 magic sign。成功时返回该页 `page_data`。
4. `POST /captcha/api/wlzshield_captcha_challenge/submit/`  
   正文 `challenge_type` 与全部页面整数之和 `answer`。

签名步骤：`timestamp|pageNum|盐` 做 MD5，十六进制反转后再 MD5，按第 8–16、24–32、0–8、16–24 位拼回，再加盐做 MD5。另有 `POST .../page/`，未核销时返回「验证已过期，请重新验证」，不能绕过 verify。

## 重点解决思路

厂商只接受真实 Gecko 里跑出来的 `wlzData`。jsdom 采集会被完整性检查拒绝，历史密文也不能拿来重放。可用路径是在同一个 RuyiDOM 进程里签发 `wsToken`、立刻 verify，再提交总和。登录态用 `dom.cookieJar.setCookieSync` 放进这个进程，页面请求走 XHR。

签发和校验必须看见同一个出口。本机混合代理会把厂商域名和站点域名送到不同出口，站点就回「IP地址不匹配」。RuyiDOM 把 `network.proxy.type` 设为直连后，两边出口一致，verify 才能过。

一个 `wsToken` 只能核销一页。并发拿同一枚 token 会得到「Token已被使用」；未核销时 `POST .../page/` 仍是「验证已过期，请重新验证」。第 1 页用 init，第 2–100 页各签发一次再 verify。下一页要新建 `CheckboxCaptcha`，并先换掉 `#login-captcha` 节点，否则 `attachShadow` 不能挂到已有 shadow root 上。`enumerateDevices` 用 200ms 超时兜底，`createEvent('Touch')` 失败时改成 `TouchEvent`，控件才会真正发出挑战请求。

`solve.py` 已跑通。`result.json` 为 `success=true`、`is_correct=true`，`message` 含「答案正确」。
