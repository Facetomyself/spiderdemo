# Environment Patch

Case: `spiderdemo-register-login`

Current external-host patch only. Append dated rounds to `experiments.md`.

## Current State

- Stage: same document-install runner rerun; structured result missing
- Executor: `RuyiDOM` (`allowNetwork=true`; not Node)
- First divergence: last structured local run remains `r56175f00023947f4985b` — channel `GET /` 200, document stayed `about:blank`; `auth/check` and `auth/captcha` were not sent. Rerun `r656200b927284d80866d` did not emit document or request fields
- Request boundary aligned: no. This rerun did not measure it
- VM morphology: not inspected (black box)

## Patch Queue

| Gap | Evidence | Status |
| --- | --- | --- |
| document stayed `about:blank` after `GET /` 200 | browser `rt_20261010022224_c1437434d7` has the homepage document; local `r56175f00023947f4985b` does not | rerun `r656200b927284d80866d` failed before JSON; location not measured |

<!-- generated:environment-patch -->
TEMPLATE-UNFILLED
<!-- /generated:environment-patch -->

## Notes

- 2026-10-10 `r56175f00023947f4985b` is `localReproduced` only: not browser fact, not `serverAccepted`. No credential submit. No cookie, token, captcha image, or fingerprint value recorded.
- Channel saw only `GET https://www.spiderdemo.cn/` 200. Response length was unavailable. Window stayed `about:blank`; `login` / `showRegister` / `toRegister` were absent and were not called.
- Missing against the homepage browser fact: `GET /admin_I/api/auth/check`, `GET /admin_I/api/auth/captcha`, and the other same-document API calls.
- Stderr on `r56175f00023947f4985b`: `SessionStoreFunctions.sys.mjs` failed to load during `loadURI`. That module is an xpcshell internal, not a page API. It was not stubbed.
- 2026-10-10 existence patch: `fromURL` / `loadURI` observed `GET /` 200 and left the document on `about:blank`. The runner now reads that same channel body and installs it with `new RuyiDOM(html, { url })`. This is document existence, not appearance, descriptor, `toString`, or fingerprint. No credential submit. No cookie, token, or password written.
- 2026-10-10 rerun `r656200b927284d80866d` is not browser fact and not `serverAccepted`. state `failed`, exitCode -1, timedOut false, elapsedMs 51388, `result` null. Location was not emitted. `GET /admin_I/api/auth/check` and `GET /admin_I/api/auth/captcha` were not in stdout, stderr, or stderrTail; that is not proof they were absent. No method, status, body length, or JSON field names were emitted. Stderr warnings came from `protobuf_min.js`, `client_signals_collector.js`, `client_signals_autorun.js`, and `fingerprint_aggregator.js`, then `Exiting due to channel error.` No cookie, token, password, or captcha image recorded.
- 2026-10-10 same-surface install: nested `new RuyiDOM(html, { url })` is gone; the already-read homepage HTML is written with the current document's `document.open` / `document.write` / `document.close`, and this slice did not rerun.
- 2026-10-10 document.write rerun `r7429e6a582b7404ea200` is not browser fact and not `serverAccepted`: state `failed`, exitCode -1, no JSON; location host/path were not emitted, and `auth/check` / `auth/captcha` had no method, status, body length, or JSON field names.
- 2026-10-10 flush rerun `r26a50520ee3b4e1da3fb` is not browser fact and not `serverAccepted`: state `failed`, exitCode -1, channel error, no stdout JSON; `channel-log.jsonl` has other GET 200 paths and does not contain `auth/check` or `auth/captcha`.

