"""Minimal Streamlit test to diagnose startup issues."""
import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

import streamlit as st
print("✓ Streamlit imported successfully")

st.set_page_config(page_title="Test", page_icon="✅")
print("✓ set_page_config called successfully")

st.title("✅ Streamlit Startup Test Successful!")
st.write("If you see this, basic Streamlit works.")

# Test environment variables
import os
if "OPENAI_API_KEY" in os.environ:
    st.success("✓ OPENAI_API_KEY found in environment")
else:
    st.error("✗ OPENAI_API_KEY not found in environment")

if "OPENAI_API_KEY" in st.secrets:
    st.success("✓ OPENAI_API_KEY found in Streamlit secrets")
else:
    st.error("✗ OPENAI_API_KEY not found in Streamlit secrets")

st.info(f"Python: {sys.version}")
