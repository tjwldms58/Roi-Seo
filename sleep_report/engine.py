"""로직 엑셀을 계산한 뒤, rules.yaml에 적힌 기준으로 섹션을 고릅니다."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import openpyxl
import yaml

from reportkit.empty import as_text, is_empty
from reportkit.errors import ReportError
from reportkit.office import recalculate

ROOT = Path(__file__).resolve().parent
RULES_PATH = ROOT / "rules.yaml"
LOGIC_PATH = ROOT / "logic" / "sleep_logic.xlsx"
KST = timezone(timedelta(hours=9))


def load_rules(path: Path | None = None) -> dict:
    path = Path(path or RULES_PATH)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data.get("sections"):
        raise ReportError("수면 로직 규칙 파일에 섹션이 없습니다.")
    return data


def build_model(workbook_path: Path, rules: dict | None = None) -> dict:
    rules = rules or load_rules()
    tokens = {str(item).strip().casefold() for item in rules.get("empty_tokens") or []}
    missing_text = rules["document"]["missing_text"]

    calculated = workbook_path.with_suffix(".calculated.xlsx")
    recalculate(workbook_path, calculated)
    book = openpyxl.load_workbook(calculated, data_only=True)
    _require_sheets(book, ["S1_Input_Raw", "S2_Input_Profile", "S4_Calc_Daily", "S7_Output_Summary"])

    raw = book["S1_Input_Raw"]
    profile = book["S2_Input_Profile"]
    daily = book["S4_Calc_Daily"]
    summary = book["S7_Output_Summary"]

    raw_headers = _headers(raw, 4)
    daily_headers = _headers(daily, 4)
    day_rows = _data_rows(raw)
    days = []
    for row in day_rows:
        label = as_text(raw.cell(row, 1).value) or f"{row}"
        raw_values = {name: raw.cell(row, col).value for name, col in raw_headers.items()}
        daily_values = {}
        daily_row = _matching_daily_row(daily, label, row)
        for name, col in daily_headers.items():
            daily_values[name] = daily.cell(daily_row, col).value
        days.append({"label": label, "row": row, "raw": raw_values, "daily": daily_values})

    monitor_headers = list(rules.get("monitor_headers") or [])
    monitored_flags = []
    for day in days:
        present = all(not is_empty(day["raw"].get(name), tokens) for name in monitor_headers)
        day["monitored"] = present
        monitored_flags.append(present)

    profile_fields = _profile_fields(profile, tokens)
    input_total, input_filled, missing_labels = _count_inputs(days, raw_headers, profile_fields, tokens)

    pages = _summary_pages(summary)
    sections = []
    omitted = []
    for spec in rules["sections"]:
        page = str(spec["page"])
        block = pages.get(page)
        title = block["title"] if block else page
        core = list(spec.get("core_headers") or [])
        core_missing = [name for name in core if _column_all_empty(days, name, tokens)]
        if core and len(core_missing) == len(core):
            omitted.append(
                {
                    "page": page,
                    "title": title,
                    "reason": "핵심 항목 없음: " + ", ".join(core_missing),
                }
            )
            continue
        if not block or (is_empty(block["stat"], tokens) and is_empty(block["meaning"], tokens)):
            omitted.append({"page": page, "title": title, "reason": "계산 결과가 비어 있어 생략"})
            continue
        partial_names = [name for name in core if _column_some_empty(days, name, tokens)]
        status = "partial" if partial_names else "full"
        reason = (
            "일부 날짜만 있어 있는 데이터로 계산했습니다."
            if status == "partial"
            else "필요 항목이 있어 전체를 표시했습니다."
        )
        chart_header = _resolve_header(daily_headers, spec.get("chart_header") or "")
        chart = _chart(days, chart_header, spec.get("unit") or "", tokens)
        sections.append(
            {
                "page": page,
                "title": title,
                "status": status,
                "reason": reason,
                "stat": block["stat"] or missing_text,
                "meaning": block["meaning"] or missing_text,
                "suggestion": block["suggestion"] or missing_text,
                "chart": chart,
            }
        )

    name = next((item["value"] for item in profile_fields if "이름" in item["label"]), "")
    dates = [as_text(day["raw"].get("날짜")) for day in days if not is_empty(day["raw"].get("날짜"), tokens)]
    period = ""
    if dates:
        period = dates[0] if len(dates) == 1 else f"{dates[0]} – {dates[-1]}"

    return {
        "document": rules["document"],
        "version": str(rules["version"]),
        "updated_at": str(rules["updated_at"]),
        "name": name or missing_text,
        "name_missing": not name,
        "period": period or missing_text,
        "sections": sections,
        "omitted": omitted,
        "filled_count": input_filled,
        "total_count": input_total,
        "monitored_count": sum(monitored_flags),
        "day_count": len(days),
        "missing_labels": missing_labels,
        "generated_at": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "source_name": Path(workbook_path).name,
    }


def _require_sheets(book, names: list[str]) -> None:
    missing = [name for name in names if name not in book.sheetnames]
    if missing:
        raise ReportError(
            "수면 로직 엑셀 형식이 아닙니다. 필요한 시트가 없습니다: " + ", ".join(missing)
        )


def _headers(sheet, row: int) -> dict[str, int]:
    found = {}
    for col in range(1, sheet.max_column + 1):
        value = sheet.cell(row, col).value
        if value is None:
            continue
        text = str(value).strip()
        if text and not text.startswith("="):
            found[text] = col
    return found


def _data_rows(sheet) -> list[int]:
    rows = []
    for row in range(5, sheet.max_row + 1):
        value = sheet.cell(row, 1).value
        if is_empty(value):
            continue
        text = str(value).strip()
        if text.startswith(("※", "S1", "=")):
            continue
        rows.append(row)
    return rows


def _matching_daily_row(sheet, label: str, fallback: int) -> int:
    for row in range(5, sheet.max_row + 1):
        if as_text(sheet.cell(row, 1).value) == label:
            return row
    return fallback


def _profile_fields(sheet, tokens: set[str]) -> list[dict]:
    fields = []
    for row in range(5, sheet.max_row + 1):
        label = sheet.cell(row, 1).value
        if is_empty(label):
            continue
        text = str(label).strip()
        if text.startswith(("※", "=")) or "자동계산" in text:
            continue
        fields.append({"label": text, "value": "" if is_empty(sheet.cell(row, 2).value, tokens) else as_text(sheet.cell(row, 2).value)})
    return fields


def _count_inputs(days, raw_headers, profile_fields, tokens):
    skip = {"요일", "날짜"}
    headers = [name for name in raw_headers if name not in skip]
    total = 0
    filled = 0
    missing = []
    for day in days:
        for name in headers:
            total += 1
            if is_empty(day["raw"].get(name), tokens):
                missing.append(f"{day['label']} {name}")
            else:
                filled += 1
    for field in profile_fields:
        total += 1
        if field["value"]:
            filled += 1
        else:
            missing.append(field["label"])
    return total, filled, missing


def _column_all_empty(days, header: str, tokens: set[str]) -> bool:
    if not days:
        return True
    return all(is_empty(day["raw"].get(header), tokens) for day in days)


def _column_some_empty(days, header: str, tokens: set[str]) -> bool:
    values = [is_empty(day["raw"].get(header), tokens) for day in days]
    return any(values) and not all(values)


def _summary_pages(sheet) -> dict[str, dict]:
    pages = {}
    for row in range(5, sheet.max_row + 1):
        page = sheet.cell(row, 1).value
        if is_empty(page):
            continue
        pages[str(page).strip()] = {
            "title": as_text(sheet.cell(row, 2).value),
            "stat": as_text(sheet.cell(row, 3).value),
            "meaning": as_text(sheet.cell(row, 4).value),
            "suggestion": as_text(sheet.cell(row, 5).value),
        }
    return pages


def _resolve_header(headers: dict[str, int], wanted: str) -> str:
    if not wanted:
        return ""
    if wanted in headers:
        return wanted
    prefix = wanted.split("(")[0]
    for name in headers:
        if name.startswith(prefix):
            return name
    return ""


def _chart(days, header: str, unit: str, tokens: set[str]):
    if not header:
        return None
    points = []
    for day in days:
        if not day["monitored"] and header not in day["daily"]:
            continue
        value = day["daily"].get(header)
        if is_empty(value, tokens) or isinstance(value, str):
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        points.append({"label": day["label"], "value": number, "display": _format_chart(number, unit)})
    if not points:
        return None
    peak = max(abs(point["value"]) for point in points) or 1
    for point in points:
        point["pct"] = round(abs(point["value"]) / peak * 100, 1)
    return {"title": header, "unit": unit, "points": points}


def _format_chart(number: float, unit: str) -> str:
    if unit == "%":
        return f"{number:.0f}%"
    if number.is_integer():
        text = f"{int(number):,}"
    else:
        text = f"{number:.1f}"
    return f"{text}{unit}" if unit else text
