import requests


class GitHubStatusCheckManager:
    def __init__(self, repository_full_name: str, short_lived_access_token: str):
        self.api_url = f"https://api.github.com/repos/{repository_full_name}/statuses"
        self.headers = {
            "Authorization": f"token {short_lived_access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def update_commit_status(
        self, commit_sha: str, state: str, target_url: str, description: str
    ) -> bool:
        endpoint = f"{self.api_url}/{commit_sha}"

        payload = {
            "state": state,
            "target_url": target_url,
            "description": description[:140],
            "context": "ai-devops/sandbox-validation",
        }

        response = requests.post(endpoint, json=payload, headers=self.headers)
        return response.status_code == 201
