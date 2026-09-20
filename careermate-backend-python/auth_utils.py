# auth_utils.py
# Small helpers shared by the auth routes: signing/verifying the JWT that
# lives in the "cm_token" cookie, and a decorator to protect routes.

import os
from functools import wraps
from datetime import datetime, timedelta, timezone

import jwt
from flask import request, jsonify, g

TOKEN_TTL_DAYS = 7


def sign_token(user):
    payload = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_TTL_DAYS),
    }
    secret = os.environ["JWT_SECRET"]
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_token(token):
    secret = os.environ["JWT_SECRET"]
    return jwt.decode(token, secret, algorithms=["HS256"])


def set_auth_cookie(response, token):
    is_prod = os.environ.get("FLASK_ENV") == "production"

    # On Render, the frontend and backend usually live on different
    # subdomains (e.g. careermate.onrender.com vs careermate-api.onrender.com).
    # Cross-site cookies require SameSite=None + Secure=True, which only
    # works over HTTPS — fine on Render, not on plain http://localhost.
    # Override via env vars if your setup differs from the default.
    secure = os.environ.get("COOKIE_SECURE", "true" if is_prod else "false").lower() == "true"
    samesite = os.environ.get("COOKIE_SAMESITE", "None" if is_prod else "Lax")

    response.set_cookie(
        "cm_token",
        token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=TOKEN_TTL_DAYS * 24 * 60 * 60,
    )


def require_auth(fn):
    """Route decorator: verifies the cm_token cookie and stashes the user
    on flask.g.user, or returns 401 if it's missing/invalid/expired."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.cookies.get("cm_token")
        if not token:
            return jsonify({"error": "Not logged in."}), 401
        try:
            payload = verify_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Session expired. Please log in again."}), 401

        g.user = {"id": payload["id"], "name": payload["name"], "email": payload["email"]}
        return fn(*args, **kwargs)

    return wrapper
