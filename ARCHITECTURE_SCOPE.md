# Architecture Scope: Deployment Pipelines & Billing Prediction

## 1. Automated Deployment Pipelines

### Trigger
After a PR is **merged** (the current pipeline creates the PR; deployment triggers when someone merges it).

```
GitHub push event (merge) → webhook → ingestion-service → Celery → deploy
```

### Webhook Addition
Extend `ingestion-service/index.js` to handle `push` events on the default branch:

| Event | Action | Behavior |
|---|---|---|
| `push` | merge to `main` | Queue deployment task |
| `push` | merge to `main` with `[skip deploy]` in message | Skip |

Only fire on the **default branch** (usually `main`). Ignore pushes to feature branches.

### New Django Model: `Deployment`
```
Deployment:
  id                  AutoField
  organization_name   CharField (tenant)
  repository_name     CharField
  commit_sha          CharField(40)
  branch              CharField (default "main")
  status              CharField  (QUEUED | BUILDING | DEPLOYING | DEPLOYED | ROLLED_BACK | FAILED)
  strategy            CharField  (docker | kubernetes | serverless | custom_script)
  target_url          URLField   (e.g. https://staging.example.com or pod IP)
  logs                TextField
  triggered_by        CharField  (auto | manual)
  created_at          DateTime
  deployed_at         DateTime  null
```

### Celery Task: `execute_deployment`
New task in `django-dashboard/dashboard/tasks.py`:

```
execute_deployment(project_id, installation_id, repository_full_name, commit_sha, branch, strategy)
```

Flow:
1. Fetch installation access token
2. Clone repo at the specific commit (via GitHub API archive or git clone)
3. Build Docker image (if strategy=docker) or apply kubectl (if strategy=kubernetes)
4. Run deployment
5. Update `Deployment.status`
6. On failure → optionally rollback (revert to previous image/commit)
7. POST status back to GitHub commit status (`deployment` state)

### New Service: `deployment-agent` (optional)
For complex deployments (Kubernetes, blue-green, canary), a separate container:

```
deployment-agent:
  build: ./deployment-agent
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
    - ~/.kube/config:/app/kube-config:ro  # optional K8s
  depends_on: [redis-broker]
```

Keeps the main Django container unburdened. Listens on a separate Celery queue (`deployments`).

### Caddy Route
```
reverse_proxy /api/v1/deployments/* django-dashboard:8000
```

### Deployment Strategies (configurable per repo)

| Strategy | Mechanism | Use Case |
|---|---|---|
| `docker` | Build image → push to registry → restart container | Single-server / Docker Compose |
| `kubernetes` | `kubectl set image` + rollout status | K8s cluster |
| `serverless` | ZIP + upload to AWS Lambda / GCF | Functions |
| `custom_script` | SSH + run deploy.sh | Legacy / bespoke |

### Rollback
If deployment fails health checks:
- Docker: restart previous container/tag
- K8s: `kubectl rollout undo`
- Serverless: alias to previous version
- Custom: the script must handle its own rollback

### Dashboard UI
New tab in the Django dashboard:
- Table: Deployments list (status, time, repo, commit)
- Detail view: logs per deployment step
- Manual trigger button: "Deploy Branch"

---

## 2. Cloud Billing Price Prediction

### Data Collection

Two modes:

#### A. Pull-based (cloud provider API polling)
New service `billing-collector` that runs on a schedule:

```
billing-collector:
  build: ./billing-collector
  environment:
    - AWS_ACCESS_KEY_ID=
    - AWS_SECRET_ACCESS_KEY=
    - GCP_SERVICE_ACCOUNT_JSON=/app/gcp-creds.json
  depends_on: [postgres-db]
```

Polling schedule (via Celery Beat or cron inside the container):

| Provider | API | Frequency |
|---|---|---|
| AWS | Cost Explorer `get_cost_and_usage` | Daily |
| GCP | Cloud Billing API | Daily |
| Azure | Cost Management API | Daily |

Stores raw cost data in PostgreSQL:

```
BillingRecord:
  id                  AutoField
  organization_name   CharField
  provider            CharField  (aws | gcp | azure)
  service             CharField  (EC2, S3, Compute Engine, etc.)
  region              CharField
  cost                DecimalField
  usage_quantity      DecimalField  null
  usage_unit          CharField  null
  recorded_at         DateField
  created_at          DateTime
```

#### B. Push-based (webhook from cloud provider)
AWS can send cost reports via SNS → SQS → webhook. GCP can publish to Pub/Sub. This could be a future enhancement.

### Prediction Model

The `billing-collector` or another Celery task runs a forecast monthly:

```
predict_billing_spend(organization_name, months_ahead=3)
```

**Approach A — Lightweight (statistical):**
Use `statsmodels` (SARIMA) or Facebook Prophet:
- Takes 12+ months of historical `BillingRecord` data
- Forecasts per-service spend for next 1-3 months
- No external API calls, runs entirely in the collector container
- Accuracy: ~70-80% with sufficient history

**Approach B — AI-powered (OpenRouter):**
Feed historical data as a prompt to the same OpenRouter model:
```
"Given this 6-month cost history: [JSON], predict next month's spend and flag anomalies."
```
- Easier to implement (no ML pipeline)
- Depends on model quality
- Higher token cost

**Recommendation: Hybrid** — start with Approach A (statistical, runs locally, no API cost), then overlay Approach B for anomaly explanations.

### New Django Model: `BillingForecast`
```
BillingForecast:
  id                  AutoField
  organization_name   CharField
  provider            CharField
  forecast_month      DateField    (the month being predicted)
  predicted_cost      DecimalField
  confidence_lower    DecimalField
  confidence_upper    DecimalField
  actual_cost         DecimalField  null (filled after month ends)
  model_used          CharField     (prophet | openrouter)
  created_at          DateTime
```

### Anomaly Detection

On each new `BillingRecord` ingestion, check:
1. Is today's cost > 2x standard deviation of last 30 days for this service?
2. Is this service's weekly spend > forecast upper bound?

If anomaly detected:
- Create `BillingAlert`
- Send email notification (reuse `send_instant_usage_invoice_email` pattern)
- Optionally POST to Slack webhook

### New Django Model: `BillingAlert`
```
BillingAlert:
  id                  AutoField
  organization_name   CharField
  provider            CharField
  service             CharField
  severity            CharField (warning | critical)
  message             TextField
  current_cost        DecimalField
  threshold_cost      DecimalField
  is_acknowledged     BooleanField (default False)
  created_at          DateTime
```

### Dashboard UI

New tab: "Cost Intelligence"

| Section | Content |
|---|---|
| Current month spend | Total + per-service breakdown (bar chart) |
| Forecast vs Actual | Line chart: actual (last 12 months) + forecast (next 3) |
| Anomalies | Table of active `BillingAlert` entries |
| Top services | Sorted by cost (pie chart) |

Charts can use Chart.js (already compatible with the existing TypeScript dashboard pattern at `dashboard/static/ts/dashboard.ts`).

### Caddy Route
```
reverse_proxy /api/v1/billing/predictions/* django-dashboard:8000
reverse_proxy /api/v1/billing/alerts/* django-dashboard:8000
```

### Cron / Celery Beat Schedule

| Task | Interval |
|---|---|
| `collect_billing_data` | Daily at 02:00 |
| `predict_billing_spend` | 1st of every month |
| `check_billing_anomalies` | Hourly |
| `cleanup_old_records` | Monthly (retain 24 months) |

---

## 3. Integration With Existing System

### New Services Summary

| Container | Purpose | Dependencies |
|---|---|---|
| `deployment-agent` (optional) | Run Docker/K8s deployments | `redis-broker`, Docker socket |
| `billing-collector` | Poll cloud APIs for cost data | `postgres-db` |

### New Celery Tasks

| Task | Queue | From |
|---|---|---|
| `execute_deployment` | `celery` (default) | Webhook push event |
| `collect_billing_data` | `celery` | Celery Beat |
| `predict_billing_spend` | `celery` | Celery Beat |
| `check_billing_anomalies` | `celery` | Celery Beat |

### New Django Models (all tenant-isolated via `organization_name`)

1. `Deployment`
2. `BillingRecord`
3. `BillingForecast`
4. `BillingAlert`

All use `TenantManager` and include `organization_name` for multi-tenant isolation, same pattern as `RunAuditLog`.

### Changes to Existing Files

| File | Change |
|---|---|
| `docker-compose.yml` | Add `billing-collector` service, optional `deployment-agent` |
| `Caddyfile` | Add routes for `/api/v1/deployments/*`, `/api/v1/billing/*` |
| `ingestion-service/index.js` | Handle `push` event |
| `django-dashboard/dashboard/tasks.py` | Add `execute_deployment` task |
| `django-dashboard/dashboard/views.py` | Add deployment + billing API views |
| `django-dashboard/dashboard/models.py` | Add 4 new models |
| `django-dashboard/dashboard/admin.py` | Register new models |
| `django-dashboard/dashboard/static/ts/dashboard.ts` | Add Cost Intelligence tab rendering |
| `django-dashboard/config/settings.py` | Add Celery Beat schedule |

---

## 4. Effort Estimate

| Feature | Containers | New Models | New Tasks | Estimated Time |
|---|---|---|---|---|
| Automated Deployments | 1 (deployment-agent) | 1 | 1 | 3-4 days |
| Billing Prediction | 1 (billing-collector) | 3 | 3 | 4-5 days |
| Dashboard UIs | 0 (existing frontend) | — | — | 1-2 days per feature |
| **Total** | **2 new** | **4 new** | **4 new** | **~8-11 days** |

### Dependencies
- Billing prediction requires cloud provider API keys (AWS IAM, GCP service account)
- Deployments require either Docker registry access (for `docker` strategy) or kubeconfig (for `kubernetes` strategy)
- Both features require Celery Beat to be running (add `celery-beat` container or integrate into existing worker with `--beat` flag)
