#!/usr/bin/env python3
"""
Startup wrapper for Hugging Face Spaces deployment.
Ensures FAISS index is built before starting the Streamlit app.
"""
import os
import sys
from pathlib import Path

print("=" * 70)
print("AI Finance Assistant - Hugging Face Startup")
print("=" * 70)

# Check if FAISS index exists
faiss_index_path = Path("src/data/faiss_index/index.faiss")

if not faiss_index_path.exists():
    print("\nFAISS index not found. Building from knowledge base...")
    print("This will take about 30-60 seconds on first startup.\n")
    
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
