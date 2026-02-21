# GCP Container Vulnerability Scanner

A comprehensive application for scanning container images in Google Cloud Platform's Artifact Registry for vulnerabilities and maintaining automated reports in Confluence.

## Features

- **Automated Vulnerability Scanning**: Scans container images using GCP Container Analysis API
- **Artifact Registry Integration**: Scans all images in your Artifact Registry repository
- **Confluence Reporting**: Automatically generates and updates vulnerability reports in Confluence
- **Flexible Deployment**: Runs on Cloud Run with optional Cloud Scheduler for automated scans
- **REST API**: Cloud Run endpoints for manual triggers and status checks
- **Configurable Severity Filtering**: Filter and report based on vulnerability severity levels

## Prerequisites

- Google Cloud Platform account with:
  - Artifact Registry enabled
  - Container Analysis API enabled
  - Cloud Run enabled
  - Cloud Scheduler enabled (optional)
  - Service account with appropriate permissions

- Confluence instance with:
  - API token for automation
  - Dedicated space for reports
  - Appropriate permissions

- Python 3.11+
- Docker (for deployment)

## Quick Start

### 1. Configure GCP Project

```bash
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  artifactregistry.googleapis.com \
  containeranalysis.googleapis.com \
  run.googleapis.com \
  cloudscheduler.googleapis.com \
  cloudbuild.googleapis.com

# Create and configure service account
gcloud iam service-accounts create container-scanner-sa

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:container-scanner-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.reader"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:container-scanner-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/containeranalysis.viewer"
```

### 2. Get Confluence API Token

Log in to your Confluence instance → Profile → Personal access tokens → Create new token

### 3. Configure Locally

```bash
cp .env.example .env
# Edit .env with your GCP project ID and Confluence credentials
nano .env

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Test Locally

```bash
# Scan all images
python -m src.cli scan-all

# Or scan a specific image
python -m src.cli scan-image us-central1-docker.pkg.dev/project/repo/image:latest
```

## Architecture

The application consists of modular components that can be extended:

- **Scanners**: Abstract interface for different vulnerability scanners (GCP Container Analysis, Trivy, etc.)
- **Reporters**: Abstract interface for publishing results (Confluence, Slack, email, etc.)
- **Models**: Standardized vulnerability and scan result data structures
- **Cloud Run Service**: REST API for manual triggers and automation
- **Cloud Scheduler**: Optional automated daily/weekly scans

## Project Structure

```
src/
├── app.py                      # Main orchestrator
├── cli.py                      # Command-line interface
├── server.py                   # Cloud Run Flask app
├── config/settings.py          # Configuration management
├── models/vulnerability.py     # Data models
├── scanners/
│   ├── base.py                 # Base scanner interface
│   └── gcp_scanner.py          # GCP implementation
└── reporters/
    ├── base.py                 # Base reporter interface
    └── confluence_reporter.py  # Confluence implementation
```

## Usage

### CLI Commands

```bash
# Scan all images and publish report
python -m src.cli scan-all

# Scan single image
python -m src.cli scan-image <image_uri>
```

### REST API (Cloud Run)

```bash
# Health check
curl https://container-scanner-xxx.run.app/health

# Trigger scan
curl -X POST https://container-scanner-xxx.run.app/scan \
  -H "Content-Type: application/json" \
  -d '{"publish": true}'
```

## Deployment

### Docker Build

```bash
docker build -t container-scanner:latest .
docker run -e GCP_PROJECT_ID=your-project \
  -e CONFLUENCE_URL=https://your-confluence.atlassian.net \
  -e CONFLUENCE_USERNAME=user@example.com \
  -e CONFLUENCE_API_TOKEN=your-token \
  -e CONFLUENCE_SPACE_KEY=YOUR_SPACE \
  container-scanner:latest python -m src.cli scan-all
```

### Cloud Run

```bash
# Build and deploy
gcloud builds submit --config cloudbuild.yaml

# Or manual deployment
gcloud run deploy container-scanner \
  --image gcr.io/$PROJECT_ID/container-scanner:latest \
  --service-account container-scanner-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --region us-central1 \
  --memory 1Gi \
  --cpu 2 \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID,CONFLUENCE_URL=...,CONFLUENCE_USERNAME=...,CONFLUENCE_API_TOKEN=...,CONFLUENCE_SPACE_KEY=...
```

### Automated Scanning (Cloud Scheduler)

```bash
gcloud scheduler jobs create http container-scanner-daily \
  --schedule="0 2 * * *" \
  --timezone="UTC" \
  --location=us-central1 \
  --uri="https://container-scanner-xxx.run.app/scan" \
  --message-body='{"publish": true}' \
  --http-method=POST \
  --oidc-service-account-email=container-scanner-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --oidc-token-audience="https://container-scanner-xxx.run.app"
```

## Configuration

Environment variables (via `.env` or Cloud Run settings):

| Variable | Required | Example |
|----------|----------|---------|
| `GCP_PROJECT_ID` | Yes | `my-project` |
| `CONFLUENCE_URL` | Yes | `https://company.atlassian.net` |
| `CONFLUENCE_USERNAME` | Yes | `user@company.com` |
| `CONFLUENCE_API_TOKEN` | Yes | `AcAbCdEfGhIjKlMnOpQrStUvWxYz` |
| `CONFLUENCE_SPACE_KEY` | Yes | `INFRA` |
| `ARTIFACT_REGISTRY_LOCATION` | No | `us-central1` (default) |
| `ARTIFACT_REGISTRY_REPOSITORY` | No | `default` |
| `LOG_LEVEL` | No | `INFO` (default) |

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_models.py -v
```

## Development

### Adding a New Scanner

1. Create class extending `BaseScanner` in `src/scanners/`
2. Implement `scan_image()` and `list_images()` methods
3. Export in `src/scanners/__init__.py`
4. Add tests in `tests/test_<scanner_name>.py`

### Adding a New Reporter

1. Create class extending `BaseReporter` in `src/reporters/`
2. Implement `report()` method
3. Export in `src/reporters/__init__.py`
4. Add tests in `tests/test_<reporter_name>.py`

## Confluence Report

The application generates HTML reports showing:

- **Summary**: Total images scanned, vulnerability counts by severity
- **Per-Image Details**: URI, digest, scan timestamp, vulnerability table
- **Automatic Updates**: Report updates with each scan, preserving history

## Troubleshooting

### Permission Denied Errors
```bash
# Verify service account permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter "bindings.members:serviceAccount:container-scanner-sa@*"
```

### No Images Found
- Verify repository name in configuration
- Check Artifact Registry location matches configuration
- Confirm service account can list images:
  ```bash
  gcloud artifacts repositories list --location=us-central1
  ```

### Cloud Run Deployment Fails
- Check Cloud Build logs: `gcloud builds log --stream`
- Verify service account has Cloud Run Admin role
- Increase timeout in `cloudbuild.yaml` if needed

## Monitoring

```bash
# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# View scheduler execution logs
gcloud logging read "resource.type=cloud_scheduler_job" --limit 20
```

## Security

- Use dedicated service account with minimal permissions
- Store Confluence API token in Cloud Secret Manager
- Enable VPC connectors for private registries
- Monitor Cloud Logging for unauthorized access
- Enable encryption at rest for scan results

## Cost Optimization

- Cloud Scheduler: Runs on schedule, not continuously (low cost)
- Cloud Run: Auto-scales with request volume
- Monitor Container Analysis API usage
- Clean up old scan results periodically

## License

MIT

## Support

- Check Troubleshooting section
- Review Cloud Logging for errors
- Open issue in repository
