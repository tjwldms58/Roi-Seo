"""시안과 같은 세로 막대·꺾은선 차트를 SVG로 그립니다."""

from __future__ import annotations

from xml.sax.saxutils import escape


def hours_label(minutes: float | None) -> str:
    if minutes is None:
        return ""
    total = int(round(minutes))
    sign = "-" if total < 0 else ""
    total = abs(total)
    hour, minute = divmod(total, 60)
    if hour and minute:
        return f"{sign}{hour}시간 {minute:02d}분"
    if hour:
        return f"{sign}{hour}시간"
    return f"{sign}{minute}분"


def combo_svg(
    points: list[dict],
    *,
    y_min: float | None = None,
    y_max: float | None = None,
    bar: str = "#a0c8c0",
    line: str = "#184048",
    width: int = 640,
    height: int = 160,
    fmt=None,
    highlight: str = "",
    highlight_color: str = "#c45c4a",
) -> str:
    rows = [point for point in points if point.get("value") is not None]
    if not rows:
        return ""
    values = [float(point["value"]) for point in rows]
    lo = min(values) if y_min is None else y_min
    hi = max(values) if y_max is None else y_max
    if hi <= lo:
        hi = lo + 1
    return _bars_and_line(
        [point["label"] for point in rows],
        values,
        values,
        lo,
        hi,
        lo,
        hi,
        bar,
        line,
        width,
        height,
        fmt or _num,
        fmt or _num,
        highlight,
        highlight_color,
        show_line_labels=False,
    )


def dual_svg(
    points: list[dict],
    *,
    bar_key: str,
    line_key: str,
    bar: str = "#a0c8c0",
    line: str = "#184048",
    width: int = 640,
    height: int = 160,
    bar_fmt=None,
    line_fmt=None,
    bar_zero: bool = True,
) -> str:
    rows = [point for point in points if point.get(bar_key) is not None or point.get(line_key) is not None]
    if not rows:
        return ""
    bar_values = [point.get(bar_key) for point in rows]
    line_values = [point.get(line_key) for point in rows]
    bar_nums = [float(value) for value in bar_values if value is not None]
    line_nums = [float(value) for value in line_values if value is not None]
    if not bar_nums and not line_nums:
        return ""
    bar_lo, bar_hi = _limits(bar_nums or [0], zero=bar_zero)
    line_lo, line_hi = _limits(line_nums or [0], zero=False)
    return _bars_and_line(
        [point["label"] for point in rows],
        bar_values,
        line_values,
        bar_lo,
        bar_hi,
        line_lo,
        line_hi,
        bar,
        line,
        width,
        height,
        bar_fmt or _num,
        line_fmt or _num,
    )


def line_svg(points: list[dict], *, color: str = "#184048", width: int = 640, height: int = 160, fmt=None) -> str:
    rows = [point for point in points if point.get("value") is not None]
    if len(rows) < 2:
        return ""
    values = [float(point["value"]) for point in rows]
    lo, hi = _limits(values, zero=False)
    pad_l, pad_r, pad_t, pad_b = 44, 16, 18, 26
    inner_w = width - pad_l - pad_r
    inner_h = height - pad_t - pad_b
    slot = inner_w / max(len(rows) - 1, 1)

    def y_of(value: float) -> float:
        return pad_t + (1 - (value - lo) / (hi - lo)) * inner_h

    def x_of(index: int) -> float:
        return pad_l + slot * index

    parts = [_open(width, height)]
    parts.extend(_grid(pad_l, pad_t, width - pad_r, inner_h, lo, hi, fmt or _clock))
    coords = " ".join(f"{x_of(index):.1f},{y_of(value):.1f}" for index, value in enumerate(values))
    parts.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2"/>')
    for index, (row, value) in enumerate(zip(rows, values)):
        parts.append(f'<circle cx="{x_of(index):.1f}" cy="{y_of(value):.1f}" r="3.5" fill="{color}"/>')
        parts.append(
            f'<text x="{x_of(index):.1f}" y="{y_of(value) - 8:.1f}" text-anchor="middle" font-size="9" fill="#184048">{escape(str((fmt or _clock)(value)))}</text>'
        )
        parts.append(
            f'<text x="{x_of(index):.1f}" y="{height - 8}" text-anchor="middle" font-size="10" fill="#5c6864">{escape(str(row["label"]))}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def stacked_svg(days: list[dict], *, width: int = 640, height: int = 200) -> str:
    rows = [day for day in days if day.get("tst")]
    if not rows:
        return ""
    peak = max(float(day["tst"]) for day in rows) * 1.18
    pad_l, pad_r, pad_t, pad_b = 52, 8, 16, 28
    inner_w = width - pad_l - pad_r
    inner_h = height - pad_t - pad_b
    slot = inner_w / len(rows)
    bar_w = min(46, slot * 0.62)
    parts = [_open(width, height)]
    parts.append(
        '<rect x="8" y="4" width="10" height="10" fill="#184048"/>'
        '<text x="22" y="13" font-size="9" fill="#5c6864">깊은수면</text>'
        '<rect x="78" y="4" width="10" height="10" fill="#68a098"/>'
        '<text x="92" y="13" font-size="9" fill="#5c6864">얕은수면</text>'
        '<rect x="148" y="4" width="10" height="10" fill="#8878a0"/>'
        '<text x="162" y="13" font-size="9" fill="#5c6864">렘수면</text>'
    )
    base = pad_t + inner_h
    for index, day in enumerate(rows):
        x = pad_l + slot * index + (slot - bar_w) / 2
        cursor = base
        for key, color in (("deep", "#184048"), ("light", "#68a098"), ("rem", "#8878a0")):
            amount = float(day.get(key) or 0)
            height_px = amount / peak * inner_h
            cursor -= height_px
            if height_px < 1:
                continue
            parts.append(
                f'<rect x="{x:.1f}" y="{cursor:.1f}" width="{bar_w:.1f}" height="{height_px:.1f}" fill="{color}"/>'
            )
            share = day.get(f"{key}_share") or 0
            if height_px > 14:
                parts.append(
                    f'<text x="{x + bar_w / 2:.1f}" y="{cursor + height_px / 2 + 3:.1f}" text-anchor="middle" font-size="8" fill="#ffffff">{int(round(share))}%</text>'
                )
        parts.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{cursor - 6:.1f}" text-anchor="middle" font-size="9" fill="#184048" font-weight="700">{escape(hours_label(day.get("tst")))}</text>'
        )
        parts.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{height - 8}" text-anchor="middle" font-size="11" fill="#243033">{escape(str(day["label"]))}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def _bars_and_line(
    labels,
    bar_values,
    line_values,
    bar_lo,
    bar_hi,
    line_lo,
    line_hi,
    bar,
    line,
    width,
    height,
    bar_fmt,
    line_fmt,
    highlight="",
    highlight_color="#c45c4a",
    show_line_labels=True,
):
    pad_l, pad_r, pad_t, pad_b = 40, 36, 20, 26
    inner_w = width - pad_l - pad_r
    inner_h = height - pad_t - pad_b
    count = len(labels)
    slot = inner_w / max(count, 1)
    bar_w = min(34, slot * 0.46)

    def y_bar(value: float) -> float:
        return pad_t + (1 - (value - bar_lo) / (bar_hi - bar_lo)) * inner_h

    def y_line(value: float) -> float:
        return pad_t + (1 - (value - line_lo) / (line_hi - line_lo)) * inner_h

    def x_of(index: int) -> float:
        return pad_l + slot * index + slot / 2

    parts = [_open(width, height)]
    parts.extend(_grid(pad_l, pad_t, width - pad_r, inner_h, bar_lo, bar_hi, bar_fmt))
    baseline = y_bar(bar_lo)
    for index, value in enumerate(bar_values):
        if value is None:
            continue
        number = float(value)
        top = y_bar(number)
        color = highlight_color if highlight and labels[index] == highlight else bar
        parts.append(
            f'<rect x="{x_of(index) - bar_w / 2:.1f}" y="{top:.1f}" width="{bar_w:.1f}" height="{max(baseline - top, 0):.1f}" rx="2" fill="{color}"/>'
        )
        parts.append(
            f'<text x="{x_of(index):.1f}" y="{top - 4:.1f}" text-anchor="middle" font-size="9" fill="#184048" font-weight="700">{escape(str(bar_fmt(number)))}</text>'
        )
    usable = [(index, float(value)) for index, value in enumerate(line_values) if value is not None]
    if len(usable) >= 2:
        coords = " ".join(f"{x_of(index):.1f},{y_line(value):.1f}" for index, value in usable)
        parts.append(f'<polyline points="{coords}" fill="none" stroke="{line}" stroke-width="2"/>')
        for index, value in usable:
            parts.append(f'<circle cx="{x_of(index):.1f}" cy="{y_line(value):.1f}" r="3" fill="{line}"/>')
            if show_line_labels and bar_values[index] is None:
                parts.append(
                    f'<text x="{x_of(index):.1f}" y="{y_line(value) - 8:.1f}" text-anchor="middle" font-size="9" fill="{line}">{escape(str(line_fmt(value)))}</text>'
                )
    for index, label in enumerate(labels):
        parts.append(
            f'<text x="{x_of(index):.1f}" y="{height - 8}" text-anchor="middle" font-size="11" fill="#243033">{escape(str(label))}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def _open(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" '
        f'font-family="ReportKR, sans-serif">'
    )


def _grid(left, top, right, inner_h, lo, hi, fmt) -> list[str]:
    parts = []
    for step in range(5):
        yy = top + inner_h * step / 4
        value = hi - (hi - lo) * step / 4
        parts.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{right}" y2="{yy:.1f}" stroke="#e6e4dc" stroke-width="1"/>')
        parts.append(
            f'<text x="{left - 6}" y="{yy + 3:.1f}" text-anchor="end" font-size="8" fill="#8a908c">{escape(str(fmt(value)))}</text>'
        )
    return parts


def _limits(values: list[float], *, zero: bool) -> tuple[float, float]:
    lo = min(values)
    hi = max(values)
    if hi == lo:
        hi = lo + 1
    if zero or (lo >= 0 and lo < hi * 0.35):
        return 0, hi * 1.22
    pad = (hi - lo) * 0.45
    return lo - pad, hi + pad * 0.55


def _num(value: float) -> str:
    if abs(value - round(value)) < 0.05:
        return str(int(round(value)))
    return f"{value:.1f}"


def _clock(minutes: float) -> str:
    total = int(round(minutes))
    while total < 0:
        total += 1440
    total %= 1440
    hour, minute = divmod(total, 60)
    return f"{hour:02d}:{minute:02d}"
