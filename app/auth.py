from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash
from urllib.parse import urlparse
from app import db
from app.models import User, AuditLog
from sqlalchemy.exc import IntegrityError

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(name) < 2 or len(name) > 100 or "@" not in email or len(password) < 10:
            flash("Enter a valid name and email. Password must contain at least 10 characters.", "error")
            return render_template("register.html")
        user = User(name=name, email=email, password_hash=generate_password_hash(password), role="buyer")
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("An account with that email already exists.", "error")
            return render_template("register.html")
        db.session.add(AuditLog(actor_id=user.id, action="user.register", entity_type="user", entity_id=user.id, details="Buyer account created"))
        db.session.commit()
        login_user(user)
        flash("Welcome! Your account is ready.", "success")
        return redirect(url_for("auctions.index"))
    return render_template("register.html")

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email, is_active=True).first()
        if user and user.check_password(password):
            login_user(user, remember=False)
            db.session.add(AuditLog(actor_id=user.id, action="user.login", entity_type="user", entity_id=user.id, details="Successful login"))
            db.session.commit()
            next_url = request.args.get("next", "")
            parsed = urlparse(next_url)
            if parsed.scheme or parsed.netloc or not next_url.startswith("/") or next_url.startswith("//"):
                next_url = url_for("auctions.index")
            return redirect(next_url or url_for("auctions.index"))
        current_app.logger.warning("Failed login for %s", email[:120])
        flash("Invalid email or password.", "error")
    return render_template("login.html")

@bp.post("/logout")
def logout():
    if current_user.is_authenticated:
        db.session.add(AuditLog(actor_id=current_user.id, action="user.logout", entity_type="user", entity_id=current_user.id, details="User logged out"))
        db.session.commit()
    logout_user()
    return redirect(url_for("auctions.index"))
