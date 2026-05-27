from __future__ import annotations
import base64
import json
import requests_mock as req_mock_module
from scripts.persist_state import commit_state_files


def test_commit_writes_seen_scholarships_and_run_log():
    seen_data = {"version": 1, "last_run_iso": "2026-05-27T16:00:00Z", "entries": []}
    run_log_append = "\n## 2026-05-27\n- 0 new, 0 deadline reminders\n"
    with req_mock_module.Mocker() as m:
        m.get(
            "https://api.github.com/repos/owner/repo/contents/state/run-log.md",
            json={
                "sha": "existing-sha",
                "content": base64.b64encode(b"# Run log\n").decode(),
            },
        )
        m.get(
            "https://api.github.com/repos/owner/repo/contents/state/seen-scholarships.json",
            status_code=404,
        )
        m.put(
            "https://api.github.com/repos/owner/repo/contents/state/seen-scholarships.json",
            json={"content": {"sha": "new-sha-1"}},
        )
        m.put(
            "https://api.github.com/repos/owner/repo/contents/state/run-log.md",
            json={"content": {"sha": "new-sha-2"}},
        )
        commit_state_files(
            pat="fake-pat",
            owner="owner",
            repo="repo",
            branch="main",
            seen_scholarships=seen_data,
            run_log_append=run_log_append,
        )
    put_history = [r for r in m.request_history if r.method == "PUT"]
    assert len(put_history) == 2
    run_log_put = next(r for r in put_history if "run-log.md" in r.url)
    body = json.loads(run_log_put.text)
    decoded = base64.b64decode(body["content"]).decode()
    assert decoded.startswith("# Run log\n")
    assert "2026-05-27" in decoded


def test_commit_handles_first_run_with_no_existing_run_log():
    with req_mock_module.Mocker() as m:
        m.get(
            "https://api.github.com/repos/owner/repo/contents/state/run-log.md",
            status_code=404,
        )
        m.get(
            "https://api.github.com/repos/owner/repo/contents/state/seen-scholarships.json",
            status_code=404,
        )
        m.put(
            "https://api.github.com/repos/owner/repo/contents/state/seen-scholarships.json",
            json={"content": {"sha": "x"}},
        )
        m.put(
            "https://api.github.com/repos/owner/repo/contents/state/run-log.md",
            json={"content": {"sha": "y"}},
        )
        commit_state_files(
            pat="fake-pat",
            owner="owner",
            repo="repo",
            branch="main",
            seen_scholarships={"version": 1, "last_run_iso": None, "entries": []},
            run_log_append="## 2026-05-27\n- first run\n",
        )
    put_history = [r for r in m.request_history if r.method == "PUT"]
    run_log_put = next(r for r in put_history if "run-log.md" in r.url)
    body = json.loads(run_log_put.text)
    decoded = base64.b64decode(body["content"]).decode()
    assert decoded.startswith("# Run log\n")
    assert "first run" in decoded
