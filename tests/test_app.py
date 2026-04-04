import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        from app.database import db
        from app.models.url import URL

        db.create_tables([URL])
        with app.test_client() as client:
            yield client
        db.drop_tables([URL])


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_ok(client):
    response = client.get("/health")
    data = response.get_json()
    assert data["status"] == "ok"


def test_shorten_returns_201(client):
    response = client.post("/shorten", json={"url": "https://google.com"})
    assert response.status_code == 201


def test_shorten_returns_short_code(client):
    response = client.post("/shorten", json={"url": "https://google.com"})
    data = response.get_json()
    assert "short_code" in data
    assert "short_url" in data


def test_shorten_missing_url_returns_400(client):
    response = client.post("/shorten", json={})
    assert response.status_code == 400


def test_unknown_short_code_returns_404(client):
    response = client.get("/doesnotexist123")
    assert response.status_code == 404


def test_redirect_works(client):
    response = client.post("/shorten", json={"url": "https://google.com"})
    short_code = response.get_json()["short_code"]

    response = client.get(f"/{short_code}")
    assert response.status_code == 302


def test_shorten_rejects_empty_url(client):
    response = client.post("/shorten", json={"url": ""})
    assert response.status_code == 400


def test_shorten_rejects_invalid_url(client):
    response = client.post("/shorten", json={"url": "not-a-url"})
    assert response.status_code == 400


def test_shorten_rejects_no_body(client):
    response = client.post("/shorten")
    assert response.status_code in [400, 415]


def test_shorten_accepts_http(client):
    response = client.post("/shorten", json={"url": "http://example.com"})
    assert response.status_code == 201


def test_shorten_accepts_https(client):
    response = client.post("/shorten", json={"url": "https://example.com"})
    assert response.status_code == 201
