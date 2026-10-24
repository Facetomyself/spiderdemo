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

静态还原签名后，用登录会话核对过两道门：坏签名是「签名验证失败，请刷新重试」；好签名且 token 为空是「缺少验证token」；好签名且 token 非空是「验证服务暂时不可用」。

控件在 jsdom 补环境里可以构造，并发起挑战请求。`https://captcha.wangluozhe.com/api/challenge` 与 `/api/verify` 当前都是网关 502。站点核销不在本地验签，而是转给这台主机，所以任意非空 token 都得到同一句不可用。没有 `wsToken` 就没有第 2–100 页，提交总和不会被判对。验证码主机恢复后，同一条 verify/submit 链才能收口。
