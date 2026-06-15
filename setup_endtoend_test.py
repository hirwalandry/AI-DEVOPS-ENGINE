import django; django.setup()
from dashboard.github_auth import refresh_installation_access_token
import requests
import base64
import time
import os

INSTALLATION_ID = '139799081'
REPO = 'hirwalandry/AI-DEVOPS-ENGINE'

token = refresh_installation_access_token(INSTALLATION_ID)
print(f'Token acquired: {token[:15]}...')

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github+json',
}

# 1. Get the default branch SHA
default_branch = 'main'
ref_resp = requests.get(
    f'https://api.github.com/repos/{REPO}/git/ref/heads/{default_branch}',
    headers=headers,
)
if ref_resp.status_code != 200:
    print(f'Failed to get ref: {ref_resp.text}')
    exit(1)
base_sha = ref_resp.json()['object']['sha']
print(f'Base SHA: {base_sha[:7]}')

# 2. Create a new branch
branch_name = f'bug-test/end-to-end-{int(time.time())}'
branch_resp = requests.post(
    f'https://api.github.com/repos/{REPO}/git/refs',
    json={'ref': f'refs/heads/{branch_name}', 'sha': base_sha},
    headers=headers,
)
if branch_resp.status_code != 201:
    print(f'Failed to create branch: {branch_resp.text}')
    exit(1)
print(f'Branch created: {branch_name}')

# 3. Create a buggy Python file
buggy_code = '''def calculate_total(items):
    total = 0
    for item in items
        total += item["price"]
    return total

def apply_discount(total, discount):
    if discount > 0
        return total - (total * discount
    return total
'''

file_path = 'e2e_test_buggy.py'
content_b64 = base64.b64encode(buggy_code.encode()).decode()

put_resp = requests.put(
    f'https://api.github.com/repos/{REPO}/contents/{file_path}',
    json={
        'message': 'test: add buggy file for E2E pipeline test',
        'content': content_b64,
        'branch': branch_name,
    },
    headers=headers,
)
if put_resp.status_code not in (200, 201):
    print(f'Failed to create file: {put_resp.text}')
    exit(1)
file_sha = put_resp.json()['content']['sha']
print(f'Buggy file created: {file_path} (sha: {file_sha[:7]})')

# 4. Create a PR
pr_title = 'test: E2E pipeline verification — buggy file with syntax errors'
pr_body = 'This PR adds a file with intentional syntax errors (missing colons). The AI DevOps bot should detect, fix, and post a comment with the corrected code.'

pr_resp = requests.post(
    f'https://api.github.com/repos/{REPO}/pulls',
    json={
        'title': pr_title,
        'head': branch_name,
        'base': default_branch,
        'body': pr_body,
        'maintainer_can_modify': True,
    },
    headers=headers,
)
if pr_resp.status_code != 201:
    print(f'Failed to create PR: {pr_resp.text}')
    exit(1)
pr_number = pr_resp.json()['number']
pr_url = pr_resp.json()['html_url']
print(f'\n=== PR CREATED ===')
print(f'PR #{pr_number}: {pr_url}')
print(f'Branch: {branch_name}')
print(f'File:   {file_path}')
print('\nNow waiting for the pipeline to trigger...')
print(f'Watch: {pr_url}')
