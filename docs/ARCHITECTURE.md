# Architecture and Design

## Goals

Deliver a maintainable, demonstrable auction workflow with sensible security boundaries, clean separation of routes and data models, observable failures, and a path to a more scalable deployment. The assignment does not prescribe a language, database, hosting provider, payment provider, or exact auction rules; assumptions are recorded separately.

## Component view

```text
Browser (responsive templates + Socket.IO client)
  | HTTPS in deployment / HTTP for local development
  v
Flask application
  ├── Auth routes (registration, login, logout)
  ├── Auction routes (browse, detail, bid, JSON snapshot)
  ├── Admin routes (create/cancel listings, audit view)
  ├── Socket.IO (broadcast new bid to an auction room)
  ├── SQLAlchemy models and transaction boundary
  └── Operational endpoints (/health, /metrics) + application logs
        |
        v
Relational database (SQLite for local demo; PostgreSQL recommended for deployment)
```

## Main entities

- **User**: unique email, password hash, role (`buyer` or `admin`), active flag, creation time.
- **Auction**: motorcycle listing and specifications, starting/current price, increment, start/end timestamps, status, seller and optional winner.
- **Bid**: immutable bid record linking an auction and bidder to an INR amount and timestamp.
- **AuditLog**: actor, action, entity reference, short detail, timestamp.

## Bid request lifecycle

1. Flask-Login verifies the session; CSRFProtect validates the form token.
2. The route parses an integer INR amount and loads the auction in a transaction (`FOR UPDATE` where the database supports row locks).
3. It refreshes the lifecycle state and rejects bids outside the live window, from the listing's seller, or below the minimum next bid.
4. It persists the bid, updates the current price, adds an audit record, and commits.
5. Only after commit, Socket.IO emits a small event to the matching auction room. Browsers update the price and recent bid list using DOM text nodes, not HTML injection.

For a public multi-instance deployment, configure PostgreSQL and a Socket.IO message queue such as Redis. SQLite ignores row-level `FOR UPDATE`; therefore SQLite is for local demonstration, not high-contention auctions. A production-grade final implementation should additionally enforce the current-price invariant in a database transaction with retry handling or a conditional update, idempotency keys, and a concurrency stress test.

## Lifecycle model

- `scheduled`: current time is before `starts_at`.
- `live`: current time is at or after `starts_at` and before `ends_at`.
- `ended`: current time is at or after `ends_at`; highest bid is assigned as winner if one exists.
- `cancelled`: admin-cancelled; status refresh does not reactivate it.

State is recalculated on page/API/admin reads. A hosted service should add a scheduler/worker to close auctions even when no one is viewing them and send winner notifications.

## API and observability

- `GET /api/auctions`: auction snapshot with status, current price, next bid, end time and bid count.
- `GET /health`: database connectivity probe; returns 503 if database query fails.
- `GET /metrics`: simple JSON counters; secure this endpoint at the proxy for a public deployment.
- Rotating log file at `instance/app.log` (non-debug runtime), Python application logs, and `X-Request-ID` response header.

## Security controls included

Werkzeug password hashing, CSRF tokens on state-changing forms, login-required and admin role checks, duplicate-email handling, basic security headers, HTTP-only and SameSite session cookie settings, maximum request size, parameterized ORM queries, and input validation. Deploy only behind HTTPS; use a unique secret; restrict metrics; rotate logs; add rate limiting, email verification, account recovery, and stronger operational alerting before public launch.

## Scaling path

1. Move from SQLite to managed PostgreSQL and apply versioned schema migrations.
2. Run behind a TLS-terminating reverse proxy with multiple application instances.
3. Add Redis-backed Socket.IO fan-out and rate limiting.
4. Add background workers for auction close, notifications, image processing, and cleanup.
5. Add metrics/tracing and centralized structured logs; configure alerts on errors, latency, database saturation, and bid failures.
6. Add a payment/escrow integration only after legal, fraud, dispute and refund flows are specified.
