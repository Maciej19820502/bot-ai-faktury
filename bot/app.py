"""Flask web application — dashboard, config editor, log viewer."""

import os
import logging
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash

from bot.config import load_config, save_config
from bot import logger_db, sanitizer, poller

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "templates"),
        static_folder=os.path.join(BASE_DIR, "static"),
    )
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
    app.config["TEMPLATES_AUTO_RELOAD"] = True

    @app.context_processor
    def inject_now():
        return {"now": datetime.now().strftime("%Y-%m-%d %H:%M")}

    # ── Dashboard ──────────────────────────────────────────

    @app.route("/")
    def dashboard():
        config = load_config()
        logs = logger_db.get_recent_logs(20)

        # Simple stats
        today = datetime.now().strftime("%Y-%m-%d")
        today_logs = [l for l in logs if l["timestamp"].startswith(today)]
        stats = {
            "total": len(today_logs),
            "replied": sum(1 for l in today_logs if l["action_taken"] == "replied"),
            "errors": sum(1 for l in today_logs if l["action_taken"] == "error"),
        }

        return render_template(
            "dashboard.html",
            logs=logs,
            stats=stats,
            poller_status="Aktywny" if app.config.get("POLLER_RUNNING") else "Zatrzymany",
            polling_interval=config.get("polling_interval_seconds", 60),
        )

    # ── Poll now ───────────────────────────────────────────

    @app.route("/poll-now", methods=["POST"])
    def poll_now():
        try:
            count = poller.poll_once()
            flash(f"Sprawdzono skrzynkę. Przetworzono wiadomości: {count}", "success")
        except Exception as e:
            flash(f"Błąd pollingu: {e}", "error")
        return redirect(url_for("dashboard"))

    # ── Config editor ──────────────────────────────────────

    @app.route("/config", methods=["GET"])
    def config_page():
        config = load_config()
        return render_template("config_editor.html", config=config)

    @app.route("/config", methods=["POST"])
    def config_save():
        config = load_config()

        # Credentials
        config["gmail_user"] = request.form.get("gmail_user", "").strip()
        gmail_pw = request.form.get("gmail_app_password", "").strip()
        if gmail_pw:
            config["gmail_app_password"] = gmail_pw.replace(" ", "")
        anthropic_key = request.form.get("anthropic_api_key", "").strip()
        if anthropic_key:
            config["anthropic_api_key"] = anthropic_key

        config["polling_interval_seconds"] = int(request.form.get("polling_interval_seconds", 60))
        config["escalation_email"] = request.form.get("escalation_email", "")
        config["max_email_length"] = int(request.form.get("max_email_length", 2000))
        config["anthropic_model"] = request.form.get("anthropic_model", "claude-sonnet-4-20250514")
        config["response_tone"] = request.form.get("response_tone", "profesjonalny i uprzejmy")

        # Parse domains
        domains_text = request.form.get("allowed_domains", "")
        domains = {}
        for line in domains_text.strip().splitlines():
            if "=" in line:
                domain, name = line.split("=", 1)
                domains[domain.strip()] = name.strip()
        config["allowed_domains"] = domains

        save_config(config)
        flash("Konfiguracja zapisana.", "success")
        return redirect(url_for("config_page"))

    # ── Prompt editor ──────────────────────────────────────

    @app.route("/prompts", methods=["GET"])
    def prompts_page():
        config = load_config()
        return render_template("prompts.html", config=config)

    @app.route("/prompts", methods=["POST"])
    def prompts_save():
        config = load_config()
        config["classification_prompt"] = request.form.get("classification_prompt", "")
        config["response_prompt"] = request.form.get("response_prompt", "")
        save_config(config)
        flash("Prompty zapisane.", "success")
        return redirect(url_for("prompts_page"))

    @app.route("/test-sanitize", methods=["POST"])
    def test_sanitize():
        config = load_config()
        test_input = request.form.get("test_input", "")
        sanitized = sanitizer.sanitize(test_input, config.get("max_email_length", 2000))
        wrapped = sanitizer.wrap_for_llm(sanitized)
        return render_template(
            "prompts.html",
            config=config,
            test_input=test_input,
            sanitized_output=wrapped,
        )

    # ── Logs ───────────────────────────────────────────────

    @app.route("/logs")
    def logs_page():
        date_from = request.args.get("date_from", "")
        date_to = request.args.get("date_to", "")
        sender = request.args.get("sender", "")

        if date_from or date_to or sender:
            logs = logger_db.get_logs_filtered(date_from, date_to, sender)
        else:
            logs = logger_db.get_recent_logs(100)

        return render_template(
            "logs.html",
            logs=logs,
            date_from=date_from,
            date_to=date_to,
            sender=sender,
        )

    return app
