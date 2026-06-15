import os
import django
import random
from datetime import datetime, timedelta, timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from dashboard.models import RunAuditLog, GitHubIntegration
from django.db import connection

MOCK_TEAMS = [
    {"org": "netflix-core-eng", "repos": ["netflix/backend-auth", "netflix/api-gateway", "netflix/ui-router"]},
    {"org": "stripe-billing-dev", "repos": ["stripe/ledger-core", "stripe/checkout-component"]},
]

MOCK_LOGS = {
    "SUCCESS": [
        "pytest passed. 14 assertions evaluated successfully.\nTarget function 'validate_token_string' optimized.",
        "jest passed. All 8 suites executed in 1.45s.\nResolved asynchronous promise rejection error inside api-handler.ts.",
    ],
    "FAILED": [
        "pytest failed. IndexError: list index out of range on line 42 inside models.py.",
        "jest failed. SyntaxError: Unexpected token '}' inside parsing block config.js.",
    ],
    "PENDING": [
        "System initializing. Allocating core microservice resources inside isolated sandbox container...",
        "Volatile virtual filesystem mounted. Pulling pre-baked environment runner images...",
    ],
}


def clear_existing_simulation_data():
    print("Scrubbing historical audit structures...")
    RunAuditLog.objects.all().delete()
    GitHubIntegration.objects.all().delete()


def seed_simulation_telemetry():
    print("Seeding enterprise multi-tenant telemetry structures...")

    for team in MOCK_TEAMS:
        org_name = team["org"]

        GitHubIntegration.objects.update_or_create(
            organization_name=org_name,
            defaults={
                "installation_id": str(random.randint(100000, 999999)),
                "encrypted_access_token": "mock_encrypted_token_value_signature",
            },
        )

        with connection.cursor() as cursor:
            cursor.execute(f"SET LOCAL app.current_tenant = '{org_name}';")

        for repo in team["repos"]:
            for i in range(random.randint(3, 6)):
                status = random.choice(["SUCCESS", "FAILED", "PENDING"])
                language = random.choice(["python", "javascript"])
                summary = random.choice(MOCK_LOGS[status])

                project_id = f"repo_{random.randint(100,999)}_pr_{random.randint(1,50)}"

                time_offset = datetime.now(timezone.utc) - timedelta(
                    hours=random.randint(1, 48), minutes=random.randint(1, 59)
                )

                log_record = RunAuditLog.objects.create(
                    organization_name=org_name,
                    project_id=project_id,
                    repository_name=repo,
                    target_language=language,
                    execution_status=status,
                    execution_summary=summary,
                )

                RunAuditLog.objects.filter(id=log_record.id).update(created_at=time_offset)

        print(f"Telemetry entries pinned to organizational workspace: {org_name}")


if __name__ == "__main__":
    clear_existing_simulation_data()
    seed_simulation_telemetry()
    print("Telemetry seed complete. Boot up your TypeScript dashboard to view real-time state changes.")
