import django; django.setup()
from dashboard.github_auth import refresh_installation_access_token
import requests
import base64

INSTALLATION_ID = '139799081'
REPO = 'hirwalandry/AI-DEVOPS-ENGINE'
PR_NUMBER = 6

token = refresh_installation_access_token(INSTALLATION_ID)
headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github+json',
}

# Get PR details
pr_resp = requests.get(f'https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}', headers=headers)
pr_data = pr_resp.json()
head_sha = pr_data['head']['sha']
base_branch = pr_data['base']['ref']
print(f'PR #{PR_NUMBER}: head={head_sha[:7]}, base={base_branch}')

# Get buggy file
file_path = 'math_utils.py'
file_resp = requests.get(
    f'https://api.github.com/repos/{REPO}/contents/{file_path}?ref={pr_data["head"]["ref"]}',
    headers=headers,
)
file_content = base64.b64decode(file_resp.json()['content']).decode()
print(f'Buggy file ({len(file_content)} chars)')

# Trigger FastAPI
fastapi_payload = {
    'project_id': f'repo_auto_pr_{PR_NUMBER}',
    'repository_full_name': REPO,
    'pull_request_number': PR_NUMBER,
    'bug_description': 'Multiple syntax errors in math_utils.py: missing colons after if, else, elif statements across three functions (is_even, factorial, fibonacci).',
    'buggy_file_content': file_content,
    'target_language': 'python',
    'installation_access_token': token,
    'base_branch': base_branch,
    'target_file_path': file_path,
    'latest_commit_sha': head_sha,
}

print(f'Sending to FastAPI...')
resp = requests.post('http://fastapi-brain:8010/api/v1/verify-infrastructure', json=fastapi_payload, timeout=120)
result = resp.json()
print(f'Status: {resp.status_code}')
print(f'Result: {result.get("status")}')
print(f'Message: {result.get("message")}')
if 'comment_result' in result:
    print(f'Comment URL: {result["comment_result"]}')
if 'logs' in result:
    print(f'\nTest logs:\n{result["logs"][:500]}')
