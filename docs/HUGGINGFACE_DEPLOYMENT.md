# Deploying AI Finance Assistant to Hugging Face Spaces

This guide provides step-by-step instructions for deploying the AI Finance Assistant to Hugging Face Spaces using Docker SDK.

## Prerequisites

1. **Hugging Face Account**: Create one at https://huggingface.co/join
2. **Hugging Face CLI**: Install with `pip install huggingface_hub`
3. **Git LFS**: Install with `brew install git-lfs` (macOS) or `apt install git-lfs` (Linux)
4. **OpenAI API Key**: Required for the application to function

## Project Files for Hugging Face

The following files are specifically configured for Hugging Face deployment:

| File | Purpose |
|------|---------|
| `Dockerfile.hf` | Docker configuration optimized for HF Spaces (port 7860, non-root user) |
| `README_HF.md` | Space README with metadata header (becomes `README.md` in the Space) |
| `.gitattributes` | Git LFS configuration for binary files (FAISS index) |
| `scripts/deploy_to_hf.sh` | Automated deployment script |

## Step-by-Step Deployment

### Step 1: Login to Hugging Face

```bash
huggingface-cli login
```

You'll be prompted for your Hugging Face token. Get it from: https://huggingface.co/settings/tokens

> **Note**: Create a token with "Write" permissions.

### Step 2: Create a New Space

```bash
huggingface-cli repo create ai-finance-assistant --type space --space_sdk docker
```

This creates a new Space at `https://huggingface.co/spaces/<your-username>/ai-finance-assistant`

### Step 3: Clone the Space Repository

```bash
cd /tmp
git clone https://huggingface.co/spaces/<your-username>/ai-finance-assistant hf-space
cd hf-space
```

### Step 4: Initialize Git LFS

```bash
git lfs install
```

### Step 5: Copy Project Files

```bash
# Set your project path
PROJECT_DIR="/path/to/ai_finance_assistant"

# Copy Dockerfile (rename from .hf version)
cp "$PROJECT_DIR/Dockerfile.hf" ./Dockerfile

# Copy README (rename for HF)
cp "$PROJECT_DIR/README_HF.md" ./README.md

# Copy configuration files
cp "$PROJECT_DIR/requirements.txt" ./
cp "$PROJECT_DIR/config.yaml" ./
cp "$PROJECT_DIR/run.py" ./

# Copy .gitattributes for LFS
cp "$PROJECT_DIR/.gitattributes" ./

# Copy source code
cp -r "$PROJECT_DIR/src" ./

# Copy Streamlit configuration
cp -r "$PROJECT_DIR/.streamlit" ./
```

### Step 6: Create .gitignore

Create a `.gitignore` file to exclude Python bytecode and other unnecessary files:

```bash
cat > .gitignore << 'GITIGNORE'
# Python bytecode
__pycache__/
*.py[cod]
*$py.class
*.so

# Environment
.env
.env.local
.venv/
venv/

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db

# Logs
*.log
GITIGNORE
```

### Step 7: Remove Existing Bytecode Files

**Important**: This step is critical. Hugging Face rejects binary files that aren't tracked by LFS.

```bash
# Remove all __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Remove all .pyc files
find . -name "*.pyc" -delete

# Remove .DS_Store files (macOS)
find . -name ".DS_Store" -delete
```

### Step 8: Track Binary Files with Git LFS

```bash
git lfs track "*.faiss"
git lfs track "*.pkl"
```

### Step 9: Verify FAISS Files Exist

```bash
ls -la src/data/faiss_index/
```

You should see:
```
index.faiss  (~3 MB)
index.pkl    (~1.7 MB)
```

### Step 10: Commit and Push

```bash
git add -A
git commit -m "Deploy AI Finance Assistant"
git push origin main
```

## Post-Deployment Configuration

### Add OpenAI API Key

1. Go to your Space settings: `https://huggingface.co/spaces/<your-username>/ai-finance-assistant/settings`
2. Scroll to **Repository secrets**
3. Click **New secret**
4. Add:
   - **Name**: `OPENAI_API_KEY`
   - **Value**: Your OpenAI API key (starts with `sk-...`)

### Optional: Add Alpha Vantage API Key

For enhanced market data functionality:
- **Name**: `ALPHA_VANTAGE_API_KEY`
- **Value**: Your Alpha Vantage API key

## Troubleshooting

### Error: "Your push was rejected because it contains binary files"

**Cause**: Python bytecode files (`.pyc`) or other binary files not tracked by LFS.

**Solution**:
```bash
# Remove bytecode files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete

# Reset git cache and re-add
git rm -r --cached .
git add -A

# Amend the commit and force push
git commit --amend -m "Deploy AI Finance Assistant"
git push origin main --force
```

### Error: Build fails with memory issues

**Cause**: PyTorch installation requires significant memory.

**Solution**: The `Dockerfile.hf` uses `faiss-cpu` and optimized PyTorch installation. Ensure you're using `Dockerfile.hf` (not the regular `Dockerfile`).

### Error: FAISS index not found

**Cause**: Git LFS files weren't properly pulled/pushed.

**Solution**:
```bash
git lfs pull
ls -la src/data/faiss_index/
```

If files are missing or show as pointers, re-copy from the source project.

### Error: Application crashes on startup

**Cause**: Missing environment variables or configuration.

**Solution**:
1. Check Space logs at `https://huggingface.co/spaces/<your-username>/ai-finance-assistant/logs`
2. Ensure `OPENAI_API_KEY` is set in secrets
3. Verify `config.yaml` is present

## Architecture Notes

### Docker Configuration (Dockerfile.hf)

Key differences from the local Dockerfile:

| Setting | Local | Hugging Face |
|---------|-------|--------------|
| Port | 8502 | 7860 |
| User | root | non-root (uid 1000) |
| Python | 3.12 | 3.11 |
| Base | Multi-stage | Single stage |

### Git LFS for Binary Files

The `.gitattributes` file configures Git LFS for:
- `*.faiss` - FAISS vector index files
- `*.pkl` - Python pickle files (FAISS metadata)
- `*.bin`, `*.model`, `*.pt`, `*.pth`, `*.onnx` - Model files (if added later)

Hugging Face natively supports Git LFS, so these files are stored efficiently.

## Updating the Space

To update your deployed Space:

```bash
cd /tmp/hf-space

# Pull latest changes
git pull origin main

# Copy updated files from source project
cp -r "$PROJECT_DIR/src" ./
# ... copy other changed files

# Clean bytecode
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Commit and push
git add -A
git commit -m "Update: <description of changes>"
git push origin main
```

## Automated Deployment Script

For convenience, use the provided deployment script:

```bash
./scripts/deploy_to_hf.sh
```

This script automates the entire process including:
- Login verification
- Space creation/cloning
- File copying
- LFS setup
- Bytecode cleanup
- Commit and push

## Resources

- [Hugging Face Spaces Documentation](https://huggingface.co/docs/hub/spaces)
- [Docker SDK Documentation](https://huggingface.co/docs/hub/spaces-sdks-docker)
- [Git LFS on Hugging Face](https://huggingface.co/docs/hub/repositories-getting-started#terminal)
- [Space Secrets](https://huggingface.co/docs/hub/spaces-overview#managing-secrets)
