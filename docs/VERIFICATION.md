# Verification — Four-agent delivery, 16 October 2026

## Executed successfully

- Installed the pinned dependency set into a local virtual environment.
- 39 automated tests passed: API/static responses, held-out group separation, recomputed accuracy, raw example feature/inference equivalence, label exclusion, error filters, upload rejection, CSV export, missing configuration, placeholder rejection, all 48 energy comparisons against independent numerical calculations, provider error propagation, Gemini request construction through the installed SDK with a mocked client, and both briefing routes.
- JavaScript syntax and Python compilation checks passed.
- GCP deployment dry-run generated the expected dedicated identities, private service and runtime variables without cloud requests.
- Unfilled GCP deployment placeholders were rejected before cloud actions.
- Archive integrity, file inventory checksums and credential exclusion were checked during packaging.

The model retains its original benchmark: 1,769 training cycles, 436 held-out cycles, 98.85% accuracy, five held-out errors. Metrics are in models/metrics.json. No model retraining was needed for the GCP integration.

Stable-only energy analysis uses 48 matched cooler/valve/accumulator settings. The equally weighted severe-minus-no-leakage difference is approximately 72.56 W; median is approximately 25.88 W. The earlier 73.56 W calculation included transitioning cycles. The UI now defaults to stable cycles; GET /api/energy?stable=0 includes both. These are measured differences, not validated factory savings.

## Not executed here

- Live Vertex AI request or Google Cloud deployment: intentionally awaiting your credentials/project.
- Docker image build or Windows launcher execution.
- Browser visual/interaction QA: a supported browser-testing capability was unavailable.
- Production factory or independent-machine validation.

Mocked provider tests validate request wiring, response handling and failures; they do not establish live model access or cloud IAM correctness for your account.

## Verify after filling credentials

1. Run locally and inspect all six screens on desktop/mobile.
2. Open cycle 242, export traces/report and upload the supplied real example.
3. Compare the three pump conditions in Energy Ledger and inspect the linked recordings.
4. Run scripts/check_gcp.py --live, then request both types of Gemini brief.
5. Review scripts/deploy_gcp.py's plan and deploy with --apply.
6. Repeat the workflow through the authenticated Cloud Run proxy and verify intended judge access.

## Added calculator verification

Seven additional tests cover independent W-to-kWh-to-INR unit calculations, both real leakage categories, P10–P90 sensitivity values, zero schedule/free tariff, fractional hours, leap-year limits, invalid/nonfinite inputs, malformed requests, unknown settings, and server recomputation before Gemini. Client-provided cost totals cannot override computed values. No live provider calls were made.

Manual acceptance: choose a setting, change tariff/hours/days, calculate, export, change an input and confirm old results clear, recalculate, and generate the configured Gemini explanation. Browser interaction/visual testing remains unexecuted here.

## Four-agent verification

Eighteen new automated tests use the installed Google Gen AI SDK content types and simulated provider replies to exercise: full coordinator + three-specialist function-calling round trip, selective follow-ups, 12-call and 70-second limits, unknown/repeated tools, model-supplied calculation override rejection, ground-truth exclusion, recomputed real-data cost, upload matching/assumption requirements, bad inputs/history, missing config, raw real sample upload, provider errors, concurrency limit, static assets, and rejection of no-tool/incomplete investigations.

These tests simulate provider responses only; no synthetic sensor readings are added. All sensor data used are the original bundled recordings. JavaScript syntax checks cover both frontend modules. Browser visual/interaction QA remains pending. Live function-calling support, actual Gemini response quality/latency, credentials and Cloud Run IAM must be checked in your project using scripts/check_gcp.py --agents and the browser workflow.

A further offline transport-contract test exercises the actual Vertex SDK HTTP request serialization, function-call parsing and function-response submission using an in-process mock HTTP transport. It makes no network requests and uses no genuine credentials. This catches integration errors beyond replacing the SDK client with a mock.
