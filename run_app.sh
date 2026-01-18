#!/bin/bash
# Run script that ensures venv Python is used

# Get the directory where this script lives
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate venv
source venv/bin/activate

# Run streamlit with the venv's Python
python -m streamlit run src/web_app/app.py --server.port 8502

# Deactivate when done
deactivate
