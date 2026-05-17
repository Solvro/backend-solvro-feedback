import logging
from urllib.parse import urlparse

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def parse_repo_url(repo_url: str) -> tuple[str, str]:
    parsed = urlparse(repo_url.rstrip("/"))
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) < 2:
        raise ValueError(f"Invalid GitHub repo URL: {repo_url}")
    return path_parts[0], path_parts[1]


def create_github_issue(repo_url: str, title: str, body: str) -> dict:
    if not settings.GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN is not configured")

    owner, repo = parse_repo_url(repo_url)
    url = f"{settings.GITHUB_API_URL}/repos/{owner}/{repo}/issues"

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    payload = {
        "title": title,
        "body": body,
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    return {
        "number": data["number"],
        "html_url": data["html_url"],
    }
