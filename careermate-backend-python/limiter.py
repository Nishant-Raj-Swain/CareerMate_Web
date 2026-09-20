# limiter.py
# A single Flask-Limiter instance shared across the app and route blueprints.
# Created here (unbound) and attached to the app with limiter.init_app(app)
# in app.py, so route files can import `limiter` and use it as a decorator
# without causing circular imports.

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
