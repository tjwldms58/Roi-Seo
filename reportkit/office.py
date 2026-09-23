"""업로드한 엑셀의 수식을 LibreOffice로 다시 계산합니다.

문장과 계산식은 코드에 두지 않고, 로직 엑셀 안에 있는 수식을 그대로 씁니다.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

from reportkit.errors import ReportError

_LOCK = threading.Lock()


def _find_soffice() -> str | None:
    found = shutil.which("soffice") or shutil.which("libreoffice")
    if found:
        return found
    for candidate in (
        Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
        Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
    ):
        if candidate.is_file():
            return str(candidate)
    return None


def recalculate(source: Path, dest: Path) -> None:
    source = Path(source)
    dest = Path(dest)
    if not source.is_file():
        raise ReportError(f"엑셀 파일을 찾을 수 없습니다: {source.name}")
    soffice = _find_soffice()
    if not soffice:
        raise ReportError("LibreOffice Calc가 설치되어 있어야 엑셀 수식을 계산할 수 있습니다.")
    with _LOCK:
        with tempfile.TemporaryDirectory(prefix="report-calc-") as folder:
            root = Path(folder)
            profile = root / "profile"
            outdir = root / "out"
            profile.mkdir()
            outdir.mkdir()
            local = root / "input.xlsx"
            shutil.copy(source, local)
            run = subprocess.run(
                [
                    soffice,
                    "--headless",
                    "--norestore",
                    "--nolockcheck",
                    "--nologo",
                    f"-env:UserInstallation={profile.as_uri()}",
                    "--convert-to",
                    "xlsx",
                    "--outdir",
                    str(outdir),
                    str(local),
                ],
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
            produced = outdir / "input.xlsx"
            if run.returncode != 0 or not produced.is_file():
                detail = (run.stderr or run.stdout or "").strip()
                raise ReportError(f"엑셀 수식을 계산하지 못했습니다. {detail[:400]}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(produced, dest)
