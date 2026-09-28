"""Exercise run.bat with a stripped-down PATH (Windows only)."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="run.bat is Windows-only")

SYSTEM32 = str(Path(os.environ.get("SYSTEMROOT", r"C:\Windows")) / "System32")
WINDOWS_APPS = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WindowsApps"


def _run_bat(bat: Path, *args: str, path: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "PATH": path, "LEADFLOW_UNATTENDED": "1"}
    return subprocess.run(
        ["cmd", "/c", str(bat), *args], env=env, capture_output=True, text=True, errors="replace", timeout=120
    )


@pytest.mark.skipif(not (ROOT / ".venv" / ".installed").exists(), reason="needs the set-up .venv")
def test_runs_with_no_python_on_path_using_the_venv(tmp_path):
    result = _run_bat(ROOT / "run.bat", str(ROOT / "data" / "raw" / "sample_leads.csv"), str(tmp_path), path=SYSTEM32)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "ranked_leads.xlsx").exists()
    assert (tmp_path / "summary.md").exists()


@pytest.mark.skipif(not (WINDOWS_APPS / "python.exe").exists(), reason="no Microsoft Store python alias here")
def test_store_python_alias_is_not_mistaken_for_python(tmp_path):
    # A fresh copy (no .venv) on a PATH where the only "python" is the Microsoft Store stub.
    shutil.copy(ROOT / "run.bat", tmp_path)
    shutil.copy(ROOT / "requirements.txt", tmp_path)
    result = _run_bat(tmp_path / "run.bat", path=f"{SYSTEM32};{WINDOWS_APPS}")
    output = result.stdout + result.stderr
    assert result.returncode == 1
    assert "Microsoft Store" not in output, output
    assert "Python 3 wasn't found" in output
    assert not (tmp_path / ".venv").exists()
