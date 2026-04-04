from flask import Blueprint, jsonify, request, redirect
import random
import string
from app.models.url import URL

url_bp = Blueprint("url", __name__)


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

    # Generate a unique short code
    short_code = generate_code()
    while URL.select().where(URL.short_code == short_code).exists():
        short_code = generate_code()

    URL.create(original_url=original_url, short_code=short_code)
    return jsonify({"short_code": short_code, "short_url": f"/{short_code}"}), 201


@url_bp.route("/<short_code>", methods=["GET"])
def redirect_url(short_code):
    try:
        url = URL.get(URL.short_code == short_code)
        return redirect(url.original_url)
    except URL.DoesNotExist:
        return jsonify({"error": "Short code not found"}), 404
