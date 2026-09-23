"""계산된 섹션을 HTML과 PDF로 바꿉니다."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from reportkit.errors import ReportError
from reportkit.pdf import html_to_pdf
from sleep_report.charts import hours_label

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def render_html(model: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["hours"] = hours_label
    template = env.get_template("report.html.j2")
    return template.render(**model)


def render_pdf(html: str) -> bytes:
    font = ROOT / "assets" / "fonts" / "NotoSansKR-Regular.otf"
    if not font.is_file():
        raise ReportError("한글 폰트를 찾을 수 없습니다.")
    return html_to_pdf(html, ROOT)
