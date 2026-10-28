# Request Chain

Case: `wlzshield-captcha`

Ordered calls. Keep the challenge chain separate from the business chain. The machine contracts are `contracts/request-parameter-lineage.v1.json` and `contracts/workflow-artifacts.v1.json`.

## Notes

- 2026-10-28 `rt_20261028005459_76baddf366`, second browsing context only: init GET 200, then vendor POST `/api/challenge` 200, then site verify POST 200 for page 2. The first context init was 401. Values are not copied here.

<!-- generated:request-chain -->
TEMPLATE-UNFILLED
<!-- /generated:request-chain -->
