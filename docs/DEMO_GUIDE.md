# Explain and demonstrate the project

## Simple pitch

“Hydraulic Black Box helps a maintenance engineer investigate suspected internal leakage in a hydraulic pump. A coordinator routes questions to diagnosis, energy and maintenance agents. They use real sensor evidence, calculate an illustrative electricity-cost scenario and produce an inspection draft the engineer reviews.”

“Our proposed application is the hydraulic power unit of a metal-forming press. The prototype uses publicly available measurements from a physical hydraulic test rig. It has not been validated on an actual factory press.”

## What makes the interaction useful

You choose evidence and ask a question. The coordinator makes tool calls to the appropriate specialists; they call deterministic tools, return evidence and explain it. You can inspect those exact outputs rather than trusting AI prose alone. Replay makes the historical sensor recordings explorable. User-entered cost assumptions can be changed and recalculated. A maintenance draft becomes an exported review artifact; it is never dispatched automatically.

## A three-minute demonstration after GCP setup

1. **0:00–0:25:** Explain the press power unit use case and clearly disclose test-rig data. Choose cycle 242.
2. **0:25–0:50:** Load local signals. Show flow/power replay; pause and scrub. Explain the model uses all native-rate readings across the complete cycle.
3. **0:50–1:40:** Start a full investigation. Show all four agents when completed, expand their tool evidence and cite a sensor/cycle reference. Provider latency varies; prepare a successful exported run as a disclosed earlier recording if needed for a video.
4. **1:40–2:15:** Enter explicit cost assumptions (for demonstration, you may enter ₹8/kWh, 16 hours/day, 300 days/year and label them as assumptions). Repeat or ask the energy agent. Show the measured W gap and deterministic INR formula. It is illustrative, not guaranteed repair savings.
5. **2:15–2:45:** Ask a diagnosis follow-up or draft an inspection plan. Show selective routing, uncertainty, and the maintenance draft.
6. **2:45–3:00:** Acknowledge review for export and download evidence. Mention Vertex AI + Cloud Run and the held-out model validation screen.

Do not call this live factory monitoring, remaining-useful-life prediction, a confirmed root-cause diagnosis, globally unique technology, or a system that autonomously repairs machinery. Do not present a simulated provider test as a live Gemini demonstration.

## Local run and test: Windows

1. Extract the complete hydraulic-black-box folder from the ZIP.
2. Install Python 3.11/3.12 with Add Python to PATH.
3. Double-click start-windows.bat; keep its window open.
4. Open http://127.0.0.1:8080. Local measurements/model work without credentials.
5. Follow README.md to fill .env and authenticate to Google Cloud; restart and refresh.
6. From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\check_gcp.py --live
.\.venv\Scripts\python.exe scripts\check_gcp.py --agents
```

The suite currently has 39 tests. The last two commands require your actual GCP configuration and incur usage. Successful automated tests do not establish live provider access or production-factory validity.
