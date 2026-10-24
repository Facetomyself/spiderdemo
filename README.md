# spiderdemo

公开的 [spiderdemo](https://www.spiderdemo.cn/) 挑战夹具，用来验证模型和 skill 的 Web 逆向能力。解题脚本、分析笔记和思路可以公开。

题目页面上的脚本、样式和样本图随解题保留，便于离线复现。账号密码、Cookie、原始 trace 和 `evidence/` 不入库。

## 本地凭据

复制 `.env.example` 为 `.env`，填写 `SPIDERDEMO_USERNAME` 和 `SPIDERDEMO_PASSWORD`。登录模块只从项目根 `.env` 读取。

## 不入库

- `.env`，以及 Cookie、session、token 的原值
- `evidence/`、`landing/`
- `node_modules/`、`__pycache__/`、`*.bin`、`*.har`、`*.log`

主仓 `reverse_ENV` 用 gitlink 固定本仓库，不把工作树内容直接提交进主仓。
