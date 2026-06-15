import django; django.setup()
from dashboard.github_auth import refresh_installation_access_token
import requests

token = refresh_installation_access_token('139799081')
headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github+json',
}
resp = requests.get('https://api.github.com/installation/repositories', headers=headers)
if resp.status_code == 200:
    repos = resp.json().get('repositories', [])
    for r in repos:
        print(f"{r['full_name']} (default_branch: {r['default_branch']})")
else:
    print('Failed:', resp.status_code, resp.text[:200])
