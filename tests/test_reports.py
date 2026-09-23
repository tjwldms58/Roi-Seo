import shutil
from pathlib import Path

import openpyxl
import pytest

from recovery_report.engine import LOGIC_PATH as RECOVERY_LOGIC
from recovery_report.engine import build_model as build_recovery
from recovery_report.render import render_html as recovery_html
from recovery_report.render import render_pdf as recovery_pdf
from recovery_report.web import create_app as recovery_app
from sleep_report.engine import LOGIC_PATH as SLEEP_LOGIC
from sleep_report.engine import build_model as build_sleep
from sleep_report.render import render_html as sleep_html
from sleep_report.render import render_pdf as sleep_pdf
from sleep_report.web import create_app as sleep_app


def _copy(src: Path, folder: Path, name: str = "input.xlsx") -> Path:
    dest = folder / name
    shutil.copy(src, dest)
    return dest


def test_sleep_sample_uses_workbook_text(tmp_path):
    model = build_sleep(_copy(SLEEP_LOGIC, tmp_path))
    pages = {item["page"]: item for item in model["sections"]}
    assert "03" in pages
    assert "301" in pages["03"]["meaning"] or "301" in pages["03"]["stat"]
    assert "06+" in pages
    assert model["filled_count"] > 0
    assert model["total_count"] >= model["filled_count"]
    assert model["version"] == "19차"
    html = sleep_html(model)
    assert "19차" in html
    assert "HEALMARU CARE" in html
    assert "데이터 기반 참고 리포트" in html
    assert "생략된 섹션은 없습니다" in html or "생성 정보" in html
    pdf = sleep_pdf(html)
    assert pdf.startswith(b"%PDF")


def test_sleep_omits_wake_duration_without_measured_time(tmp_path):
    path = _copy(SLEEP_LOGIC, tmp_path)
    book = openpyxl.load_workbook(path)
    sheet = book["S1_Input_Raw"]
    for row in range(5, 12):
        sheet.cell(row, 18).value = None
    book.save(path)
    model = build_sleep(path)
    omitted = {item["page"] for item in model["omitted"]}
    assert "06+" in omitted
    assert "03" in {item["page"] for item in model["sections"]}


def test_sleep_reference_comes_from_config_sheet(tmp_path):
    path = _copy(SLEEP_LOGIC, tmp_path)
    book = openpyxl.load_workbook(path)
    config = book["S3_Config"]
    config["B6"].value = 50
    config["D6"].value = 50
    book.save(path)
    model = build_sleep(path)
    page = next(item for item in model["sections"] if item["page"] == "04")
    assert "50%" in page["meaning"] or "50%" in page["stat"]


def test_sleep_blank_core_omits_sections(tmp_path):
    path = _copy(SLEEP_LOGIC, tmp_path)
    book = openpyxl.load_workbook(path)
    sheet = book["S1_Input_Raw"]
    for row in range(5, 12):
        for col in range(3, 20):
            sheet.cell(row, col).value = None
    book.save(path)
    model = build_sleep(path)
    assert model["sections"] == []
    assert model["omitted"]
    assert model["filled_count"] < model["total_count"]


def test_recovery_sample_keeps_capability_page(tmp_path):
    model = build_recovery(_copy(RECOVERY_LOGIC, tmp_path))
    ids = [item["id"] for item in model["sections"]]
    assert "cover" in ids
    assert "capability" in ids
    assert "cancer" in ids
    assert model["content"]["name"].startswith("김OO")
    assert model["content"]["arm_delta"].startswith("-2")
    # 양식의 예비 입력칸(추가 지표 행)은 샘플에서 비어 있다. 섹션은 그대로 그린다.
    assert 0 < model["filled_count"] < model["total_count"]
    assert model["omitted"] == []
    html = recovery_html(model)
    assert "HEALMARU CARE" in html
    assert "데이터 기반 참고 리포트" in html
    pdf = recovery_pdf(html)
    assert pdf.startswith(b"%PDF")


def test_recovery_omits_capability_when_names_missing(tmp_path):
    path = _copy(RECOVERY_LOGIC, tmp_path)
    book = openpyxl.load_workbook(path)
    sheet = book["04_운동별체력변화"]
    for row in range(7, 13):
        for col in range(1, 5):
            sheet.cell(row, col).value = None
    book.save(path)
    model = build_recovery(path)
    assert "capability" not in [item["id"] for item in model["sections"]]
    assert any(item["id"] == "capability" for item in model["omitted"])
    assert "summary" in [item["id"] for item in model["sections"]]
    assert model["filled_count"] < model["total_count"]


def test_web_uploads(tmp_path, monkeypatch):
    sleep_client = sleep_app().test_client()
    page = sleep_client.get("/")
    assert "19차" in page.get_data(as_text=True)
    with SLEEP_LOGIC.open("rb") as handle:
        response = sleep_client.post(
            "/generate",
            data={"file": (handle, "sleep.xlsx")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
    assert "PDF 받기" in response.get_data(as_text=True)

    recovery_client = recovery_app().test_client()
    with RECOVERY_LOGIC.open("rb") as handle:
        response = recovery_client.post(
            "/generate",
            data={"file": (handle, "recovery.xlsx")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
    assert "PDF 받기" in response.get_data(as_text=True)
    template = recovery_client.get("/template")
    assert template.status_code == 200
    assert template.data[:2] == b"PK"
