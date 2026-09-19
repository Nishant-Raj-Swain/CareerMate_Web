# auth.py
# Registration, login, logout and "who am I" endpoints.

import re

import bcrypt
from flask import Blueprint, request, jsonify, g

from db import get_db
from auth_utils import sign_token, set_auth_cookie, require_auth
from limiter import limiter

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@auth_bp.post("/register")
@limiter.limit("20 per 15 minutes")
def register():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are all required."}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Enter a valid email address."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        db.close()
        return jsonify({"error": "An account with that email already exists."}), 409

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    cursor = db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash),
    )
    db.commit()
    user = {"id": cursor.lastrowid, "name": name, "email": email}
    db.close()

    token = sign_token(user)
    resp = jsonify({"user": user})
    set_auth_cookie(resp, token)
    return resp, 201


@auth_bp.post("/login")
@limiter.limit("20 per 15 minutes")
def login():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    db = get_db()
    row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    db.close()

    if not row or not bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
        return jsonify({"error": "Incorrect email or password."}), 401

    user = {"id": row["id"], "name": row["name"], "email": row["email"]}
    token = sign_token(user)
    resp = jsonify({"user": user})
    set_auth_cookie(resp, token)
    return resp


@auth_bp.post("/logout")
def logout():
    resp = jsonify({"ok": True})
    resp.delete_cookie("cm_token")
    return resp


@auth_bp.get("/me")
@require_auth
def me():
    return jsonify({"user": g.user})
