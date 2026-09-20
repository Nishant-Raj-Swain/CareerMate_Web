# contact.py
# Stores messages from the site's contact form and emails them to the
# team's inbox.

import re

from flask import Blueprint, request, jsonify

from db import get_db
from limiter import limiter
from mailer import send_contact_email

contact_bp = Blueprint("contact", __name__)

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@contact_bp.post("")
@limiter.limit("10 per 15 minutes")
def send_message():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip().lower()
    message = (body.get("message") or "").strip()

    if not name or not email or not message:
        return jsonify({"error": "Name, email and message are all required."}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Enter a valid email address."}), 400
    if len(message) > 4000:
        return jsonify({"error": "Message is too long."}), 400

    db = get_db()
    db.execute(
        "INSERT INTO messages (name, email, message) VALUES (?, ?, ?)",
        (name, email, message),
    )
    db.commit()
    db.close()

    # Best-effort: the message is already safely stored above, so a mail
    # server hiccup doesn't cost the visitor's submission.
    emailed = send_contact_email(name, email, message)

    return jsonify({"ok": True, "emailed": emailed}), 201
