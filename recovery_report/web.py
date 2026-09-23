"""종합 레포트 로컬 웹 화면."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, send_file, send_from_directory, url_for

from recovery_report import __version__
from recovery_report.engine import LOGIC_PATH, ROOT, build_model, load_rules
from recovery_report.render import render_html, render_pdf
from reportkit.errors import ReportError

PACKAGE = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs" / "recovery"


def create_app() -> Flask:
    app = Flask(__name__, template_folder=str(PACKAGE / "templates"))
    app.secret_key = "recovery-report-local"
    OUTPUT.mkdir(parents=True, exist_ok=True)

    @app.get("/fonts/<name>")
    def fonts(name: str):
        if name not in {"NotoSansKR-Regular.otf", "NotoSansKR-Bold.otf"}:
            abort(404)
        return send_from_directory(ROOT.parent / "assets" / "fonts", name)

    @app.get("/")
    def index():
        rules = load_rules()
        return render_template(
            "index.html",
            rules=rules,
            app_version=__version__,
            section_count=len(rules["sections"]),
        )

    @app.get("/template")
    def template_file():
        return send_file(LOGIC_PATH, as_attachment=True, download_name="종합레포트_양식.xlsx")

    @app.post("/generate")
    def generate():
        upload = request.files.get("file")
        if upload is None or not upload.filename.lower().endswith(".xlsx"):
            flash("xlsx 파일을 올려 주세요.")
            return redirect(url_for("index"))
        report_id = uuid.uuid4().hex
        folder = OUTPUT / report_id
        folder.mkdir(parents=True, exist_ok=True)
        source = folder / "input.xlsx"
        upload.save(source)
        try:
            model = build_model(source)
            pdf = render_pdf(render_html(model))
        except ReportError as exc:
            flash(str(exc))
            return redirect(url_for("index"))
        (folder / "report.pdf").write_bytes(pdf)
        (folder / "log.json").write_text(json.dumps(_log(model), ensure_ascii=False, indent=2), encoding="utf-8")
        return redirect(url_for("result", report_id=report_id))

    @app.get("/result/<report_id>")
    def result(report_id: str):
        folder = _folder(report_id)
        log = json.loads((folder / "log.json").read_text(encoding="utf-8"))
        return render_template("result.html", report_id=report_id, log=log)

    @app.get("/download/<report_id>/<kind>")
    def download(report_id: str, kind: str):
        folder = _folder(report_id)
        if kind == "pdf":
            return send_file(folder / "report.pdf", as_attachment=True, download_name="종합레포트.pdf")
        if kind == "log":
            return send_file(folder / "log.json", as_attachment=True, download_name="종합레포트_로그.json")
        return redirect(url_for("index"))

    return app


def _folder(report_id: str) -> Path:
    if not report_id.isalnum():
        raise ReportError("레포트를 찾을 수 없습니다.")
    folder = OUTPUT / report_id
    if not folder.is_dir():
        raise ReportError("레포트를 찾을 수 없습니다.")
    return folder


def _log(model: dict) -> dict:
    return {
        "logic_version": model["version"],
        "logic_updated_at": model["updated_at"],
        "source_file": model["source_name"],
        "generated_at": model["generated_at"],
        "filled_count": model["filled_count"],
        "total_count": model["total_count"],
        "missing_fields": model["missing_labels"],
        "sections": [
            {"id": item["id"], "title": item["title"], "status": item["status"], "reason": item["reason"]}
            for item in model["sections"]
        ],
        "omitted_sections": model["omitted"],
    }


def main() -> None:
    create_app().run(host="127.0.0.1", port=8082, debug=False)
