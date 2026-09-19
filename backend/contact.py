# contact.py
# Stores messages from the site's contact form.

import re

from flask import Blueprint, request, jsonify

from db import get_db
from limiter import limiter

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

    return jsonify({"ok": True}), 201
