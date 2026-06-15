# Hacker News "Show HN" Launch Template

## Title

```
Show HN: An air-gapped AI bug-fixer that validates patches in isolated Docker sandboxes
```

## First Comment (paste immediately after submitting)

```
Hi HN,

I built an autonomous AI DevOps pipeline that ingests repository bugs, constructs code patches,
runs automated tests inside completely air-gapped Docker sandboxes, and opens validated Pull
Requests natively back on GitHub.

Most AI coding agents present a glaring enterprise liability: they expect you to execute
unverified, AI-generated code strings directly on your primary systems, or they leak
proprietary intellectual property out to public LLM datasets.

I wanted an infrastructure layer that solves this, specifically optimized to run efficiently
on affordable, multi-tenant bare-metal CPU instances without massive operational costs.

Here is the architectural choices I implemented to make the system enterprise-grade:

1. High-Speed Edge Gateways: Ingestion is written in Node.js to parse GitHub webhooks within
   2ms. It evaluates changed file paths before queueing tasks, dropping non-functional events
   (e.g., changes to READMEs or images) immediately to prevent CPU thrashed bottlenecks.

2. In-Memory Compliance Scrubbers: Payloads hit a FastAPI core brain where an in-memory
   middleware regex-scrubs hardcoded variables (AWS tokens, GitHub keys, DB secrets) in
   volatile memory before data ever moves downstream.

3. Zero-Data-Retention Routing: Using LiteLLM, requests are dynamically abstracted to
   Enterprise ZDR models (like AWS Bedrock or Azure AI models) using 'data_collection: deny'
   policies to legally protect source code from being logged or used for LLM training.

4. Air-Gapped Docker Sandboxing: Generated patches are written to a temporary host path and
   mounted Read-Only into pre-baked local container pools ('local-pytest-sandbox' and
   'local-jest-sandbox'). The container network is entirely disabled, and resource limits are
   hard-throttled to 512MB RAM and 2 CPU cores via the Docker Python SDK to stop
   loop-overflow attacks.

5. Database-Layer Tenancy (PostgreSQL RLS): To prevent tenant data leaks on the history
   dashboard, I bypassed error-prone Django ORM application filtering. Instead, Django
   middleware injects the active tenant ID directly into PostgreSQL session configuration
   parameters on every transaction. The isolation boundaries are actively enforced directly by
   the database engine using Row-Level Security policies.

6. Non-Blocking Event Loops: High-latency container execution and OpenRouter roundtrips are
   completely offloaded to a local Redis-backed Celery cluster running exponential backoff
   retries and global async 'on_failure' exception captures linked directly to SendGrid and
   Slack webhooks.

I have spent the last few weeks testing this full-stack setup, and it natively manages
full-stack Python and JavaScript patches seamlessly. The codebase is open-source, and you can
spin up the entire cluster locally via Docker Compose to trace the telemetry yourself.

I'd love to get your feedback on the container containment architecture, the database
security model, and how you manage untrusted code execution inside your pipelines!

Repo URL: https://github.com/your-org/your-repo
```
