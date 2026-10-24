# 字体反爬（SVG 和 canvas）

## 解题思路

这一题要采集 100 页、每页 10 个数，再把它们加总提交。接口不返回明文字段，只给一段 SVG。页面脚本会把 SVG 画进 canvas，并在像素上撒噪点；噪点只影响截图，不影响路径本身，所以本地只解析 `svg_content`。

每页固定 40 条 `<path>`。每条路径是一个数字的轮廓，坐标带少量扰动。同一页里，数字内部的水平间距小，两个数之间的间距大，按这个拐点切开，得到 10 个多位数（这一次都是 4 位）。

单个字形直接做 OCR 会把 6/0、2/3 偶发看错。把全部 4000 个字形按归一化墨迹聚类后，自然分成 10 类，类内形状一致。每类抽一小部分，用本机 ddddocr 做多数票命名，再用轮廓规则（孔数、宽高比、上下左右墨迹）交叉确认。十个类刚好对应 0 到 9，且 OCR 纯度是 1 之后，才按页拼数求和。

## 请求链

1. `GET /font_anti/api/font_svg_challenge/init/?challenge_type=font_svg_challenge`  
   打开本题会话。未初始化时，分页接口返回 `need_init`。
2. `GET /font_anti/api/font_svg_challenge/page/{n}/?challenge_type=font_svg_challenge`  
   `n` 从 1 到 `total_pages`（100）。用 `collect_pages` 异步拉取，并发 4。遇到 429 或失败响应就退避重试，不按页顺序串行等待。响应里的有效字段是 `svg_content`。
3. `POST /font_anti/api/font_svg_challenge/submit/`  
   JSON 体是 `challenge_type` 和整数 `answer`。只有 `is_correct=true` 且文案含「答案正确」才算通过。

分页和提交都不需要额外签名头。`anti_automation.js` 里的翻页校验只在浏览器点击时生效，不参与这几个接口。

## 重点解决思路

SVG 路径只用 `M L H V Q Z`。`transform` 一律是 `translate(x, y) scale(0.04, -0.04)`，先缩放再平移，Y 轴被翻正。二次贝塞尔拉直后，按奇偶规则填充，内孔不会被涂实。

聚类用的是裁紧后的 32×48 二值图，不靠某一种系统字体做模板。命名只信类内多数票：孔数至少 3 的类是 8，单孔类在 0/6/9 之间，无孔类再用宽高比和墨迹分布区分 1/4/7/3/5/2。规则和 OCR 不一致且纯度不够时直接中止，不提交。

这一次 4000 条轮廓被分成 10 类，每类 OCR 纯度都是 1，每页都切出 10 个数。提交后站点返回 `is_correct: true`，消息是「答案正确！🎉 恭喜首次通过！ (font_svg_challenge)」。
