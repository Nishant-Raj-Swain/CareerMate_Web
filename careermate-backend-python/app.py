# app.py
# Entry point. Wires up extensions and mounts the route blueprints.

import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify
from flask_cors import CORS

from db import init_db
from limiter import limiter
from auth import auth_bp
from contact import contact_bp


def create_app():
    app = Flask(__name__)

    # Fail fast if the secret hasn't been set — better than signing
    # tokens with a weak default.
    if not os.environ.get("JWT_SECRET"):
        raise RuntimeError(
            "JWT_SECRET is not set. Copy .env.example to .env and fill it in."
        )

    CORS(
        app,
        supports_credentials=True,
        origins=[os.environ.get("CLIENT_ORIGIN", "http://localhost:5500")],
    )

    limiter.init_app(app)
    init_db()

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(contact_bp, url_prefix="/api/contact")

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True, "service": "careermate-backend"})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found."}), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception(e)
        return jsonify({"error": "Something went wrong on our end."}), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4000))
    debug = os.environ.get("FLASK_ENV") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
