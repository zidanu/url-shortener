# URL Shortener — MLH PE Hackathon 2026

A production-grade URL shortening service built with Flask, Peewee, and PostgreSQL.

## Architecture

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

## API Endpoints

| Method | Endpoint | Description | Body |
|--------|----------|-------------|------|
| GET | `/health` | Health check | — |
| POST | `/shorten` | Create short URL | `{"url": "https://example.com"}` |
| GET | `/<code>` | Redirect to original URL | — |

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

## Failure Modes

| Failure | Symptom | Resolution |
|---------|---------|------------|
| DB connection fails | 500 error on all routes | Check PostgreSQL is running, verify `.env` credentials |
| Short code not found | 404 JSON error | Code doesn't exist in DB — check if DB was seeded |
| App crashes | No response | Check logs, restart with `uv run run.py` |

## Technical Decisions

- **Flask** — lightweight, easy to test, good for APIs
- **Peewee** — simple ORM with minimal boilerplate
- **PostgreSQL** — reliable, production-grade database
- **uv** — fast dependency management, handles Python versioning
