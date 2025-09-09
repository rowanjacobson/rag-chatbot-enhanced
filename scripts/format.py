#!/usr/bin/env python3
"""Format Python code using black."""

import subprocess
import sys
from pathlib import Path


def main():
    """Format all Python code with black."""
    project_root = Path(__file__).parent.parent

    print("🎨 Formatting Python code with black...")

    try:
        result = subprocess.run(
            ["uv", "run", "black", "."],
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
            print("✅ Code formatting completed successfully!")
        else:
            print("❌ Code formatting failed!")
            sys.exit(result.returncode)

    except FileNotFoundError:
        print("❌ Error: uv not found. Please install uv first.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running black: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
