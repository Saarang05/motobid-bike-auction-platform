from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify, current_app
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from app import db, socketio
from app.models import Auction, Bid, AuditLog, utcnow

bp = Blueprint("auctions", __name__)

@bp.get("/")
def index():
    now = utcnow()
    auctions = Auction.query.order_by(Auction.status.asc(), Auction.ends_at.asc()).all()
    changed = False
    for auction in auctions:
        changed = auction.refresh_status(now) or changed
    if changed:
        db.session.commit()
    status = request.args.get("status", "all")
    if status in ("live", "scheduled", "ended"):
        auctions = [a for a in auctions if a.status == status]
    q = request.args.get("q", "").strip().lower()
    if q:
        auctions = [a for a in auctions if q in f"{a.title} {a.make} {a.model}".lower()]
    return render_template("index.html", auctions=auctions, active_status=status, search=q)

@bp.get("/auctions/<int:auction_id>")
def detail(auction_id):
    auction = db.get_or_404(Auction, auction_id)
    if auction.refresh_status():
        db.session.commit()
    bids = Bid.query.filter_by(auction_id=auction.id).order_by(Bid.created_at.desc()).limit(20).all()
    return render_template("auction_detail.html", auction=auction, bids=bids)

@bp.post("/auctions/<int:auction_id>/bid")
@login_required
def place_bid(auction_id):
    amount_raw = request.form.get("amount", "")
    try:
        amount = int(amount_raw)
    except (TypeError, ValueError):
        flash("Enter a whole-number bid amount in INR.", "error")
        return redirect(url_for("auctions.detail", auction_id=auction_id))
    try:
        # Row locking is effective on databases that support it (e.g. PostgreSQL).
        auction = Auction.query.filter_by(id=auction_id).with_for_update().first_or_404()
        auction.refresh_status()
        if auction.status != "live":
            raise ValueError("Bidding is only open while an auction is live.")
        if auction.seller_id == current_user.id:
            raise ValueError("You cannot bid on your own listing.")
        if amount < auction.next_bid:
            raise ValueError(f"Your bid must be at least ₹{auction.next_bid:,}.")
        bid = Bid(auction_id=auction.id, bidder_id=current_user.id, amount=amount)
        auction.current_price = amount
        db.session.add(bid)
        db.session.add(AuditLog(actor_id=current_user.id, action="auction.bid", entity_type="auction", entity_id=auction.id, details=f"Bid placed: INR {amount}"))
        db.session.commit()
        payload = {"auction_id": auction.id, "amount": amount, "bidder": current_user.name, "next_bid": auction.next_bid, "bid_count": auction.bid_count}
        socketio.emit("bid_update", payload, to=f"auction_{auction.id}")
        flash("Bid placed successfully!", "success")
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Bid transaction failed for auction %s", auction_id)
        flash("We could not place your bid. Please refresh and try again.", "error")
    return redirect(url_for("auctions.detail", auction_id=auction_id))

@bp.get("/api/auctions")
def api_auctions():
    auctions = Auction.query.order_by(Auction.ends_at.asc()).all()
    now = utcnow()
    changed = False
    for a in auctions:
        changed = a.refresh_status(now) or changed
    if changed:
        db.session.commit()
    return jsonify([{"id": a.id, "title": a.title, "status": a.status, "current_price": a.current_price, "next_bid": a.next_bid, "ends_at": a.ends_at.isoformat(), "bid_count": a.bid_count} for a in auctions])

@socketio.on("join_auction")
def join_auction(data):
    from flask_socketio import join_room
    try:
        auction_id = int(data.get("auction_id"))
        if Auction.query.get(auction_id):
            join_room(f"auction_{auction_id}")
    except (ValueError, TypeError, AttributeError):
        return
