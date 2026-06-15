import django; django.setup()
from dashboard.github_auth import refresh_installation_access_token
import requests

token = refresh_installation_access_token('139799081')
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}
resp = requests.get('https://api.github.com/repos/hirwalandry/AI-DEVOPS-ENGINE/issues/5/comments', headers=headers)
if resp.status_code == 200:
    comments = resp.json()
    print(f'Comments on PR #5: {len(comments)}')
    for c in comments:
        print(f'  From: {c["user"]["login"]} at {c["created_at"]}')
        print(f'  Body preview: {c["body"][:300]}')
        print()
else:
    print('Failed:', resp.text[:200])
