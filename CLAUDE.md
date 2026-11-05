# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Frontend
```bash
cd frontend
npm install       # first time
npm run dev       # dev server on :5173 (proxies /api → :8000)
npm run build     # output to frontend/dist/
npm run preview   # preview production build
```

### Backend
```bash
cd backend
pip install -r requirements.txt   # first time
uvicorn main:app --reload         # dev server on :8000
```

## Architecture

Single-page portfolio with a vanilla JS/HTML frontend (no framework) and a FastAPI backend.

**Frontend** (`frontend/`) — plain `index.html` + assets, bundled by Vite. Production build outputs to `frontend/dist/`. The frontend is currently fully static: it makes no `/api` calls (no contact form, analytics, or live Medium feed) because the backend is not deployed. Design: beige + forest green with a purple accent, light/dark themes via CSS tokens on `:root`. During development, Vite still proxies `/api/*` to `localhost:8000` if those features are reintroduced.

**Backend** (`backend/`) — FastAPI app split into three routers mounted at:
- `POST /api/contact` — sends email via SendGrid (`contact.py`); falls back to console logging if `SENDGRID_API_KEY` is absent (dev mode). Fields are HTML-escaped before insertion into the email body; name capped at 100 chars, message at 2000 chars.
- `GET  /api/medium` — fetches and parses the Medium RSS feed for `MEDIUM_USERNAME` (default: `kartikkale03`), returns up to N posts with thumbnails and tags.
- `POST /api/analytics/track` — appends JSON events to a `.jsonl` log file; `GET /api/analytics/summary` aggregates counts and requires HTTP Basic Auth (`ANALYTICS_USER` / `ANALYTICS_PASS`). Allowed event types are the `ALLOWED` set in `analytics.py`.

Rate limiting is applied via `slowapi`: 5/hour on contact, 30/minute on analytics tracking.

## Deployment

**Frontend → Vercel**
- `vercel.json` is at the repo root; it builds from `frontend/` and outputs `frontend/dist/`.
- `/api/*` requests are rewritten to the backend URL. Update `vercel.json` with your backend URL before deploying, or set it as a Vercel environment variable.

**Backend → Railway / Render**
- `backend/Procfile` contains the start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Set all environment variables in the platform dashboard (see `backend/.env.example`).
- Point `ALLOWED_ORIGINS` to your Vercel frontend URL in production.

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in values:

```
SENDGRID_API_KEY=       # omit for dev (emails print to console)
CONTACT_FROM_EMAIL=kartikkale03@gmail.com
CONTACT_TO_EMAIL=kartikkale03@gmail.com
MEDIUM_USERNAME=kartikkale03
ALLOWED_ORIGINS=http://localhost:5173   # comma-separated in prod
ANALYTICS_LOG_PATH=./analytics.jsonl
ANALYTICS_USER=admin
ANALYTICS_PASS=changeme                 # set a strong password in prod
```
