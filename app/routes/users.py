from flask import Blueprint, jsonify, request
import datetime
import csv
import io
from app.models.user import User

users_bp = Blueprint("users", __name__)


@users_bp.route("/users", methods=["GET"])
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    users = User.select().order_by(User.id).paginate(page, per_page)
    return jsonify(
        [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
    ), 200


@users_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    try:
        u = User.get_by_id(user_id)
        return jsonify(
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
        ), 200
    except User.DoesNotExist:
        return jsonify({"error": "User not found"}), 404


@users_bp.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing request body"}), 400

    username = data.get("username")
    email = data.get("email")

    if username is None or email is None:
        return jsonify({"error": "Missing username or email"}), 400

    if not isinstance(username, str) or not isinstance(email, str):
        return jsonify({"error": "Invalid data types"}), 400

    if not username.strip() or not email.strip():
        return jsonify({"error": "Missing username or email"}), 400

    if "@" not in email:
        return jsonify({"error": "Invalid email"}), 400

    try:
        existing = User.get(User.username == username)
        existing.email = email
        existing.save()
        return jsonify(
            {
                "id": existing.id,
                "username": existing.username,
                "email": existing.email,
                "created_at": existing.created_at.isoformat()
                if existing.created_at
                else None,
            }
        ), 201
    except User.DoesNotExist:
        pass

    # If user already exists with same username AND email, return them
    try:
        existing = User.get((User.username == username) & (User.email == email))
        return jsonify(
            {
                "id": existing.id,
                "username": existing.username,
                "email": existing.email,
                "created_at": existing.created_at.isoformat()
                if existing.created_at
                else None,
            }
        ), 201
    except User.DoesNotExist:
        pass

    try:
        u = User.create(
            username=username, email=email, created_at=datetime.datetime.now()
        )
        return jsonify(
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "created_at": u.created_at.isoformat(),
            }
        ), 201
    except Exception as e:
        return jsonify({"error": "Username or email already exists"}), 400


@users_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    try:
        u = User.get_by_id(user_id)
    except User.DoesNotExist:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing request body"}), 400

    if "username" in data:
        if not isinstance(data["username"], str):
            return jsonify({"error": "Invalid data type for username"}), 400
        u.username = data["username"]
    if "email" in data:
        if not isinstance(data["email"], str):
            return jsonify({"error": "Invalid data type for email"}), 400
        u.email = data["email"]

    u.save()
    return jsonify(
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
    ), 200


@users_bp.route("/users/bulk", methods=["POST"])
def bulk_import_users():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    content = file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    imported = 0
    for row in reader:
        try:
            User.get_or_create(
                id=int(row["id"]),
                defaults={
                    "username": row["username"],
                    "email": row["email"],
                    "created_at": row["created_at"],
                },
            )
            imported += 1
        except Exception:
            continue

    return jsonify({"imported": imported}), 201


@users_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        u = User.get_by_id(user_id)
        u.delete_instance()
        return jsonify({"message": "User deleted"}), 200
    except User.DoesNotExist:
        return jsonify({"error": "User not found"}), 404
