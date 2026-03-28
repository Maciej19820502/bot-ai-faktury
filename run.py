"""Entry point — starts Flask app + background email poller."""

import os
import sys
import logging

from dotenv import load_dotenv

# Ensure project root is on the path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(ROOT_DIR, "bot.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def main():
    from bot.generate_test_data import ensure_test_data
    from bot.logger_db import init_db
    from bot.config import load_config
    from bot.app import create_app
    from bot.poller import poll_once

    # Step 1: Generate test data if needed
    ensure_test_data()

    # Step 2: Initialize database
    init_db()
    logger.info("Database initialized.")

    # Step 3: Create Flask app
    app = create_app()

    # Step 4: Start background poller
    config = load_config()
    interval = config.get("polling_interval_seconds", 60)

    has_gmail = (
        bool(config.get("gmail_user") or os.environ.get("GMAIL_USER"))
        and bool(config.get("gmail_app_password") or os.environ.get("GMAIL_APP_PASSWORD"))
    )

    if has_gmail:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            scheduler = BackgroundScheduler()
            scheduler.add_job(poll_once, "interval", seconds=interval, id="email_poller")
            scheduler.start()
            app.config["POLLER_RUNNING"] = True
            logger.info("Email poller started (every %ds).", interval)
        except Exception as e:
            logger.warning("Could not start poller: %s", e)
            app.config["POLLER_RUNNING"] = False
    else:
        logger.warning(
            "GMAIL_USER / GMAIL_APP_PASSWORD not set — poller disabled.\n"
            "Set them in .env file. See .env.example for format.",
        )
        app.config["POLLER_RUNNING"] = False

    # Step 5: Launch Flask
    print("\n" + "=" * 60)
    print("  BOT AI — Prototyp obsługi zapytań AP/AR")
    print("  Panel: http://localhost:5000")
    print("=" * 60 + "\n")

    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
