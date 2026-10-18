# Inception: requirements and acceptance

User goal: a reviewable end-to-end factory-maintenance prototype for a Google builder hackathon, with real internet data, interactive UI, Google Cloud integration and credential placeholders.

Scope: hydraulic pump internal leakage investigation for a proposed metal-forming press power unit. Evidence is UCI hydraulic test-rig data, not production-factory data. No synthetic readings, remaining-useful-life claims or autonomous physical actions.

Acceptance:
1. Local startup loads the bundled classifier and original measured data without Google credentials.
2. The user chooses a recording/upload, replays original samples, starts an investigation and can ask follow-ups.
3. Full mode executes one coordinator and three specialists, each grounded in tools; follow-ups choose relevant specialists.
4. Explicit user tariff/schedule produce deterministic illustrative INR scenarios with assumptions.
5. Tool evidence is inspectable and exportable; a maintenance draft requires review acknowledgement for export.
6. Placeholder credentials disable cloud AI; provider failures do not become fake AI results.
7. Model/data benchmarks remain reproducible and distinct from retrospective energy comparisons.
8. Tests, Windows/Linux launchers, Dockerfile, private Cloud Run deployment and operational guidance are packaged.

Requirements authorized by the user's request to implement the four agents and all previously proposed interactive features. Local reversible implementation needs no additional conversational approval. GCP account configuration and live deployment remain with the user as requested.
