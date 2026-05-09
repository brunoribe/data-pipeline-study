from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import venv
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
VENV_DIR = SCRIPT_DIR / ".venv"
REQUIREMENTS_PATH = SCRIPT_DIR / "requirements.txt"
GENERATOR_PATH = SCRIPT_DIR / "generate_practice_datasets.py"
REQUIREMENTS_STAMP = VENV_DIR / ".requirements.sha256"


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description=(
            "Create or reuse a script-local virtualenv, install scripts/requirements.txt, "
            "and run the practice dataset generator."
        )
    )
    parser.add_argument(
        "--refresh-venv",
        action="store_true",
        help="Reinstall the script dependencies before running the generator.",
    )
    return parser.parse_known_args()


def venv_python_path() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def requirements_hash() -> str:
    return hashlib.sha256(REQUIREMENTS_PATH.read_bytes()).hexdigest()


def run_command(command: list[str]) -> None:
    subprocess.run(command, check=True, cwd=REPO_ROOT)


def ensure_virtualenv(refresh: bool) -> Path:
    python_path = venv_python_path()
    if not python_path.exists():
        print(f"Creating script virtualenv at {VENV_DIR}...")
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)

    current_requirements_hash = requirements_hash()
    installed_requirements_hash = (
        REQUIREMENTS_STAMP.read_text(encoding="utf-8").strip() if REQUIREMENTS_STAMP.exists() else None
    )

    if refresh or installed_requirements_hash != current_requirements_hash:
        print("Installing script dependencies from scripts/requirements.txt...")
        run_command([str(python_path), "-m", "pip", "install", "-r", str(REQUIREMENTS_PATH)])
        REQUIREMENTS_STAMP.write_text(current_requirements_hash, encoding="utf-8")

    return python_path


def main() -> None:
    args, generator_args = parse_args()
    python_path = ensure_virtualenv(args.refresh_venv)
    run_command([str(python_path), str(GENERATOR_PATH), *generator_args])


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from error
    except KeyboardInterrupt:
        if VENV_DIR.exists() and not venv_python_path().exists():
            shutil.rmtree(VENV_DIR, ignore_errors=True)
        raise SystemExit(130)