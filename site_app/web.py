"""수면·종합 레포트를 한 주소에서 나눠 여는 웹사이트."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, abort, render_template, send_from_directory
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from recovery_report.web import create_app as create_recovery_app
from sleep_report.web import create_app as create_sleep_app

ROOT = Path(__file__).resolve().parent
FONTS = ROOT.parent / "assets" / "fonts"


def create_site() -> Flask:
    app = Flask(__name__, template_folder=str(ROOT / "templates"))
    app.secret_key = "healmaru-site-local"

    @app.get("/fonts/<name>")
    def fonts(name: str):
        if name not in {"NotoSansKR-Regular.otf", "NotoSansKR-Bold.otf"}:
            abort(404)
        return send_from_directory(FONTS, name)

    @app.get("/")
    def home():
        return render_template("home.html")

    app.wsgi_app = DispatcherMiddleware(
        app.wsgi_app,
        {
            "/sleep": create_sleep_app().wsgi_app,
            "/recovery": create_recovery_app().wsgi_app,
        },
    )
    return app


def main() -> None:
    create_site().run(host="127.0.0.1", port=8080, debug=False)
