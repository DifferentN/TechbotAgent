#!/usr/bin/env python3
"""Install and verify the local runtime used by ui_diff_skill."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


SKILL_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = SKILL_ROOT / "requirements.txt"


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=SKILL_ROOT, env=env, check=True)


def venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def venv_playwright(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "playwright.exe"
    return venv_dir / "bin" / "playwright"


def directory_size(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def verify(python: Path, *, browser_smoke_test: bool, adb_check: bool) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SKILL_ROOT)
    run(
        [
            str(python),
            "-c",
            (
                "import numpy, scipy, cv2, skimage, requests, PIL, playwright, appium; "
                "print('Python dependencies: OK')"
            ),
        ],
        env=env,
    )
    run([str(python), str(SKILL_ROOT / "scripts" / "run_ui_diff.py"), "--help"], env=env)

    if browser_smoke_test:
        run(
            [
                str(python),
                "-c",
                (
                    "from playwright.sync_api import sync_playwright; "
                    "p=sync_playwright().start(); "
                    "b=p.chromium.launch(headless=True); "
                    "print('Chromium:', b.version); "
                    "b.close(); p.stop()"
                ),
            ]
        )

    if adb_check:
        adb = shutil.which("adb")
        if not adb:
            raise SystemExit("ADB_NOT_FOUND: install Android platform-tools or use --skip-adb-check")
        run([adb, "version"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Install and verify ui_diff_skill dependencies")
    parser.add_argument(
        "--venv",
        type=Path,
        default=SKILL_ROOT / ".venv",
        help="virtual environment path (default: <skill>/.venv)",
    )
    parser.add_argument("--check-only", action="store_true", help="verify the existing environment without installing")
    parser.add_argument("--skip-browser-install", action="store_true", help="do not install Playwright Chromium")
    parser.add_argument("--skip-browser-smoke-test", action="store_true", help="do not launch headless Chromium during verification")
    parser.add_argument("--skip-adb-check", action="store_true", help="do not require adb on PATH")
    args = parser.parse_args()

    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10 or newer is required")
    if not REQUIREMENTS.is_file():
        raise SystemExit(f"Requirements file not found: {REQUIREMENTS}")

    target_venv = args.venv.expanduser().resolve()
    python = venv_python(target_venv)
    playwright = venv_playwright(target_venv)

    if not args.check_only:
        if not python.is_file():
            run([sys.executable, "-m", "venv", str(target_venv)])
        run([str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)])
        if not args.skip_browser_install:
            run([str(playwright), "install", "chromium"])
    elif not python.is_file():
        raise SystemExit(f"Virtual environment not found: {target_venv}")

    verify(
        python,
        browser_smoke_test=not args.skip_browser_smoke_test,
        adb_check=not args.skip_adb_check,
    )
    used = directory_size(target_venv)
    print(f"ui_diff_skill is ready: {python}")
    print(f"Virtual environment size: {used / (1024 ** 2):.0f} MiB")


if __name__ == "__main__":
    main()
