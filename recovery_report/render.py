"""종합 레포트 HTML과 PDF."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from reportkit.errors import ReportError

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def render_html(model: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    return env.get_template("report.html.j2").render(**model)


def render_pdf(html: str) -> bytes:
    if not (ROOT / "assets" / "fonts" / "NotoSansKR-Regular.otf").is_file():
        raise ReportError("한글 폰트를 찾을 수 없습니다.")
    return HTML(string=html, base_url=str(ROOT)).write_pdf()
