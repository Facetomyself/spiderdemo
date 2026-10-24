# Web Case Index

Case: `spiderdemo-register-login`

Read only the files in `web_case.py next` → `docs.read`. Use this index for current status. Do not open `experiments.md` unless a section is named.

## File Map

| File | Read when |
| --- | --- |
| interfaces.md | new endpoint or request boundary |
| request-chain.md | call order, challenge versus business |
| crypto-parameters.md | signer, hash, encryption, encoding |
| risk-analysis.md | challenge, throttle, lease, scale |
| environment-patch.md | RuyiDOM or host patch |
| pure-compute.md | browser-free generator |
| experiments.md | named rejected route only |
| index.md | current status only |

## Current State

- Case status: login client is `modules/login`. Credentials are `SPIDERDEMO_USERNAME` and `SPIDERDEMO_PASSWORD` in the project-root `.env`. The password is not copied into docs.
- Login boundary: `POST /admin_I/api/auth/login` JSON fields `username` and `password`. No captcha field. Accepted login sets `sessionid`. Readback is `GET /admin_I/api/user/stats`.
- `cs_stable_gate` was present on the browser login request and is not minted by the login module.
- `firstDivergence=environment-gap` still describes the earlier RuyiDOM gap. `requestBoundaryAligned=true` and `serverAccepted=true` describe the login wire.
- Login observation run `rt_20261010083653_880526e2a7` is still `state=stopped` with no integrityReceipt. Active browser-fact receipt is the sealed run `rt_20261010022224_c1437434d7`.
- Live `LoginClient.login` for account `mengmaa` returned `登录成功` and set `sessionid`. `user_stats` returned `success=true` (`login_count=2`). No `cs_stable_gate` was sent.
- Open challenges: 31 folders under `challenges/`. Closed and skipped: `control_challenge`, `slide_sum2_challenge` (`开发中`). Solving is protocol-only. Browser collector stays off.

## Route And Landing Decisions

- Product hit: none recorded this slice
- Active evidence plane: `ruyitrace` run `rt_20261010022224_c1437434d7` (3.3.0 verified; three gates and integrityReceipt passed)
- Landing primary: `env-patch` (not locked)
- RuyiDOM: `r56175f00023947f4985b` completed; result `diverged` (`localReproduced`, not `serverAccepted`); `firstDivergence=environment-gap`. Same runner rerun `r656200b927284d80866d` failed before JSON (`local` engine output missing; not `serverAccepted`).

## Blocker

- Login wire is `modules/login`. Live replay for `mengmaa` already succeeded.
- `rt_20261010083653_880526e2a7` is `stopped`, so it is not a completed browser-fact receipt.
- Register module is not written. Crawler test folders are not created.

## Next Minimal Action

- Stamped `compact_replay_done` with `turnGate=blocked`. Stay on the proven login request. Do not start a collector or crawler test folders.
- Later calls use `modules.login.login_from_env`, which reads the project `.env`.
- Do not open another capture for the `stopped` login run. Do not copy cookie values or passwords into notes.

## Last Experiment

- Pointer: `none`

<!-- generated:index -->
- Case: `spiderdemo-register-login`
- Status: `triage`
- Stage: `recon`
<!-- /generated:index -->
