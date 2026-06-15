# Air-Gapped Multi-Language AI DevOps Engine

[![License](https://shields.io)](https://opensource.org)
[![Python](https://shields.io)](https://python.org)
[![Node.js](https://shields.io)](https://nodejs.org)
[![Docker](https://shields.io)](https://docker.com)

An autonomous, zero-data-retention AI DevOps pipeline designed to safely ingest, sanitize, patch, and verify full-stack **Python** and **JavaScript/TypeScript** codebases.

This engine solves a critical enterprise vulnerability: running or streaming untrusted, AI-generated code patches without exposing proprietary code to public LLM datasets or executing unverified scripts on host infrastructure.

---

## System Architecture Blueprint

The framework implements a strict **separation of concerns** across an isolated microservice topology, optimized to run concurrently on local resource-constrained CPU/GPU environments:

```
GITHUB UNIVERSE (Webhooks & REST API)
         │
         │
┌────────┴────────────────────────┐
│ (Webhook Event)                 │ (OAuth Token / PR Action)
│                                 │
▼                                 ▼
┌─────────────────────┐           ┌─────────────────────┐
│   Node.js Gateway   │───────►   │   FastAPI Brain     │
│ (Ingestion Layer)   │ Internal  │  (Sandbox Engine)   │
└─────────────────────┘ Transit   └──────────┬──────────┘
         │                                    │
(Verify Origin)                     (Mounts Ephemeral VFS)
         │                                    │
         ▼                                    ▼
┌─────────────────────┐           ┌─────────────────────┐
│   Django Core DB    │           │ Docker Engine Host  │
│ (Metadata Only/Auth)│           │ (Pre-baked Images)  │
└─────────────────────┘           └──────────┬──────────┘
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼ (Python Strategy)       ▼ (JavaScript Strategy)   ▼
         ┌─────────────────────┐    ┌─────────────────────┐
         │ local-pytest-runner │    │  local-jest-runner  │
         │ (Isolated Container)│    │ (Isolated Container)│
         └─────────────────────┘    └─────────────────────┘
```

---

## Core Enterprise Security Vectors

### 1. Zero-Data-Retention (ZDR) & Data Minimization
- **Zero Code Persistence:** The primary database state layer (PostgreSQL) is strictly barred from storing customer source code trees or branch diff hashes. It logs only operational indexing metadata.
- **ZDR Inference Protocol:** Outbound AI completions utilize an LLM abstraction router mapping exclusively to providers enforcing legal Zero-Data-Retention SLAs (AWS Bedrock, Azure AI, Google Vertex). Data is processed in volatile memory, excluded from training, and destroyed instantly.

### 2. Local In-Memory Secret Scrubbing
An integrated high-speed regex profiling middleware scans code payloads in volatile memory, masking sensitive variables (AWS keys, Stripe tokens, GitHub tokens, database credentials) prior to transit, ensuring compliance perimeters are never crossed.

### 3. Air-Gapped Sandbox Isolation
Untrusted, AI-generated code is never run on primary server hardware. It is mounted **Read-Only (`mode: ro`)** into ephemeral, pre-baked Docker containers (`local-pytest-sandbox` and `local-jest-sandbox`).
- Networks are entirely air-gapped (no public transit).
- Resource throttles are strictly enforced per run: **Max 512MB RAM** and **Max 2 CPU logical cores** to eliminate billing runway loops or script-level DoS attacks.

### 4. Database Multi-Tenant Separation via PostgreSQL RLS
Bypassing vulnerable application-level filters (`.filter()`), data separation is executed directly within the storage engine using **PostgreSQL Row-Level Security (RLS)**. Django middleware sets database session configuration states on every transaction, making it physically impossible for tenant records to cross perimeters.

---

## Microservice Directory Structure

```
├── ingestion-service/    # High-concurrency Node.js Express incoming webhook edge gateway
├── core-brain/           # FastAPI automation router, LiteLLM orchestration, Docker engine client
├── django-dashboard/     # Django management SaaS app, encrypted credentials, async Celery worker queues
├── sandbox-env/          # Base configurations for pre-baked immutable test runners (Pytest / Jest)
├── infra/
│   ├── patch-bot.sh           # CLI client for developer terminals
│   ├── cleanup-sandbox.sh     # Automated container leak cleanup script
│   └── backup_database.sh     # Nightly S3 database backup script
├── docker-compose.yml    # Production orchestration
├── docker-compose.local.yml  # Local development stack
├── docker-compose.web.yml    # Web worker profile (scaled)
├── docker-compose.worker.yml # Compute worker profile (scaled)
├── Caddyfile                  # Production reverse proxy with auto TLS
├── SECURITY_WHITEPAPER.md     # SOC 2 / ISO 27001 alignment documentation
└── ONBOARDING_CHECKLIST.md    # Customer installation blueprint
```

---

## Quickstart Local Development Deployment

### Prerequisites
- Docker & Docker Compose
- Node.js v18+ & Python 3.11+

### 1. Pre-Bake Testing Container Images Locally

```bash
docker build -t local-pytest-sandbox -f ./sandbox-env/Dockerfile.python ./sandbox-env/
docker build -t local-jest-sandbox -f ./sandbox-env/Dockerfile.javascript ./sandbox-env/
```

### 2. Launch the Microservice Stack

```bash
docker compose -f docker-compose.local.yml up --build -d
```

### 3. Trigger a Local Simulated Webhook Run

```bash
curl -X POST http://localhost/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=mock_signature_field" \
  -d '{
    "action": "opened",
    "pull_request": { "number": 1 },
    "repository": { "id": 101, "full_name": "local-org/test-repo", "clone_url": "local_vfs" },
    "installation": { "id": 202 }
  }'
```

---

## Business Metrics & ROI

This system decreases active engineering hours spent on localized bug remediation by automating data parsing, patch generation, and sandboxed validation loops. Development teams scale release velocity safely while reducing dependency overhead and preserving total infrastructure security.
