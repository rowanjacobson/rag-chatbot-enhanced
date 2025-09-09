#!/usr/bin/env python3
"""Run linting checks using flake8."""

import subprocess
import sys
from pathlib import Path


def main():
    """Run linting checks on Python code."""
    project_root = Path(__file__).parent.parent

    print("🔍 Running linting checks with flake8...")

    try:
        result = subprocess.run(
            ["uv", "run", "flake8", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode == 0:
            print("✅ No linting issues found!")
        else:
            print("❌ Linting issues detected. Please fix them before committing.")
            sys.exit(result.returncode)

    except FileNotFoundError:
        print("❌ Error: uv not found. Please install uv first.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running flake8: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
