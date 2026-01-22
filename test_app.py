"""
Minimal test version to verify HuggingFace deployment works.
"""
import streamlit as st

st.set_page_config(
    page_title="AI Finance Assistant",
    page_icon="📈",
    layout="wide"
)

st.title("🎉 AI Finance Assistant - Deployment Test")
st.success("✅ App is running successfully on HuggingFace Spaces!")

st.info("If you see this message, the deployment infrastructure is working correctly.")

st.write("Next step: Add the full application code back gradually.")
