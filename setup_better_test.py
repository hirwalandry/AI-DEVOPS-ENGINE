import django; django.setup()
from dashboard.github_auth import refresh_installation_access_token
import requests
import base64
import time

INSTALLATION_ID = '139799081'
REPO = 'hirwalandry/AI-DEVOPS-ENGINE'

token = refresh_installation_access_token(INSTALLATION_ID)
headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github+json',
}

# Close the old PR #5
print('Closing old PR #5...')
requests.patch(
    f'https://api.github.com/repos/{REPO}/pulls/5',
    json={'state': 'closed'},
    headers=headers,
)

# Create a realistic buggy Python file
# Missing colons, wrong indentation, missing return
buggy_code = '''def is_even(number):
    if number % 2 == 0
        return True
    else
        return False

def factorial(n):
    if n == 0
        result = 1
    else
        result = n * factorial(n - 1)
    return result

def fibonacci(n):
    if n <= 0
        return []
    elif n == 1
        return [0]
    elif n == 2
        return [0, 1]
    else
        seq = [0, 1]
        for i in range(2, n):
            seq.append(seq[i-1] + seq[i-2])
        return seq
'''

# Create new branch
default_branch = 'main'
ref_resp = requests.get(
    f'https://api.github.com/repos/{REPO}/git/ref/heads/{default_branch}',
    headers=headers,
)
base_sha = ref_resp.json()['object']['sha']
branch_name = f'bug-test/v2-{int(time.time())}'
requests.post(
    f'https://api.github.com/repos/{REPO}/git/refs',
    json={'ref': f'refs/heads/{branch_name}', 'sha': base_sha},
    headers=headers,
)
print(f'Branch: {branch_name}')

# Write buggy file
file_path = 'math_utils.py'
content_b64 = base64.b64encode(buggy_code.encode()).decode()
requests.put(
    f'https://api.github.com/repos/{REPO}/contents/{file_path}',
    json={
        'message': 'test: add math_utils with syntax errors for E2E test',
        'content': content_b64,
        'branch': branch_name,
    },
    headers=headers,
)
print(f'File: {file_path} ({len(buggy_code)} chars)')

# Create PR
pr_resp = requests.post(
    f'https://api.github.com/repos/{REPO}/pulls',
    json={
        'title': '[AI DevOps E2E] math_utils.py with missing colons',
        'head': branch_name,
        'base': default_branch,
        'body': 'This PR adds math_utils.py with intentional syntax errors (missing colons in if/else/elif). The AI DevOps bot should detect, fix, and post a comment with the corrected code.',
        'maintainer_can_modify': True,
    },
    headers=headers,
)
pr_number = pr_resp.json()['number']
pr_url = pr_resp.json()['html_url']
print(f'\n=== PR #{pr_number} ===')
print(f'URL: {pr_url}')
print(f'Waiting 10s for GitHub to index...')
time.sleep(10)

# Get head SHA
pr_data = requests.get(
    f'https://api.github.com/repos/{REPO}/pulls/{pr_number}',
    headers=headers,
).json()
head_sha = pr_data['head']['sha']
print(f'Head SHA: {head_sha}')

# Now trigger FastAPI directly
fastapi_payload = {
    'project_id': f'repo_auto_pr_{pr_number}',
    'repository_full_name': REPO,
    'pull_request_number': pr_number,
    'bug_description': 'Multiple syntax errors in math_utils.py: missing colons after if, else, elif statements throughout three functions (is_even, factorial, fibonacci).',
    'buggy_file_content': buggy_code,
    'target_language': 'python',
    'installation_access_token': token,
    'base_branch': default_branch,
    'target_file_path': file_path,
    'latest_commit_sha': head_sha,
}

print(f'\nSending to FastAPI...')
try:
    resp = requests.post('http://fastapi-brain:8010/api/v1/verify-infrastructure', json=fastapi_payload, timeout=120)
    result = resp.json()
    print(f'Status: {resp.status_code}')
    print(f'Result: {result.get("status")}')
    print(f'Message: {result.get("message")}')
    if 'comment_result' in result:
        print(f'Comment URL: {result["comment_result"]}')
    if 'pr_result' in result:
        print(f'PR Result: {result["pr_result"]}')
    if 'logs' in result:
        logs_preview = result['logs'][:400]
        print(f'\nTest logs:\n{logs_preview}')
except Exception as e:
    print(f'Error: {e}')

print(f'\nWatch the PR: {pr_url}')
