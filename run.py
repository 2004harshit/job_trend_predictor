"""
run.py  —  Single entry point for Job Trend Predictor API
==========================================================

Usage
-----
# Use CSV (default — no DB needed)
python run.py

# Use Neon PostgreSQL
python run.py --db neon

# Use local PostgreSQL
python run.py --db postgres

# Change port / host
python run.py --port 8080 --host 127.0.0.1

# Production mode (uses gunicorn if installed, else waitress)
python run.py --env production --db csv

Full option list
----------------
  --db      {csv, neon, postgres}   Data source  (default: csv)
  --port    INT                      Port         (default: 5000)
  --host    STR                      Host         (default: 0.0.0.0)
  --env     {development, production} Flask env   (default: development)
  --debug                            Force debug mode on
"""

import argparse
import os
import sys
import logging

# ── make sure project root is on the path ──────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("run")


# ── CLI ─────────────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Job Trend Predictor API — unified launcher",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--db",
        choices=["csv", "neon", "postgres"],
        default="csv",
        help=(
            "Data source to use:\n"
            "  csv      — read from local CSV file  (default)\n"
            "  neon     — Neon cloud PostgreSQL (needs NEON_URL in .env)\n"
            "  postgres — local/self-hosted PostgreSQL (needs LOCAL_PG_* in .env)\n"
        ),
    )
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on (default: 5000)")
    parser.add_argument("--host", default="0.0.0.0",   help="Host to bind  (default: 0.0.0.0)")
    parser.add_argument(
        "--env",
        choices=["development", "production"],
        default="development",
        help="Flask environment (default: development)",
    )
    parser.add_argument("--debug", action="store_true", help="Force debug mode on")
    return parser.parse_args()


def main():
    args = parse_args()

    # ── load .env ────────────────────────────────────────────────────────────
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(ROOT, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info(f"Loaded .env from {env_path}")
        else:
            logger.warning(".env file not found — using system environment variables only")
    except ImportError:
        logger.warning("python-dotenv not installed — skipping .env load")

    # ── tell the app which DB to use via env var ─────────────────────────────
    os.environ["DATA_SOURCE"] = args.db
    os.environ["FLASK_ENV"]   = args.env

    logger.info(f"Data source : {args.db.upper()}")
    logger.info(f"Environment : {args.env}")
    logger.info(f"Listening on: http://{args.host}:{args.port}")

    # ── import app AFTER env vars are set ────────────────────────────────────
    from src.api.app import create_app
    app = create_app()

    debug = args.debug or args.env == "development"

    if args.env == "production":
        # try gunicorn → waitress → flask dev server
        try:
            import gunicorn.app.base  # noqa: F401

            class StandaloneGunicorn(gunicorn.app.base.BaseApplication):
                def __init__(self, application, options=None):
                    self.options    = options or {}
                    self.application = application
                    super().__init__()

                def load_config(self):
                    for key, value in self.options.items():
                        self.cfg.set(key.lower(), value)

                def load(self):
                    return self.application

            options = {
                "bind":    f"{args.host}:{args.port}",
                "workers": 2,
                "timeout": 120,
            }
            logger.info("Starting with Gunicorn")
            StandaloneGunicorn(app, options).run()
        except ImportError:
            try:
                from waitress import serve
                logger.info("Starting with Waitress")
                serve(app, host=args.host, port=args.port)
            except ImportError:
                logger.warning("Neither gunicorn nor waitress found — falling back to Flask dev server")
                app.run(host=args.host, port=args.port, debug=False)
    else:
        app.run(host=args.host, port=args.port, debug=debug)


if __name__ == "__main__":
    main()