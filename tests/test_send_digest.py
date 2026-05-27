from __future__ import annotations
from unittest.mock import MagicMock, patch
from scripts.send_digest import send_digest


def test_send_digest_calls_smtp_with_credentials_and_body():
    fake_smtp = MagicMock()
    fake_smtp_ctx = MagicMock()
    fake_smtp_ctx.__enter__.return_value = fake_smtp
    fake_smtp_ctx.__exit__.return_value = False
    with patch("scripts.send_digest.smtplib.SMTP_SSL", return_value=fake_smtp_ctx) as smtp_cls:
        send_digest(
            sender_address="brody.internships@gmail.com",
            sender_password="fake-app-password",
            recipient="imajedimastr@gmail.com",
            subject="Scholarship Digest — 2026-05-27",
            body_text="Hello world\n",
        )
    smtp_cls.assert_called_once_with("smtp.gmail.com", 465)
    fake_smtp.login.assert_called_once_with(
        "brody.internships@gmail.com", "fake-app-password"
    )
    fake_smtp.send_message.assert_called_once()
    sent_msg = fake_smtp.send_message.call_args[0][0]
    assert sent_msg["Subject"] == "Scholarship Digest — 2026-05-27"
    assert sent_msg["From"] == "brody.internships@gmail.com"
    assert sent_msg["To"] == "imajedimastr@gmail.com"
    assert "Hello world" in sent_msg.get_content()


def test_send_digest_handles_unicode_in_body():
    fake_smtp = MagicMock()
    fake_smtp_ctx = MagicMock()
    fake_smtp_ctx.__enter__.return_value = fake_smtp
    fake_smtp_ctx.__exit__.return_value = False
    with patch("scripts.send_digest.smtplib.SMTP_SSL", return_value=fake_smtp_ctx):
        send_digest(
            sender_address="x@example.com",
            sender_password="p",
            recipient="y@example.com",
            subject="Test subject",
            body_text="Body with accents: e accent\n",
        )
    sent_msg = fake_smtp.send_message.call_args[0][0]
    assert "accents" in sent_msg.get_content()
