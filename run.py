#!/usr/bin/env python3
"""
Main entry point for AI Finance Assistant.
Runs the Streamlit web application.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run the Streamlit application."""
    # Get the path to the app
    app_path = Path(__file__).parent / "src" / "web_app" / "app.py"

    # Run streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.port", "8501",
        "--browser.gatherUsageStats", "false"
    ])


if __name__ == "__main__":
    main()
