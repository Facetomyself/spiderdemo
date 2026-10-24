# s18 login capture

- runtime: RuyiTrace appVersion 3.3.0, buildId 20260913011646, verification verified. No other capture was running. Previous run `rt_20261010073916_6f589cbd54` stayed stopped; it was not stopped again and not re-registered.
- runId: `rt_20261010083653_880526e2a7`
- status after gate: state `running`, phase `capturing`, gateEnabled true. Browser left on the homepage. No login, no register, no form fill, no `capture_stop`.
- request.json: mode `interactive`, url homepage, profile `dom-observe`, fingerprintMode `baseline`, sensitivity `private-redacted`, gated true, durationSeconds 600, proxy mode `direct`. switches only `MOZ_DOM_HTTP_PACKET_TRACE=1` and `MOZ_DOM_TRACE_ASYNC=1`. No preset, no JSCall, no Opcode, no WebSocket, no env-probe, no fingerprint-observe. Tool default `traceLimit` 500000 was written; it was not set by this slice.
- activeRuns.ruyitrace points at this run after `web_case.py run --plane ruyitrace`.
