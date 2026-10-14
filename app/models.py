from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import check_password_hash
from app import db


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="buyer")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    bids = db.relationship("Bid", back_populates="bidder", lazy=True)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"


class Auction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    make = db.Column(db.String(80), nullable=False)
    model = db.Column(db.String(80), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    mileage_km = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    starting_price = db.Column(db.Integer, nullable=False)
    current_price = db.Column(db.Integer, nullable=False)
    bid_increment = db.Column(db.Integer, nullable=False, default=500)
    status = db.Column(db.String(20), nullable=False, default="scheduled", index=True)
    starts_at = db.Column(db.DateTime, nullable=False, index=True)
    ends_at = db.Column(db.DateTime, nullable=False, index=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    bids = db.relationship("Bid", back_populates="auction", cascade="all, delete-orphan", order_by="Bid.created_at.desc()")
    seller = db.relationship("User", foreign_keys=[seller_id])
    winner = db.relationship("User", foreign_keys=[winner_id])

    @property
    def bid_count(self):
        return len(self.bids)

    @property
    def next_bid(self):
        return self.current_price + self.bid_increment

    def refresh_status(self, now=None):
        now = now or utcnow()
        if self.status in ("cancelled", "ended"):
            return False
        old = self.status
        if now < self.starts_at:
            self.status = "scheduled"
        elif now < self.ends_at:
            self.status = "live"
        else:
            self.status = "ended"
            top_bid = Bid.query.filter_by(auction_id=self.id).order_by(Bid.amount.desc(), Bid.created_at.asc()).first()
            self.winner_id = top_bid.bidder_id if top_bid else None
        return old != self.status


class Bid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    auction_id = db.Column(db.Integer, db.ForeignKey("auction.id"), nullable=False, index=True)
    bidder_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    amount = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    auction = db.relationship("Auction", back_populates="bids")
    bidder = db.relationship("User", back_populates="bids")


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    action = db.Column(db.String(80), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.String(500), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    actor = db.relationship("User")
