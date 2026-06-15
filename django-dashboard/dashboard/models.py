import hashlib
import os
from django.db import models
from cryptography.fernet import Fernet
from django.conf import settings


class EncryptedField(models.CharField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        f = Fernet(settings.FERNET_KEYS[0].encode())
        return f.decrypt(value.encode()).decode()

    def get_prep_value(self, value):
        if value is None:
            return value
        f = Fernet(settings.FERNET_KEYS[0].encode())
        return f.encrypt(value.encode()).decode()


class GitHubIntegration(models.Model):
    organization_name = models.CharField(max_length=255, unique=True)
    installation_id = models.CharField(max_length=100, unique=True)
    encrypted_access_token = EncryptedField(max_length=512)
    registered_at = models.DateTimeField(auto_now_add=True)


class TenantManager(models.Manager):
    def for_tenant(self, tenant_name):
        return self.filter(organization_name=tenant_name)


class RunAuditLog(models.Model):
    organization_name = models.CharField(max_length=255, db_index=True)
    project_id = models.CharField(max_length=255, db_index=True)
    repository_name = models.CharField(max_length=255)
    target_language = models.CharField(max_length=50)
    execution_status = models.CharField(max_length=50)
    execution_summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()


class DeveloperAPIKey(models.Model):
    organization_name = models.CharField(max_length=255, db_index=True)
    prefix = models.CharField(max_length=16)
    hashed_key = models.CharField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_key_for_org(org_name: str) -> tuple[str, "DeveloperAPIKey"]:
        raw_secret = os.urandom(24).hex()
        prefix = "sk_live_"
        full_key = f"{prefix}{raw_secret}"
        hashed = hashlib.sha256(full_key.encode("utf-8")).hexdigest()
        instance = DeveloperAPIKey.objects.create(
            organization_name=org_name,
            prefix=prefix,
            hashed_key=hashed,
        )
        return full_key, instance


class Deployment(models.Model):
    STATUS_CHOICES = [
        ('QUEUED', 'Queued'),
        ('BUILDING', 'Building'),
        ('DEPLOYING', 'Deploying'),
        ('DEPLOYED', 'Deployed'),
        ('ROLLED_BACK', 'Rolled Back'),
        ('FAILED', 'Failed'),
    ]
    STRATEGY_CHOICES = [
        ('docker', 'Docker'),
        ('kubernetes', 'Kubernetes'),
        ('serverless', 'Serverless'),
        ('custom_script', 'Custom Script'),
    ]
    organization_name = models.CharField(max_length=255, db_index=True)
    repository_name = models.CharField(max_length=255)
    commit_sha = models.CharField(max_length=40)
    branch = models.CharField(max_length=255, default='main')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='QUEUED')
    strategy = models.CharField(max_length=20, choices=STRATEGY_CHOICES, default='docker')
    target_url = models.URLField(blank=True, default='')
    logs = models.TextField(blank=True, default='')
    triggered_by = models.CharField(max_length=20, default='auto')
    created_at = models.DateTimeField(auto_now_add=True)
    deployed_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()
