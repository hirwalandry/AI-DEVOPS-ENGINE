# Zero-Downtime Production Database Migration Guide

Updating database table schemas on a live system can cause server interruptions. If a background Celery task tries to write data using an old database schema model while your Django application is halfway through a migration, the task will throw an exception, fail asynchronously, and trigger an unwanted Slack alert.

To deploy database model schema updates on your Hetzner server without taking down active background tasks, use the **Three-Phase Schema Migration Strategy** below.

---

## Overview

```
[ Phase A: Expand Schema ] ──► [ Phase B: Deploy App Code ] ──► [ Phase C: Contract Schema ]
           │                                │                                │
           ▼                                ▼                                ▼
  Add new columns/tables.         Update code to write to         Drop old columns/tables
  Old columns remain untouched.   new fields. Backward-safe.      safely after deployment.
```

---

## Phase A: Additive Structural Expansion (No Disruptions)

If you need to change a field (for example, renaming `execution_summary` to `telemetry_logs_json`), **never drop or modify the old field immediately**.

1. Create a migration that **adds** the new column while leaving the old column completely active.
2. Apply the migration to your live Hetzner database container:

```bash
docker exec -it $(docker ps -f name=django-dashboard -q) python manage.py migrate
```

**Why this is safe:** Because the old column still exists, active background Celery workers can continue writing metrics to it without throwing errors.

---

## Phase B: Dual-Write Application Deployment

1. Update your Django backend and Celery code models to **write to both columns simultaneously**, but **read data exclusively from the new schema column**.
2. Build and restart your application web servers and background workers using Docker Compose rolling updates:

```bash
docker compose up -d --no-deps --build django-dashboard celery-worker
```

**Why this is safe:** This migrates your live system's processing logic to the new schema without a single second of service down-time.

---

## Phase C: Subtractive Consolidation (Clean Up Storage)

1. Run a background script to parse historic database records, copying data from the old column over to the new field for old logs.
2. Once your historical records match, create a final migration file that **deletes the legacy column** from your schema layout.
3. Push the clean-up migration to production.

Your database is now completely optimized, and your background workflows never encountered an operational constraint.

---

## Example: Renaming `execution_summary` to `telemetry_logs_json`

### Phase A Migration

```python
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0002_enable_rls"),
    ]

    operations = [
        migrations.AddField(
            model_name="runauditlog",
            name="telemetry_logs_json",
            field=models.JSONField(null=True, blank=True),
        ),
    ]
```

### Phase B Code (dual-write in model save)

```python
class RunAuditLog(models.Model):
    execution_summary = models.TextField()
    telemetry_logs_json = models.JSONField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.telemetry_logs_json and not self.execution_summary:
            self.execution_summary = json.dumps(self.telemetry_logs_json)
        super().save(*args, **kwargs)
```

### Phase C Migration (drop the old column)

```python
class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0003_add_telemetry_logs_json"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="runauditlog",
            name="execution_summary",
        ),
    ]
```
