# MotoBid — Bike Auction Platform

A Flask-based motorcycle auction application built for the Software Engineering Internship assignment. Includes account registration/login, admin-managed listings, scheduled/live/ended/cancelled auction states, validated bidding, live bid broadcasts, audit events, health/metrics endpoints, tests, Docker packaging, and architecture/deployment documentation.

> **Important:** This is an internship-assignment implementation, not a certified real-money marketplace. Sample motorcycles are demonstration content, not verified advertisements. Before public production use, complete the hardening items in `docs/ASSUMPTIONS_AND_TRADEOFFS.md` (payment/escrow, legal terms, verified vehicle/seller workflow, stronger concurrency guarantees and monitoring).

## Features

- Responsive buyer experience: browse/search/filter auctions, motorcycle detail/specifications, recent bids, registration and login.
- Auction lifecycle: scheduled → live → ended; admin can cancel non-ended listings. Status is recalculated when auctions are viewed or the API is queried.
- Bidding: authenticated buyers only, integer INR amounts, minimum increment, cannot bid on own listing, database transaction, audit event and Socket.IO update to viewers of that auction.
- Admin console: create auctions, cancel listings, review activity audit trail.
- Security fundamentals: password hashing, CSRF protection on forms, role checks, basic security headers, bounded request body, environment-based secrets, no user-supplied HTML rendering.
- Operations: `/health`, `/metrics`, rotating app log, request ID response header, pytest suite, Docker and Compose.

## Demo access

Local default admin: `admin@bikeauction.local` / `ChangeMe123!`

**Change this password and `SECRET_KEY` before deployment.** Demo credentials are only for a local instance. Sample listings are automatically created on first database initialization.

## Quick start (Linux)

1. Install Python 3.11+ and pip. In a terminal, enter the project directory.
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Set environment variables (recommended):
   ```bash
   cp .env.example .env
   # Edit .env and set a unique SECRET_KEY and ADMIN_PASSWORD.
   set -a; source .env; set +a
   ```
5. Start the app:
   ```bash
   python run.py
   ```
6. Open `http://127.0.0.1:5000`. Admin dashboard: log in with the admin credentials, then choose **Admin**. Health check: `http://127.0.0.1:5000/health`.
7. Run tests:
   ```bash
   pytest -q
   ```

## Docker quick start

```bash
cp .env.example .env
# Edit .env: use a long random SECRET_KEY and a strong ADMIN_PASSWORD.
docker compose up --build -d
docker compose logs -f web
```
Open `http://127.0.0.1:5000`. Stop with `docker compose down`; the database volume is retained. `docker compose down -v` also deletes that data.

## Project layout

```text
app/
  __init__.py       app factory, extensions, health/metrics, security headers
  models.py         User, Auction, Bid, AuditLog models
  auth.py           registration/login/logout
  auctions.py       auction browse/detail/API/bidding/Socket.IO room
  admin.py          admin console and auction management
  templates/        server-rendered accessible HTML templates
  static/           responsive CSS and real-time browser client
 tests/              pytest coverage for core flows
 docs/               architecture, deployment, assumptions/trade-offs
 Dockerfile
 docker-compose.yml
 run.py
```

## API and operational endpoints

- `GET /api/auctions` — JSON snapshot of auctions and calculated status.
- `GET /health` — checks the database connection; returns HTTP 200 or 503.
- `GET /metrics` — basic counts as JSON. Restrict access at the reverse proxy before exposing publicly; this is not a Prometheus exporter.
- `POST /auctions/<id>/bid` — authenticated form action protected by CSRF.

## Deployment status

This package is deploy-ready but is **not yet hosted on a public URL**. A public deployment requires a hosting account and your explicit deployment steps. See `docs/DEPLOYMENT.md`; do not publish the default credentials.
