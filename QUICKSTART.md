# Quick Start Guide

Get the GCP Container Vulnerability Scanner up and running in minutes.

## Prerequisites

- GCP project with billing enabled
- Confluence instance with admin access
- Python 3.11+ (for local development)
- `gcloud` CLI installed

## Step 1: GCP Setup (5 minutes)

```bash
# Set project ID
export PROJECT_ID="my-gcp-project"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  artifactregistry.googleapis.com \
  containeranalysis.googleapis.com \
  run.googleapis.com \
  cloudscheduler.googleapis.com \
  cloudbuild.googleapis.com

# Create service account
gcloud iam service-accounts create container-scanner-sa \
  --display-name="Container Vulnerability Scanner"

# Grant minimum required roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:container-scanner-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.reader"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:container-scanner-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/containeranalysis.viewer"
```

## Step 2: Confluence Setup (2 minutes)

1. Log into your Confluence instance
2. Navigate to *Profile > Personal Settings > Personal access tokens*
3. Click *Create token*
4. Name it "Container Scanner"
5. Copy the generated token
6. Create a Confluence space (or note the existing space key, e.g., "INFRA")

## Step 3: Local Configuration (2 minutes)

```bash
# Clone and navigate to repository
cd /workspaces/gcp-container-scanner

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

Fill in these values:

```env
GCP_PROJECT_ID=my-gcp-project
CONFLUENCE_URL=https://mycompany.atlassian.net
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=<token-from-step-2>
CONFLUENCE_SPACE_KEY=INFRA
```

## Step 4: Test Locally (3 minutes)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Try a scan
python -m src.cli scan-all

# Or scan specific image
python -m src.cli scan-image us-central1-docker.pkg.dev/$PROJECT_ID/repo/image:latest
```

## Step 5: Deploy to Cloud Run (5 minutes)

### Option A: Using Cloud Build (Recommended)

```bash
# Deploy using Cloud Build configuration
gcloud builds submit --config cloudbuild.yaml
```

### Option B: Manual Deployment

```bash
# Build container
gcloud builds submit --tag gcr.io/$PROJECT_ID/container-scanner:latest

# Deploy to Cloud Run
gcloud run deploy container-scanner \
  --image gcr.io/$PROJECT_ID/container-scanner:latest \
  --service-account container-scanner-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --region us-central1 \
  --memory 1Gi \
  --cpu 2 \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID,\
CONFLUENCE_URL=https://mycompany.atlassian.net,\
CONFLUENCE_USERNAME=your-email@company.com,\
CONFLUENCE_API_TOKEN=$(grep CONFLUENCE_API_TOKEN .env | cut -d= -f2),\
CONFLUENCE_SPACE_KEY=INFRA"
```

The command will output your Cloud Run URL.

## Step 6: Test Cloud Run Deployment

```bash
# Get your Cloud Run URL from the deploy output
export CLOUD_RUN_URL="https://container-scanner-xxx.run.app"

# Health check
curl $CLOUD_RUN_URL/health

# Trigger scan
curl -X POST $CLOUD_RUN_URL/scan \
  -H "Content-Type: application/json" \
  -d '{"publish": true}'
```

Check your Confluence space for the generated report!

## Step 7: Setup Automated Scanning (Optional)

```bash
# Create a daily scheduled scan at 2 AM UTC
gcloud scheduler jobs create http container-scanner-daily \
  --schedule="0 2 * * *" \
  --timezone="UTC" \
  --location=us-central1 \
  --uri="$CLOUD_RUN_URL/scan" \
  --message-body='{"publish": true}' \
  --http-method=POST \
  --oidc-service-account-email=container-scanner-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --oidc-token-audience=$CLOUD_RUN_URL
```

## What's Next?

- **View logs**: `gcloud logging read "resource.type=cloud_run_revision" --limit 50`
- **Customize reports**: Edit [src/reporters/confluence_reporter.py](src/reporters/confluence_reporter.py)
- **Add scanners**: Create new scanner in [src/scanners/](src/scanners/)
- **Monitor**: Set up Cloud Logging alerts for failed scans

## Troubleshooting

### Can't find images in scan
- Verify `ARTIFACT_REGISTRY_REPOSITORY` setting matches your repository name
- Check service account has `artifactregistry.reader` role
- Ensure images exist: `gcloud artifacts repositories list --location=us-central1`

### Confluence report not updating
- Verify `CONFLUENCE_SPACE_KEY` is correct
- Confirm `CONFLUENCE_API_TOKEN` hasn't expired
- Check Cloud Run logs: `gcloud logging read "resource.type=cloud_run_revision"`

### Cloud Run deployment fails
- Check build logs: `gcloud builds log --stream`
- Verify service account email is correct
- Try manual build: `docker build -t test:latest .`

## Performance Tips

- For large registries (100+ images), increase Cloud Run memory to 2Gi
- Adjust `SCAN_BATCH_SIZE` based on your scanning infrastructure
- Use Cloud Scheduler to avoid peak hours
- Monitor Container Analysis API quotas

---

## Common Commands Reference

```bash
# View all images in registry
gcloud artifacts docker images list us-central1-docker.pkg.dev/$PROJECT_ID/containers

# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision" --limit 20 --stream

# View Confluence page
echo "https://mycompany.atlassian.net/wiki/spaces/INFRA/pages/..."

# Check scheduler job
gcloud scheduler jobs describe container-scanner-daily --location=us-central1

# Update Cloud Run environment variables
gcloud run services update container-scanner \
  --update-env-vars KEY=VALUE \
  --region=us-central1
```

For more detailed information, see [README.md](README.md).
