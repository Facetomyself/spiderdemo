## 解题思路

本题共 30 页，每页 10 个整数，提交全部页的总和。`init` 直接给出第 1 页。第 2 页到第 30 页每次都要先取一张弧度滑块，把拼图块沿给定弧线拖到缺口，站点确认后才返回该页数字。

拼图在本机用 OpenCV 模板匹配定位，不调用外部打码。背景是 840×540，滑块块约 120×100。先把图画到一半分辨率，按 6° 粗搜旋转，再在最佳角附近 ±8° 用原图、alpha 蒙版和 `TM_CCOEFF_NORMED` 精修。匹配左上角要落在接口给出的 `slider_y` 上，块中心到最近弧点的距离不超过 3 像素，相关分数不低于 0.8，弧点下标落在 8 到 91。左上角那块深色轮廓是干扰缺口，不参与计分。

通过后的页用 `collect_pages` 异步采集，并发 4。单页失败就换一张新验证码重试，429 按 1.5 倍退避。30 页数字求和后交给站点提交接口，以站点返回的正确判定为准。

## 请求链

登录走 `SpiderSession`，Cookie 只留在客户端。题目接口都带本页 Referer。

1. `GET /captcha/api/cap7_challenge/init/?challenge_type=cap7_challenge`  
   取 `page_data` 和 `total_pages`。这里只有第 1 页。
2. `GET /captcha/api/cap7_challenge/captcha_image/`  
   读取 `arc_path.points`（100 个图像坐标）、`slider_y`、`image_info` 和两张图。`captcha_id` 一次性使用，不落盘。
3. `POST /captcha/api/cap7_challenge/page/`  
   JSON 字段为 `distance`、`trajectory_encoded`、`rotation_angle`、`page_num`、`challenge_type`、`captcha_id`、`container_width`、`container_height`。轨迹是 `{x,y,t}` 数组的紧凑 JSON，再做标准 Base64。容器尺寸按样式取 400×240。返回 `success` 且 `page_data` 有 10 个数才收下这一页。
4. `POST /captcha/api/cap7_challenge/submit/`  
   正文只有 `challenge_type` 和全部页的整数和 `answer`。

## 重点解决思路

页面把 840×540 用 cover 放进 400×240：缩放 `400/840`，垂直偏移 `(240-540*scale)/2`。滑块可拖距离是 `400-120*scale`。记录点是滑块中心相对容器边框盒的坐标，因此在缩放后的弧点上再加 2 像素边框。设目标弧点下标为 `index`，则 `distance = index/99*maxDrag`，`rotation_angle = index/99*360`。

轨迹门先于距离和角度。点数少于 10 是格式错误，多于 50 是数据异常；间隔几乎均匀会被判成“请正常拖动”；随机或高密度时间戳即使坐标就在弧线上，也会一直是“请重新操作”。站点接受的是固定 17 点：沿弧长从起点均匀取到目标点，相邻间隔用这一组毫秒差：`78, 51, 1, 156, 59, 29, 42, 36, 32, 39, 49, 84, 56, 29, 97, 825`。时间戳用当前毫秒，并等到最后一点之后再提交。姿态没过门就不提交，避免浪费这一张验证码。
