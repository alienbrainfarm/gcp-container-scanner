# Deployment Guide

Complete guide for deploying the GCP Container Vulnerability Scanner to production.

## Prerequisites Checklist

- [ ] GCP project created with billing enabled
- [ ] `gcloud` CLI installed and authenticated
- [ ] Confluence instance and API token obtained
- [ ] Service account roles configured
- [ ] Docker knowledge (basic)
- [ ] Container Registry or Artifact Registry configured

## Deployment Options

### 1. Cloud Run (Recommended - Easiest)

Cloud Run is the easiest way to deploy. It auto-scales and you only pay for execution time.

#### Manual Deployment

```bash
# 1. Set variables
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export SERVICE_NAME="container-scanner"

gcloud config set project $PROJECT_ID

# 2. Build container image
gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/$SERVICE_NAME:latest

# 3. Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
  --region $REGION \
  --platform managed \
  --memory 1Gi \
  --cpu 2 \
  --timeout 300 \
  --service-account container-scanner-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars \
    GCP_PROJECT_ID=$PROJECT_ID,\
CONFLUENCE_URL=$(grep CONFLUENCE_URL .env | cut -d= -f2),\
CONFLUENCE_USERNAME=$(grep CONFLUENCE_USERNAME .env | cut -d= -f2),\
CONFLUENCE_API_TOKEN=$(grep CONFLUENCE_API_TOKEN .env | cut -d= -f2),\
CONFLUENCE_SPACE_KEY=$(grep CONFLUENCE_SPACE_KEY .env | cut -d= -f2),\
LOG_LEVEL=INFO \
  --allow-unauthenticated \
  --no-gen2
```

Note: Remove `--allow-unauthenticated` if using Cloud Scheduler with OIDC tokens.

#### Cloud Build Deployment (CI/CD)

1. **Connect GitHub repository:**
   ```bash
   gcloud builds connect --repository-name=gcp-container-scanner
   ```

2. **Create Cloud Build trigger:**
   ```bash
   gcloud builds triggers create github \
     --name="deploy-container-scanner" \
     --owner=your-github-username \
     --repo=gcp-container-scanner \
     --branch-pattern="^main$" \
     --build-config=cloudbuild.yaml
   ```

3. **Push to trigger deployment:**
   ```bash
   git push origin main
   ```

### 2. Cloud Run with VPC Connector (Private Registry)

For private Artifact Registries:

```bash
# 1. Create VPC connector (one time)
gcloud compute networks vpc-access connectors create cloud-run-connector \
  --network default \
  --region $REGION \
  --min-instances 2 \
  --max-instances 10

# 2. Deploy with VPC connector
gcloud run deploy container-scanner \
  --image gcr.io/$PROJECT_ID/container-scanner:latest \
  --vpc-connector cloud-run-connector \
  --region $REGION \
  # ... other options ...
```

### 3. Kubernetes Deployment (Advanced)

For GKE clusters:

```bash
# 1. Create GKE cluster (if needed)
gcloud container clusters create vulnerability-scanner \
  --zone us-central1-a \
  --num-nodes 3

# 2. Get credentials
gcloud container clusters get-credentials vulnerability-scanner \
  --zone us-central1-a

# 3. Deploy using Kubernetes manifests
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s/deployment.yaml
kubectl apply -f deploy/k8s/service.yaml

# 4. Check deployment
kubectl get pods -n scanner
kubectl logs -n scanner -l app=container-scanner
```

## Environment Configuration

### Via Environment Variables (Cloud Run)

```bash
gcloud run services update container-scanner \
  --update-env-vars VAR_NAME=value \
  --region us-central1
```

### Via Secret Manager (Recommended for Secrets)

```bash
# 1. Create secret
echo "your-confluence-token" | gcloud secrets create confluence-api-token --data-file=-

# 2. Grant Cloud Run access
gcloud secrets add-iam-policy-binding confluence-api-token \
  --member="serviceAccount:container-scanner-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# 3. Update Cloud Run to use secret
gcloud run services update container-scanner \
  --update-secrets CONFLUENCE_API_TOKEN=confluence-api-token:latest \
  --region us-central1
```

## Scheduling Scans

### Cloud Scheduler

#### Create daily scan job (2 AM UTC)

```bash
gcloud scheduler jobs create http container-scanner-daily \
  --schedule "0 2 * * *" \
  --timezone "UTC" \
  --location $REGION \
  --http-method POST \
  --uri "https://container-scanner-xxx.run.app/scan" \
  --message-body '{"publish": true}' \
  --oidc-service-account-email container-scanner-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --oidc-token-audience "https://container-scanner-xxx.run.app"
```

#### Create hourly scan job

```bash
gcloud scheduler jobs create http container-scanner-hourly \
  --schedule "0 * * * *" \
  --timezone "UTC" \
  --location $REGION \
  --uri "https://container-scanner-xxx.run.app/scan" \
  --http-method POST \
  --message-body '{"publish": false}' \
  --oidc-service-account-email container-scanner-sa@$PROJECT_ID.iam.gserviceaccount.com
```

#### Pause/Resume schedule

```bash
# Pause
gcloud scheduler jobs pause container-scanner-daily --location=$REGION

# Resume
gcloud scheduler jobs resume container-scanner-daily --location=$REGION
```

## Monitoring

### Cloud Logging

```bash
# View recent Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=container-scanner" \
  --limit 50

# Stream logs in real time
gcloud logging read "resource.type=cloud_run_revision" --stream

# Filter by severity
gcloud logging read "severity>=ERROR AND resource.type=cloud_run_revision" --limit 20

# Export logs to BigQuery
gcloud logging sinks create container-scanner-bq \
  bigquery.googleapis.com/projects/$PROJECT_ID/datasets/logs \
  --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="container-scanner"'
```

### Cloud Monitoring (Metrics)

```bash
# Create uptime check
gcloud monitoring uptime-checks create cloud-run-scanner \
  --display-name "Container Scanner Health" \
  --resource-type "uptime-url" \
  --monitored-resource "https://container-scanner-xxx.run.app/health" \
  --http-check-method GET

# Create alert policy
gcloud alpha monitoring policies create \
  --notification-channels=projects/$PROJECT_ID/notificationChannels/123456 \
  --display-name="Container Scanner Failures" \
  --condition-display-name="Cloud Run failures" \
  --duration 300s \
  --threshold-value 5 \
  --comparison COMPARISON_GT
```

## Scaling & Performance

### Cloud Run Auto-scaling

```bash
gcloud run services update container-scanner \
  --min-instances 1 \
  --max-instances 100 \
  --region $REGION
```

### Container Resources

```bash
# Update memory and CPU
gcloud run services update container-scanner \
  --memory 2Gi \
  --cpu 2 \
  --timeout 600 \
  --region $REGION
```

### Performance Tuning

| Setting | Impact | Recommendation |
|---------|--------|-----------------|
| Memory | Scan speed | 1Gi for <50 images, 2Gi for >100 images |
| CPU | Scan speed | 1 CPU baseline, 2 CPU for large scans |
| Timeout | Max scan duration | 300s for <50 images, 600s for >100 images |
| Max instances | Concurrent requests | 10-100 depending on budget |

## Updating Deployment

### Redeploy Updated Image

```bash
# Build new image
gcloud builds submit --tag gcr.io/$PROJECT_ID/container-scanner:latest

# Deploy latest
gcloud run deploy container-scanner \
  --image gcr.io/$PROJECT_ID/container-scanner:latest \
  --region $REGION
```

### Update Environment Variables

```bash
gcloud run services update container-scanner \
  --update-env-vars NEW_VAR=value,ANOTHER_VAR=value2 \
  --region $REGION
```

### Rollback to Previous Version

```bash
# List revisions
gcloud run revisions list --service=container-scanner --region=$REGION

# Traffic to previous revision
gcloud run services update-traffic container-scanner \
  --to-revisions REVISION_ID=100 \
  --region $REGION
```

## Troubleshooting Deployment

### Service Fails to Start

```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=container-scanner" --limit 50

# Check service details
gcloud run services describe container-scanner --region $REGION

# Check Cloud Build logs
gcloud builds log LATEST_BUILD_ID
```

### Service Times Out

```bash
# Increase timeout
gcloud run services update container-scanner \
  --timeout 600 \
  --region $REGION

# Check for stuck processes
gcloud logging read "resource.type=cloud_run_revision AND textPayload=~'timeout'" \
  --region $REGION
```

### Permission Denied Errors

```bash
# Verify service account permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter "bindings.members:serviceAccount:container-scanner-sa@*"

# Add missing role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:container-scanner-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/required-role"
```

## Cost Estimation

### Typical Monthly Costs

| Service | Free Tier | Cost |
|---------|-----------|------|
| Cloud Run | 2M requests/month | $0.40 per 1M requests |
| Container Analysis | 1000 scans/day | Free |
| Cloud Scheduler | 3 jobs free | $0.10/job after |
| Cloud Logging | 50GB free | $0.50/GB after |

Example: 1 daily scan
- Cloud Run: ~100 requests/month = **Free tier**
- Container Analysis: ~30 scans/month = **Free tier**
- Cloud Scheduler: 1 job = **Free tier**
- Total: **~$0/month** (within free tier)

## Recovery & Backup

### Confluence Report Backup

```bash
# Export Confluence page
curl -X GET \
  -H "Authorization: Bearer $CONFLUENCE_API_TOKEN" \
  "https://your-domain.atlassian.net/wiki/api/v2/pages/PAGE_ID/body/export/view" \
  > backup.html
```

### Service Restore

```bash
# Get previous working revision
gcloud run revisions list --service=container-scanner --region=$REGION

# Deploy specific revision
gcloud run services update-traffic container-scanner \
  --to-revisions REVISION_ID=100 \
  --region $REGION
```

## Post-Deployment Validation

### Test Health Check

```bash
curl https://container-scanner-xxx.run.app/health
```

### Test Full Scan

```bash
curl -X POST https://container-scanner-xxx.run.app/scan \
  -H "Content-Type: application/json" \
  -d '{"publish": true}'
```

### Verify Confluence Report

Visit your Confluence space and confirm the report appears.

### Check Monitoring

```bash
# View metrics
gcloud monitoring read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="container-scanner"' \
  --format json
```

---

For more help, see:
- [README.md](README.md) - Architecture & concepts
- [QUICKSTART.md](QUICKSTART.md) - 5-minute setup
- [GCP Documentation](https://cloud.google.com/run/docs)
