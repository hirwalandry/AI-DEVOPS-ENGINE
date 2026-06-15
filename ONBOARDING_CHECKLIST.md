# Enterprise Onboarding Checklist

**Product:** Autonomous AI Code Remediation Engine  
**Target:** Corporate Enterprise Engineering Division  
**Version:** 1.0

---

## Phase 1: Legal & Compliance Clearance (Pre-Technical)

- [ ] **Execute Zero-Data-Retention SLA Addendum** — Secure signatures from the client's legal or procurement team. This document legally binds your platform to delete code post-inference and guarantees no data is ever used for model training.
- [ ] **Provide Technical Security Whitepaper** — Hand off your completed Security Posture document (`SECURITY_WHITEPAPER.md`) directly to their Chief Information Security Officer (CISO) or Application Security team for architectural review.
- [ ] **Exchange Secret Clearance Tokens** — Securely hand over the system's static configuration metadata schemas to confirm compliance limits.

---

## Phase 2: Administrative Organization Handshake

- [ ] **Initialize Corporate Billing Account** — Direct the customer's DevOps Lead or Engineering Manager to your Django Billing Panel. Have them initiate a Stripe Checkout Session to register their corporate credit card or corporate ACH banking coordinates.
- [ ] **Trigger GitHub App Organization Installation** — Have a GitHub Organization Owner click the "Install GitHub App" anchor on your platform.
- [ ] **Apply Repository Restrictions** — Instruct the admin to toggle access settings inside GitHub from "All Repositories" to "Only Select Repositories". This allows them to run your beta tool within a controlled environment (e.g., a single test repository) without exposing their entire codebase.

---

## Phase 3: CI/CD Injection Loop & Verification

- [ ] **Generate Core Developer Tokens** — Guide the Engineering Manager to your Django API Key Dashboard. Have them click "Generate New Secret Key" and record the displayed token string (`sk_live_...`) securely.
- [ ] **Inject GitHub Actions Workflow Secrets** — Instruct their team to add a secret named `PATCHBOT_API_KEY` directly inside their GitHub repository settings, pasting your generated token string into the target field.
- [ ] **Commit the Test Pipeline File** — Drop your automated `.github/workflows/ai-patchbot.yml` tracking file into their codebase's primary development branch.
- [ ] **Trigger the First Autonomous Run** — Instruct a developer to push a minor code change or a file with a known, localized syntax issue.
- [ ] **Verify End-to-End Success** — Confirm the following sequence executes correctly:
  - Webhook triggers your Node.js gateway.
  - Task runs inside your asynchronous Celery worker ring.
  - Bug fix completes safety validation checks inside the FastAPI isolated container.
  - Green checkmark displays natively on the GitHub Commit Status Check interface.
  - Real-time transactional tracking invoice drops cleanly into their corporate inbox via SendGrid.
