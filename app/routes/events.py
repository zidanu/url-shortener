from flask import Blueprint, jsonify, request
from app.models.event import Event
import json
import datetime

events_bp = Blueprint("events", __name__)


def event_to_dict(e):
    details = e.details
    try:
        details = json.loads(e.details) if e.details else None
    except Exception:
        pass
    return {
        "id": e.id,
        "url_id": e.url_id,
        "user_id": e.user_id,
        "event_type": e.event_type,
        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        "details": details,
    }


@events_bp.route("/events", methods=["GET"])
def list_events():
    url_id = request.args.get("url_id", type=int)
    event_type = request.args.get("event_type")
    query = Event.select().order_by(Event.id)
    if url_id:
        query = query.where(Event.url_id == url_id)
    if event_type:
        query = query.where(Event.event_type == event_type)
    return jsonify([event_to_dict(e) for e in query]), 200


@events_bp.route("/events", methods=["POST"])
def create_event():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing request body"}), 400

    url_id = data.get("url_id")
    event_type = data.get("event_type")

    if not url_id or not event_type:
        return jsonify({"error": "Missing url_id or event_type"}), 400

    details = data.get("details")
    if details and not isinstance(details, (dict, str)):
        return jsonify({"error": "Invalid details format"}), 400

    if isinstance(details, dict):
        details = json.dumps(details)

    e = Event.create(
        url_id=url_id,
        user_id=data.get("user_id"),
        event_type=event_type,
        timestamp=datetime.datetime.now(),
        details=details,
    )
    return jsonify(event_to_dict(e)), 201
