"""Commit updated state files back to GitHub via the Contents API."""
from __future__ import annotations
import base64
import json
import sys
from typing import Any
import requests

API_BASE = "https://api.github.com"
RUN_LOG_HEADER = "# Run log\n"


def commit_state_files(
    *,
    pat: str,
    owner: str,
    repo: str,
    branch: str,
    seen_scholarships: dict[str, Any],
    run_log_append: str,
) -> None:
    """Update state/seen-scholarships.json (full replace) and state/run-log.md (append)."""
    _put_file(
        pat=pat, owner=owner, repo=repo, branch=branch,
        path="state/seen-scholarships.json",
        new_content=json.dumps(seen_scholarships, indent=2) + "\n",
        commit_message="state: update seen-scholarships",
    )
    existing = _get_file_text(pat, owner, repo, "state/run-log.md")
    if existing is None:
        existing = RUN_LOG_HEADER
    elif not existing.endswith("\n"):
        existing += "\n"
    new_log = existing + run_log_append
    _put_file(
        pat=pat, owner=owner, repo=repo, branch=branch,
        path="state/run-log.md",
        new_content=new_log,
        commit_message="state: append run log",
    )


def _get_file_text(pat: str, owner: str, repo: str, path: str) -> str | None:
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}"
    resp = requests.get(url, headers=_headers(pat), timeout=30)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    payload = resp.json()
    return base64.b64decode(payload["content"]).decode("utf-8")


def _put_file(
    *, pat: str, owner: str, repo: str, branch: str,
    path: str, new_content: str, commit_message: str,
) -> None:
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}"
    sha = _get_sha(pat, owner, repo, path)
    body: dict[str, Any] = {
        "message": commit_message,
        "branch": branch,
        "content": base64.b64encode(new_content.encode("utf-8")).decode("ascii"),
    }
    if sha is not None:
        body["sha"] = sha
    resp = requests.put(url, headers=_headers(pat), json=body, timeout=30)
    resp.raise_for_status()


def _get_sha(pat: str, owner: str, repo: str, path: str) -> str | None:
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}"
    resp = requests.get(url, headers=_headers(pat), timeout=30)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()["sha"]


def _headers(pat: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def main() -> int:
    from dotenv import load_dotenv
    import os
    load_dotenv()
    if len(sys.argv) < 3:
        print("usage: persist_state <seen_json_path> <run_log_append_path>", file=sys.stderr)
        return 2
    with open(sys.argv[1], encoding="utf-8") as f:
        seen = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f:
        append = f.read()
    commit_state_files(
        pat=os.environ["GITHUB_PAT"],
        owner=os.environ["GITHUB_REPO_OWNER"],
        repo=os.environ["GITHUB_REPO_NAME"],
        branch=os.environ.get("GITHUB_BRANCH", "main"),
        seen_scholarships=seen,
        run_log_append=append,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
