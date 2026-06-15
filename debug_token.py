import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()
from dashboard.models import GitHubIntegration
gi = GitHubIntegration.objects.get(installation_id='139799081')
token = gi.encrypted_access_token

import requests
headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github.v3+json'}

r = requests.get('https://api.github.com/installation/repositories', headers=headers)
print('Installation repos status:', r.status_code)
if r.status_code == 200:
    repos = r.json()['repositories']
    print('Has access to repos:', [repo['full_name'] for repo in repos])
else:
    print('Error:', r.text[:200])

r = requests.get('https://api.github.com/repos/hirwalandry/AI-DEVOPS-ENGINE', headers=headers)
print('\nRepo exists:', r.status_code)
if r.status_code == 200:
    print('Default branch:', r.json().get('default_branch'))
else:
    print('Error:', r.text[:200])
