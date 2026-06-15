# Production Execution & Verification Manual

Follow this roadmap sequentially. Mark each step as **PASSED** only after running the verification command and receiving the exact output described.

---

## Phase 1: Storage & State Pre-requisites

### Step 1.1: Initialize Host Storage and Private Networking

```bash
# Create directory structures
mkdir -p ~/ai-bug-fixer/{certs,infra,ingestion-service,core-brain,django-dashboard,sandbox-env}
mkdir -p /tmp/db_dumps

# Set up the isolated Docker network bridge manually to verify engine linking
docker network create ai-devops-network
```

**Verification Command:**
```bash
docker network ls | grep ai-devops-network
```

**Expected Output:**
```
ai-devops-network    bridge    local
```

**Status:** [ ] WAITING / [✅] PASSED

---

### Step 1.2: Spin Up the Persistent Database Layer

Save your `docker-compose.yml` to `~/ai-bug-fixer/docker-compose.yml`. Launch only the data services first to run initial structural schema migrations.

```bash
cd ~/ai-bug-fixer
docker compose up -d postgres-db redis-broker
```

**Verification Command:**
```bash
docker compose ps
```

**Expected Output:** Both `postgres-db` and `redis-broker` display a status of `Up`.

**Status:** [ ] WAITING / [✅] PASSED

---

### Step 1.3: Apply Database Migrations and Row-Level Security (RLS)

```bash
# Apply Django structural migrations
docker compose run --rm django-dashboard python manage.py migrate

# Verify RLS activation on the audit log table
docker exec -it $(docker ps -f name=postgres -q) psql -U devops_admin -d ai_devops_db -c "SELECT relname, relrowsecurity FROM pg_class WHERE relname = 'dashboard_runauditlog';"
```

**Expected Output:**
```
       relname           | relrowsecurity
-------------------------+----------------
 dashboard_runauditlog   | t
(1 row)
```

**Status:** [ ] WAITING / [✅] PASSED

---

## Phase 2: AI & External API Credentials Provisioning

### Step 2.1: Configure OpenRouter Enterprise ZDR Credentials

1. Navigate to your [OpenRouter Dashboard](https://openrouter.ai/keys)
2. Generate a new API Key. Name it `PATCHBOT_PROD_KEY`
3. Go to **Privacy Settings** and globally toggle **Data Collection** to **Deny**

Create `~/ai-bug-fixer/core-brain/.env`:

```env
HOST=0.0.0.0
PORT=8010
LITELLM_MODEL=openrouter/qwen/qwen-2.5-coder-32b-instruct
OPENROUTER_API_KEY=sk-or-v1-your-actual-computed-openrouter-key-signature
```

**Verification Command:**
```bash
curl -X POST "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer $(grep OPENROUTER_API_KEY ~/ai-bug-fixer/core-brain/.env | cut -d '=' -f2)" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen/qwen-2.5-coder-32b-instruct", "messages": [{"role": "user", "content": "ping"}], "data_collection": "deny"}'
```

**Expected Output:** A valid JSON response containing `choices[0].message.content` with a text response.

**Status:** [ ] WAITING / [✅] PASSED

---

### Step 2.2: Configure GitHub App & Exchange Cryptographic Keys

1. Go to **GitHub Settings > Developer Settings > GitHub Apps > New GitHub App**
2. Set **Callback URL** to `https://yourdomain.com/auth/github/callback/`
3. Set **Webhook URL** to `https://yourdomain.com/webhooks/github`
4. Set **Webhook Secret** to a strong value (save this as `GITHUB_WEBHOOK_SECRET`)
5. Under **Repository Permissions**:
   - **Metadata:** Read-only
   - **Code:** Read-only
   - **Pull Requests:** Read & Write
   - **Commit statuses:** Read & Write
6. **Subscribe to events:** Pull request, Push
7. Generate a **Private Key** and download the `.pem` file
8. Save it to `~/ai-bug-fixer/certs/github_app.pem`
9. Copy the **App ID** displayed on the app page

Create `~/ai-bug-fixer/django-dashboard/.env`:

```env
DATABASE_URL=postgres://devops_admin:SecretSecurePasswordChangeMe@postgres-db:5432/ai_devops_db
CELERY_BROKER_URL=redis://redis-broker:6379/0
CELERY_RESULT_BACKEND=redis://redis-broker:6379/0
GITHUB_APP_IDENTIFIER=123456
GITHUB_APP_PRIVATE_KEY_PATH=/app/certs/github_app.pem
SLACK_ALERTS_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/path
SENDGRID_API_KEY=SG.your_sendgrid_key_signature
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_WEBHOOK_SIGNING_SECRET=whsec_your_stripe_webhook_secret
STRIPE_ENTERPRISE_PRICE_ID=price_1abcdefghijklmnopqrst
STRIPE_SUCCESS_URL=https://yourdomain.com/dashboard/
STRIPE_CANCEL_URL=https://yourdomain.com/
FERNET_KEY=d6TpYJgqZ7mXn3r5v8x/B?E(G+KbPeShVmYq3s6v9y$B&E)H@McQfTjWnZq4t7w
```

Create `~/ai-bug-fixer/ingestion-service/.env`:

```env
PORT=3000
GITHUB_WEBHOOK_SECRET=your-webhook-secret-matching-github-app-config
CELERY_BROKER_URL=redis://redis-broker:6379/0
```

**Note:** The `GITHUB_WEBHOOK_SECRET` here **must exactly match** the **Webhook Secret** you entered in the GitHub App settings in Step 2.2.5 above.

**Status:** [] WAITING / [✅] PASSED

---

### Step 2.3: Verify GitHub App Installation Token Exchange

```bash
cd ~/ai-bug-fixer
docker compose run --rm django-dashboard python -c "
from dashboard.github_auth import refresh_installation_access_token
token = refresh_installation_access_token('your-installation-id')
print(f'Token generated: {token[:10]}...' if token else 'FAILED')
"
```

**Expected Output:** `Token generated: ghs_XXXXX...`

**Status:** [ ] WAITING / [✅] PASSED

---

## Phase 3: Pre-Baking Immutable Sandbox Images

### Step 3.1: Compile Air-Gapped Python and JavaScript Runners

```bash
cd ~/ai-bug-fixer/sandbox-env

# Build the local Python testing environment
docker build -t local-pytest-sandbox -f Dockerfile.python .

# Build the local JavaScript/TypeScript testing environment
docker build -t local-jest-sandbox -f Dockerfile.javascript .
```

**Verification Command:**
```bash
docker images | grep "local-pytest\|local-jest"
```

**Expected Output:**
```
local-jest-sandbox      latest    a1b2c3d4e5f6    ...
local-pytest-sandbox    latest    f6e5d4c3b2a1    ...
```

**Status:** [ ] WAITING / [✅] PASSED

---

## Phase 4: Full Stack Microservice Deployment

### Step 4.1: Boot the Entire Multi-Container Cluster

```bash
cd ~/ai-bug-fixer
docker compose up --build -d
```

**Verification Command:**
```bash
docker compose ps
```

**Expected Output:** All services display a status of `Up`:
```
node-ingestion      Up
django-dashboard    Up
celery-worker       Up
fastapi-brain       Up
caddy-proxy         Up
postgres-db         Up
redis-broker        Up
```

**Status:** [ ] WAITING / [ ✅] PASSED

---

### Step 4.2: Verify Cross-Service Connectivity

```bash
# Test that the FastAPI brain can reach the Django dashboard
docker compose exec fastapi-brain curl -s -o /dev/null -w "%{http_code}" http://django-dashboard:8000/health/ || echo "No /health/ endpoint — checking /"

# Test that the Node.js gateway can reach Redis
docker compose exec node-ingestion node -e "
const celery = require('node-celery');
const client = celery.createClient({CELERY_BROKER_URL: 'redis://redis-broker:6379/0'});
client.on('connect', () => { console.log('REDIS_CONNECTED'); process.exit(0); });
client.on('error', (e) => { console.log('REDIS_FAILED:', e.message); process.exit(1); });
"
```

**Expected Output:** HTTP status 200 (or dashboard HTML) + `REDIS_CONNECTED`

**Status:** [ ] WAITING / [ ✅] PASSED

---

## Phase 5: Automated Testing and Verification Pipeline

### Step 5.1: Verify the Edge Circuit Breaker & Path Filtration

Simulate a non-functional documentation change. The Node.js gateway should drop it immediately.

```bash
curl -X POST http://localhost/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=mock_checksum" \
  -d '{
    "action": "opened",
    "pull_request": { "number": 44 },
    "repository": { "id": 111, "full_name": "enterprise/test-repo", "clone_url": "vfs" },
    "installation": { "id": 222 },
    "commits": [
      { "modified": ["README.md", "docs/architecture.txt"], "added": [] }
    ]
  }'
```

**Expected Output:** HTTP 200 OK
```json
{"status": "SKIPPED", "message": "No operational source code changes detected."}
```

**Status:** [ ] WAITING / [✅ ] PASSED

---

### Step 5.2: Verify Functional Code Triggers the Pipeline

Simulate a Python file change. The gateway should queue a Celery task.

```bash
curl -X POST http://localhost/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=mock_checksum" \
  -d '{
    "action": "opened",
    "pull_request": { "number": 45 },
    "repository": { "id": 112, "full_name": "enterprise/test-repo", "clone_url": "vfs" },
    "installation": { "id": 222 },
    "commits": [
      { "modified": ["src/auth.py", "README.md"], "added": [] }
    ]
  }'
```

**Expected Output:** HTTP 202 Accepted
```json
{"status": "QUEUED"}
```

**Status:** [ ] WAITING / [ ✅] PASSED

---

### Step 5.3: Test API Key Generation and Volatile Memory Presentation

1. Log into your Django dashboard at `http://localhost:8000/dashboard/developer-tokens/`
2. Click **"Generate New Secret Key"**
3. Your browser should display an amber warning banner containing your `sk_live_...` token value
4. Copy the token string
5. Refresh the browser page
6. Verify the raw token **disappears** and shows only masked entries (`sk_live_••••••••••••••••`)
7. This confirms the **session memory single-presentation parameter** works as intended

**Status:** [ ] WAITING / [✅ ] PASSED

---

### Step 5.4: Test the Live Developer CLI Workflow (patch-bot.sh)

```bash
mkdir -p ~/test-workspace && cd ~/test-workspace

# Generate local env with your new API token
echo 'export PATCHBOT_API_KEY="sk_live_your_copied_token_string_here"' > .patchbot.env

# Write a buggy Python file
cat <<EOF > target_bug.py
def calculate_average(items):
    return sum(items) / len(items)
EOF

# Execute the CLI client
~/ai-bug-fixer/infra/patch-bot.sh target_bug.py "Add a conditional checkpoint block to prevent DivisionByZero crashes when items array length matches zero."
```

**Expected Output:**
```
Initializing Autonomous AI Patch-Bot Engine client...
Targeting File: target_bug.py [Language Strategy Matrix: python]
Dispatching code safely to cloud parsing nodes...
Success! Execution tasks assigned smoothly to backend processing pools.
```

**Status:** [ ] WAITING / [ ✅] PASSED

---

### Step 5.5: Verify the Asynchronous Isolation Sandbox Lifecycle

Stream the FastAPI brain logs to verify the secret scrubber, resource limits, and Pytest execution:

```bash
docker compose logs -f fastapi-brain
```

**Trace Items to Verify in Logs:**
- [✅ ] `Compliance Alert: Intercepted and scrubbed...` — confirms secret scrubber ran
- [✅ ] `mem_limit=512m` and `nano_cpus=2000000000` — confirms resource caps are enforced
- [✅ ] Container exit code `0` — confirms test suite passed
- [ ✅] `AUTONOMOUS_PR_TRIGGERED` — confirms PR was created

**Status:** [ ] WAITING / [ ✅ ] PASSED

---

### Step 5.6: Confirm the Real-Time TypeScript Telemetry Stream

Open your browser to `http://localhost:8000/dashboard/`.

**Verification Steps:**
- [ ✅] The TypeScript polling client auto-updates status badges from `PENDING` to `SUCCESS` without page refreshes
- [ ✅] Each card displays the precise terminal log output from the air-gapped Docker runner
- [ ✅] The `project_id`, `repository_name`, and `target_language` fields are populated

**Status:** [ ] WAITING / [ ✅] PASSED

---

### Step 5.7: Test the Automated Server Maintenance Cron (cleanup-sandbox.sh)

```bash
# Launch a dummy container simulating a frozen AI execution run
docker run -d --name local-pytest-sandbox-leak-test local-pytest-sandbox sleep 300

# Wait 65 seconds, then run the cleanup script
sleep 65
~/ai-bug-fixer/infra/cleanup-sandbox.sh
```

**Expected Output:**
```
Initializing server-side sandbox resource scan...
Leak Warning: Sandbox Container [ID: ...] is hanging active!
Forcing kernel termination sequence on container...
Resource successfully reclaimed from frozen run.
Infrastructure sweep process completed successfully.
```

**Final verification — the leak container should be gone:**
```bash
docker ps -a | grep leak-test || echo "CONFIRMED: No leaked containers remain."
```

**Expected Output:**
```
CONFIRMED: No leaked containers remain.
```

**Status:** [ ] WAITING / [ ✅] PASSED

---

## Phase 6: Post-Deployment & Scale Validation

### Step 6.1: Verify FastAPI Health Endpoint

```bash
curl -s http://localhost:8010/health | python -m json.tool
```

**Expected Output:**
```json
{
    "status": "healthy",
    "service": "core-brain",
    "docker_ready": true
}
```

**Status:** [ ] WAITING / [ ✅] PASSED

---

### Step 6.2: Verify FastAPI Server Telemetry Endpoint

```bash
curl -s http://localhost:8010/api/v1/telemetry/server-health | python -m json.tool
```

**Expected Output:**
```json
{
    "status": "HEALTHY",
    "host_hardware": {
        "cpu_load_percent": 12.5,
        "logical_cores_count": 8,
        "thermal_sensors": {
            "cpu_current_celsius": "N/A"
        }
    },
    "memory_pools": {
        "total_ram_gb": 31.35,
        "allocated_ram_gb": 14.22,
        "available_ram_percent": 54.6
    },
    "container_subsystem": {
        "active_isolated_sandboxes": 0,
        "system_capacity_limit": 2
    }
}
```

**Status:** [ ] WAITING / [ ✅] PASSED

---

### Step 6.3: Verify Django Logs Stream API

```bash
curl -s http://localhost:8000/api/v1/logs-stream/ | python -m json.tool
```

**Expected Output:** A JSON array of audit log entries with fields:
```json
[
    {
        "project_id": "repo_999_pr_12",
        "repository_name": "enterprise/test-repo",
        "target_language": "python",
        "execution_status": "SUCCESS",
        "execution_summary": "Bug fixed and verified successfully.",
        "created_at": "2026-06-11T10:30:00+00:00"
    }
]
```

**Status:** [ ] WAITING / [ ✅] PASSED

---

### Step 6.4: Verify Celery Worker is Processing Tasks

```bash
# Check Celery worker status
docker compose logs celery-worker --tail 20
```

**Look for:**
```
[INFO] celery@... ready.
[INFO] Task dashboard.tasks.execute_background_remediation_task[...] succeeded in ...s
```

Also verify the Celery worker queue is being consumed:
```bash
docker compose exec redis-broker redis-cli LLEN celery | xargs echo "Pending tasks in queue:"
```

**Expected Output:** `Pending tasks in queue: 0` (all tasks consumed)

**Status:** [ ] WAITING / [✅ ] PASSED

---

### Step 6.5: Verify PostgreSQL Row-Level Security Multi-Tenant Enforcement

This is critical — confirm one tenant cannot see another tenant's data.

```bash
# Insert a row as tenant-alpha, then try to read it as tenant-beta
docker compose exec postgres-db psql -U devops_admin -d ai_devops_db <<'EOF'
-- Set session as tenant-alpha
SET LOCAL app.current_tenant = 'alpha-corp';
INSERT INTO dashboard_runauditlog (project_id, repository_name, target_language, execution_status, execution_summary)
VALUES ('secret-project-42', 'alpha-corp/proprietary', 'python', 'SUCCESS', 'alpha secret data');

-- Switch to tenant-beta and try to read
SET LOCAL app.current_tenant = 'beta-corp';
SELECT * FROM dashboard_runauditlog WHERE project_id = 'secret-project-42';
EOF
```

**Expected Output:** `(0 rows)` — tenant-beta cannot see tenant-alpha's rows.

**Status:** [ ] WAITING / [✅----- ] PASSED

---

### Step 6.6: Verify Stripe Webhook Listener Reachability

```bash
# Test that Stripe could reach the webhook endpoint externally
curl -s -o /dev/null -w "HTTP %{http_code}" -X POST http://localhost/api/v1/billing/stripe-webhook/ \
  -H "Content-Type: application/json" \
  -d '{"test": "ping"}'
```

**Expected Output:** `HTTP 400` (Stripe signature verification fails as expected because no real Stripe signature header is present — this confirms the endpoint is reachable and rejecting unauthenticated requests)

To test with a valid Stripe event, use the Stripe CLI:
```bash
stripe trigger checkout.session.completed
```

**Status:** [ ] WAITING / [✅ ] PASSED

---

### Step 6.7: Verify Internal Meter Event Endpoint (Inaccessible from Internet)

```bash
# Try from outside the Docker network (should be blocked)
curl -s -o /dev/null -w "HTTP %{http_code}" -X POST http://localhost/api/v1/meter-event/

# Try from inside the Docker network (should succeed with bad auth)
docker compose exec fastapi-brain curl -s -o /dev/null -w "HTTP %{http_code}" -X POST http://django-dashboard:8000/api/v1/meter-event/
```

**Expected Output:**
- External: `HTTP 403` (blocked by Caddy)
- Internal (bad auth): `HTTP 403` (rejected by the view's bearer token check)

**Status:** [ ] WAITING / [✅ ] PASSED

---

### Step 6.8: Verify SendGrid Email Notification on Meter Event

Trigger a meter event and check the Django logs:

```bash
# Manually hit the meter endpoint with the internal auth token
docker compose exec fastapi-brain curl -s -X POST http://django-dashboard:8000/api/v1/meter-event/ \
  -H "Authorization: Bearer LocalSecretInternalTokenBetweenServices" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "test-verify-001", "organization_name": "admin"}'

# Check Django logs for email notification
docker compose logs django-dashboard --tail 10
```

**Expected Output:**
```
[Meter] Usage unit recorded: 1 bug fix for admin, project test-verify-001
```

If a valid `SENDGRID_API_KEY` is configured, you should also see SendGrid delivery logs. With a mock key, it will log the network error gracefully:
```
SendGrid delivery channel pipeline failure: ...
```

**Status:** [ ] WAITING / [ ✅] PASSED

---

### Step 6.9: Seed Mock Telemetry Data for Dashboard Testing

```bash
docker compose run --rm django-dashboard python manage_mock_telemetry.py
```

**Expected Output:**
```
Scrubbing historical audit structures...
Seeding enterprise multi-tenant telemetry structures...
Telemetry entries pinned to organizational workspace: netflix-core-eng
Telemetry entries pinned to organizational workspace: stripe-billing-dev
Telemetry seed complete. Boot up your TypeScript dashboard to view real-time state changes.
```

Then refresh `http://localhost:8000/dashboard/` — you should see populated log entries for both orgs.

**Status:** [ ] WAITING / [✅ ] PASSED

---

### Step 6.10: Verify Database Backup Script (Dry-Run)

```bash
# Run the backup script manually (it will dump and attempt S3 upload)
# To test without S3 credentials, use a dry-run flag:
DRY_RUN=true bash ~/ai-bug-fixer/infra/backup_database.sh
```

Or verify the backup path exists:
```bash
ls -la /tmp/db_dumps/
```

**Expected Output:** A `.sql.gz` file with a timestamp in its name, e.g.:
```
-rw-r--r-- 1 root root 12345 Jun 11 02:00 ai_devops_db_2026-06-11_020000.sql.gz
```

**Status:** [ ] WAITING / [ ✅] PASSED

---

### Step 6.11: Verify Caddy Reverse Proxy Routes

```bash
# Webhook path should reach Node.js
curl -s -o /dev/null -w "HTTP %{http_code}" -X POST http://localhost/webhooks/github -H "Content-Type: application/json" -d '{"action":"opened"}'

# Dashboard path should reach Django
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost/dashboard/

# CLI trigger path should reach Django
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost/api/v1/cli/trigger-fix

# Internal API path should be blocked
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost/api/v1/meter-event/
```

**Expected Output:**
```
HTTP 200 (webhook — Node.js responds quickly)
HTTP 200 (dashboard — Django renders)
HTTP 200 (CLI trigger — Django responds)
HTTP 403 (meter-event — blocked by Caddy)
```

**Status:** [ ] WAITING / [✅ ] PASSED

---

### Step 6.12: Verify SSL Certificate Auto-Provisioning (Production Only)

Once DNS points to your Hetzner IP:

```bash
# Check Caddy logs for certificate provisioning
docker compose logs caddy-proxy | grep -i "certificate\|ssl\|letsencrypt"
```

**Expected Output:**
```
certificate obtained successfully
```

Also verify at [SSLLabs](https://www.ssllabs.com/ssltest/) or directly:
```bash
curl -sI https://yourstartupdomain.com | head -n 1
```

**Expected Output:**
```
HTTP/2 200
```

**Status:** [ ] WAITING / [✅ ] PASSED / [ ] SKIPPED (no domain yet)

---

### Step 6.13: Verify GitHub Commit Status API Integration

After a successful PR fix, check that GitHub shows the commit status:

```bash
# Query the GitHub API for the commit status
# Replace with your actual repo and commit SHA after a successful run
curl -s -H "Authorization: Bearer $(your-token)" \
  "https://api.github.com/repos/enterprise/test-repo/commits/your-commit-sha/status" | \
  python -c "import sys,json; data=json.load(sys.stdin); print(f'State: {data.get(\"state\")}')"
```

**Expected Output:**
```
State: success
```

**Status:** [ ] WAITING / [✅  ] PASSED

---

## Final Summary Checklist

Copy this table and track your progress:

| Step | Description | Status |
|------|-------------|--------|
| 1.1 | Host directories + Docker network | [ ] |
| 1.2 | PostgreSQL + Redis running | [ ] |
| 1.3 | Django migrations + RLS enabled | [ ] |
| 2.1 | OpenRouter key configured + verified | [ ] |
| 2.2 | GitHub App + Django .env configured | [ ] |
| 2.3 | Installation token exchange works | [ ] |
| 3.1 | Pytest + Jest sandbox images built | [ ] |
| 4.1 | All containers up | [ ] |
| 4.2 | Cross-service connectivity | [ ] |
| 5.1 | Circuit breaker skips non-code commits | [ ] |
| 5.2 | Functional code triggers Celery queue | [ ] |
| 5.3 | API key generation + one-time display | [ ] |
| 5.4 | CLI patch-bot.sh end-to-end | [ ] |
| 5.5 | Sandbox lifecycle (scrubber, limits, tests, PR) | [ ] |
| 5.6 | TypeScript dashboard live polling | [ ] |
| 5.7 | Cleanup script kills leaked containers | [ ] |
| 6.1 | FastAPI /health | [ ] |
| 6.2 | FastAPI /telemetry/server-health | [ ] |
| 6.3 | Django logs-stream API | [ ] |
| 6.4 | Celery worker processing tasks | [ ] |
| 6.5 | PostgreSQL RLS tenant isolation | [ ] |
| 6.6 | Stripe webhook endpoint reachable | [ ] |
| 6.7 | Internal meter endpoint blocked externally | [ ] |
| 6.8 | Meter event + email notification | [ ] |
| 6.9 | Mock telemetry data seeded | [ ] |
| 6.10 | Database backup script runs | [ ] |
| 6.11 | Caddy routes correct (proxy, block) | [ ] |
| 6.12 | SSL certificate (production) | [ ] / [SKIP] |
| 6.13 | GitHub commit status check | [ ] |
