"""
Entry point for Streamlit Cloud deployment.
Executes the actual app from src/web_app/app.py
"""

import sys
from pathlib import Path

# Add project root to path so imports work
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Execute the actual app file directly
app_file = project_root / "src" / "web_app" / "app.py"
exec(open(app_file).read())

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
