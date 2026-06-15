from flask import Flask, jsonify

from app.api.routes import api


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(api)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app
