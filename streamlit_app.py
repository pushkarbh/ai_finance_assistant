"""Streamlit Cloud entry point with error handling."""
import streamlit as st
import sys
import traceback

st.set_page_config(
    page_title="AI Finance Assistant",
    page_icon="📈",
    layout="wide"
)

try:
    # Import and run the actual app
    import sys
    from pathlib import Path
    
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    st.write("✓ Basic imports successful")
    st.write(f"✓ Project root: {project_root}")
    
    # Check FAISS files
    faiss_path = project_root / "src" / "data" / "faiss_index" / "index.faiss"
    if faiss_path.exists():
        st.write(f"✓ FAISS index found at {faiss_path}")
    else:
        st.error(f"✗ FAISS index NOT found at {faiss_path}")
        st.write(f"Contents of src/data: {list((project_root / 'src' / 'data').iterdir())}")
    
    st.write("Attempting to import app modules...")
    
    from src.web_app.app import main
    
    st.write("✓ App modules imported successfully")
    st.write("Starting main app...")
    
    main()
    
except Exception as e:
    st.error("❌ **Critical Error:**")
    st.code(f"{type(e).__name__}: {str(e)}")
    st.code(traceback.format_exc())
    st.stop()
