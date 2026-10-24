# s22 live login

`LoginClient` 对 `https://www.spiderdemo.cn/admin_I/api/auth/login` 做了一次真实登录。账号是用户给出的 `mengmaa`。密码、Cookie、token 不写入本笔记。

没有传 `cs_stable_gate`。

结果：

- `success=true`，message `登录成功`
- `sessionid` 已写入客户端 cookie jar
- 随后 `GET /admin_I/api/user/stats` 返回 `success=true`
- stats 公开字段：`total_score=0`，`completed_challenges=0`，`user_rank=1098`，`login_count=2`

请求与已接受的浏览器登录同形：POST、JSON、字段只有 `username` 和 `password`。这次用户名 7 个字符、密码 6 个字符，与 `rt_20261010083653_880526e2a7` 里成功的那次登录长度类一致。
