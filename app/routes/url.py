from flask import Blueprint, jsonify, request, redirect
import random
import string
import redis
import os
import datetime
from app.models.url import URL
from app.models.event import Event

url_bp = Blueprint("url", __name__)


def get_redis():
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True,
    )


def generate_code(length=6):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def is_valid_url(url):
    return url.startswith("http://") or url.startswith("https://")


@url_bp.route("/shorten", methods=["POST"])
def shorten():
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "Missing 'url' field"}), 400

    original_url = data["url"]

    if not isinstance(original_url, str):
        return jsonify({"error": "url must be a string"}), 400

    title = data.get("title", None)

    if not original_url or not original_url.strip():
        return jsonify({"error": "URL cannot be empty"}), 400

    if not is_valid_url(original_url):
        return jsonify(
            {"error": "Invalid URL, must start with http:// or https://"}
        ), 400

    short_code = generate_code()
    while URL.select().where(URL.short_code == short_code).exists():
        short_code = generate_code()

    url = URL.create(
        original_url=original_url,
        short_code=short_code,
        title=title,
        is_active=True,
        updated_at=datetime.datetime.now(),
    )

    # Log event
    try:
        Event.create(
            url=url,
            event_type="created",
            details=f'{{"short_code":"{short_code}","original_url":"{original_url}"}}',
        )
    except Exception:
        pass

    # Cache it
    try:
        r = get_redis()
        r.setex(short_code, 3600, original_url)
    except Exception:
        pass

    return jsonify(
        {
            "short_code": short_code,
            "short_url": f"/{short_code}",
            "title": title,
            "is_active": True,
        }
    ), 201


@url_bp.route("/<short_code>", methods=["GET"])
def redirect_url(short_code):
    # Check cache first
    try:
        r = get_redis()
        cached = r.get(f"url:{short_code}")
        if cached:
            # Still log the click event even when serving from cache
            try:
                url = URL.get(URL.short_code == short_code)
                if not url.is_active:
                    return jsonify({"error": "Short URL is inactive"}), 410
                Event.create(
                    url_id=url.id,
                    event_type="click",
                    details=f'{{"short_code":"{short_code}"}}',
                )
            except Exception:
                pass
            return redirect(cached)
        inactive = r.get(f"inactive:{short_code}")
        if inactive:
            return jsonify({"error": "Short URL is inactive"}), 410
    except Exception:
        pass

    # Fall back to DB
    try:
        url = URL.get(URL.short_code == short_code)
        if not url.is_active:
            try:
                r = get_redis()
                r.setex(f"inactive:{short_code}", 3600, "1")
            except Exception:
                pass
            return jsonify({"error": "Short URL is inactive"}), 410

        # Cache and redirect
        try:
            r = get_redis()
            r.setex(f"url:{short_code}", 3600, url.original_url)
        except Exception:
            pass

        # Log click event
        try:
            Event.create(
                url_id=url.id,
                event_type="click",
                details=f'{{"short_code":"{short_code}"}}',
            )
            url.updated_at = datetime.datetime.now()
            url.save()
        except Exception:
            pass

        return redirect(url.original_url)
    except URL.DoesNotExist:
        return jsonify({"error": "Short code not found"}), 404
