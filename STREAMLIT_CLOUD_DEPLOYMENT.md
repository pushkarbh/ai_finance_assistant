# Streamlit Community Cloud Deployment Guide

Complete guide to deploying your Streamlit app to Streamlit Community Cloud.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Prepare Your Repository](#prepare-your-repository)
3. [Create Streamlit Cloud Account](#create-streamlit-cloud-account)
4. [Deploy Your App](#deploy-your-app)
5. [Configure Secrets](#configure-secrets)
6. [Manage Your App](#manage-your-app)
7. [Troubleshooting](#troubleshooting)
8. [Cost & Limits](#cost--limits)

---

## Prerequisites

### Required:
- ✅ GitHub account
- ✅ Your Streamlit app code
- ✅ `requirements.txt` file
- ✅ API keys (OpenAI, etc.)

### Optional but Recommended:
- `.streamlit/config.toml` for theme customization
- `README.md` with app description
- `.gitignore` to exclude sensitive files

---

## Prepare Your Repository

### 1. Create GitHub Repository

**Option A: Via GitHub Web UI**
1. Go to https://github.com/new
2. Repository name: `ai-finance-assistant` (or your app name)
3. Visibility: Public (required for free tier)
4. Click "Create repository"

**Option B: Via Command Line**
```bash
# Navigate to your project
cd /Users/pushkar/IK_Agentic_AI/ai_finance_assistant

# Initialize git if not already done
git init

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*.pyc
.Python
venv/
env/

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
.DS_Store

# Data (if large binary files)
# src/data/faiss_index/*.faiss
# src/data/faiss_index/*.pkl

# Testing
.pytest_cache/
htmlcov/

# Logs
*.log
EOF

# Add all files
git add .

# Commit
git commit -m "Initial commit for Streamlit Cloud deployment"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/ai-finance-assistant.git

# Push to GitHub
git push -u origin main
```

### 2. Verify Repository Structure

Your GitHub repo should have:

```
your-repo/
├── requirements.txt           # REQUIRED
├── src/
│   └── web_app/
│       └── app.py            # Your main Streamlit app
├── .streamlit/
│   └── config.toml           # Optional: theme settings
├── README.md                 # Recommended
└── .gitignore                # Recommended
```

### 3. Requirements.txt Best Practices

**✅ DO:**
```txt
# Pin major versions but allow minor updates
streamlit>=1.31.0
langchain>=0.1.0
openai>=1.12.0
pandas>=2.0.0
```

**❌ DON'T:**
```txt
# Avoid exact pinning unless necessary
streamlit==1.31.0  # Too strict
```

### 4. Handle Large Binary Files

**If you have large files (>50MB):**

**Option A: Upload via GitHub UI** (for files 50-100MB)
1. Go to your repo on GitHub
2. Navigate to the folder
3. Click "Add file" → "Upload files"
4. Upload binary files (FAISS index, models, etc.)

**Option B: Exclude and rebuild** (recommended for FAISS indexes)
```bash
# Add to .gitignore
echo "src/data/faiss_index/*.faiss" >> .gitignore
echo "src/data/faiss_index/*.pkl" >> .gitignore

# Rebuild index on app startup (add to your app.py)
```

**Option C: Use Git LFS** (for very large files)
```bash
# Install Git LFS
brew install git-lfs  # macOS
# or: sudo apt install git-lfs  # Linux

# Initialize
git lfs install

# Track large files
git lfs track "*.faiss"
git lfs track "*.pkl"

# Add .gitattributes
git add .gitattributes

# Commit and push
git add .
git commit -m "Add large files with LFS"
git push
```

---

## Create Streamlit Cloud Account

### 1. Sign Up

1. Go to https://streamlit.io/cloud
2. Click **"Sign up"** or **"Continue with GitHub"**
3. Authorize Streamlit to access your GitHub repositories
4. Accept permissions (Streamlit needs read access to deploy your app)

### 2. Dashboard Overview

After signing in, you'll see:
- **Your apps**: List of deployed apps
- **New app**: Button to deploy new apps
- **Settings**: Account and workspace settings

---

## Deploy Your App

### Step-by-Step Deployment

**1. Click "New app"**

**2. Fill in deployment form:**

```
Repository: YOUR_USERNAME/ai-finance-assistant
Branch: main
Main file path: src/web_app/app.py
```

**Example:**
- **Repository**: `pbhi0717/ai-finance-assistant`
- **Branch**: `main`
- **Main file path**: `src/web_app/app.py`

**3. Advanced Settings (Optional - Click to expand):**

**App URL (Custom subdomain):**
```
your-app-name.streamlit.app
```

**Python version:**
```
3.11  (or 3.12 if needed)
```

**Secrets:** (See next section)

**4. Click "Deploy"**

### Deployment Process

You'll see:
```
🔄 Installing dependencies...
📦 Building your app...
🚀 Launching...
✅ Your app is live!
```

**First deployment takes 3-5 minutes.**

---

## Configure Secrets

Secrets are environment variables stored securely by Streamlit Cloud.

### Add Secrets During Deployment

**In "Advanced settings" → "Secrets":**

```toml
# Format: TOML
OPENAI_API_KEY = "sk-proj-your-actual-key-here"

# Multiple secrets
OPENAI_API_KEY = "sk-..."
ALPHA_VANTAGE_KEY = "your-key"

# Can also use quotes
[api_keys]
openai = "sk-..."
alpha_vantage = "abc123"
```

### Add Secrets After Deployment

1. Go to your app dashboard: https://share.streamlit.io/
2. Click on your app
3. Click **⋮ (three dots)** → **Settings**
4. Go to **Secrets** section
5. Add your secrets in TOML format:

```toml
OPENAI_API_KEY = "sk-proj-your-key"
```

6. Click **Save**
7. App will automatically reboot with new secrets

### Access Secrets in Your Code

```python
import streamlit as st

# Access secrets
api_key = st.secrets["OPENAI_API_KEY"]

# Or with nested structure
api_key = st.secrets["api_keys"]["openai"]
```

### Test Secrets Locally

Create `.streamlit/secrets.toml` locally (DO NOT commit to git):

```toml
OPENAI_API_KEY = "sk-proj-test-key"
```

Add to `.gitignore`:
```bash
echo ".streamlit/secrets.toml" >> .gitignore
```

---

## Manage Your App

### Update Your App

**Any push to the connected branch triggers auto-deployment:**

```bash
# Make changes locally
cd /Users/pushkar/IK_Agentic_AI/ai_finance_assistant

# Edit files
nano src/web_app/app.py

# Commit and push
git add .
git commit -m "Update feature X"
git push

# App auto-deploys in 2-3 minutes
```

### Reboot Your App

**Via Dashboard:**
1. Go to https://share.streamlit.io/
2. Click on your app
3. Click **⋮** → **Reboot app**

**Via URL:**
```
https://your-app-name.streamlit.app/?reboot=true
```

### View Logs

**Real-time logs:**
1. Go to your app dashboard
2. Click **⋮** → **Logs**
3. See real-time output, errors, and print statements

**In your code:**
```python
import streamlit as st

# These appear in logs
print("Debug message")  # Shows in logs
st.write("User message")  # Shows in app AND logs
```

### Delete Your App

1. Go to https://share.streamlit.io/
2. Click on your app
3. Click **⋮** → **Settings**
4. Scroll to bottom → **Delete app**
5. Confirm deletion

---

## Troubleshooting

### Common Issues

#### 1. Module Not Found Error

**Problem:**
```
ModuleNotFoundError: No module named 'langchain'
```

**Solution:**
- Verify `requirements.txt` includes the module
- Check spelling and version
- Push updated `requirements.txt` to GitHub

#### 2. App Won't Start / Stuck on "Launching"

**Causes:**
- Large dependencies taking time to install
- App crashes during initialization
- Import errors

**Solutions:**
```python
# Add error handling at top of app.py
try:
    import expensive_module
except ImportError as e:
    st.error(f"Failed to import: {e}")
    st.stop()
```

Check logs for actual error message.

#### 3. Secrets Not Working

**Problem:**
```
KeyError: 'OPENAI_API_KEY'
```

**Solutions:**
- Verify secret name matches exactly (case-sensitive)
- Check TOML format is correct
- Reboot app after adding secrets

**Correct usage:**
```python
# Check if secret exists first
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    st.error("API key not configured")
    st.stop()
```

#### 4. File Not Found Errors

**Problem:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'config.yaml'
```

**Solution:**
Use absolute paths relative to script location:

```python
from pathlib import Path

# Get script directory
script_dir = Path(__file__).parent

# Load files relative to script
config_path = script_dir / "config.yaml"
```

#### 5. Large Files Rejected

**Problem:**
```
error: file too large (>100MB)
```

**Solutions:**
- Use Git LFS (see above)
- Upload via GitHub UI
- Exclude and rebuild on startup
- Store in external service (S3, HF Hub)

#### 6. Slow App Performance

**Solutions:**
- Use `@st.cache_data` for expensive computations
- Use `@st.cache_resource` for model loading
- Optimize imports (lazy loading)
- Reduce initial data loading

```python
@st.cache_data(ttl=3600)
def load_data():
    # Cached for 1 hour
    return expensive_operation()

@st.cache_resource
def load_model():
    # Cached until app restart
    return Model()
```

---

## Cost & Limits

### Free Tier

**Includes:**
- ✅ Unlimited public apps
- ✅ 1GB RAM per app
- ✅ 1 CPU core per app
- ✅ Community support
- ✅ Auto-scaling (sleeps after inactivity)

**Limitations:**
- ⏸️ Apps sleep after 7 days of inactivity
- 🔓 Must be public repos (open source)
- 📊 Shared resources

### Paid Tiers

**Starter ($20/month per developer):**
- Private repos
- Custom subdomains
- More resources
- No sleep

**Team/Enterprise:**
- SSO
- Advanced security
- Dedicated resources
- SLA support

**Pricing:** https://streamlit.io/cloud/pricing

---

## Quick Reference Commands

### Initial Setup
```bash
# Create GitHub repo
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/USERNAME/REPO.git
git push -u origin main
```

### Updates
```bash
# Make changes
git add .
git commit -m "Description of changes"
git push
# App auto-deploys
```

### Secrets Format
```toml
# .streamlit/secrets.toml (local)
# OR Streamlit Cloud dashboard → Settings → Secrets

OPENAI_API_KEY = "sk-..."
API_SECRET = "abc123"

[database]
host = "localhost"
port = 5432
```

### Access Secrets
```python
import streamlit as st

api_key = st.secrets["OPENAI_API_KEY"]
db_host = st.secrets["database"]["host"]
```

---

## Comparison: Streamlit Cloud vs HuggingFace Spaces

| Feature | Streamlit Cloud | HuggingFace Spaces |
|---------|----------------|-------------------|
| **Setup Difficulty** | ⭐ Easy | ⭐⭐⭐ Complex (Docker) |
| **Deployment Time** | 3-5 min | 10-30 min |
| **Native Streamlit** | ✅ Yes | ❌ Via Docker only |
| **Free Tier** | ✅ Unlimited public apps | ✅ Limited resources |
| **Auto-deploy on push** | ✅ Yes | ✅ Yes |
| **Secrets Management** | ✅ Built-in (TOML) | ✅ Environment variables |
| **Custom Domain** | 💰 Paid tier | ✅ Free subdomain |
| **Private Repos** | 💰 Paid tier | ✅ Free |
| **Best For** | Streamlit apps | ML models, demos |

**Recommendation:**
- **Streamlit Cloud**: Best for Streamlit apps (no Docker needed)
- **HuggingFace**: Good for ML demos, already have HF account

---

## Support & Resources

- **Documentation**: https://docs.streamlit.io/streamlit-community-cloud
- **Community Forum**: https://discuss.streamlit.io/
- **Status Page**: https://streamlitstatus.com/
- **GitHub Issues**: https://github.com/streamlit/streamlit/issues

---

## Next Steps

✅ **App deployed successfully!**

**1. Share your app:**
- URL: `https://your-app.streamlit.app`
- Add to portfolio
- Share on social media

**2. Monitor usage:**
- Dashboard shows app views
- Check logs for errors
- Monitor API costs separately

**3. Iterate:**
- Push updates to GitHub
- App auto-deploys
- Test in production

**4. Scale up (if needed):**
- Upgrade to paid tier
- Get custom domain
- Enable private repos

---

**Happy deploying! 🚀**
