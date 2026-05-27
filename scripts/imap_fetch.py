"""Fetch Gmail messages with a given label via IMAP.

Outputs a list of records:
    {message_id, sender, subject, date, body}
"""
from __future__ import annotations
import email
import imaplib
import json
import sys
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any


def fetch_labeled_messages(
    *,
    address: str,
    app_password: str,
    label: str,
    since_iso: str | None,
) -> list[dict[str, Any]]:
    """Connect to Gmail IMAP, select the label, return all messages as records."""
    conn = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    try:
        conn.login(address, app_password)
        conn.select(f'"{label}"', readonly=True)
        search_args: list[str] = ["ALL"]
        if since_iso:
            since_date = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))
            search_args = ["SINCE", since_date.strftime("%d-%b-%Y")]
        status, data = conn.search(None, *search_args)
        if status != "OK" or not data or not data[0]:
            return []
        msg_ids = data[0].split()
        records: list[dict[str, Any]] = []
        for msg_id in msg_ids:
            status, msg_data = conn.fetch(msg_id, "(RFC822)")
            if status != "OK" or not msg_data:
                continue
            raw = msg_data[0][1]
            records.append(_parse_eml(raw))
        return records
    finally:
        try:
            conn.logout()
        except Exception:
            pass


def _parse_eml(raw_bytes: bytes) -> dict[str, Any]:
    msg = email.message_from_bytes(raw_bytes)
    body = _extract_text_body(msg)
    date_hdr = msg.get("Date", "")
    try:
        date_iso = parsedate_to_datetime(date_hdr).isoformat()
    except Exception:
        date_iso = date_hdr
    return {
        "message_id": msg.get("Message-ID", "").strip(),
        "sender": msg.get("From", "").strip(),
        "subject": msg.get("Subject", "").strip(),
        "date": date_iso,
        "body": body,
    }


def _extract_text_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(
                        part.get_content_charset() or "utf-8", errors="replace"
                    )
        return ""
    payload = msg.get_payload(decode=True)
    if not payload:
        return ""
    return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")


def main() -> int:
    """CLI entry — reads creds from env and prints JSON list to stdout."""
    from dotenv import load_dotenv
    import os
    load_dotenv()
    records = fetch_labeled_messages(
        address=os.environ["IMAJE_GMAIL_ADDRESS"],
        app_password=os.environ["IMAJE_GMAIL_APP_PASSWORD"],
        label=os.environ.get("SCHOLARSHIP_LABEL", "Scholarships"),
        since_iso=os.environ.get("SINCE_ISO"),
    )
    json.dump(records, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
