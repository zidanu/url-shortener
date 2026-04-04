from flask import Blueprint, jsonify, request
from app.models.event import Event
import json

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
    query = Event.select().order_by(Event.id)
    if url_id:
        query = query.where(Event.url_id == url_id)
    return jsonify([event_to_dict(e) for e in query]), 200
