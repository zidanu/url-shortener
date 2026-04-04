import csv
import os
from app import create_app
from app.database import db
from app.models.user import User
from app.models.url import URL
from app.models.event import Event

app = create_app()


def seed_users(filepath):
    print("Seeding users...")
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    with db.atomic():
        for batch in [rows[i : i + 100] for i in range(0, len(rows), 100)]:
            for row in batch:
                User.get_or_create(
                    id=int(row["id"]),
                    defaults={
                        "username": row["username"],
                        "email": row["email"],
                        "created_at": row["created_at"],
                    },
                )
    print(f"  Done: {len(rows)} users")


def seed_urls(filepath):
    print("Seeding URLs...")
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    with db.atomic():
        for row in rows:
            URL.get_or_create(
                id=int(row["id"]),
                defaults={
                    "user_id": row["user_id"],
                    "short_code": row["short_code"],
                    "original_url": row["original_url"],
                    "title": row.get("title"),
                    "is_active": row["is_active"].lower() == "true",
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                },
            )
    print(f"  Done: {len(rows)} URLs")


def seed_events(filepath):
    print("Seeding events...")
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    with db.atomic():
        for row in rows:
            Event.get_or_create(
                id=int(row["id"]),
                defaults={
                    "url_id": int(row["url_id"]),
                    "user_id": int(row["user_id"]) if row["user_id"] else None,
                    "event_type": row["event_type"],
                    "timestamp": row["timestamp"],
                    "details": row.get("details"),
                },
            )
    print(f"  Done: {len(rows)} events")


if __name__ == "__main__":
    with app.app_context():
        seed_users("users.csv")
        seed_urls("urls.csv")
        seed_events("events.csv")
    print("Seeding complete!")
