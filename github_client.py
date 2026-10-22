"""Small GitHub REST adapter.  It deliberately reads only public open Issues."""
from __future__ import annotations

import os
from typing import Iterable

import requests

from core import IssueEvidence

API_ROOT = "https://api.github.com"


class GitHubScanError(RuntimeError):
    pass


def fetch_open_issues(repositories: Iterable[str], per_repo: int = 30, token: str | None = None) -> list[IssueEvidence]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "EvidenceScout-MVP",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = token or os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    results: list[IssueEvidence] = []
    for repo in repositories:
        response = requests.get(
            f"{API_ROOT}/repos/{repo}/issues",
            headers=headers,
            params={"state": "open", "per_page": min(per_repo, 100), "sort": "comments", "direction": "desc"},
            timeout=18,
        )
        if response.status_code == 403:
            raise GitHubScanError("GitHub API rate limit reached. Add a personal token in Streamlit secrets or wait before retrying.")
        if response.status_code == 404:
            raise GitHubScanError(f"Repository not found or unavailable: {repo}")
        response.raise_for_status()
        for item in response.json():
            if "pull_request" in item:
                continue
            reactions = sum(item.get("reactions", {}).get(key, 0) for key in ("+1", "heart", "rocket", "eyes"))
            results.append(IssueEvidence(
                repo=repo,
                number=item["number"],
                title=item.get("title", "Untitled issue"),
                body=item.get("body") or "",
                url=item["html_url"],
                comments=item.get("comments", 0),
                reactions=reactions,
                created_at=item.get("created_at", ""),
                labels=tuple(label["name"] for label in item.get("labels", [])),
            ))
    return results
