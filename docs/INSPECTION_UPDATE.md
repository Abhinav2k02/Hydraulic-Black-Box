# Inspection update v3

This update adds four capabilities to the existing four-agent application.

1. Verification planner: deterministic hypotheses, missing information and next checks are included in the diagnosis evidence and maintenance draft. Gemini explains them; it does not invent measurements.
2. Manual-based guidance: a curated, paraphrased reference card points to Parker P1/PD service information, printed page 3. It includes a direct link and applicability warning. This is not full-document retrieval, live web search or a verified manual for the dataset pump. No manufacturer numeric limits are applied to the rig.
3. Uncertainty handling: a training-range/neighbor-disagreement review gate. Any of 84 features outside the training minimum/maximum, or any of the three nearest training examples disagreeing with the predicted class, triggers “Pause and verify.” These are fixed screening rules, not calibrated probabilities or a factory OOD guarantee.
4. PDF export: server-recomputed measurements, uncertainty reasons, verification steps, manual citation, optional cost assumptions and user-entered review notes. Works without Gemini. AI prose is not included. Nothing is sent to a maintenance system.

## Real-data evaluation

Run `python scripts/evaluate_review_gate.py` from the project root to regenerate `models/review_gate_metrics.json`.

The existing 436 held-out cycles contain 5 classifier errors. The rules flag 299 cycles, including 4 of those errors and 295 correct predictions. One classifier error remains among 137 unflagged cycles. This gate is conservative and misses an error; all cases still need engineer review. Do not present 4/5 as factory validation. Rules were not tuned on test labels. No classifier retraining or new sensor data was introduced.

## UI behavior

- Choose a recording, then click “View readings (no AI needed)” to see the result, uncertainty, checklist and PDF export.
- “Check pump with AI” runs the existing four-agent workflow. The elapsed-time indicator shows actual request waiting time; it does not invent live agent events. Completed tool activity remains in Technical details.
- AI messages render escaped headings, bold text, code spans and bullets. Raw HTML and arbitrary model links are not enabled.
- Expand checklist steps for the reason, missing evidence and intended decision. Ticking a step means reviewed, not repaired.
- Notes/check marks persist in the current view across follow-up questions. Changing data or cost inputs resets the context; download before doing so. Refreshing also loses these browser-only notes.
- PDF cost estimates use current explicit form inputs. The PDF clearly separates scenario leakage class from the classifier result.

## Agent integration

`app/verification.py` owns the gate and verification evidence. `app/server.py` attaches them to each local result. `app/agents/tools.py` passes them into diagnosis and maintenance tools. `app/agents/prompts.py` instructs Gemini to explain review flags, use short sections/bullets and cite supplied references. The agent runtime and cloud configuration are unchanged.

`app/reporting.py` renders PDFs. Bundled DejaVu fonts make layout independent of fonts on Windows/Cloud Run; licensing is in `app/fonts/LICENSE.txt`. ReportLab is the only new runtime package.

## Checks performed

45 Python tests passed, including real-data upload/report routes, agent tool contracts, invalid input, cost validation and PDF content. JavaScript syntax and formatting/HTML-escaping checks passed. A two-page cost-enabled PDF was rendered and visually reviewed. No live Vertex request, Windows execution, Cloud Run redeployment or interactive browser visual inspection was performed in this build environment. Verify your configured live agents after applying the update.

To run Python checks: `python -m unittest discover -s tests -v`. The PDF text test requires optional `pypdf`; without it that one test is explicitly skipped. To include it: `python -m pip install pypdf`.

If Node is installed, run `node tests/test_frontend.cjs` for safe formatting checks.

## Scope

The source remains the real UCI hydraulic test-rig dataset. The metal-forming factory is a proposed application. Do not claim confirmed root cause, live factory readings, automatic repairs or guaranteed savings. The reference card is a starting point for qualified review, not an equipment-specific service procedure.
