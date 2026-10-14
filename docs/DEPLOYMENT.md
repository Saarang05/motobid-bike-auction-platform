# Deployment Instructions

## Local Linux deployment

Follow the Quick Start section in the root README. The app listens on port 5000 by default. Keep it bound to localhost for development unless you intentionally need LAN access.

## Docker deployment

1. Install Docker Engine and the Docker Compose plugin on your Linux machine.
2. Copy `.env.example` to `.env`; configure a long random `SECRET_KEY` and unique `ADMIN_PASSWORD`.
3. Run `docker compose up --build -d`.
4. Check `docker compose ps`, `docker compose logs -f web`, and `curl http://127.0.0.1:5000/health`.
5. Back up the `auction_data` volume regularly. To stop, run `docker compose down`.

## Public hosting checklist

This repository does not provision cloud infrastructure or create a public URL by itself. To submit the requested deployed link, choose a host that supports Python web services and WebSockets, provision a PostgreSQL database, set environment variables in the host dashboard, and deploy this repository. Configure:

- `SECRET_KEY`: cryptographically random, private value.
- `DATABASE_URL`: PostgreSQL connection string from the managed database.
- `ADMIN_EMAIL` and `ADMIN_PASSWORD`: unique bootstrap admin credentials.
- `PORT`: supplied by the host if it requires a dynamic port.
- HTTPS and WebSocket forwarding; do not use permissive Socket.IO CORS settings.
- Persistent log collection and protected `/metrics` access.

For multi-instance deployment, configure a Redis message queue for Socket.IO and use a production worker arrangement supported by the chosen host. The included Compose setup is a useful single-instance demonstration, not a complete high-availability topology. Do not publish `.env`, the SQLite database, or demo credentials in Git.

## Before sharing the URL

- Change the seeded admin password and secret key.
- Confirm the deployed health check and database persistence.
- Create a non-admin account and test valid/invalid bids.
- Verify live updates with two browser sessions.
- Confirm the host's WebSocket and timeout behavior.
- Confirm no secrets or private data are present in repository history.
