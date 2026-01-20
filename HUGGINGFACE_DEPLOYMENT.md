# Hugging Face Spaces Deployment Guide

## Prerequisites

1. **Hugging Face Account**: Sign up at https://huggingface.co/
2. **OpenAI API Key**: Get from https://platform.openai.com/api-keys
3. **Git**: Installed and configured

## Deployment Steps

### 1. Create New Space

1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Configure:
   - **Owner**: Your username/organization
   - **Space name**: `ai-finance-assistant`
   - **License**: MIT
   - **SDK**: Streamlit
   - **Visibility**: Public (or Private)
4. Click **"Create Space"**

### 2. Configure API Key

1. In your new Space, go to **Settings** → **Repository secrets**
2. Click **"Add a secret"**
3. Add:
   - **Name**: `OPENAI_API_KEY`
   - **Value**: Your OpenAI API key (starts with `sk-...`)
4. Click **"Save"**

### 3. Prepare Local Repository

```bash
# Clone your new HF Space
git clone https://huggingface.co/spaces/YOUR_USERNAME/ai-finance-assistant
cd ai-finance-assistant

# Copy files from your project
# Copy all source files
cp -r /path/to/your/project/src .
cp -r /path/to/your/project/config.yaml .

# Copy requirements.txt
cp /path/to/your/project/requirements.txt .

# Copy .streamlit config
cp -r /path/to/your/project/.streamlit .

# Rename README_HF.md to README.md
cp /path/to/your/project/README_HF.md README.md
```

### 4. Verify File Structure

Your HF Space should have:

```
ai-finance-assistant/
├── README.md                    # HF frontmatter + description
├── requirements.txt             # Python dependencies
├── config.yaml                  # App configuration
├── .streamlit/
│   └── config.toml             # Streamlit settings
└── src/
    ├── agents/
    ├── core/
    ├── data/
    │   ├── faiss_index/
    │   └── knowledge_base/
    ├── rag/
    ├── utils/
    ├── web_app/
    │   └── app.py              # Main entry point
    └── workflow/
```

### 5. Push to Hugging Face

```bash
# Add all files
git add .

# Commit changes
git commit -m "Initial deployment of AI Finance Assistant"

# Push to HF
git push
```

### 6. Monitor Deployment

1. Go to your Space URL: `https://huggingface.co/spaces/YOUR_USERNAME/ai-finance-assistant`
2. Watch the **Logs** tab for build progress
3. Wait for build to complete (~5-10 minutes for first build)
4. Once ready, the **App** tab will show your running application

## Important Notes

### File Size Limits
- **Single file**: Max 50GB
- **Total Space**: No hard limit, but large spaces take longer to build
- Your FAISS index and knowledge base should be fine

### Environment Variables
- API keys are accessed via `os.getenv("OPENAI_API_KEY")`
- Your app already handles this correctly in `src/core/config.py`

### Memory & Resources
- Free tier: 2 CPU cores, 16GB RAM
- Should be sufficient for your app
- If you need more, upgrade to paid tier

### Persistence
- Hugging Face Spaces are **ephemeral** - no persistent storage
- User uploads (portfolio CSV) are temporary
- FAISS index and knowledge base are part of the deployment (read-only)

## Troubleshooting

### Build Fails
- Check **Logs** tab for specific errors
- Common issues:
  - Missing dependencies in requirements.txt
  - Import errors (check file paths)
  - API key not configured

### App Won't Load
- Verify `app_file: src/web_app/app.py` in README.md frontmatter
- Check Streamlit config in `.streamlit/config.toml`
- Ensure port 7860 in config

### API Errors
- Verify `OPENAI_API_KEY` is set in Repository secrets
- Check key is valid and has credits

### Slow Performance
- First load takes time (model initialization)
- Enable caching (already implemented)
- Consider upgrading Space tier if needed

## Post-Deployment

### Update Your Space
```bash
# Make changes locally
# Commit and push
git add .
git commit -m "Update: description of changes"
git push
```

### Monitor Usage
- Check **Analytics** tab for usage stats
- Monitor API costs in OpenAI dashboard

### Share Your Space
- URL: `https://huggingface.co/spaces/YOUR_USERNAME/ai-finance-assistant`
- Embed in websites, share on social media
- Add to your portfolio

## Alternative: Deploy via Web UI

Instead of Git, you can use HF's web interface:

1. Create Space as above
2. Click **"Files"** tab
3. Click **"Add file"** → **"Upload files"**
4. Drag and drop your project files
5. Maintain the directory structure
6. Commit changes

## Cost Considerations

- **Hugging Face Spaces**: Free tier available (sufficient for most users)
- **OpenAI API**: Pay per token used
  - GPT-4o-mini: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
  - Monitor usage to avoid unexpected costs
  - Consider adding rate limiting for public deployments

## Security Best Practices

1. **Never commit API keys** to Git
2. **Use Repository secrets** for all sensitive data
3. **Enable XsrfProtection** (already configured)
4. **Monitor access logs** regularly
5. **Set Space to Private** if needed

## Support

- **Hugging Face Docs**: https://huggingface.co/docs/hub/spaces
- **Streamlit Docs**: https://docs.streamlit.io/
- **Community Forum**: https://discuss.huggingface.co/

---

Happy deploying! 🚀
