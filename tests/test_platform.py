from datetime import timedelta
from app import db
from app.models import User, Auction, Bid, utcnow


def login(client, email="buyer@test.local", password="correct-horse-battery"):
    return client.post("/auth/login", data={"email": email, "password": password}, follow_redirects=True)


def test_home_and_health(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").json["status"] == "ok"


def test_registration(client):
    response = client.post("/auth/register", data={"name": "New Rider", "email": "new@test.local", "password": "strong-password-123"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome" in response.data


def test_bid_requires_login(app, client):
    with app.app_context():
        admin = User.query.filter_by(email="admin@test.local").first()
        now = utcnow()
        auction = Auction(title="Live test bike", make="Honda", model="CB", year=2022, mileage_km=1000, description="Test listing", starting_price=100000, current_price=100000, bid_increment=500, starts_at=now-timedelta(hours=1), ends_at=now+timedelta(hours=1), seller_id=admin.id, status="live")
        db.session.add(auction); db.session.commit(); auction_id = auction.id
    response = client.post(f"/auctions/{auction_id}/bid", data={"amount": 100500})
    assert response.status_code in (302, 401)


def test_valid_bid_is_saved(app, client):
    with app.app_context():
        admin = User.query.filter_by(email="admin@test.local").first()
        now = utcnow()
        auction = Auction(title="Live test bike", make="Honda", model="CB", year=2022, mileage_km=1000, description="Test listing", starting_price=100000, current_price=100000, bid_increment=500, starts_at=now-timedelta(hours=1), ends_at=now+timedelta(hours=1), seller_id=admin.id, status="live")
        db.session.add(auction); db.session.commit(); auction_id = auction.id
    login(client)
    response = client.post(f"/auctions/{auction_id}/bid", data={"amount": 100500}, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        auction = db.session.get(Auction, auction_id)
        assert auction.current_price == 100500
        assert Bid.query.filter_by(auction_id=auction_id).count() == 1


def test_bid_below_minimum_rejected(app, client):
    with app.app_context():
        admin = User.query.filter_by(email="admin@test.local").first()
        now = utcnow()
        auction = Auction(title="Live test bike", make="Honda", model="CB", year=2022, mileage_km=1000, description="Test listing", starting_price=100000, current_price=100000, bid_increment=500, starts_at=now-timedelta(hours=1), ends_at=now+timedelta(hours=1), seller_id=admin.id, status="live")
        db.session.add(auction); db.session.commit(); auction_id = auction.id
    login(client)
    client.post(f"/auctions/{auction_id}/bid", data={"amount": 100001}, follow_redirects=True)
    with app.app_context():
        assert Bid.query.filter_by(auction_id=auction_id).count() == 0


def test_non_admin_cannot_open_admin(client):
    login(client)
    assert client.get("/admin/").status_code == 403
