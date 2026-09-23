"""샤오미 수면 표에서 로직 엑셀 S1·S2가 읽는 칸만 옮깁니다."""

from __future__ import annotations

import re
import shutil
from datetime import date, datetime, time
from pathlib import Path

import openpyxl

from reportkit.errors import ReportError
from sleep_report.engine import LOGIC_PATH

DAY_SLOTS = 7
FIRST_DATA_ROW = 5
WEEKDAYS = "월화수목금토일"

# 샤오미 머리글 → 로직 S1 머리글. 로직에 없는 칸(낮잠, 스트레스, 암종 등)은 넣지 않습니다.
COLUMN_MAP = {
    "잠든 시각": "취침시각",
    "깬 시각": "기상시각",
    "수면준비시간 (분)": "입면잠복기_분(SOL)",
    "깊은수면 시간": "깊은수면_분",
    "얕은수면 시간": "얕은수면_분",
    "REM 시간": "렘수면_분",
    "수면시 평균 심박수 (BPM)": "심박수_평균_bpm",
    "평균 호흡수 (BPM)": "호흡수_평균_회/분",
    "평균 혈중 산소포화도 (%)": "SpO2_평균_%",
    "활력점수": "활력점수_기기값(0~100)",
    "각성 (분)": "각성시간_실측_분(기기값,선택)",
    "수면효율성 (%)": "수면효율_기기값_%(선택,17차)",
}
DURATION_HEADERS = {"깊은수면 시간", "얕은수면 시간", "REM 시간"}
TIME_HEADERS = {"잠든 시각", "깬 시각"}
PROFILE_MAP = {
    "고객명": "이름",
    "성별": "성별",
    "나이": "나이",
    "체중(KG)": "체중",
    "키(CM)": "키",
}


def workbook_kind(path: Path) -> str:
    book = openpyxl.load_workbook(path, read_only=True, data_only=False)
    try:
        if "S1_Input_Raw" in book.sheetnames:
            return "logic"
        if _source_sheet(book) is not None:
            return "xiaomi"
    finally:
        book.close()
    return "unknown"


def list_people(path: Path) -> list[dict]:
    book = openpyxl.load_workbook(path, data_only=False)
    try:
        sheet, header_row, headers = _require_source(book)
        grouped: dict[str, list[dict]] = {}
        order: list[str] = []
        for row in range(header_row + 1, sheet.max_row + 1):
            record = _read_row(sheet, row, headers)
            if record is None:
                continue
            name = record["name"]
            if name not in grouped:
                grouped[name] = []
                order.append(name)
            grouped[name].append(record)
    finally:
        book.close()

    people = []
    for name in order:
        rows = grouped[name]
        dated = [item["date"] for item in rows if item["date"]]
        nights = sum(1 for item in rows if _is_night(item))
        profile = _profile_from(rows)
        people.append(
            {
                "name": name,
                "age": profile["age"],
                "sex": profile["sex"],
                "start": dated[0].isoformat() if dated else "",
                "end": dated[-1].isoformat() if dated else "",
                "days": len(rows),
                "nights": nights,
            }
        )
    return people


def fill_logic(source: Path, dest: Path, person_name: str) -> str:
    """로직 양식 복사본의 입력칸만 채웁니다. 수식 칸은 그대로 둡니다.

    로직 시트가 7일만 받으므로, 그보다 길면 최근 7일만 넣습니다.
    반환값은 결과 화면에 보여줄 안내 문장입니다. 안내가 없으면 빈 문자열입니다.
    """
    shutil.copy(LOGIC_PATH, dest)
    book = openpyxl.load_workbook(source, data_only=False)
    logic = openpyxl.load_workbook(dest)
    try:
        sheet, header_row, headers = _require_source(book)
        rows = []
        for row in range(header_row + 1, sheet.max_row + 1):
            record = _read_row(sheet, row, headers)
            if record is None or record["name"] != person_name:
                continue
            rows.append(record)
        if not rows:
            raise ReportError(f"'{person_name}' 님의 수면 기록을 찾지 못했습니다.")
        rows.sort(key=lambda item: item["date"] or date.min)
        notice = ""
        if len(rows) > DAY_SLOTS:
            skipped = len(rows) - DAY_SLOTS
            rows = rows[-DAY_SLOTS:]
            notice = (
                f"{person_name} 님의 기록이 {skipped + DAY_SLOTS}일이라, "
                "수면 로직이 받는 최근 7일만 넣었습니다."
            )
        _write_inputs(logic, rows)
        logic.save(dest)
        return notice
    finally:
        book.close()
        logic.close()


def _require_source(book):
    found = _source_sheet(book)
    if found is None:
        names = []
        for sheet in book.worksheets:
            for col in range(1, min(sheet.max_column or 1, 40) + 1):
                value = sheet.cell(1, col).value
                if value:
                    names.append(str(value).strip())
        shown = ", ".join(names[:12]) if names else "없음"
        raise ReportError(
            "샤오미 수면 표에서 필요한 칸을 찾지 못했습니다. "
            "1행에 날짜, 고객명, 잠든 시각이 있어야 합니다. "
            f"찾은 머리글: {shown}"
        )
    return found


def _source_sheet(book):
    for sheet in book.worksheets:
        for row in range(1, 4):
            headers = _header_map(sheet, row)
            if {"날짜", "고객명", "잠든 시각"} <= set(headers):
                return sheet, row, headers
    return None


def _header_map(sheet, row: int) -> dict[str, int]:
    found = {}
    for col in range(1, (sheet.max_column or 0) + 1):
        value = sheet.cell(row, col).value
        if value is None:
            continue
        text = str(value).strip()
        if text:
            found[text] = col
    return found


def _read_row(sheet, row: int, headers: dict[str, int]) -> dict | None:
    name = _text(sheet.cell(row, headers["고객명"]).value)
    day = _as_date(sheet.cell(row, headers["날짜"]).value)
    if not name and day is None:
        return None
    if not name:
        name = "이름 없음"
    values = {}
    for source_name, col in headers.items():
        if source_name in COLUMN_MAP or source_name in PROFILE_MAP:
            values[source_name] = sheet.cell(row, col).value
    return {"name": name, "date": day, "values": values}


def _profile_from(rows: list[dict]) -> dict:
    profile = {"age": "", "sex": ""}
    for record in rows:
        if not profile["age"]:
            profile["age"] = _text(record["values"].get("나이"))
        if not profile["sex"]:
            profile["sex"] = _text(record["values"].get("성별"))
    return profile


def _is_night(record: dict) -> bool:
    values = record["values"]
    return all(_text(values.get(name)) for name in ("잠든 시각", "깬 시각", "깊은수면 시간"))


def _write_inputs(logic, rows: list[dict]) -> None:
    raw = logic["S1_Input_Raw"]
    raw_headers = _header_map(raw, 4)
    for row in range(FIRST_DATA_ROW, FIRST_DATA_ROW + DAY_SLOTS):
        for col in range(1, 20):
            raw.cell(row, col).value = None
    for offset, record in enumerate(rows):
        row = FIRST_DATA_ROW + offset
        if record["date"]:
            raw.cell(row, raw_headers["요일"]).value = WEEKDAYS[record["date"].weekday()]
            cell = raw.cell(row, raw_headers["날짜"])
            cell.value = record["date"]
            cell.number_format = "YYYY-MM-DD"
        for source_name, logic_name in COLUMN_MAP.items():
            if logic_name not in raw_headers or source_name not in record["values"]:
                continue
            written = _logic_value(source_name, record["values"].get(source_name))
            cell = raw.cell(row, raw_headers[logic_name])
            cell.value = written
            if source_name in TIME_HEADERS and isinstance(written, time):
                cell.number_format = "HH:MM"

    profile = logic["S2_Input_Profile"]
    targets = {}
    for row in range(5, 10):
        label = _text(profile.cell(row, 1).value)
        for prefix in ("이름", "성별", "나이", "체중", "키"):
            if label.startswith(prefix):
                targets[prefix] = row
    for row in targets.values():
        profile.cell(row, 2).value = None
    chosen = _profile_from(rows)
    weight = _first_number(rows, "체중(KG)")
    height = _first_number(rows, "키(CM)")
    written = {
        "이름": rows[0]["name"] if rows[0]["name"] != "이름 없음" else None,
        "성별": chosen["sex"] or None,
        "나이": _number(chosen["age"]) if chosen["age"] else None,
        "체중": weight,
        "키": height,
    }
    for prefix, value in written.items():
        if prefix in targets and value is not None:
            profile.cell(targets[prefix], 2).value = value
    if weight is None or height is None:
        # 체중·키가 없으면 BMI/BMR 수식이 0으로 계산되어 음수가 됩니다. 그 칸은 비웁니다.
        for row in range(5, profile.max_row + 1):
            label = _text(profile.cell(row, 1).value)
            if label.startswith(("BMI", "기초대사량")):
                profile.cell(row, 2).value = None


def _logic_value(source_name: str, value):
    if source_name in TIME_HEADERS:
        return _as_time(value)
    if source_name in DURATION_HEADERS:
        return _duration_minutes(value)
    if source_name == "날짜":
        return _as_date(value)
    return _number(value)


def _first_number(rows: list[dict], source_name: str):
    for record in rows:
        number = _number(record["values"].get(source_name))
        if number is not None:
            return number
    return None


def _duration_minutes(value):
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    text = str(value).strip()
    if not text:
        return None
    match = re.fullmatch(r"(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?", text, flags=re.IGNORECASE)
    if match and (match.group(1) or match.group(2)):
        return int(match.group(1) or 0) * 60 + int(match.group(2) or 0)
    return _number(text)


def _as_time(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, time):
        return value
    text = str(value).strip()
    match = re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", text)
    if not match:
        return None
    return time(int(match.group(1)), int(match.group(2)), int(match.group(3) or 0))


def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip() if value is not None else ""
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _number(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if number.is_integer():
        return int(number)
    return number


def _text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()
