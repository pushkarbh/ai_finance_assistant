"""
Entry point for Streamlit Cloud deployment.
Works both locally and on Streamlit Cloud.
"""

import sys
from pathlib import Path

# Add project root to path so imports work
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import everything from the actual app
# This makes all Streamlit commands execute as if they're in this file
from src.web_app.app import *

# The app runs automatically when src.web_app.app is imported
# because it contains Streamlit commands at the module level

    try:
        # Import and run the initialization
        from scripts.init_rag import main as init_rag_main
        init_rag_main()
        print("\nFAISS index built successfully!")
    except Exception as e:
        print(f"\nERROR: Failed to build FAISS index: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
else:
    print("\nFAISS index found. Skipping rebuild.")

print("\nStarting Streamlit application...")
print("=" * 70)
print()

# Now import and run the actual Streamlit app
# This must be done AFTER the index is built
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    import sys
    
    # Set the arguments for streamlit run
    sys.argv = [
        "streamlit",
        "run",
        "src/web_app/app.py",
        "--server.port=7860",
        "--server.address=0.0.0.0",
        "--server.headless=true"
    ]
    
    sys.exit(stcli.main())
