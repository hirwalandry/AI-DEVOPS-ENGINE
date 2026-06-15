from django.contrib import admin
from .models import GitHubIntegration, RunAuditLog, Deployment


@admin.register(GitHubIntegration)
class GitHubIntegrationAdmin(admin.ModelAdmin):
    list_display = ('organization_name', 'installation_id', 'registered_at')
    readonly_fields = ('registered_at',)


@admin.register(RunAuditLog)
class RunAuditLogAdmin(admin.ModelAdmin):
    list_display = ('project_id', 'repository_name', 'target_language', 'execution_status', 'created_at')
    list_filter = ('execution_status', 'target_language')
    readonly_fields = ('created_at',)


@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    list_display = ('repository_name', 'commit_sha', 'status', 'strategy', 'created_at', 'deployed_at')
    list_filter = ('status', 'strategy')
    readonly_fields = ('created_at', 'deployed_at')
