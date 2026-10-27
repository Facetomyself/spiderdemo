# Experiments

Case: `wlzshield-captcha`

Append-only experiment and dated notes. Do not read this file unless `docs/web/index.md` names a section.

<!-- generated:experiments -->
TEMPLATE-UNFILLED
<!-- /generated:experiments -->

## 2026-10-25 capture start

- Action: `ruyitrace_capture_start` after `web_case.py next` on this case.
- Runtime: RuyiTrace 3.3.0, verification verified, BuildID 20260913011646.
- Run: `rt_20261025083508_3ee1b02eff`, mode interactive, profile dom-observe, fingerprintMode baseline, duration 600s.
- Evidence root is under `workspace/spiderdemo/evidence/web/ruyitrace/` because the MCP project is the top-level workspace directory. The parent web-case id remains `spiderdemo-register-login`.
- Page opened: the wlzshield challenge URL. Waiting for one logged-in checkbox pass. No second navigation.
- Stopped at 2026-10-25T08:41:22Z. Integrity receipt passed. State on disk is `stopped` (manual stop), so the nested case still has no `completed` ruyitrace receipt.
- Vendor `POST /api/challenge` returned `status=true`, message class 认证成功, `wsToken` length 352, three times. No vendor cookie. Body keys: timestamp, wlzData (`1:`, length 41579 then 41747), siteKey length 32, type checkbox. Sender frame function name `mV` in `wlzshield.min.js`.
- Before site login, init and verify were HTTP 401 `need_login`. After login, verify pages 2 and 3 were HTTP 200 with `page_data` length 10. Cookie names on the site calls: `cs_stable_gate`, `sessionid`.
- The unused pre-login token, replayed later through the project login client, got HTTP 200 `Token已过期` for pages 4 and 2. Tokens are not reusable after this delay.
- `fingerprintMode=baseline` still produced 认证成功. The accepting environment is the Firefox runtime, not the host machine profile.
- RuyiDOM `fromURL` (Firefox 135, allow-network) received HTTP 301/200 for the challenge document, then the window stayed `about:blank` (`htmlLen` 39, `WlzShield` undefined, no container). No vendor call. Windowless navigation did not commit the page.

## 2026-10-25 popup-tab capture

- Run: `rt_20261025090734_84aef8a9bb`. Preset jscall-detail, profile label still `dom-observe`, fingerprintMode baseline, duration 600s. Runtime 3.3.0 verified.
- Stopped at 2026-10-25T09:09:47Z. Integrity pass. State on disk is `stopped`.
- The checkbox was completed in a tab that opened after login. HTTP for that tab is process 32816: init before login HTTP 401 `need_login`; after login init HTTP 200, `page_data` length 10, `total_pages` 100; vendor POST HTTP 200 `认证成功`, `wsToken` length 352, `wlzData` length 41983, prefix `1:`; verify page 2 HTTP 200 `验证成功，获取第2页数据`.
- JSCall detail file exists only for process 53396. Process 32816 has jscall records and no detail file, and no dict lines containing `wlzshield.min.js`. `mV` detail slots are VM operands (program counters, truncated arrays, return `next`). No detail slot held the `1:` payload or a length-352 token. `AES.encrypt` was not among captured names.
- `script_filter` was empty. Process 53396 `dropped_limit` is in the millions at the 100000 cap. A breakpoint on the name `mV` is the VM dispatcher, not the XHR send.
- Shape-only decrypt of packet `000083` with the jsdom AES key failed. Same framing: one colon, separator index 16, 12-byte header, ciphertext 31472 bytes. PKCS7 error class `ERR_OSSL_BAD_DECRYPT`. jsdom packed length 96235, browser `wlzData` length 41983. Note: `agent-notes/wlzshield-keycmp-20261025.md`.

## 2026-10-25 vendors detail

- Run: `rt_20261025090734` 的下一轮 `rt_20261025092534_766ba10ee4`. Record filter and detail both `vendors.min.js`. Value cap 4096. Stopped 2026-10-25T09:33:38Z. Integrity pass.
- HTTP: init 401 `need_login`, then init 200 `page_data` length 10, vendor POST 200 `认证成功` token length 352, `wlzData` length 41855 prefix `1:`, verify page 2 HTTP 200 `验证成功`.
- Process 46648 is the only detail shard: 7240 detail calls, 226 vendor functions. `encrypt` argc 3 and argc 4: every object argument is a bare `Object` tag, 6 bytes, no properties. `encryptBlock` argc 2: arg0 truncated int array length 368 or 367, arg1 int32, `this` is a bare object. `words` field count 0, `sigBytes` field count 0.
- No key/iv pair. Decrypt not attempted. Note: `agent-notes/wlzshield-vendors-detail-20261025.md`.
- `encryptBlock` arg0 at offset 0 is already dense: 1461 of 1472 bytes nonzero, all four byte lanes used. Adjacent calls differ only in the 8 words at the current offset. This is packed plaintext, not the one-byte-per-word layout seen in jsdom. Note: `agent-notes/wlzshield-block-layout-20261025.md`.
- One local post with `WLZ_REPACK=1` rewrote the sparse gzip (18133 low bytes) into a dense WordArray. Gunzip keys: sessionId, deviceId, fingerprints, behavior, risks, tracks, hash. Key class word16. Vendor HTTP 200 `认证失败`, token length 0. Note: `agent-notes/wlzshield-repack-20261025.md`.
- Replaying packet `000105` to the vendor returned HTTP 200 `认证成功`, token length 268, not all alphanumeric. Immediate site verify for pages 2 and 3 was HTTP 200, `success=false`, error `IP地址不匹配`, `page_data` length 0. The old ciphertext is not a solver. Note: `agent-notes/wlzshield-replay-verify-20261025.md`.
- `new RuyiDOM(html, { url })` ran the page: location is the challenge path, `WlzShield` is an object, `#login-captcha` exists with 0 children. One click sent no `/api/challenge`. The widget is mounted by `showCaptchaForPage`. Note: `agent-notes/wlzshield-ruyidom-html-20261025.md`.
- `showCaptchaForPage(2)` settled. Container child count stayed 0. Open shadow root contains one `STYLE` and no input. Three same-origin iframes have no button. No `/api/challenge`. Note: `agent-notes/wlzshield-ruyidom-mount-20261025.md`.
- The lexical captcha instance has `elTriggerCheckbox` and the layout methods. Calling `initDOM`, `createEmbedLayout`, and `createTriggerWidget` left the shadow as `STYLE,DIV` with no input. Console error: `获取数据失败: SecurityError: Permission to call 'fetch' denied.` Note: `agent-notes/wlzshield-ruyidom-instance-20261025.md`.
- A `beforeParse` XHR shim replaced `window.fetch`. The page called it once and did not raise SecurityError. `elTriggerCheckbox` stayed null, the shadow stayed `STYLE`, and `startVerification()` sent no `/api/challenge`. Note: `agent-notes/wlzshield-ruyidom-click-20261025.md`.
- After the layout calls, `elTriggerCheckbox` was a DIV with `isConnected=false`. Clicking it and the shadow DIV, then calling `startWlz()`, still sent no `/api/challenge`. Note: `agent-notes/wlzshield-ruyidom-div-20261025.md`.
- Appending that DIV into the container shadow made `isConnected=true`. Click plus `startWlz()` still sent no `/api/challenge`. The RuyiDOM UI branch stops here. Note: `agent-notes/wlzshield-ruyidom-attach-20261025.md`.
