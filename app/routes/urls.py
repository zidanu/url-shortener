from flask import Blueprint, jsonify, request
import datetime
import random
import string
import csv
import io
from app.models.url import URL
from app.models.user import User
from app.models.event import Event

urls_bp = Blueprint("urls", __name__)


def generate_code(length=6):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def url_to_dict(u):
    return {
        "id": u.id,
        "user_id": int(u.user_id) if u.user_id else None,
        "short_code": u.short_code,
        "original_url": u.original_url,
        "title": u.title,
        "is_active": u.is_active,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "updated_at": u.updated_at.isoformat() if u.updated_at else None,
    }


@urls_bp.route("/urls", methods=["GET"])
def list_urls():
    user_id = request.args.get("user_id", type=int)
    is_active = request.args.get("is_active")
    query = URL.select().order_by(URL.id)
    if user_id:
        query = query.where(URL.user_id == str(user_id))
    if is_active is not None:
        active_bool = is_active.lower() == "true"
        query = query.where(URL.is_active == active_bool)
    return jsonify([url_to_dict(u) for u in query]), 200


@urls_bp.route("/urls/<int:url_id>", methods=["DELETE"])
def delete_url(url_id):
    try:
        u = URL.get_by_id(url_id)
        u.delete_instance()
        return jsonify({"message": "URL deleted"}), 200
    except URL.DoesNotExist:
        return jsonify({"error": "URL not found"}), 404


@urls_bp.route("/urls/bulk", methods=["POST"])
def bulk_import_urls():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    content = file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    imported = 0
    for row in reader:
        try:
            # Validate user exists
            user_id = row.get("user_id")
            if user_id:
                try:
                    User.get_by_id(int(user_id))
                except User.DoesNotExist:
                    continue  # Skip rows with invalid user_id

            data = {
                "user_id": user_id,
                "short_code": row["short_code"],
                "original_url": row["original_url"],
                "title": row.get("title"),
                "is_active": row["is_active"].lower() == "true",
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            URL.insert(id=int(row["id"]), **data).on_conflict(
                conflict_target=[URL.id], update=data
            ).execute()
            imported += 1
        except Exception:
            continue

    return jsonify({"imported": imported}), 201


@urls_bp.route("/urls/<identifier>", methods=["GET"])
def get_url(identifier):
    # Try by ID first
    try:
        url_id = int(identifier)
        u = URL.get_by_id(url_id)
        return jsonify(url_to_dict(u)), 200
    except (ValueError, URL.DoesNotExist):
        pass

    # Try by short code
    try:
        u = URL.get(URL.short_code == identifier)
        return jsonify(url_to_dict(u)), 200
    except URL.DoesNotExist:
        return jsonify({"error": "URL not found"}), 404


@urls_bp.route("/urls", methods=["POST"])
def create_url():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing request body"}), 400

    original_url = data.get("original_url")
    user_id = data.get("user_id")
    title = data.get("title")

    if not original_url:
        return jsonify({"error": "Missing original_url"}), 400

    if not isinstance(original_url, str):
        return jsonify({"error": "Invalid data type for original_url"}), 400

    if not original_url.startswith("http://") and not original_url.startswith(
        "https://"
    ):
        return jsonify({"error": "Invalid URL"}), 400

    # Validate user_id type
    if user_id is not None:
        if not isinstance(user_id, int):
            return jsonify({"error": "user_id must be an integer"}), 400
        try:
            User.get_by_id(user_id)
        except User.DoesNotExist:
            return jsonify({"error": "User not found"}), 404

    short_code = generate_code()
    while URL.select().where(URL.short_code == short_code).exists():
        short_code = generate_code()

    now = datetime.datetime.now()
    u = URL.create(
        user_id=str(user_id) if user_id else None,
        short_code=short_code,
        original_url=original_url,
        title=title,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    try:
        Event.create(
            url_id=u.id,
            event_type="created",
            details=f'{{"short_code":"{short_code}","original_url":"{original_url}"}}',
        )
    except Exception:
        pass

    return jsonify(url_to_dict(u)), 201


@urls_bp.route("/urls/<int:url_id>", methods=["PUT"])
def update_url(url_id):
    try:
        u = URL.get_by_id(url_id)
    except URL.DoesNotExist:
        return jsonify({"error": "URL not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing request body"}), 400

    if "title" in data:
        u.title = data["title"]
    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            return jsonify({"error": "is_active must be a boolean"}), 400
        u.is_active = data["is_active"]
        # Invalidate Redis cache when URL is deactivated
        try:
            import redis
            import os

            r = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                decode_responses=True,
            )
            if not u.is_active:
                r.delete(f"url:{u.short_code}")
                r.setex(f"inactive:{u.short_code}", 3600, "1")
            else:
                r.delete(f"inactive:{u.short_code}")
                r.setex(f"url:{u.short_code}", 3600, u.original_url)
        except Exception:
            pass
    if "original_url" in data:
        u.original_url = data["original_url"]

    u.updated_at = datetime.datetime.now()
    u.save()
    return jsonify(url_to_dict(u)), 200
