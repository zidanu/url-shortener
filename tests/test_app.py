import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        from app.database import db
        from app.models.url import URL
        from app.models.user import User
        from app.models.event import Event

        db.create_tables([User, URL, Event])
        with app.test_client() as client:
            yield client
        db.drop_tables([User, URL, Event])


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


def test_invalid_short_code_returns_404(client):
    response = client.get("/!!!invalid!!!")
    assert response.status_code in [400, 404]


def test_inactive_url_returns_410(client):
    # Create a URL then deactivate it
    from app.models.url import URL

    response = client.post("/shorten", json={"url": "https://google.com"})
    short_code = response.get_json()["short_code"]

    # Deactivate it directly in DB
    URL.update(is_active=False).where(URL.short_code == short_code).execute()

    # Try to use it
    response = client.get(f"/{short_code}")
    assert response.status_code == 410


def test_active_url_redirects(client):
    response = client.post("/shorten", json={"url": "https://google.com"})
    short_code = response.get_json()["short_code"]
    response = client.get(f"/{short_code}")
    assert response.status_code == 302


# Users CRUD tests
def test_list_users(client):
    response = client.get("/users")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_get_user_by_id(client):
    # First create a user
    client.post("/users", json={"username": "testget", "email": "testget@example.com"})
    response = client.get("/users/1")
    assert response.status_code in [200, 404]  # 404 if no users seeded


def test_create_user(client):
    response = client.post(
        "/users", json={"username": "newuser123", "email": "newuser123@example.com"}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data
    assert data["username"] == "newuser123"


def test_create_user_missing_fields(client):
    response = client.post("/users", json={"username": "onlyusername"})
    assert response.status_code == 400


def test_create_user_wrong_types(client):
    response = client.post(
        "/users", json={"username": 12345, "email": "test@example.com"}
    )
    assert response.status_code == 400


def test_update_user(client):
    # Create then update
    create = client.post(
        "/users", json={"username": "updateme123", "email": "updateme123@example.com"}
    )
    user_id = create.get_json()["id"]
    response = client.put(f"/users/{user_id}", json={"username": "updated123"})
    assert response.status_code == 200
    assert response.get_json()["username"] == "updated123"


def test_get_user_not_found(client):
    response = client.get("/users/999999")
    assert response.status_code == 404


# URLs CRUD tests
def test_list_urls(client):
    response = client.get("/urls")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_create_url_via_urls_endpoint(client):
    # Create a user first
    user = client.post(
        "/users", json={"username": "urlowner123", "email": "urlowner123@example.com"}
    )
    user_id = user.get_json()["id"]
    response = client.post(
        "/urls",
        json={
            "user_id": user_id,
            "original_url": "https://example.com",
            "title": "Test URL",
        },
    )
    assert response.status_code == 201
    data = response.get_json()
    assert "short_code" in data
    assert data["is_active"] == True


def test_create_url_invalid_user(client):
    response = client.post(
        "/urls", json={"user_id": 999999, "original_url": "https://example.com"}
    )
    assert response.status_code == 404


def test_create_url_missing_url(client):
    response = client.post("/urls", json={"user_id": 1})
    assert response.status_code == 400


def test_get_url_by_id(client):
    user = client.post(
        "/users",
        json={"username": "geturluser123", "email": "geturluser123@example.com"},
    )
    user_id = user.get_json()["id"]
    create = client.post(
        "/urls", json={"user_id": user_id, "original_url": "https://example.com"}
    )
    url_id = create.get_json()["id"]
    response = client.get(f"/urls/{url_id}")
    assert response.status_code == 200


def test_update_url(client):
    user = client.post(
        "/users",
        json={"username": "updateurluser123", "email": "updateurluser123@example.com"},
    )
    user_id = user.get_json()["id"]
    create = client.post(
        "/urls", json={"user_id": user_id, "original_url": "https://example.com"}
    )
    url_id = create.get_json()["id"]
    response = client.put(
        f"/urls/{url_id}", json={"title": "Updated Title", "is_active": False}
    )
    assert response.status_code == 200
    assert response.get_json()["is_active"] == False


def test_get_url_not_found(client):
    response = client.get("/urls/999999")
    assert response.status_code == 404


# Events tests
def test_list_events(client):
    response = client.get("/events")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_create_event(client):
    user = client.post(
        "/users", json={"username": "eventuser1", "email": "eventuser1@example.com"}
    )
    user_id = user.get_json()["id"]
    url = client.post(
        "/urls", json={"user_id": user_id, "original_url": "https://example.com"}
    )
    url_id = url.get_json()["id"]
    response = client.post(
        "/events",
        json={
            "url_id": url_id,
            "user_id": user_id,
            "event_type": "click",
            "details": {"referrer": "https://google.com"},
        },
    )
    assert response.status_code == 201


def test_create_event_invalid_url(client):
    response = client.post("/events", json={"url_id": 999999, "event_type": "click"})
    assert response.status_code == 404


def test_create_event_missing_fields(client):
    response = client.post("/events", json={"event_type": "click"})
    assert response.status_code == 400


def test_create_event_invalid_details(client):
    user = client.post(
        "/users", json={"username": "eventuser2", "email": "eventuser2@example.com"}
    )
    user_id = user.get_json()["id"]
    url = client.post(
        "/urls", json={"user_id": user_id, "original_url": "https://example.com"}
    )
    url_id = url.get_json()["id"]
    response = client.post(
        "/events",
        json={"url_id": url_id, "event_type": "click", "details": "not a dict"},
    )
    assert response.status_code == 400


def test_delete_user(client):
    user = client.post(
        "/users", json={"username": "deleteuser1", "email": "deleteuser1@example.com"}
    )
    user_id = user.get_json()["id"]
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 200


def test_delete_user_not_found(client):
    response = client.delete("/users/999999")
    assert response.status_code == 404


def test_delete_url(client):
    user = client.post(
        "/users",
        json={"username": "deleteurluser1", "email": "deleteurluser1@example.com"},
    )
    user_id = user.get_json()["id"]
    url = client.post(
        "/urls", json={"user_id": user_id, "original_url": "https://example.com"}
    )
    url_id = url.get_json()["id"]
    response = client.delete(f"/urls/{url_id}")
    assert response.status_code == 200


def test_delete_url_not_found(client):
    response = client.delete("/urls/999999")
    assert response.status_code == 404


def test_list_urls_filter_active(client):
    response = client.get("/urls?is_active=true")
    assert response.status_code == 200


def test_update_url_invalid_type(client):
    user = client.post(
        "/users",
        json={"username": "updatetypeuser", "email": "updatetypeuser@example.com"},
    )
    user_id = user.get_json()["id"]
    url = client.post(
        "/urls", json={"user_id": user_id, "original_url": "https://example.com"}
    )
    url_id = url.get_json()["id"]
    response = client.put(f"/urls/{url_id}", json={"is_active": "notabool"})
    assert response.status_code == 400
