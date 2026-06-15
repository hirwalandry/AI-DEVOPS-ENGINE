import django; django.setup()
from dashboard.github_auth import refresh_installation_access_token
import requests

token = refresh_installation_access_token('139799081')
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}
resp = requests.get('https://api.github.com/repos/hirwalandry/AI-DEVOPS-ENGINE/issues/6/comments', headers=headers)
for c in resp.json():
    print(f'From: {c["user"]["login"]}')
    print(f'URL: {c["html_url"]}')
    print(f'Body ({len(c["body"])} chars):')
    print(c['body'])
