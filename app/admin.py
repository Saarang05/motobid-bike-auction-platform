from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user, login_required
from app import db
from app.models import Auction, AuditLog, User, utcnow

bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return fn(*args, **kwargs)
    return wrapped

@bp.get("/")
@admin_required
def dashboard():
    auctions = Auction.query.order_by(Auction.created_at.desc()).all()
    for auction in auctions:
        auction.refresh_status()
    db.session.commit()
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(30).all()
    return render_template("admin.html", auctions=auctions, users=User.query.count(), logs=logs)

@bp.route("/auctions/new", methods=["GET", "POST"])
@admin_required
def create_auction():
    if request.method == "POST":
        try:
            title = request.form["title"].strip()
            make = request.form["make"].strip()
            model = request.form["model"].strip()
            year = int(request.form["year"])
            mileage = int(request.form["mileage_km"])
            price = int(request.form["starting_price"])
            increment = int(request.form["bid_increment"])
            starts = datetime.fromisoformat(request.form["starts_at"])
            ends = datetime.fromisoformat(request.form["ends_at"])
            description = request.form["description"].strip()
            image_url = request.form.get("image_url", "").strip()
            if not all([title, make, model, description]) or len(title) > 140 or len(description) > 5000:
                raise ValueError("Please complete all text fields within the stated limits.")
            if year < 1900 or year > utcnow().year + 1 or mileage < 0 or price < 1 or increment < 1:
                raise ValueError("Check the year, mileage, starting price and bid increment.")
            if starts >= ends or ends <= utcnow():
                raise ValueError("End time must be after start time and in the future.")
            if image_url and not image_url.startswith(("https://", "http://")):
                raise ValueError("Image URL must start with http:// or https://")
            auction = Auction(title=title, make=make, model=model, year=year, mileage_km=mileage, description=description, image_url=image_url or None, starting_price=price, current_price=price, bid_increment=increment, starts_at=starts, ends_at=ends, seller_id=current_user.id)
            auction.refresh_status()
            db.session.add(auction)
            db.session.flush()
            db.session.add(AuditLog(actor_id=current_user.id, action="auction.create", entity_type="auction", entity_id=auction.id, details=f"Created auction: {title}"))
            db.session.commit()
            flash("Auction created.", "success")
            return redirect(url_for("admin.dashboard"))
        except (ValueError, KeyError) as exc:
            db.session.rollback()
            flash(str(exc) or "Please check the form values.", "error")
    return render_template("auction_form.html")

@bp.post("/auctions/<int:auction_id>/cancel")
@admin_required
def cancel_auction(auction_id):
    auction = db.get_or_404(Auction, auction_id)
    if auction.status == "ended":
        flash("An ended auction cannot be cancelled.", "error")
    else:
        auction.status = "cancelled"
        db.session.add(AuditLog(actor_id=current_user.id, action="auction.cancel", entity_type="auction", entity_id=auction.id, details="Auction cancelled by admin"))
        db.session.commit()
        flash("Auction cancelled.", "success")
    return redirect(url_for("admin.dashboard"))

@bp.post("/users/<int:user_id>/toggle")
@admin_required
def toggle_user(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "error")
    else:
        user.is_active = not user.is_active
        db.session.add(AuditLog(actor_id=current_user.id, action="user.status", entity_type="user", entity_id=user.id, details=f"is_active={user.is_active}"))
        db.session.commit()
        flash("User status updated.", "success")
    return redirect(url_for("admin.dashboard"))
