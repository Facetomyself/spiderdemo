# Web Case Index

Case: `wlzshield-captcha`

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

- Case status: `analyzing`
- Current stage: `proof`
- Current hypothesis: a vendors.min.js closure snapshot can show the AES key binding that object-detail recorded only as an Object tag
- Exit criterion for this stage: closure value shapes include a 16-byte key or `sigBytes`, or the snapshot has no such binding and this recorder stops
- Last `web_case.py next` action: `ruyitrace_capture_start` (`turnGate=run`)
- Closed run: `rt_20261025083508_3ee1b02eff`. Vendor accepted (`wsToken` length 352). Site verify accepted pages 2 and 3. Later replay returned `Token已过期`.
- Closed run: `rt_20261025085441_b91a7ddaa4` completed with no `/api/challenge`.
- Closed run: `rt_20261025090734_84aef8a9bb`, stopped 2026-10-25T09:09:47Z, integrity pass. The checkbox ran in a tab opened after login. HTTP process 32816 recorded init 401, then init 200, vendor `认证成功` with token length 352, and verify page 2 `验证成功`. JSCall detail is process 53396. Those `mV` slots are VM operands, not encrypt arguments. The jsdom AES key does not open that ciphertext (`ERR_OSSL_BAD_DECRYPT`).
- Closed run: `rt_20261025092534_766ba10ee4`, stopped 2026-10-25T09:33:38Z, integrity pass. Vendor `认证成功`, token length 352, verify page 2 `验证成功`, `wlzData` length 41855. vendors.min.js detail is process 46648: `encrypt` arguments are object tags with no properties; `encryptBlock` arg0 is a truncated int array (length 368 or 367). No `words` / `sigBytes` fields, so the AES key was not recovered.

## Route And Landing Decisions

- Product hit:
- Active evidence plane:
- Landing primary:

## Blocker

- Observation:
- Classification:

## Next Minimal Action

- Action: one checkbox click while `rt_20261025112440_81a9fa0874` is capturing
- Required fresh evidence: vendors.min.js closure binding names and value shapes
- Stop condition: a 16-byte key or `sigBytes` binding is recorded, or the snapshot has neither and this recorder stops

## Last Experiment

- Pointer: `none`

<!-- generated:index -->
- Case: `wlzshield-captcha`
- Status: `triage`
- Stage: `recon`
<!-- /generated:index -->
