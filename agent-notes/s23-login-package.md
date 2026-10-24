# s23 login package

登录模块从 `protocol/login.py` 挪到 `modules/login`。实现仍是 username/password JSON POST，不铸造 `cs_stable_gate`。

凭据文件：`workspace/spiderdemo/.env`。键名 `SPIDERDEMO_USERNAME`、`SPIDERDEMO_PASSWORD`。账号名 `mengmaa`。密码不写入本笔记。`.env.example` 只有空键。`git check-ignore` 命中 `.gitignore` 的 `workspace/*`，`.env` 不会进仓库。

入口：`LoginClient`，或 `login_from_env()` 读项目根 `.env`。

旧的请求形状单测跟着模块挪到 `modules/login/test_client.py`。没有新建「一个测试一个文件夹」的能力测试目录。

登录观察轮 `rt_20261010083653_880526e2a7` 仍是 `stopped`，没有 integrityReceipt。不为此再开 capture。active ruyitrace 指回已封存的 `rt_20261010022224_c1437434d7`。随后 `web_case.py next` 盖章 `compact_replay_done`，`turnGate=blocked`。不升 collector。
