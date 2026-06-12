"""Command-line entry point for the Streamlit app."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run the Streamlit project app."""
    app_path = Path(__file__).with_name("app.py")
    return subprocess.call([sys.executable, "-m", "streamlit", "run", str(app_path)])


if __name__ == "__main__":
    raise SystemExit(main())
