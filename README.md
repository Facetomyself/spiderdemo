# spiderdemo

[spiderdemo](https://www.spiderdemo.cn/) 的题解。站点是公开的爬虫练习站，一共 33 道题，其中 2 道还在开发，仓库里做了开放的 31 道。

每题一个目录。里面是能再跑的 `solve.py`、当时从页面上拿下来的脚本和样本，以及中文的 `ANALYSIS.md`。题解和思路都公开。人可以顺着目录看某题怎么做完；也可以把这个仓库丢给模型或 skill，看它能不能自己把题做出来。

账号密码、Cookie、原始 trace 不在仓库里。

## 先看哪里

| 想看什么 | 去哪 |
| --- | --- |
| 某题怎么做 | `challenges/<题>/ANALYSIS.md` |
| 再跑一遍 | `challenges/<题>/solve.py` |
| 站点认不认 | 同目录 `result.json`，只留提交接口的公开字段 |
| 登录怎么发 | `modules/login`，过程记录在 `docs/web/` |
| 做题时的随手笔记 | `agent-notes/`。比较碎，正式题解以每题的 `ANALYSIS.md` 为准 |

带下划线的 `_probe.py`、`_fetch_page.py` 这类文件是写题时的探测，不是入口。入口是 `solve.py`。

## 目录

```
modules/login/     登录。只从项目根 .env 读账号密码
modules/runtime.py 登录后的 HTTP 会话，以及多页并发采集
challenges/        一题一个文件夹，名单在 catalog.json
docs/web/          登录边界、请求链、参数和补环境记录
agent-notes/       过程笔记
```

`challenges/CONTRACT.md` 是做题时给自己的约定，和下面「怎么算做完」是同一套。

## 准备

仓库根复制 `.env.example` 为 `.env`，填这两行：

```
SPIDERDEMO_USERNAME=
SPIDERDEMO_PASSWORD=
```

登录是 `POST /admin_I/api/auth/login`，JSON 只有 `username` 和 `password`，没有验证码字段。通过后站点下发名为 `sessionid` 的 Cookie。`modules.login.login_from_env` 读 `.env`，`modules.runtime.SpiderSession` 拿这只 Cookie 去打后面的题。

依赖是做题时实际用到的那些：`httpx`，验证码用的 `ddddocr`、`Pillow`、`onnxruntime`，第 28 题的 WebSocket 用 `websockets`。第 28 题的加解密在 Node 里跑 `challenges/28-jsvmp2/_sdk_codec.js`，本机需要 Node。

## 跑一题

在仓库根执行。`PYTHONPATH` 指到仓库根，这样 `solve.py` 能导入 `modules`。

```powershell
$env:PYTHONPATH = (Get-Location).Path
python challenges\01-header-check\solve.py
```

进程退出码 0，并且该题 `result.json` 里能看到站点接受，才算这次跑通。每题的 `solve.py` 都会把提交结果写回自己的 `result.json`。

多页数字题用 `collect_pages` 并发拉，不按页一张一张等。默认并发在各题脚本里，常见是 4。

## 怎么算做完

站点自己的提交接口认了才算。响应里 `is_correct` 为真，或者文案里有「答案正确」一类的完成说明。HTTP 200、页面能打开、本地算出一个数，都不算。

`result.json` 只留这次判定的公开字段。不要往里面写 Cookie、token、密码，也不要写验证码原图。

做题方式就这几条：

- 把页面上的算法、字体、验证码在本地还原出来，或者补环境后自己算出请求。不用浏览器把题点完。Playwright、Selenium、Puppeteer 以及「打开页面让脚本自己跑完」都不算这套题解。
- 验证码只用本机库。滑块用 `ddddocr` 的 `slide_match` / `slide_comparison`。不把图片发给打码平台。
- 需要看真实执行时，可以对本地脚本下断点，或做一次带登录态的 trace。trace 用来搞清请求，不是交卷方式。

`ANALYSIS.md` 固定三节：`解题思路`、`请求链`、`重点解决思路`。分页、签名、字体、验证码、加密各自怎么落地，写在这三节里。

## 题目

名单以 `challenges/catalog.json` 为准。下面是开放的 31 道。分值是站点上的分。

| 目录 | 题目 | 分 | 站点上的说法 |
| --- | --- | --- | --- |
| `01-header-check` | 请求头检测 | 10 | 头顺序，控制台发包也会被看 |
| `02-ob-encrypt` | 加解密 | 20 | obfuscator 混淆 |
| `03-protobuf` | protobuf 加密 | 20 | 魔改 MD5，魔改 protobuf |
| `04-wasm` | WASM | 10 | 反调试加基本 WASM |
| `05-ob1-wall` | 柳暗花明又一墙 | 10 | 变种 obfuscator |
| `06-jsvmp` | jsvmp | 30 | 自定义 protobuf，还有 CSS |
| `07-css-offset` | CSS 偏移 | 20 | 把偏移过的样式还原回来 |
| `08-font` | 字体反爬 | 10 | 字体反爬 |
| `09-font-sprites` | 字体反爬（雪碧图） | 20 | 雪碧图 |
| `10-font-svg` | 字体反爬（SVG 和 canvas） | 20 | SVG 和 canvas |
| `11-cap1` | 第一代验证码 | 10 | 字符验证码 |
| `12-cap2-gif` | GIF 动态验证码 | 12 | GIF |
| `13-cap3-math` | 计算题验证码 | 12 | 算式 |
| `14-cap4` | 第二代验证码 | 10 | 第二代 |
| `15-cap5-slider` | 第二代验证码（随机滑块） | 15 | 随机滑块 |
| `16-slide-scratch` | 滑动刮刮乐 | 20 | 刮刮乐 |
| `17-slide-puzzle` | 滑动拼图 | 20 | 拼图 |
| `18-cap6-dual` | 双滑块验证码 | 15 | 两个滑块 |
| `19-slide-cylinder` | 圆柱验证码 | 20 | 圆柱 |
| `20-cap8-click` | 点选验证码 | 20 | 点选 |
| `21-hash` | 摘要算法 | 10 | MD5、SHA、HMAC |
| `22-symmetry` | 对称加密 | 10 | AES、DES |
| `23-asymmetric` | 非对称加密 | 10 | RSA 等，页面脚本里带密钥 |
| `24-cap7-arc` | 弧度验证码 | 25 | 弧度 |
| `25-panel-console` | 控制台检测 | 15 | 答案在控制台 |
| `26-click-stitch` | 点击拼图验证码 | 15 | 点击拼图 |
| `27-press-rotate` | 按压旋转验证码 | 26 | 按压旋转 |
| `28-jsvmp2` | Jsvmp2 | 35 | JSVMP 加 WebSocket。站点题号因两题未开放，页面上也可能标成 T30 |
| `29-wlzshield` | 无感验证码 | 25 | 无感 |
| `30-jsfuck` | JSFUCK | 15 | JSFuck，AA 混淆 |
| `31-zerowidth` | ZeroWidth | 20 | 零宽字符，100 页 |

另外两题站点按钮还是「开发中」，没有页面入口，仓库里没有对应目录：`control_challenge`（控制流加强）、`slide_sum2_challenge`（计算题验证码 plus）。

页面上的 JS、CSS、WASM、字体和样本图留在各题目录里，是为了离线还能把 `solve.py` 和 `ANALYSIS.md` 对上。这些文件是站点当时下发的题目材料。

## 不进仓库

`.gitignore` 挡掉这些：

- `.env`。示例只有 `.env.example`，值是空的
- `evidence/`、`landing/`。trace、抓包和登录态都在这里
- `node_modules/`、`__pycache__/`
- `*.bin`、`*.har`、`*.log`、`*.pcap`

第 29 题本地装过 jsdom，`node_modules` 不提交。需要时在 `challenges/29-wlzshield` 里按 `package.json` 自己装。

## 和主仓的关系

这个目录在 `reverse_ENV` 里是 `workspace/spiderdemo`，主仓用 gitlink 指到本仓库的某一次提交，不把题解文件直接提交进主仓。改题解先在本仓库提交并推送，再挪主仓的 gitlink。
