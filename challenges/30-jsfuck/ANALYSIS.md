# JSFUCK

## 解题思路

题目要采集 100 页、每页 10 个数，求和后提交。页面脚本里，动态位移是 AA 混淆，页请求签名是 JSFuck。两段都在本地还原成明文算法，再用 Python 复算，不打开浏览器跑页面。

位移：对 `spiderdemo_caesar_2025_{页码}` 做 MD5，取十六进制前两位转成整数，再 `% 25 + 1`。服务端返回的 `page_data` 是按这个位移做过凯撒的数字。解密就是同一套凯撒、位移取负：字母模 26，数字模 10，其它字符不动。

签名用同一位移加密三份材料：页码字符串、挑战类型 `jsfuck_challenge`，以及 `{页码}_{挑战类型}_{毫秒时间戳}`。前两份进查询参数 `p` 和 `t`，第三份进请求头 `X-Caesar-Token`，时间戳原文进 `ts`。

## 请求链

1. `GET /authentication/api/jsfuck_challenge/init/?challenge_type=jsfuck_challenge`。成功时 `page_data` 就是第 1 页密文，和页面脚本一样，第 1 页不走签名接口。
2. 第 2 到 100 页用 `asyncio` 并发请求 `GET /authentication/api/jsfuck_challenge/page/{页}/?challenge_type=jsfuck_challenge&p=...&t=...&ts=...`，请求头带 `X-Caesar-Token`。并发不超过 4。遇到 429 就指数退避再试。
3. 每页按该页位移解密，得到 10 个整数。
4. 100 页求和后 `POST /authentication/api/jsfuck_challenge/submit/`，JSON 体是 `challenge_type` 和 `answer`。

## 重点解决思路

JSFuck 表达式最终会调用 `Function`。它先反复用 `location`、`escape`、`unescape` 拼字符，所以本地执行时要补上题目页的 `location.href`，否则会在取字符时中断。补环境之后，最后一次构造出的函数体就是签名赋值：按页算位移，再凯撒加密页码、类型和 token。

AA 段同样是构造函数执行。还原后的函数只做一件事：用上面的 MD5 规则写出 `window._shift_value`。凯撒本体在脚本前部是明文，字母和数字的模运算按这段直接移植。

提交接口返回 `is_correct: true`，消息为答案正确，才算通过。
