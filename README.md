# Hydraulic Black Box · Four-Agent Maintenance Workbench

Local product with real hydraulic measurements, a trained leakage model, an interactive four-agent investigation workspace, original-sample replay, matched-condition energy/cost comparisons, and Google Gemini on Vertex AI integration. Includes Cloud Run source deployment tooling and credential placeholders.

**Start here:** no GCP credentials are needed to explore the data, run the model, upload a measurement, or compare energy. Gemini needs your project, model and authentication. No live Google Cloud deployment or provider call has been made for you.

## New in this ZIP: four agents and interactive investigation

The default **Agent workspace** starts with a selected evidence source and no generated AI findings. The application contains four logical Gemini agents: coordinator, diagnosis, energy & cost, and maintenance. Each has separate instructions and an allowlist of tools; all share your configured Gemini model. This is a Google Gen AI SDK implementation, not Google ADK or Agent Engine.

1. Choose a recorded cycle (try **242**) and click **Use recording**, or upload the real sample JSON.
2. Click **Explore measured signals locally**. Inspect the local classifier result, then play, pause, scrub, change sensor, or change replay speed. The display uses real historical samples, never simulated live readings.
3. Fill GCP credentials as below, restart the server and refresh the browser.
4. Click **Run full investigation**. The coordinator delegates to all three specialists, then combines their findings. Tool evidence and agent activity appear when the request completes.
5. Ask follow-ups in chat; the coordinator chooses the relevant specialists. To calculate costs, enable the scenario and explicitly enter tariff/hours/days. No cost assumptions are prefilled in this workspace. Changing evidence or assumptions resets the conversation.
6. Inspect the maintenance draft, optionally add your engineer name/notes, acknowledge review for export, and download JSON. This does not send, approve in an external system, or schedule maintenance. Export the whole investigation to retain its tool evidence.

A recorded energy setting comes from retrospective component annotations. Uploads require you to explicitly select a comparison setting. Neither proves identical factory conditions. Classification uses the complete cycle even when replay is paused partway through it.

Each AI request permits at most 12 model calls and a 70-second budget, with a maximum 20 seconds per call. Slow providers can exhaust it; retry a focused question. The UI shows completed execution events, not streamed agent activity or hidden model reasoning. No chat database is included; refresh loses in-tab history. Missing config or provider failures are explicit, with no fake offline AI response.

Read **docs/AGENTS.md** for architecture, **docs/DEMO_GUIDE.md** for a presentation walkthrough, and **aidlc-docs/** for inception, construction and operations artifacts. AI-DLC means AI-Driven Development Life Cycle; these adapted documents do not claim formal methodology certification.

## 1. Run on Windows

Install Python **3.11 or 3.12**, extract this entire ZIP, and double-click `start-windows.bat`. Open **http://127.0.0.1:8080** after the server starts. The first launch downloads Python dependencies.

Or, in PowerShell from the project folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.server
```

macOS/Linux: run `bash start.sh`. Stop with Ctrl+C.

## 2. Fill the GCP placeholders

Copy `.env.example` to `.env` in the project root and fill:

```dotenv
GOOGLE_CLOUD_PROJECT=YOUR_GCP_PROJECT_ID
GOOGLE_CLOUD_LOCATION=global
GEMINI_MODEL=YOUR_AVAILABLE_GEMINI_MODEL_ID
GOOGLE_APPLICATION_CREDENTIALS=
PORT=8080
```

Choose a Gemini model enabled in your project/location. Authentication options:

- **Local ADC:** leave the credentials field blank; run `gcloud auth application-default login` and `gcloud auth application-default set-quota-project YOUR_GCP_PROJECT_ID`.
- **Local service-account JSON:** save the Google-issued key file as `credentials/service-account.json`, and set `GOOGLE_APPLICATION_CREDENTIALS=credentials/service-account.json` in `.env`. The provided `.json.example` is only a field guide; it is not a usable key.
- **Cloud Run:** use the attached runtime service account. Do not upload a private key or set a local credential path in Cloud Run.

The server automatically loads `.env`; already-set environment variables take precedence. Restart after changes. Enable billing and the Vertex AI API and grant the calling identity Vertex AI User access. Google Cloud CLI login for deployment and ADC login for local application access are separate.

Using the Python interpreter from your virtual environment:

```bash
python scripts/check_gcp.py
python scripts/check_gcp.py --live
python scripts/check_gcp.py --agents
```

The first command checks configuration only. The second makes a real provider request. The third performs a real full four-agent investigation and verifies that all four agents complete; it incurs multiple Vertex requests and requires a function-calling-capable Gemini model. Placeholder values keep the UI's Gemini buttons disabled. Credentials/model access are verified only on a live request; failures are explicit.

## 3. Deploy the full app to GCP

Copy `config/gcp.example.json` to `config/gcp.json` and replace the project ID and model ID. Authenticate the Google Cloud CLI, then run from the project folder:

```bash
gcloud auth login
python scripts/deploy_gcp.py
python scripts/deploy_gcp.py --apply
```

The first command displays the deployment plan without making cloud requests. `--apply` enables APIs, creates/reuses build and runtime service accounts, grants their scoped roles, builds this source and deploys a private Cloud Run service. The deploying identity needs the prerequisite administrative/deployment permissions described in `docs/GOOGLE_CLOUD.md`.

Use Google Cloud Shell if you prefer not to install the CLI locally. Upload/extract this ZIP there, fill `config/gcp.json`, then run the deployment script. Runtime credentials are supplied by Cloud Run automatically.

## What is implemented

| Screen | Working functionality |
|---|---|
| Agent workspace | Interactive chat, coordinator + three specialists, recorded replay, local screening, tool evidence and reviewed draft exports |
| Overview | Search/filter 2,205 real cycles, including held-out errors |
| Investigation | Real sensor traces, leakage classification, descriptive evidence, similar training cases, recorded-label disclosure |
| Energy Ledger | Compare stable real cycles with the same cooler/valve/accumulator labels; measured power, energy, variability, traceable cycle IDs |
| Model validation | Held-out metrics, confusion matrix and inspectable mistakes |
| Data & provenance | Attribution, sampling rates, transformations and original archive checksum |

Upload a full-rate measurement JSON and obtain a prediction. Download a real upload example in the app. Export investigation JSON, sensor CSV or energy comparison JSON. Both investigation and energy screens have implemented Vertex AI brief endpoints.

## New: illustrative leakage cost calculator

Open **Energy Ledger**, select a matched setting, and scroll to **What might leakage cost?** Choose weak or severe leakage, enter your electricity price in INR/kWh, operating hours/day and operating days/year, then click **Calculate scenario**. Prefilled values are editable examples only.

The app computes annual extra energy, illustrative annual cost and average monthly cost from the selected measured power difference. It also shows a P10–P90 sensitivity range across the 48 recorded settings using the same user assumptions. This range is not a confidence interval for the selected setting.

Click **Explain cost estimate with Gemini** after configuration to explain those exact server-calculated figures and assumptions. **Export cost scenario** includes the inputs, calculation, original cycle IDs, source information and limitations. Editing inputs or switching settings clears stale calculations and explanations.

Formula: extra W / 1,000 × hours/day × operating days/year × INR/kWh. This assumes the test-rig gap persists for the entire entered schedule. It excludes maintenance costs, downtime, taxes and demand charges; it is not guaranteed factory savings. The monthly amount is the annual scenario divided by 12, not a month-specific electricity bill.

## Data and scope

Proposed factory application: pump internal-leakage screening for a metal-forming press hydraulic power unit. The underlying measurements come from a **real hydraulic test rig**, not a production press. No synthetic sensor readings are used.

All cycles' derived features/display traces and the evaluated model are bundled. The 73 MiB original archive is separately downloadable and reproducible through `scripts/prepare_data.py`. Display traces retain one original sample each second; model features use every original native-rate sample. No generated machine history or fabricated live sensor feed is included.

The classifier recognizes three leakage labels; it does not certify machine safety or predict remaining lifetime. Its reported 98.85% accuracy applies to the bundled 436-cycle group-held-out benchmark. Energy analysis uses recorded labels and the full dataset retrospectively; it is separate from classifier evaluation. Stable-only comparisons cover 48 matched settings. Their equally weighted mean severe-leakage power difference is approximately 72.56 W. This is a measured test-rig difference, not guaranteed factory savings or proof that leakage alone caused it.

## Reproduce and test

```bash
python scripts/prepare_data.py
python scripts/train.py
python -m unittest discover -s tests -v
```

Original source SHA-256:
`24128aad2ee45eea7e6b63ebbd9992cdf25d0483a2cebefbfc13bc69079af1f2`

See `docs/VERIFICATION.md` for executed checks and limits. API routes and model design are in `docs/ARCHITECTURE.md`. Packaging is reproducible with `python scripts/package_project.py`; it excludes actual credential JSON, `.env`, local GCP config, virtual environments and the original large archive.

## Key files

- `.env.example`: local runtime configuration placeholders.
- `credentials/service-account.json.example`: illustrative credential fields.
- `config/gcp.example.json`: non-secret deployment configuration.
- `scripts/deploy_gcp.py`: Cloud Run source deploy, plan/apply modes.
- `scripts/check_gcp.py`: configuration and live Vertex checks.
- `Dockerfile`: production Gunicorn entrypoint; only runtime assets copied.
- `app/vertex.py`: Google Gen AI SDK integration with Vertex AI.
- `app/energy.py`: measured matched-setting comparisons.
- `docs/GOOGLE_CLOUD.md`: account setup, permissions and verification.
- `docs/BUILD_AND_SUBMIT.md`: presentation and submission planning.

Application source: MIT. Dataset: CC BY 4.0; see `DATA_LICENSE.md`.
