# Architecture and data contract

## Runtime

- Python Flask serves the HTML/CSS/JavaScript UI and JSON API from one origin.
- NumPy loads a compressed measured-data bundle. scikit-learn loads the bundled ExtraTrees model.
- Feature vectors have 84 values: 14 physical sensors × mean, standard deviation (population), minimum, maximum, range, and end-minus-start.
- Inference accepts no component labels. Temperature, flow, pressure, power and vibration are observed inputs.
- Similar cases use root mean squared standardized feature distance to training recordings. The training-set standard deviations define scaling. Self matches are excluded.
- Evidence deviations compare each channel’s mean against no-leakage training cycles. This is descriptive evidence, not a causal attribution.
- Gemini receives the prediction, uncalibrated vote shares, evidence, similar training cases and scope constraints. It does not receive the selected cycle’s ground-truth labels.
- Gemini output is rendered as plain text rather than executable HTML. The UI does not execute model output.
- One server process with four request threads fits the demo. No durable storage or user authentication is included; use Cloud Run IAM for restricted access.

## Endpoints

| Method / path | Result |
|---|---|
| GET `/health` | Model readiness |
| GET `/api/meta` | Sensor dictionary, provenance, metrics and AI configuration status |
| GET `/api/cycles` | Paginated recordings with `page`, `class`, `split`, `q`, `errors` filters |
| GET `/api/cycles/242` | Prediction, signals, evidence and separately labelled annotations |
| GET `/api/cycles/242/csv` | 60 original samples at one-second intervals for all channels |
| GET `/api/sample` | Real full-rate example cycle JSON |
| POST `/api/analyze` | Recompute features and classify uploaded sensor arrays |
| POST `/api/brief/242` | Gemini investigation, if configured |

## Upload schema

A JSON object containing `sensors`, with keys PS1–PS6, EPS1, FS1–FS2, TS1–TS4 and VS1. PS/EPS arrays contain 6000 numeric values; FS arrays 600; TS/VS arrays 60. Values must be finite. The file must fit in 2 MiB. Download `data/sample-cycle.json` for an actual complete example. Metadata may accompany the arrays but labels are never used for inference.

Only upload synchronized 60-second measurements from the same sensor semantics and units. A structurally valid upload is not proof of compatibility with an unfamiliar factory. The app cannot automatically detect all domain shifts or sensor calibration errors.

## Validation design

Group definition: every consecutive run of identical four-component settings receives one group ID. The stable flag is excluded from grouping. GroupShuffleSplit uses a 25% group holdout and seed 42; because group sizes vary, the cycle proportion differs from 25%. Exactly 1,769 cycles train the model and 436 test it. The final model is not refit on test data.

Classifier: 180 ExtraTrees, balanced class weighting, minimum leaf size 2, random seed 42, two CPU workers. All parameters are specified before test scoring. No hyperparameter search was performed against the test set.

Limitations: repeated settings and temporally nearby groups can remain correlated across the split. Group holdout is stronger than randomly splitting adjacent cycles but does not establish new-machine, new-site or future-time performance. A production pilot requires a frozen chronological or machine-held-out test, instrument validation and a maintenance engineer’s assessment. Tree vote shares are uncalibrated; there is no claimed 99% certainty of failure.

## File map

- `scripts/prepare_data.py`: reproducible source download and processing.
- `scripts/train.py`: split, training, metric computation, serialization.
- `app/server.py`: API, validation, model inference, optional Google AI.
- `app/static/`: responsive UI; no remote frontend dependencies.
- `data/`: real derived records, metadata, original source documentation and a raw upload example.
- `models/`: trained model, evaluation IDs and computed metrics.
- `tests/`: meaningful data, model and API verification.
- `Dockerfile`: Cloud Run-compatible container entrypoint.

## Version 2: Energy Ledger and GCP configuration

`app/config.py` automatically reads local `.env` without overriding process environment. It validates placeholder values and credential-path existence; cloud authentication is resolved by Google's SDK. `app/vertex.py` implements real Vertex calls with a 45-second timeout, bounded output and plain-text rendering. Both brief routes propagate explicit failures.

GET `/api/energy` compares stable cycles by the tuple (cooler, valve, accumulator), using recorded pump labels to form three groups. `stable=0` also includes transitioning recordings. For each group it reports the count, original cycle IDs, mean EPS1 power, standard deviation of cycle means, measured energy per 60-second cycle, and extra energy relative to no leakage. This descriptive full-dataset analysis does not enter prediction features or held-out metrics. It does not control for every possible confounder.

POST `/api/energy/brief/<cooler>-<valve>-<accumulator>` asks Vertex AI to explain a valid stable-only comparison. This retrospective brief explicitly contains recorded settings; the original classifier briefing still excludes the selected cycle's ground-truth annotations.

Deploy with `scripts/deploy_gcp.py` using `config/gcp.json`. The default is a no-network plan; `--apply` performs cloud changes. Runtime identity is distinct from build identity, and the deployment remains IAM-restricted by default.

## Cost scenario API

POST `/api/energy/cost/<setting>` accepts numeric `tariff_inr_kwh` (0–10000), `hours_per_day` (0–24), integer `days_per_year` (0–366) and `leakage` (1 or 2). It derives the power difference from recorded data on the server. The response contains assumptions, annual hours, measured power gap, annual kWh, annual INR, average monthly INR and cross-setting P10–P90 sensitivity. Booleans, strings, missing values and nonfinite values are rejected.

POST `/api/energy/brief/<setting>` optionally accepts the same input object. It recomputes the scenario on the server and sends the computed values and their limits to Vertex AI. No-body requests retain the original measured-energy explanation. The UI discards stale asynchronous results after any input/setting change, clears the previous brief and disables scenario export until recalculated.

The sensitivity range is a distribution across recorded setting-level power differences, not an uncertainty interval or a causal guarantee. No statistical noise, synthetic sensor readings or fake tariffs are introduced into the measurement dataset.

## Four-agent extension

- app/agents/prompts.py: four role prompts and grounding policy.
- app/agents/runtime.py: bounded Gemini function-call loop and coordinator delegation.
- app/agents/tools.py: server-owned diagnosis, retrospective ledger, deterministic cost and maintenance draft tools.
- app/static/agents.js: source selection, chat/history, recorded-sample replay, execution evidence and draft review/export.
- aidlc-docs/: adapted inception, construction and operations artifacts; see docs/AGENTS.md for precise boundaries.
- GET /api/agents: roster, configuration availability and budgets.
- POST /api/investigate: question (1–2000 characters), cycle_id or measurement, optional setting_id for uploads, optional cost_inputs, full_investigation boolean, at most eight user/assistant history items. Server recomputes all evidence. Returns coordinator answer, specialist results, execution trace and any structured draft. No durable session storage.

The original classifier brief excludes current ground truth. The new energy agent intentionally uses recorded component setting annotations for retrospective matching, disclosed independently of classifier findings. It compares all recorded leakage groups; it does not expose the selected cycle's actual leakage label as diagnosis evidence.
