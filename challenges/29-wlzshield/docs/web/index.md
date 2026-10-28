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

- Case status: `diagnosing`
- Current stage: `recon`
- Current hypothesis: tab 2 of `rt_20261028005459_76baddf366` accepted the vendor checkbox and site verify for page 2. Nested `next` now treats that integrity-pass manual stop as a finished trace.
- Exit criterion for this stage: one ruyijs parameter-analysis receipt, then `local-hit` or `env-bound`.
- Last `web_case.py next` action: `pair_host_observations` (`turnGate=blocked`)
- Host scope `0e707482e2a60d9fa549c732c4b812ebc60d9ac06beccc7a863140e038814afc` baseline `1dd2ed3c46a9473c9b98bb23ab4dbea0` completed with exit code 0. The collector ran RuyiDOM and wrote a raw summary. `host pair` then returned: browser pair requires a verified completed RuyiTrace artifact run. The trace manifest remains `stopped` with caseId `spiderdemo-register-login`. No second capture. No site acceptance. `_issue_token` is still empty.

## Route And Landing Decisions

- Product hit:
- Active evidence plane:
- Landing primary:

## Blocker

- Observation:
- Classification:

## Next Minimal Action

- Action: `pair_host_observations` stays blocked
- Required fresh evidence: a verified completed RuyiTrace artifact for this challenge. The current manifest is still `stopped`, and its caseId is `spiderdemo-register-login`
- Stop condition: `host pair` accepts that artifact, or the case records why this trace cannot be paired. No site acceptance until then

## Last Experiment

- Pointer: `2026-10-28 host pair`

<!-- generated:index -->
- Case: `wlzshield-captcha`
- Status: `triage`
- Stage: `recon`
<!-- /generated:index -->
