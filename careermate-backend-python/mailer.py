# mailer.py
# Sends the contact form's message as an email using plain SMTP. Works with
# Gmail (with an app password), Outlook, or any transactional email service
# that exposes SMTP credentials (SendGrid, Mailgun, Resend, Postmark, etc).
#
# If SMTP_HOST isn't set, sending is skipped (and logged) rather than
# raising — the message still gets saved to the database either way, so a
# missing mail config never breaks the contact form for the visitor.

import os
import smtplib
from email.message import EmailMessage


def send_contact_email(name: str, email: str, message: str) -> bool:
    host = os.environ.get("SMTP_HOST")
    if not host:
        print("[mailer] SMTP_HOST not set — skipping email send (message was still saved).")
        return False

    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")
    receiver = os.environ.get("CONTACT_RECEIVER_EMAIL", "hello@careermate.app")
    mail_from = os.environ.get("MAIL_FROM", user or receiver)

    msg = EmailMessage()
    msg["Subject"] = f"New CareerMate contact form message from {name}"
    msg["From"] = mail_from
    msg["To"] = receiver
    # Replying to the email goes straight back to the visitor, not to mail_from.
    msg["Reply-To"] = email
    msg.set_content(
        f"New message from the CareerMate contact form:\n\n"
        f"Name:  {name}\n"
        f"Email: {email}\n\n"
        f"Message:\n{message}\n"
    )

    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.starttls()
            if user and password:
                server.login(user, password)
            server.send_message(msg)
        return True
    except Exception as exc:  # noqa: BLE001 — log and degrade gracefully
        print(f"[mailer] Failed to send contact email: {exc}")
        return False
