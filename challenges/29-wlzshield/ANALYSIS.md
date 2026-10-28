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

静态还原签名后，用登录会话核对过这几道门：坏签名是「签名验证失败，请刷新重试」；好签名且 token 为空是「缺少验证token」；好签名且 token 非空、但不是厂商认可的 `wsToken` 时，站点返回「无效的Token」。

`https://captcha.wangluozhe.com/api/challenge` 已经恢复。只带 siteKey 的 POST 是 HTTP 400，正文 `认证失败`、`wsToken` 为空。控件在 jsdom 里能跑完采集，挑战正文字段仍是 `timestamp`、`wlzData`、`siteKey`、`type=checkbox`。`getEncryptedPayload` 在当前补环境里返回空串；把 `calculateHash` 得到的指纹密文按浏览器 Origin 提交后，厂商回 HTTP 200，`status=false`，`msg=认证失败`，`wsToken` 仍为空。完整性检查会把 jsdom 标成原生函数、`document.all`、XHR、节点栈和环境代理都不通过，所以这一条密文换不到能过站点 verify 的 token。没有这个 token，第 2–100 页拿不到，总和也不能提交。

2026-10-28 的浏览器现场里，登录后的第二个标签完成过一次勾选：厂商返回认证成功，`wsToken` 长度 352，站点 verify 第 2 页返回验证成功。这个 token 不能拿来重放。随后 ruyijs 参数分析不可用，RuyiDOM 基线没有发出挑战请求，host pair 也不接受父级仍标成 `stopped`、caseId 还是登录案的那次 trace。`solve.py` 还没有可提交的 100 页总和。`result.json` 仍是 `success=false`，`error` 为 `验证服务暂时不可用`，没有改成通过。
