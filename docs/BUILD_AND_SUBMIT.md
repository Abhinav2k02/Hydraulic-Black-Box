# Finish and present the competition entry

## What to say

“Hydraulic Black Box helps a maintenance engineer investigate internal leakage in a press hydraulic pump. It turns measured sensor cycles into a screening result, traceable evidence and a verification plan. Our prototype is validated on real public test-rig measurements; production-factory validation is the next step.”

Avoid saying the data came from an actual named factory, claiming causal proof, or treating the held-out benchmark as demonstrated industrial savings. The app has no real maintenance history or work orders and invents none.

## Team plan from this delivered product

- Developer 1: rerun ingestion and training, verify the partition, inspect the five held-out errors, add a harder chronological or condition-held-out benchmark if time permits.
- Developer 2: verify desktop/mobile UI, uploads and exports; record the final demo.
- Developer 3 (if available): configure Vertex AI and Cloud Run, verify live calls and judge access.
- Developer 4 (if available): obtain feedback from one hydraulic-maintenance engineer, build the deck, document limitations and evidence.

For two people, combine roles 1+3 and 2+4. Prioritize live Google AI verification, deployment, error transparency and a coherent 3-minute demo before adding more equipment types.

## Suggested three-minute video

0:00–0:25 — Show the press hydraulic power-unit use case and the source provenance. Explain that this is real test-rig evidence.

0:25–1:05 — Open held-out cycle 242. Show pressure/flow traces and the leakage prediction. Explain the difference between tree vote share and calibrated confidence.

1:05–1:45 — Generate an actual Gemini brief on the deployed app. Show evidence-linked observations, alternatives and verification steps. Do not splice a mock response into a “live” demonstration.

1:45–2:20 — Reveal the recorded label; open the validation page and a misclassified held-out cycle. This makes the benchmark auditable.

2:20–2:45 — Upload the real example JSON and export the result. Show that inference is functional rather than a static dashboard.

2:45–3:00 — State the next validation step: one factory pilot with aligned sensor semantics, calibration and an independent test set.

## Six-slide deck outline

1. Specific problem and user: investigating internal pump leakage in a press hydraulic power unit.
2. Product workflow: recording → classifier → evidence → Gemini investigation → maintenance verification.
3. Real data and provenance: UCI, attribution, test-rig limitation.
4. Architecture and meaningful Google AI contribution.
5. Measured holdout results and observed errors; separate estimates from measured outcomes.
6. Pilot plan, team, deployed demo URL and source repository.

## Official requirements checked 11 October 2026

Official pages list a working prototype using Google AI/agentic tooling and deployment on Cloud Run or Firebase, an English proposal deck converted to PDF, and a publicly accessible three-minute demonstration video link. Team size is 2–4. Registration/team formation is listed through October 11 and prototype submission through October 18. Confirm the exact cutoff/timezone inside the event portal; these pages alone do not establish the hour.

Select **Manufacturing: Intelligent Operations & Industrial Efficiency**. The public requirements page also contains inconsistent legacy category names under “Category Specification”; confirm the actual dropdown/requirements in the portal or with the organizer rather than changing this manufacturing use case to fit that stray text.

Prepare: deployed app URL with verified judge access, real Google AI integration, PDF pitch deck, video link, repository/source and setup instructions, dataset attribution, team details. Repository requirements and upload field limits should be confirmed inside the portal. The ZIP is not itself a completed competition submission; no submission was made for you.

Sources: https://aibuildercup.com/ and https://aibuildercup.com/themes.html. Organizer contact listed there: support+aibuildercup@hack2skill.com.

## Updated product angle (16 October delivery)

The implemented Energy Ledger adds a retrospective comparison of measured motor power under matching recorded cooler, valve and accumulator settings. Demonstrate the stable-only view, show original cycle IDs, and ask Gemini for an explanation with limitations. Emphasize observable test-rig energy differences; do not claim proven factory savings or globally unique fault-diagnosis technology. Use docs/GOOGLE_CLOUD.md for the now-scripted GCP setup.

## Calculator demo extension

On Energy Ledger, select one matched condition, enter an explicitly illustrative tariff and schedule, then calculate. Change the electricity price and recalculate to demonstrate a real interaction. Explain that the sensitivity range reflects different measured settings, not a guarantee of repair savings. Use Gemini to explain the server-calculated numbers and what must be measured in an actual factory. Export the scenario with its assumptions and source cycle IDs.
