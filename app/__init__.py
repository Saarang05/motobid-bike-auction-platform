import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, request, g
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash


db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO(cors_allowed_origins=[], async_mode="threading")
csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "unsafe-local-secret-change-before-deploy"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///auction.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_HTTPONLY=True,
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
        PORT=int(os.getenv("PORT", "5000")),
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    _configure_logging(app)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    csrf.init_app(app)
    socketio.init_app(app, cors_allowed_origins=app.config.get("SOCKETIO_CORS_ALLOWED_ORIGINS", []), async_mode="threading")

    from app.models import User, Auction, Bid, AuditLog
    from app.auth import bp as auth_bp
    from app.auctions import bp as auctions_bp
    from app.admin import bp as admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(auctions_bp)
    app.register_blueprint(admin_bp)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.before_request
    def request_context():
        g.request_id = request.headers.get("X-Request-ID", os.urandom(8).hex())

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-Request-ID"] = getattr(g, "request_id", "unknown")
        return response

    @app.get("/health")
    def health():
        try:
            db.session.execute(db.text("SELECT 1"))
            return jsonify(status="ok", database="ok"), 200
        except Exception:
            app.logger.exception("Health check failed")
            return jsonify(status="degraded", database="error"), 503

    @app.get("/metrics")
    def metrics():
        # Minimal operational endpoint; restrict exposure at the reverse proxy in production.
        return jsonify(users=User.query.count(), auctions=Auction.query.count(), bids=Bid.query.count(), audit_events=AuditLog.query.count())

    with app.app_context():
        db.create_all()
        _seed_admin(app)

    app.logger.info("Bike Auction Platform initialized")
    return app


def _configure_logging(app):
    app.logger.setLevel(logging.INFO)
    if not app.debug and not app.testing:
        handler = RotatingFileHandler(os.path.join(app.instance_path, "app.log"), maxBytes=1_000_000, backupCount=3)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        app.logger.addHandler(handler)


def _seed_admin(app):
    from app.models import User
    email = os.getenv("ADMIN_EMAIL", "admin@bikeauction.local").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")
    admin = User.query.filter_by(email=email).first()
    if not admin:
        admin = User(name="Platform Admin", email=email, password_hash=generate_password_hash(password), role="admin", is_active=True)
        db.session.add(admin)
        db.session.commit()
        app.logger.warning("Bootstrap admin created for %s; change the password before public deployment", email)
    # Demo inventory makes a fresh local install useful immediately. All entries are clearly sample listings.
    from datetime import timedelta
    from app.models import Auction, utcnow
    if Auction.query.count() == 0:
        now = utcnow()
        samples = [
            dict(title="The Everyday Escape", make="Royal Enfield", model="Interceptor 650", year=2022, mileage_km=8400, description="Sample listing. Twin-cylinder roadster with comfortable ergonomics, clean presentation and a characterful exhaust note. Inspect the bike and verify documents before purchase.", starting_price=210000, current_price=210000, bid_increment=2500, starts_at=now-timedelta(hours=2), ends_at=now+timedelta(days=1), image_url="https://images.unsplash.com/photo-1558981806-ec527fa84c39?auto=format&fit=crop&w=1000&q=85"),
            dict(title="Weekend Sport Machine", make="Kawasaki", model="Ninja 300", year=2021, mileage_km=15300, description="Sample listing. Lightweight sport motorcycle suited to weekend rides and city commutes. Condition and service history are illustrative; verify all details independently.", starting_price=235000, current_price=235000, bid_increment=2000, starts_at=now-timedelta(hours=1), ends_at=now+timedelta(days=2), image_url="https://images.unsplash.com/photo-1558981403-c5f9899a28bc?auto=format&fit=crop&w=1000&q=85"),
            dict(title="Classic Road Companion", make="Honda", model="CB350 H'ness", year=2023, mileage_km=5100, description="Sample listing. A modern classic with relaxed road manners and a timeless silhouette. This is demo content, not a verified vehicle advertisement.", starting_price=175000, current_price=175000, bid_increment=1500, starts_at=now+timedelta(days=1), ends_at=now+timedelta(days=3), image_url="https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?auto=format&fit=crop&w=1000&q=85"),
            dict(title="Adventure Ready Tourer", make="BMW", model="G 310 GS", year=2022, mileage_km=9700, description="Sample listing. Compact adventure-style motorcycle for mixed-road exploring. Demo listing only; inspect condition and documentation before any real transaction.", starting_price=245000, current_price=245000, bid_increment=2500, starts_at=now-timedelta(days=3), ends_at=now-timedelta(days=2), image_url="https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?auto=format&fit=crop&w=1000&q=75"),
        ]
        for values in samples:
            auction = Auction(**values, seller_id=admin.id)
            auction.refresh_status(now)
            db.session.add(auction)
        db.session.commit()
