"""수면·종합 레포트를 한 주소에서 나눠 여는 웹사이트."""

from __future__ import annotations

import socket
from pathlib import Path

from flask import Flask, abort, render_template, send_from_directory
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from recovery_report.web import create_app as create_recovery_app
from sleep_report.web import create_app as create_sleep_app

ROOT = Path(__file__).resolve().parent
FONTS = ROOT.parent / "assets" / "fonts"
PORT = 8080


def create_site() -> Flask:
    app = Flask(__name__, template_folder=str(ROOT / "templates"))
    app.secret_key = "healmaru-site-local"

    @app.get("/fonts/<name>")
    def fonts(name: str):
        if name not in {"NotoSansKR-Regular.woff2", "NotoSansKR-Bold.woff2"}:
            abort(404)
        return send_from_directory(FONTS, name, mimetype="font/woff2")

    @app.get("/")
    def home():
        return render_template("home.html", share_urls=share_urls())

    app.wsgi_app = DispatcherMiddleware(
        app.wsgi_app,
        {
            "/sleep": create_sleep_app().wsgi_app,
            "/recovery": create_recovery_app().wsgi_app,
        },
    )
    return app


def share_urls() -> list[str]:
    """같은 공유기에 있는 동료가 열 수 있는 주소."""
    found: list[str] = []
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        found.append(sock.getsockname()[0])
        sock.close()
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            found.append(info[4][0])
    except OSError:
        pass
    urls = []
    for ip in found:
        if _private_ipv4(ip) and ip not in urls:
            urls.append(ip)
    return [f"http://{ip}:{PORT}" for ip in urls]


def _private_ipv4(ip: str) -> bool:
    parts = ip.split(".")
    if len(parts) != 4 or not all(part.isdigit() for part in parts):
        return False
    first, second = int(parts[0]), int(parts[1])
    if first == 10:
        return True
    if first == 192 and second == 168:
        return True
    return first == 172 and 16 <= second <= 31


def main() -> None:
    urls = share_urls()
    print("이 컴퓨터에서 열 주소: http://127.0.0.1:8080")
    if urls:
        print("동료에게 보낼 주소: " + "  ".join(urls))
        print("같은 와이파이에 있는 컴퓨터에서 위 주소를 엽니다. 이 창은 닫지 마세요.")
    else:
        print("와이파이에 연결되면 동료에게 보낼 주소가 첫 화면에 나옵니다. 이 창은 닫지 마세요.")
    create_site().run(host="0.0.0.0", port=PORT, debug=False)
