#!/bin/bash
# Startup script for Hugging Face Spaces
# This ensures FAISS index is built before Streamlit starts

echo "==================================================================="
echo "AI Finance Assistant - Hugging Face Startup"
echo "==================================================================="

# Check if FAISS index exists
if [ ! -f "src/data/faiss_index/index.faiss" ]; then
    echo ""
    echo "FAISS index not found. Building from knowledge base..."
    echo ""
    
    # Run the initialization script
    python scripts/init_rag.py
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to build FAISS index"
        exit 1
    fi
    
    echo ""
    echo "FAISS index built successfully!"
else
    echo ""
    echo "FAISS index found. Skipping rebuild."
fi

echo ""
echo "Starting Streamlit application..."
echo "==================================================================="
echo ""

# Start Streamlit
streamlit run src/web_app/app.py --server.port 7860 --server.address 0.0.0.0 --server.headless true
