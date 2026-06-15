import re
from django.db import connection


class PostgreSQLTenantIsolationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = getattr(request, "organization_name", None)

        if not tenant and request.user.is_authenticated:
            from .models import GitHubIntegration
            if GitHubIntegration.objects.filter(organization_name=request.user.username).exists():
                tenant = request.user.username

        if not tenant:
            from .models import GitHubIntegration
            integration = GitHubIntegration.objects.first()
            tenant = integration.organization_name if integration else "default"

        request.tenant = tenant

        if tenant:
            if not re.match(r'^[a-zA-Z0-9_.-]+$', tenant):
                tenant = "default"
            with connection.cursor() as cursor:
                cursor.execute(f"SET LOCAL app.current_tenant = '{tenant}';")

        response = self.get_response(request)
        return response
