# CareerMate Backend (Python / Flask)

The same API as the Node version, rewritten in Flask: real registration and
login with hashed passwords and session cookies, plus a contact-form
endpoint. Data lives in a local SQLite file — nothing extra to install.

## 1. Set up a virtual environment and install dependencies

```bash
cd careermate-backend-python
python -m venv venv

# activate it
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

## 2. Configure

```bash
cp .env.example .env
```

Open `.env` and set:
- `JWT_SECRET` — a long random string. Generate one with:
  ```bash
  python -c "import secrets; print(secrets.token_hex(48))"
  ```
- `CLIENT_ORIGIN` — the exact URL your frontend is served from (e.g.
  `http://localhost:5500`). Cookies only get sent back if this matches.

## 3. Run

```bash
python app.py
```

You should see the Flask dev server start on `http://localhost:4000`. A
SQLite file is created automatically at `data/careermate.db` the first time
you start the server.

For production, don't use the built-in dev server — run it behind
something like `gunicorn`:

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:4000 app:app
```

## API reference

Identical shape to the Node version. All responses are JSON. Auth
endpoints set/read an **httpOnly cookie** (`cm_token`), so the frontend
must call `fetch` with `credentials: "include"`.

| Method | Endpoint              | Body                        | Notes                            |
|--------|-----------------------|------------------------------|------------------------------------|
| POST   | `/api/auth/register`  | `{ name, email, password }` | Creates a user, logs them in       |
| POST   | `/api/auth/login`     | `{ email, password }`       | Logs an existing user in           |
| POST   | `/api/auth/logout`    | —                            | Clears the session cookie          |
| GET    | `/api/auth/me`        | —                            | Returns the logged-in user or 401  |
| POST   | `/api/contact`        | `{ name, email, message }`  | Stores a contact-form message      |
| GET    | `/api/health`         | —                            | Simple uptime check                |

Errors look like `{ "error": "..." }` with an appropriate status code (400
validation, 401 auth, 409 duplicate email, 429 rate-limited, 500 server
error). Login/register are limited to 20 attempts / 15 minutes per IP,
contact to 10 messages / 15 minutes per IP.

## 4. Point the frontend at it

Same drop-in JavaScript as the Node version — the API shape is identical.
In `careermate.html`, replace the `localStorage`-based `doLogin` /
`doRegister` / contact-form handlers with `fetch` calls to
`http://localhost:4000/api/...`, using `credentials: "include"`. See the
Node backend's README for the exact snippets — they work unchanged against
this Flask API.

## Deploying on Render

1. Push this `backend/` folder to a GitHub repo (can be the same repo as
   the frontend, in its own subfolder).
2. On [render.com](https://render.com): **New +** → **Web Service** → connect
   the repo → set **Root Directory** to `backend` (skip this if the repo
   root *is* the backend).
3. Render should auto-detect Python. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT`
   - **Instance Type:** Free is fine to start.
4. Under **Environment**, add:
   - `JWT_SECRET` — click "Generate" or paste your own long random string
   - `CLIENT_ORIGIN` — the exact URL your frontend will be served from
     (you'll get/confirm this after deploying the frontend — you can
     redeploy this env var later)
   - `FLASK_ENV` = `production`
5. Click **Create Web Service**. Render builds and starts it, then gives
   you a URL like `https://careermate-backend.onrender.com`. Visit
   `<that-url>/api/health` to confirm it's live.
6. Point your frontend's `API` constant at that URL.

A ready-made `render.yaml` is included if you'd rather deploy via Render's
**Blueprint** feature (New + → Blueprint) instead of the manual steps above.

### ⚠️ Important: the free tier's disk is not persistent

Render's free web services use an **ephemeral filesystem** — every deploy,
restart, or scale-to-zero wipes it, including `data/careermate.db`. That's
fine for testing, but any accounts people register will disappear.

For real user data you need one of:
- A **paid instance type** with a **persistent disk** attached (see the
  commented-out `disk:` block in `render.yaml`) — the SQLite file then
  survives restarts.
- Or switch to **Render's managed Postgres** (has a free tier). This means
  swapping `sqlite3` in `db.py` for `psycopg2` — the queries in this
  project are simple enough that little else needs to change. Ask if you'd
  like this rewritten for Postgres.

### Cross-origin cookies

If your frontend and backend end up on two different Render URLs (e.g.
`careermate.onrender.com` and `careermate-backend.onrender.com`), the login
cookie needs `SameSite=None; Secure` to survive the cross-site request —
`auth_utils.py` already does this automatically when `FLASK_ENV=production`.
Just make sure `CLIENT_ORIGIN` on the backend exactly matches your
frontend's real URL (including `https://`), or the browser will reject it.

## Other hosts

Works the same way on Railway, Fly.io, a VPS, or PythonAnywhere — the
`Procfile` (`gunicorn app:app`) is the standard entry point most of them
expect.

## Project structure

```
careermate-backend-python/
├── data/                 # SQLite file lives here (created automatically)
├── app.py                # app entry point
├── auth.py                # register / login / logout / me routes
├── auth_utils.py           # JWT signing/verification + @require_auth decorator
├── contact.py              # contact form route
├── db.py                   # opens the DB, creates tables
├── limiter.py               # shared rate limiter
├── requirements.txt
├── Procfile               # tells Render/other hosts how to start the app
├── render.yaml             # optional: Render Blueprint config
├── .env.example
└── README.md
```
