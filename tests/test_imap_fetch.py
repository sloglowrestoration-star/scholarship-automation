"""Tests for imap_fetch — fetching labeled messages from Gmail via IMAP.

We stub imaplib at the module level so no network call is made.
"""
from __future__ import annotations
from pathlib import Path
from unittest.mock import MagicMock, patch
from scripts import imap_fetch

FIXTURES = Path(__file__).parent / "fixtures" / "emails"


def _fake_imap_with_messages(eml_paths):
    """Build a MagicMock IMAP4_SSL connection that returns the given .eml fixtures."""
    mock_imap = MagicMock()
    mock_imap.login.return_value = ("OK", [b"Logged in"])
    mock_imap.select.return_value = ("OK", [b"3"])
    ids = b" ".join(str(i + 1).encode() for i in range(len(eml_paths)))
    mock_imap.search.return_value = ("OK", [ids])

    def fake_fetch(msg_id, _spec):
        idx = int(msg_id) - 1
        body = eml_paths[idx].read_bytes()
        return ("OK", [(b"header", body)])

    mock_imap.fetch.side_effect = fake_fetch
    mock_imap.logout.return_value = ("BYE", [b"Logging out"])
    return mock_imap


def test_fetch_returns_records_for_each_eml():
    eml_paths = [
        FIXTURES / "scholarships_com_sample.eml",
        FIXTURES / "fastweb_sample.eml",
        FIXTURES / "calpoly_listserv_sample.eml",
    ]
    fake = _fake_imap_with_messages(eml_paths)
    with patch.object(imap_fetch.imaplib, "IMAP4_SSL", return_value=fake):
        results = imap_fetch.fetch_labeled_messages(
            address="imajedimastr@gmail.com",
            app_password="dummy",
            label="Scholarships",
            since_iso=None,
        )
    assert len(results) == 3
    assert results[0]["message_id"] == "<msg-001@scholarships.com>"
    assert results[1]["message_id"] == "<msg-002@fastweb.com>"
    assert results[2]["message_id"] == "<msg-003@calpoly.edu>"
    assert "Future Engineers of America" in results[0]["body"]


def test_fetch_uses_since_filter_when_provided():
    fake = _fake_imap_with_messages([])
    with patch.object(imap_fetch.imaplib, "IMAP4_SSL", return_value=fake):
        imap_fetch.fetch_labeled_messages(
            address="imajedimastr@gmail.com",
            app_password="dummy",
            label="Scholarships",
            since_iso="2026-05-25T00:00:00Z",
        )
    search_args = fake.search.call_args[0]
    assert any("SINCE" in str(a) for a in search_args)


def test_fetch_returns_empty_list_when_no_messages():
    fake = MagicMock()
    fake.login.return_value = ("OK", [b""])
    fake.select.return_value = ("OK", [b"0"])
    fake.search.return_value = ("OK", [b""])
    fake.logout.return_value = ("BYE", [b""])
    with patch.object(imap_fetch.imaplib, "IMAP4_SSL", return_value=fake):
        results = imap_fetch.fetch_labeled_messages(
            address="imajedimastr@gmail.com",
            app_password="dummy",
            label="Scholarships",
            since_iso=None,
        )
    assert results == []


def test_fetch_records_have_required_fields():
    eml_paths = [FIXTURES / "scholarships_com_sample.eml"]
    fake = _fake_imap_with_messages(eml_paths)
    with patch.object(imap_fetch.imaplib, "IMAP4_SSL", return_value=fake):
        results = imap_fetch.fetch_labeled_messages(
            address="imajedimastr@gmail.com",
            app_password="dummy",
            label="Scholarships",
            since_iso=None,
        )
    record = results[0]
    for field in ("message_id", "sender", "subject", "date", "body"):
        assert field in record, f"missing {field}"
