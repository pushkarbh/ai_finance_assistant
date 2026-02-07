#!/bin/bash
# Deploy AI Finance Assistant to Hugging Face Spaces
# Usage: ./scripts/deploy_to_hf.sh

set -e

# Configuration
HF_USERNAME="pbhi0717"
SPACE_NAME="ai-finance-assistant"
SPACE_REPO="${HF_USERNAME}/${SPACE_NAME}"

echo "=== Deploying AI Finance Assistant to Hugging Face Spaces ==="
echo "Target: https://huggingface.co/spaces/${SPACE_REPO}"
echo ""

# Check if huggingface-cli is installed
if ! command -v huggingface-cli &> /dev/null; then
    echo "Error: huggingface-cli not found. Install with: pip install huggingface_hub"
    exit 1
fi

# Check if git-lfs is installed
if ! command -v git-lfs &> /dev/null; then
    echo "Error: git-lfs not found. Install with: brew install git-lfs"
    exit 1
fi

# Check login status
echo "Checking Hugging Face login status..."
if ! huggingface-cli whoami &> /dev/null; then
    echo "Not logged in. Please run: huggingface-cli login"
    exit 1
fi
echo "Logged in as: $(huggingface-cli whoami 2>/dev/null | head -1)"
echo ""

# Create temporary directory for deployment
DEPLOY_DIR=$(mktemp -d)
echo "Using temporary directory: ${DEPLOY_DIR}"

# Clone the space (creates it if it doesn't exist)
echo "Cloning/creating space repository..."
cd "${DEPLOY_DIR}"

# Try to clone existing space, or create new one
if ! git clone "https://huggingface.co/spaces/${SPACE_REPO}" space 2>/dev/null; then
    echo "Space doesn't exist. Creating new space..."
    huggingface-cli repo create "${SPACE_NAME}" --type space --space_sdk docker
    git clone "https://huggingface.co/spaces/${SPACE_REPO}" space
fi

cd space

# Initialize Git LFS
echo "Setting up Git LFS..."
git lfs install

# Copy files from source
SOURCE_DIR="$(dirname "$(dirname "$(realpath "$0")")")"
echo "Copying files from: ${SOURCE_DIR}"

# Copy essential files
cp "${SOURCE_DIR}/Dockerfile.hf" ./Dockerfile
cp "${SOURCE_DIR}/README_HF.md" ./README.md
cp "${SOURCE_DIR}/requirements.txt" ./
cp "${SOURCE_DIR}/config.yaml" ./
cp "${SOURCE_DIR}/.gitattributes" ./
cp "${SOURCE_DIR}/run.py" ./

# Copy source directories
cp -r "${SOURCE_DIR}/src" ./
cp -r "${SOURCE_DIR}/.streamlit" ./

# Track LFS files
echo "Tracking binary files with Git LFS..."
git lfs track "*.faiss"
git lfs track "*.pkl"

# Verify FAISS files
echo ""
echo "Verifying FAISS index files..."
ls -la src/data/faiss_index/

# Stage all files
git add -A

# Show what will be committed
echo ""
echo "Files to be committed:"
git status --short

echo ""
read -p "Ready to push to Hugging Face Spaces? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    git commit -m "Deploy AI Finance Assistant"
    git push origin main
    echo ""
    echo "=== Deployment Complete ==="
    echo "Your space is available at: https://huggingface.co/spaces/${SPACE_REPO}"
    echo ""
    echo "IMPORTANT: Set your OPENAI_API_KEY in Space Settings > Repository secrets"
else
    echo "Deployment cancelled."
fi

# Cleanup
cd /
rm -rf "${DEPLOY_DIR}"
