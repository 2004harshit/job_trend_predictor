"""
src/api/app.py
==============
Flask application factory.

Registers:
  - Fresher blueprint   → /api/fresher/*   (recommendations + analytics)
  - Counselor blueprint → /api/counselor/* (market pulse, skill gap, etc.)
  - Global health       → /api/health
"""

import logging
import os
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)  # enable CORS for all origins (restrict in production if needed)

    # ── register blueprints ──────────────────────────────────────────────────
    from src.api.fresher.routes  import fresher_bp
    from src.api.counselor.routes import counselor_bp

    app.register_blueprint(fresher_bp,   url_prefix="/api/fresher")
    app.register_blueprint(counselor_bp, url_prefix="/api/counselor")

    # ── global health check ──────────────────────────────────────────────────
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({
            "status":    "healthy",
            "timestamp": datetime.now().isoformat(),
            "service":   "Job Trend Predictor API",
            "version":   "2.0.0",
            "data_source": os.environ.get("DATA_SOURCE", "csv"),
            "features": {
                "fresher":   "/api/fresher/",
                "counselor": "/api/counselor/",
            },
        })

    # ── 404 / 500 handlers ───────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error":   "Not found",
            "message": "The requested endpoint does not exist",
            "tip":     "Try GET /api/health to see available features",
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "error":   "Internal server error",
            "message": "An unexpected error occurred — check server logs",
        }), 500

    logger.info("Flask app created  ✓  blueprints: fresher, counselor")
    return app