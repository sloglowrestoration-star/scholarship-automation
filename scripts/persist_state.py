"""Commit updated state files back to GitHub.

Prefers `git` CLI when running inside a clone of the target repo (no token
needed beyond whatever git is configured with). Falls back to the GitHub
Contents API when git is unavailable or the working tree is not the repo —
this requires GITHUB_PAT with contents:write on the repo.
"""
from __future__ import annotations
import base64
import json
import os
import subprocess
import sys
from pathlib import Path
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
    """Update state/seen-scholarships.json (full replace) and state/run-log.md (append).

    Tries git CLI first; falls back to the Contents API on any git failure.
    """
    seen_text = json.dumps(seen_scholarships, indent=2) + "\n"
    if _try_git_commit(owner=owner, repo=repo, branch=branch,
                       seen_text=seen_text, run_log_append=run_log_append):
        return
    _api_commit(pat=pat, owner=owner, repo=repo, branch=branch,
                seen_text=seen_text, run_log_append=run_log_append)


def _try_git_commit(*, owner: str, repo: str, branch: str,
                    seen_text: str, run_log_append: str) -> bool:
    """Commit state via git CLI if cwd is a clone of owner/repo. Returns True on success."""
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL, text=True, timeout=10,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False
    expected_suffix = f"{owner}/{repo}".lower()
    try:
        remote = subprocess.check_output(
            ["git", "-C", root, "remote", "get-url", "origin"],
            stderr=subprocess.DEVNULL, text=True, timeout=10,
        ).strip().lower()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    if expected_suffix not in remote:
        return False
    root_path = Path(root)
    seen_path = root_path / "state" / "seen-scholarships.json"
    log_path = root_path / "state" / "run-log.md"
    seen_path.write_text(seen_text, encoding="utf-8")
    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else RUN_LOG_HEADER
    if existing and not existing.endswith("\n"):
        existing += "\n"
    log_path.write_text(existing + run_log_append, encoding="utf-8")
    try:
        subprocess.check_call(["git", "-C", root, "add", "state/seen-scholarships.json", "state/run-log.md"], timeout=15)
        # Skip commit if nothing changed
        status = subprocess.check_output(["git", "-C", root, "status", "--porcelain"], text=True, timeout=10)
        if not status.strip():
            return True
        subprocess.check_call(
            ["git", "-C", root, "commit", "-m", "state: scheduled run update"],
            timeout=30,
        )
        subprocess.check_call(["git", "-C", root, "push", "origin", branch], timeout=60)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def _api_commit(*, pat: str, owner: str, repo: str, branch: str,
                seen_text: str, run_log_append: str) -> None:
    _put_file(
        pat=pat, owner=owner, repo=repo, branch=branch,
        path="state/seen-scholarships.json",
        new_content=seen_text,
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
