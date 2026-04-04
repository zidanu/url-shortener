from dotenv import load_dotenv
from flask import Flask, jsonify

from app.database import init_db
from app.routes import register_routes


def create_app():
    load_dotenv()
    app = Flask(__name__)
    init_db(app)
    from app import models  # noqa: F401 - registers models with Peewee
    from app.database import db
    from app.models.url import URL

    with app.app_context():
        db.create_tables([URL])
    register_routes(app)

    @app.route("/health")
    def health():
        return jsonify(status="ok")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app
