import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()
from dashboard.models import DeveloperAPIKey, GitHubIntegration

DeveloperAPIKey.objects.filter(prefix='sk_live_').delete()

integration = GitHubIntegration.objects.first()
org_name = integration.organization_name if integration else 'admin'

raw_key, key_record = DeveloperAPIKey.generate_key_for_org(org_name)

print(f'Your API Key: {raw_key}')
