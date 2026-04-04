from flask import Blueprint, jsonify, request, redirect
import random
import string
import redis
import os
from app.models.url import URL

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

    if not original_url or not original_url.strip():
        return jsonify({"error": "URL cannot be empty"}), 400

    if not is_valid_url(original_url):
        return jsonify(
            {"error": "Invalid URL, must start with http:// or https://"}
        ), 400

    short_code = generate_code()
    while URL.select().where(URL.short_code == short_code).exists():
        short_code = generate_code()

    URL.create(original_url=original_url, short_code=short_code)

    # Cache the new short code immediately
    try:
        r = get_redis()
        r.setex(short_code, 3600, original_url)  # cache for 1 hour
    except Exception:
        pass  # if Redis is down, still work without cache

    return jsonify({"short_code": short_code, "short_url": f"/{short_code}"}), 201


@url_bp.route("/<short_code>", methods=["GET"])
def redirect_url(short_code):
    # Check cache first
    try:
        r = get_redis()
        cached_url = r.get(short_code)
        if cached_url:
            return redirect(cached_url)
    except Exception:
        pass  # if Redis is down, fall through to DB

    # Fall back to DB
    try:
        url = URL.get(URL.short_code == short_code)
        # Cache it for next time
        try:
            r = get_redis()
            r.setex(short_code, 3600, url.original_url)
        except Exception:
            pass
        return redirect(url.original_url)
    except URL.DoesNotExist:
        return jsonify({"error": "Short code not found"}), 404
