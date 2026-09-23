"""HTML을 PDF로 바꿉니다. WeasyPrint가 없으면 크롬이나 엣지로 만듭니다."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from reportkit.errors import ReportError

_SCRIPT = re.compile(r"<script\b[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)


def html_to_pdf(html: str, base_dir: Path) -> bytes:
    try:
        from weasyprint import HTML
    except (ImportError, OSError):
        return _browser_pdf(html, base_dir)
    try:
        return HTML(string=html, base_url=str(base_dir)).write_pdf()
    except OSError:
        return _browser_pdf(html, base_dir)


def _browser_pdf(html: str, base_dir: Path) -> bytes:
    browser = _find_browser()
    if browser is None:
        raise ReportError("PDF를 만들 크롬이나 엣지를 찾지 못했습니다.")
    fonts = (Path(base_dir) / "assets" / "fonts").as_uri()
    html = _SCRIPT.sub("", html).replace('url("assets/fonts/', f'url("{fonts}/')
    with tempfile.TemporaryDirectory(prefix="report-pdf-") as folder:
        root = Path(folder)
        page = root / "report.html"
        output = root / "report.pdf"
        page.write_text(html, encoding="utf-8")
        run = subprocess.run(
            [
                str(browser),
                "--headless=new",
                "--disable-gpu",
                "--no-first-run",
                "--no-pdf-header-footer",
                f"--user-data-dir={root / 'profile'}",
                f"--print-to-pdf={output}",
                page.as_uri(),
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if not output.is_file() or output.stat().st_size < 100:
            detail = (run.stderr or run.stdout or "").strip()
            raise ReportError(f"PDF를 만들지 못했습니다. {detail[:300]}")
        return output.read_bytes()


def _find_browser() -> Path | None:
    for name in ("google-chrome", "chrome", "msedge", "microsoft-edge"):
        found = shutil.which(name)
        if found:
            return Path(found)
    roots = [
        os.environ.get("PROGRAMFILES", r"C:\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", ""),
    ]
    relatives = (
        r"Google\Chrome\Application\chrome.exe",
        r"Microsoft\Edge\Application\msedge.exe",
    )
    for root in roots:
        if not root:
            continue
        for relative in relatives:
            candidate = Path(root) / relative
            if candidate.is_file():
                return candidate
    return None
