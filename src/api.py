"""GitHub REST API wrapper — all calls cached via st.cache_data (5-min TTL)."""
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Union

import requests
import streamlit as st


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get(url: str, token: str, raw: bool = False) -> Any:
    headers = _headers(token)
    if raw:
        headers["Accept"] = "application/vnd.github.raw"
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text if raw else resp.json()


def _all_pages(path: str, token: str, limit: int = 500) -> list:
    results: list = []
    url = f"https://api.github.com{path}{'&' if '?' in path else '?'}per_page=100"
    while url and len(results) < limit:
        resp = requests.get(url, headers=_headers(token), timeout=15)
        if not resp.ok:
            break
        results.extend(resp.json())
        match = re.search(r'<([^>]+)>;\s*rel="next"', resp.headers.get("Link", ""))
        url = match.group(1) if match else None
    return results


@st.cache_data(ttl=300, show_spinner=False)
def fetch_repo(repo: str, token: str) -> dict:
    return _get(f"https://api.github.com/repos/{repo}", token)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_languages(repo: str, token: str) -> dict:
    return _get(f"https://api.github.com/repos/{repo}/languages", token)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_contributors(repo: str, token: str) -> list:
    return _all_pages(f"/repos/{repo}/contributors", token)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_commits(repo: str, token: str, days: int = 30) -> list:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    return _all_pages(f"/repos/{repo}/commits?since={since}", token, limit=500)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_contributor_stats(repo: str, token: str) -> list:
    """GitHub returns 202 while it computes stats — retry with backoff."""
    url = f"https://api.github.com/repos/{repo}/stats/contributors"
    for attempt in range(5):
        resp = requests.get(url, headers=_headers(token), timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data:           # 200 with [] also means "still computing"
                return data
        time.sleep(2 * (attempt + 1))   # 2,4,6,8,10s → up to 30s total
    return []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_commit_detail(repo: str, sha: str, token: str) -> dict:
    """Single-commit detail — includes stats.{additions, deletions, total}."""
    try:
        return _get(f"https://api.github.com/repos/{repo}/commits/{sha}", token)
    except Exception:
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_contents(repo: str, token: str, path: str = "") -> Union[list, dict]:
    try:
        return _get(f"https://api.github.com/repos/{repo}/contents/{path}", token)
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_raw_file(url: str, token: str) -> str:
    try:
        return _get(url, token, raw=True)
    except Exception:
        return ""


@st.cache_data(ttl=60, show_spinner=False)
def fetch_workflow_runs(repo: str, token: str) -> list:
    """Most recent run per workflow name."""
    try:
        data = _get(
            f"https://api.github.com/repos/{repo}/actions/runs?per_page=30", token
        )
        runs = data.get("workflow_runs", []) if isinstance(data, dict) else []
        seen: dict = {}
        for run in runs:
            name = run.get("name", "")
            if name and name not in seen:
                seen[name] = run
        return list(seen.values())
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_tree(repo: str, token: str) -> list:
    """Return every file blob in the repo's default branch as a flat list."""
    try:
        repo_info  = _get(f"https://api.github.com/repos/{repo}", token)
        branch     = repo_info.get("default_branch", "main")
        branch_obj = _get(f"https://api.github.com/repos/{repo}/branches/{branch}", token)
        sha        = branch_obj["commit"]["commit"]["tree"]["sha"]
        tree       = _get(
            f"https://api.github.com/repos/{repo}/git/trees/{sha}?recursive=1", token
        )
        return [e for e in tree.get("tree", []) if e.get("type") == "blob"]
    except Exception:
        return []
