"""Send a plain-text digest email via Gmail SMTP."""
from __future__ import annotations
import smtplib
import sys
from email.message import EmailMessage


def send_digest(
    *,
    sender_address: str,
    sender_password: str,
    recipient: str,
    subject: str,
    body_text: str,
) -> None:
    msg = EmailMessage()
    msg["From"] = sender_address
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body_text, charset="utf-8")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_address, sender_password)
        smtp.send_message(msg)


def main() -> int:
    """CLI entry — reads body from a file path argv[1], subject from argv[2]."""
    from dotenv import load_dotenv
    import os
    load_dotenv()
    if len(sys.argv) < 3:
        print("usage: send_digest <body_file_path> <subject>", file=sys.stderr)
        return 2
    body_path, subject = sys.argv[1], sys.argv[2]
    with open(body_path, encoding="utf-8") as f:
        body = f.read()
    send_digest(
        sender_address=os.environ["SENDER_GMAIL_ADDRESS"],
        sender_password=os.environ["SENDER_GMAIL_APP_PASSWORD"],
        recipient=os.environ["DIGEST_RECIPIENT"],
        subject=subject,
        body_text=body,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
