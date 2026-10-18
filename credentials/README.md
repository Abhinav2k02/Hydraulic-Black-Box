# Credentials placeholder

`service-account.json.example` is an illustrative placeholder, not a usable key.
For local service-account authentication, download an actual JSON key from your Google Cloud account (if your organization's policy permits it), save the downloaded file as `credentials/service-account.json`, and set its path in `.env`. Do not manually invent or edit private-key fields.

Alternatively, leave GOOGLE_APPLICATION_CREDENTIALS blank and use `gcloud auth application-default login`. Cloud Run uses its attached service account; never upload a key file to the container. Real JSON files in this folder are excluded from Git, Cloud Build source, Docker and the ZIP packaging script.
