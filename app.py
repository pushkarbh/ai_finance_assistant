import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Direct execution of the real app
with open('src/web_app/app.py') as f:
    code = compile(f.read(), 'src/web_app/app.py', 'exec')
    exec(code, {'__name__': '__main__', '__file__': str(Path(__file__).parent / 'src/web_app/app.py')})

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
