import django; django.setup()
from dashboard.github_auth import refresh_installation_access_token
import requests
import base64
import json

INSTALLATION_ID = '139799081'
REPO = 'hirwalandry/AI-DEVOPS-ENGINE'
PR_NUMBER = 5

token = refresh_installation_access_token(INSTALLATION_ID)
print(f'Token acquired: {token[:15]}...')

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github+json',
}

# 1. Get the PR details
pr_resp = requests.get(f'https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}', headers=headers)
if pr_resp.status_code != 200:
    print(f'Failed to get PR: {pr_resp.text}')
    exit(1)
pr_data = pr_resp.json()
head_sha = pr_data['head']['sha']
base_branch = pr_data['base']['ref']
print(f'PR #{PR_NUMBER}: head={head_sha[:7]}, base={base_branch}')

# 2. Get the buggy file content
file_path = 'e2e_test_buggy.py'
file_resp = requests.get(
    f'https://api.github.com/repos/{REPO}/contents/{file_path}?ref={pr_data["head"]["ref"]}',
    headers=headers,
)
if file_resp.status_code != 200:
    print(f'Failed to get file: {file_resp.text}')
    exit(1)
file_content_b64 = file_resp.json()['content']
file_content = base64.b64decode(file_content_b64).decode()
print(f'Buggy file content ({len(file_content)} chars):')
print(file_content[:200] + '...')

# 3. Get the PR diff / list changed files
files_resp = requests.get(
    f'https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/files',
    headers=headers,
)
changed_files = files_resp.json() if files_resp.status_code == 200 else []
all_files = [f['filename'] for f in changed_files]
print(f'Changed files in PR: {all_files}')

# 4. Send to FastAPI for fix
bug_description = f"Multiple syntax errors in {file_path}: missing colons after for-loop and if-statement, missing closing parenthesis in return statement."

fastapi_payload = {
    'project_id': f'repo_auto_pr_{PR_NUMBER}',
    'repository_full_name': REPO,
    'pull_request_number': PR_NUMBER,
    'bug_description': bug_description,
    'buggy_file_content': file_content,
    'target_language': 'python',
    'installation_access_token': token,
    'base_branch': base_branch,
    'target_file_path': file_path,
    'latest_commit_sha': head_sha,
}

print(f'\nSending to FastAPI...')
try:
    resp = requests.post('http://fastapi-brain:8010/api/v1/verify-infrastructure', json=fastapi_payload, timeout=120)
    print(f'Status: {resp.status_code}')
    result = resp.json()
    print(f'Result status: {result.get("status")}')
    print(f'Message: {result.get("message")}')
    if 'comment_result' in result:
        print(f'Comment: {result["comment_result"]}')
    if 'pr_result' in result:
        print(f'PR: {result["pr_result"]}')
    if 'logs' in result:
        print(f'\nTest logs:\n{result["logs"][:500]}')
except Exception as e:
    print(f'Error: {e}')
