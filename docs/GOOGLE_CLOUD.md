# Google Cloud integration guide

## Services and identities

Cloud Run hosts the Flask API and dashboard. Cloud Build creates the image from the included Dockerfile. Artifact Registry stores the image. Vertex AI runs Gemini. Application data and model weights are bundled into the image; no Cloud SQL, storage bucket or additional database is needed.

Two service accounts are used:

| Identity | Role | Purpose |
|---|---|---|
| hydraulic-build | roles/run.builder | Build source for Cloud Run |
| hydraulic-runtime | roles/aiplatform.user | Call Gemini from the deployed application |

Use a billing-enabled project. The deploy script enables run, cloudbuild, artifactregistry, aiplatform and iam APIs. It creates missing service accounts and grants the roles above. It requires an administrator/deployer identity with permission to enable APIs, create service accounts, modify project IAM and deploy source. Deployer prerequisites include Cloud Run Source Developer, Service Usage Consumer and Service Account User access on the identities it attaches/uses. An organization administrator may need to provision these; the script cannot bypass an IAM denial.

Official deployment role details: https://docs.cloud.google.com/run/docs/configuring/services/build-service-account

## Local authentication

1. Copy `.env.example` to `.env` and fill project/model/location.
2. Choose ADC or a Google-issued service-account key as described in README.md.
3. Grant the calling identity `roles/aiplatform.user`; enable `aiplatform.googleapis.com` and billing.
4. Run `python scripts/check_gcp.py --live` using the project virtual environment.
5. Start the app; open a recording or energy comparison and request a brief.

An example credential JSON file is provided solely to show the expected fields. Replace it with an actual downloaded credential file; writing placeholder text into the private-key field cannot create credentials. Local key paths are resolved relative to this project root. Cloud Run uses Application Default Credentials from its attached identity, with no key file.

Vertex AI quickstart: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/quickstart

## Deployment

Copy/edit `config/gcp.example.json` to `config/gcp.json`. The config is deliberately separate from local `.env`: no local credential path is sent to GCP. Required non-secret fields are project ID, Cloud Run region, Vertex location, model ID, service name and service-account names. Placeholder values are rejected before any deployment action.

Run `gcloud auth login`, then `python scripts/deploy_gcp.py` to see the plan. Run again with `--apply` when ready to create/update resources. Billing charges may apply to your account. Use a new service name if you do not intend to replace an existing service. Reruns reuse matching service accounts and update that named service.

The script sets only project/location/model in the runtime environment. It deploys 1 CPU, 1 GiB memory, up to two instances, concurrency four, and a 90-second request timeout. The production server is Gunicorn; the local launcher uses Flask on loopback.

By default the deployed app requires Cloud Run IAM access. For local access after deployment:

```bash
gcloud run services proxy hydraulic-black-box --project YOUR_PROJECT_ID --region asia-south1 --port 8081
```

Open the proxy address printed by gcloud. Adjust name/region to match your configuration. This lets you use the application without making the service anonymous. Grant judges appropriate access or deliberately configure public access for submission and verify it from a separate session. This prototype has a per-process concurrency bound for Gemini requests; it has no per-user billing quota.

## End-to-end verification after credentials

1. `/health` responds successfully.
2. Overview loads the 2,205 real recordings.
3. Cycle 242 loads; CSV and JSON exports download.
4. Download/upload the full-rate sample; confirm identical classifier output.
5. Energy Ledger displays 48 matched settings and an exportable comparison.
6. A Gemini investigation and an energy brief both return real text.
7. Inspect Cloud Run logs if a provider request fails.
8. Verify access from the intended reviewer account/session.

## Troubleshooting

- Disabled Gemini button: placeholders are still present, or the local key path is missing. Restart after `.env` edits.
- “Configured” means values exist, not that credentials/model access were already tested.
- Provider failure: check model availability in the selected location, API, IAM, billing and quotas. Server logs carry the diagnostic; responses never fabricate a successful brief.
- IAM failure during deploy: ask the project administrator for the documented role missing from the error. The build and runtime identities have different roles.
- Cold-start/import failure: verify all data/model files were uploaded and pinned requirements installed.
- Access denied opening Cloud Run: use the authenticated proxy or grant invoker access to the intended reviewer.

Actual `.env` and key JSON files are excluded by `.gcloudignore` and `.dockerignore`. The Dockerfile also copies only app/data/models/requirements. No secrets belong in frontend code, Git, deployment configuration JSON or the submitted ZIP.

## Four-agent live verification

Select a Vertex Gemini model available in your project/location with function-calling support. The same configured model powers four logical agents with separate instructions and tool permissions. No separate agent deployment or Google Agent Engine registration is needed.

After the ordinary --live check, run `python scripts/check_gcp.py --agents`. This performs multiple real billed model calls, checks all four agents complete on recorded cycle 242, and fails explicitly on unavailable credentials/model/protocol support. Then run a full investigation in the browser, inspect tool evidence and test a follow-up. The budget is 12 model calls/70 seconds with no SDK retries; provider latency can exhaust it. Cloud Run and Gunicorn retain 90-second timeouts. Two AI requests are allowed at once. Cloud Run stays private by default.
