import pytest
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

@pytest.fixture()
def app(tmp_path):
    database = tmp_path / "test.db"
    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False, "SECRET_KEY": "test-secret", "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database}", "SOCKETIO_CORS_ALLOWED_ORIGINS": []})
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(name="Test Admin", email="admin@test.local", password_hash=generate_password_hash("correct-horse-battery"), role="admin")
        buyer = User(name="Test Buyer", email="buyer@test.local", password_hash=generate_password_hash("correct-horse-battery"), role="buyer")
        db.session.add_all([admin, buyer])
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()
