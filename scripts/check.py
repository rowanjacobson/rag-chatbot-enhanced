#!/usr/bin/env python3
"""Run all code quality checks."""

import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status."""
    print(f"🔄 {description}...")

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode == 0:
            print(f"✅ {description} passed!")
            return True
        else:
            print(f"❌ {description} failed!")
            return False

    except FileNotFoundError as e:
        print(f"❌ Error: Command not found - {e}")
        return False
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False


def main():
    """Run all code quality checks."""
    project_root = Path(__file__).parent.parent

    print("🚀 Running all code quality checks...")
    print("=" * 50)

    # Change to project root
    original_cwd = Path.cwd()
    try:
        import os

        os.chdir(project_root)

        checks = [
            (["uv", "run", "black", ".", "--check"], "Black formatting check"),
            (["uv", "run", "flake8", "."], "Flake8 linting check"),
        ]

        all_passed = True

        for command, description in checks:
            success = run_command(command, description)
            all_passed &= success
            print("-" * 30)

        if all_passed:
            print("🎉 All code quality checks passed!")
            sys.exit(0)
        else:
            print("💥 Some code quality checks failed!")
            print("Run 'python scripts/format.py' to auto-fix formatting issues.")
            sys.exit(1)

    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    main()
