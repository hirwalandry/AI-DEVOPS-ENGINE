import time
import jwt
import requests
from django.conf import settings
from django.db import transaction
from .models import GitHubIntegration


def generate_github_app_jwt() -> str:
    issued_at = int(time.time()) - 60
    expires_at = issued_at + (10 * 60)

    payload = {
        "iat": issued_at,
        "exp": expires_at,
        "iss": settings.GITHUB_APP_IDENTIFIER,
    }

    with open(settings.GITHUB_APP_PRIVATE_KEY_PATH, "r") as key_file:
        private_key = key_file.read()

    return jwt.encode(payload, private_key, algorithm="RS256")


def refresh_installation_access_token(installation_id: str) -> str:
    app_jwt = generate_github_app_jwt()

    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"

    response = requests.post(url, headers=headers)
    if response.status_code != 201:
        raise Exception(f"Failed to authenticate secure installation context: {response.text}")

    token_data = response.json()
    token = token_data["token"]

    with transaction.atomic():
        integration = GitHubIntegration.objects.get(installation_id=installation_id)
        integration.encrypted_access_token = token
        integration.save()

    return token
