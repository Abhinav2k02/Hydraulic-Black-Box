# Operations: demo and deployment runbook

1. Install Python 3.11/3.12; extract ZIP; run start-windows.bat or bash start.sh.
2. Open http://127.0.0.1:8080. In Agent workspace choose cycle 242, load local signals, play/scrub replay and change sensor. No AI claims appear before a successful investigation.
3. Configure .env and Google credentials using docs/GOOGLE_CLOUD.md. Restart. Run scripts/check_gcp.py --live and --agents using the virtual environment Python. Both live checks incur provider usage.
4. Click Run full investigation. Check four completed agent cards and inspect the classifier, ledger and draft tools in the activity log. Numeric findings must agree with the tools.
5. Ask a focused diagnosis follow-up and confirm relevant routing. Enable cost inputs, supply your values, and repeat the full investigation; check the calculate_cost evidence against the Energy Ledger calculator.
6. Review the maintenance draft, acknowledge review for export, download JSON. No external dispatch occurs. Export the whole investigation too.
7. Upload the original sample JSON. Classification works without labels. For an energy comparison select a documented matched setting explicitly; this is a user assumption, not evidence the upload came from that setting.
8. Run the full unittest suite. Review docs/VERIFICATION.md for checks run here and unverified account/browser/Windows/Docker behavior.
9. Fill config/gcp.json, review scripts/deploy_gcp.py's plan, and use --apply when ready. Default service remains private; verify access through the Cloud Run authenticated proxy. Configure judge access deliberately using your competition's requirements.

Errors: 400 = invalid input or missing selected setting; 429 = two AI runs already busy; 503 = config placeholders; 502 = provider/function-calling/protocol/budget failure. Inspect server/Cloud Run logs. Select a function-calling-capable model supported in your Vertex project/location. Budget failures may be resolved with a narrower follow-up. Config present does not prove billing, IAM or model access.

The app has no durable database. Browser refresh loses chat context and reviewed-draft state. Download evidence you need to retain. Cloud Run instance memory is ephemeral. Do not expose this demo broadly without appropriate identity, request limits and operational hardening. Existing Cloud Run deployment uses IAM-restricted access by default.

Rollback: redeploy the previous tested Cloud Run revision via the Google Cloud console, or run the previous ZIP locally. No schema migration is necessary. This delivery has not been deployed to your account.
