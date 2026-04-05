# URL Shortener — MLH PE Hackathon 2026

A production-grade URL shortening service built with Flask, Peewee, and PostgreSQL.

## Architecture
- **Nginx** — load balancer, splits traffic between two app instances
- **App1/App2** — Flask app running on Gunicorn with 8 workers each
- **PostgreSQL** — primary database for URL storage
- **Redis** — caching layer for fast redirects

## Stack
- **Flask** — web framework
- **Peewee** — ORM
- **PostgreSQL** — database
- **uv** — package manager
- **pytest** — testing
- **GitHub Actions** — CI/CD

## Setup

### Prerequisites
- Python 3.13+
- PostgreSQL
- uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Installation
```bash
git clone <your-repo-url>
cd PE-Hackathon-Template-2026
uv sync
cp .env.example .env
# Edit .env with your database credentials
```

### Database Setup
```bash
sudo -u postgres createdb hackathon_db
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
uv run python -c "
from app import create_app
from app.database import db
from app.models.url import URL
app = create_app()
with app.app_context():
    db.create_tables([URL])
"
```

### Running
```bash
uv run run.py
```

### Verify
```bash
curl http://localhost:5000/health
# → {"status": "ok"}
```

## Deploy Guide

### Start (Production)
```bash
docker compose up -d
```

### Seed the database
```bash
docker compose exec app1 uv run python seed.py
```

### Verify deployment
```bash
curl http://localhost:8080/health
# → {"status": "ok"}
```

### Rollback
```bash
# Roll back to previous image
git checkout <previous-commit>
docker compose up -d --build

# Or just restart current version
docker compose restart
```

### Troubleshooting
| Problem | Cause | Fix |
|---------|-------|-----|
| Port 8080 in use | Another service on port 80/8080 | Change port in docker-compose.yml |
| DB auth failed | Wrong credentials in .env | Check DATABASE_USER and DATABASE_PASSWORD |
| App won't start | DB not ready | Wait 10s, Docker healthcheck will retry |
| Tests fail in CI | DB table missing | Tables auto-created in test fixture |

## API Endpoints

| Method | Endpoint | Description | Body |
|--------|----------|-------------|------|
| GET | `/health` | Health check | — |
| POST | `/shorten` | Create short URL | `{"url": "https://example.com"}` |
| GET | `/<code>` | Redirect to original URL | — |
| GET | `/users` | List all users | — |
| POST | `/users` | Create user | `{"username": "x", "email": "x@x.com"}` |
| GET | `/users/<id>` | Get user by ID | — |
| PUT | `/users/<id>` | Update user | `{"username": "new"}` |
| DELETE | `/users/<id>` | Delete user | — |
| POST | `/users/bulk` | Bulk import users CSV | multipart/form-data |
| GET | `/urls` | List all URLs | — |
| POST | `/urls` | Create URL | `{"user_id": 1, "original_url": "https://..."}` |
| GET | `/urls/<id>` | Get URL by ID | — |
| PUT | `/urls/<id>` | Update URL | `{"title": "x", "is_active": false}` |
| DELETE | `/urls/<id>` | Delete URL | — |
| POST | `/urls/bulk` | Bulk import URLs CSV | multipart/form-data |
| GET | `/events` | List all events | — |
| POST | `/events` | Create event | `{"url_id": 1, "event_type": "click"}` |

### Example Usage
```bash
# Shorten a URL
curl -X POST http://localhost:5000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://google.com"}'
# → {"short_code": "YNSxLI", "short_url": "/YNSxLI"}

# Use the short URL
curl -L http://localhost:5000/YNSxLI
# → redirects to https://google.com
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_NAME` | PostgreSQL database name | `hackathon_db` |
| `DATABASE_HOST` | Database host | `localhost` |
| `DATABASE_PORT` | Database port | `5432` |
| `DATABASE_USER` | Database user | `postgres` |
| `DATABASE_PASSWORD` | Database password | `postgres` |
| `FLASK_DEBUG` | Enable debug mode | `false` |

## Testing
```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=app --cov-report=term-missing  # with coverage
```

## Running with Docker

### Start
```bash
docker compose up --build
```

### Run in background
```bash
docker compose up -d
```

### Stop
```bash
docker compose down
```

### Verify
```bash
curl http://localhost:5000/health
# → {"status": "ok"}
```

## Chaos Engineering (Reliability Gold Demo)

The app is configured with `restart: always` in docker-compose.yml. To demonstrate automatic recovery:
```bash
# 1. Start containers
docker compose up -d

# 2. Get the host PID of the app container
docker inspect url-shortener-app-1 --format '{{.State.Pid}}'

# 3. Kill it (simulates a crash)
sudo kill -9 <PID>

# 4. Watch it restart automatically
watch -n 1 docker ps

# 5. Confirm it's back
curl http://localhost:5000/health
```

## Technical Decisions

- **Flask** — lightweight, easy to test, good for APIs
- **Peewee** — simple ORM with minimal boilerplate  
- **PostgreSQL** — reliable, production-grade database
- **uv** — fast dependency management, handles Python versioning
- **Docker + restart: always** — ensures the service recovers automatically from crashes without manual intervention
- **pytest + GitHub Actions** — every push is tested automatically, broken code never reaches main

## Documentation

- [Runbook](docs/runbook.md) — emergency response guide
- [Capacity Plan](docs/capacity.md) — scaling limits and load test results

## Failure Modes

| Failure | Symptom | Resolution |
|---------|---------|------------|
| DB connection fails | 500 error on all routes | Check PostgreSQL is running, verify `.env` credentials |
| Short code not found | 404 JSON error | Code doesn't exist in DB — check if DB was seeded |
| App crashes | No response | Check logs, restart with `uv run run.py` |
