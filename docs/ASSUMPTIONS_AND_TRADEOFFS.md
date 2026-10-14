# Assumptions, Trade-offs, and Remaining Production Work

## Assignment assumptions

1. **Currency:** prices are integer Indian rupees; no fractional paise or currency conversion.
2. **Roles:** visitors can browse; registered buyers can bid; administrators can create/cancel auctions and review audit events. Admin is not a vehicle inspector.
3. **Auction timing:** a bid is valid only when server time is within the live window. Minimum next bid equals current price plus the configured increment. No automatic bid extension is applied.
4. **Winner:** highest bid at close wins; ties are ordered by earliest bid timestamp. No bid means no winner.
5. **Listing images:** optional external HTTP(S) image URL; image ownership and availability are not verified.
6. **Sample data:** initial records are illustrative demo listings, not genuine offers or verified vehicle information.
7. **Payments:** payment, deposits, escrow, refunds, transfer of ownership, dispute resolution, seller verification and fraud controls were not specified and are not implemented.
8. **Deployment:** a deployment-ready package is supplied, but a public URL cannot be asserted until a hosting account/database is configured and the app is actually deployed.

## Engineering trade-offs

- **Flask + server-rendered templates:** fewer moving parts, quick local setup and readable code. A separate frontend/backend split was not necessary for the assignment's core flows.
- **SQLite by default:** zero-service local development. It is not suitable for high-contention production bidding; use PostgreSQL and validate concurrency under load.
- **Socket.IO:** demonstrates near-real-time price updates. A message broker is required for reliable cross-process/multi-instance fan-out.
- **Read-triggered lifecycle refresh:** keeps the demo self-contained. A scheduler/worker is required to close auctions at the exact deadline without a page/API read.
- **Basic JSON metrics:** simple demonstration, not a full monitoring system. Add Prometheus/OpenTelemetry, centralized logs, dashboards and alerting for production.
- **No migrations yet:** `create_all()` initializes a fresh database. Use Alembic/Flask-Migrate for schema changes and production upgrades.
- **Simple rate protection:** no built-in rate limiter or bid anti-sniping/abuse model. Add request throttling, account verification, fraud detection and idempotency before public use.

## Production readiness gaps to close before handling real transactions

- PostgreSQL transaction/conditional-update strategy with concurrency and race-condition tests.
- Migration workflow, backups, restore drills, and database retention policy.
- HTTPS, secret manager, rotation procedures, restrictive CORS, secure proxy configuration, rate limiting and abuse monitoring.
- Email verification, password reset, session revocation and login throttling.
- Verified sellers, vehicle documentation, inspection reports, moderation and takedown process.
- Payment provider, deposits/escrow, settlement, refunds, disputes, tax and legal terms.
- Background auction scheduler, notifications, durable event delivery and winner workflow.
- Accessibility audit, cross-browser testing, dependency scanning, CI pipeline, load tests, error tracking and operational runbooks.

The assignment prioritizes quality of engineering decisions over raw feature count. These trade-offs are intentionally documented rather than presenting unsupported payment or verification features as complete.
