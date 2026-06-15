import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()
from dashboard.models import GitHubIntegration
gi = GitHubIntegration.objects.get(installation_id='139799081')
token = gi.encrypted_access_token

import requests, base64, time
headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github.v3+json'}
repo = 'hirwalandry/AI-DEVOPS-ENGINE'
base = 'main'

# Step 1: Get base branch SHA
r = requests.get(f'https://api.github.com/repos/{repo}/git/ref/heads/{base}', headers=headers)
print('1. Get branch:', r.status_code)
if r.status_code == 200:
    sha = r.json()['object']['sha']
    print('   SHA:', sha[:10])
else:
    print('   Error:', r.text[:200])
    exit()

# Step 2: Create new branch
branch = f'ai-remediation/test-{int(time.time())}'
r = requests.post(f'https://api.github.com/repos/{repo}/git/refs',
    json={'ref': f'refs/heads/{branch}', 'sha': sha}, headers=headers)
print('2. Create branch:', r.status_code)
if r.status_code != 201:
    print('   Error:', r.text[:200])
    exit()

# Step 3: Get file SHA (file may not exist)
file_path = 'app_patch.py'
r = requests.get(f'https://api.github.com/repos/{repo}/contents/{file_path}?ref={base}', headers=headers)
print('3. Get file:', r.status_code)
file_sha = r.json()['sha'] if r.status_code == 200 else None
print('   SHA:', file_sha)

# Step 4: Create/update file
content = base64.b64encode(b'print("hello world")\n').decode()
payload = {'message': 'test commit', 'content': content, 'branch': branch}
if file_sha:
    payload['sha'] = file_sha
r = requests.put(f'https://api.github.com/repos/{repo}/contents/{file_path}',
    json=payload, headers=headers)
print('4. Commit file:', r.status_code)
if r.status_code in [200, 201]:
    print('   OK')
else:
    print('   Error:', r.text[:200])

# Step 5: Create PR
pr = requests.post(f'https://api.github.com/repos/{repo}/pulls',
    json={'title': 'Test PR', 'head': branch, 'base': base, 'body': 'Testing'},
    headers=headers)
print('5. Create PR:', pr.status_code)
if pr.status_code == 201:
    print('   URL:', pr.json()['html_url'])
else:
    print('   Error:', pr.text[:200])
