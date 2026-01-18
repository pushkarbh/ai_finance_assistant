# Docker Deployment Guide

## Quick Start

### 1. Build and Run with Docker Compose (Recommended)

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OPENAI_API_KEY
nano .env

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

Access the app at: **http://localhost:8502**

### 2. Build and Run with Docker (Manual)

```bash
# Build the image
docker build -t ai-finance-assistant .

# Run the container
docker run -d \
  --name ai-finance-assistant \
  -p 8502:8502 \
  -e OPENAI_API_KEY=your_api_key_here \
  -v $(pwd)/src/data:/app/src/data \
  ai-finance-assistant

# View logs
docker logs -f ai-finance-assistant

# Stop and remove
docker stop ai-finance-assistant
docker rm ai-finance-assistant
```

## Configuration

### Environment Variables

Required:
- `OPENAI_API_KEY`: Your OpenAI API key

Optional:
- `LOG_LEVEL`: Logging level (default: INFO)
- `STREAMLIT_SERVER_PORT`: Port to run on (default: 8502)

### Volumes

The container uses these volumes:

1. **config.yaml**: Application configuration (read-only)
   ```bash
   -v ./config.yaml:/app/config.yaml:ro
   ```

2. **Data directory**: FAISS index and knowledge base
   ```bash
   -v ./src/data:/app/src/data
   ```

## Production Deployment

### Resource Limits

Adjust in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

### Health Checks

The container includes health checks:
```bash
# Check container health
docker ps

# Should show "healthy" status after ~40 seconds
```

### Logging

View logs:
```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f ai-finance-assistant
```

## Development Mode

For development with hot-reload:

```yaml
# Uncomment in docker-compose.yml
volumes:
  - ./src:/app/src  # Mount source code
```

Then:
```bash
docker-compose up
```

## Troubleshooting

### Container won't start

Check logs:
```bash
docker-compose logs
```

Common issues:
- Missing `OPENAI_API_KEY` in `.env`
- Port 8502 already in use
- Insufficient memory

### FAISS index not found

Ensure data directory exists:
```bash
mkdir -p src/data/faiss_index
mkdir -p src/data/knowledge_base
```

Then rebuild:
```bash
docker-compose down
docker-compose up --build
```

### Permission issues

Fix data directory permissions:
```bash
chmod -R 755 src/data
```

## Multi-Architecture Build

For ARM64 (Apple Silicon) and AMD64:

```bash
# Build for multiple architectures
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ai-finance-assistant:latest \
  --push .
```

## Cloud Deployment

### AWS ECS / Fargate

1. Push image to ECR:
```bash
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag ai-finance-assistant:latest <account>.dkr.ecr.us-east-1.amazonaws.com/ai-finance-assistant:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/ai-finance-assistant:latest
```

2. Create task definition with:
   - Port mapping: 8502
   - Environment variables: OPENAI_API_KEY
   - Memory: 4GB
   - CPU: 2 vCPU

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/ai-finance-assistant

# Deploy
gcloud run deploy ai-finance-assistant \
  --image gcr.io/PROJECT_ID/ai-finance-assistant \
  --platform managed \
  --port 8502 \
  --memory 4Gi \
  --set-env-vars OPENAI_API_KEY=your_key
```

### Azure Container Instances

```bash
# Create resource group
az group create --name ai-finance-rg --location eastus

# Create container
az container create \
  --resource-group ai-finance-rg \
  --name ai-finance-assistant \
  --image ai-finance-assistant:latest \
  --dns-name-label ai-finance-app \
  --ports 8502 \
  --environment-variables OPENAI_API_KEY=your_key
```

## Security Best Practices

1. **Never commit .env file**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Use secrets management** (production):
   - AWS Secrets Manager
   - Google Secret Manager
   - Azure Key Vault

3. **Run as non-root user** (add to Dockerfile):
   ```dockerfile
   RUN useradd -m -u 1000 appuser
   USER appuser
   ```

4. **Scan for vulnerabilities**:
   ```bash
   docker scan ai-finance-assistant
   ```

## Monitoring

### Prometheus Metrics

Add to Dockerfile:
```dockerfile
EXPOSE 9090
```

### Log Aggregation

Use Docker logging drivers:
```yaml
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## Backup

Backup data directory:
```bash
tar -czf ai-finance-backup-$(date +%Y%m%d).tar.gz src/data/
```

Restore:
```bash
tar -xzf ai-finance-backup-20260118.tar.gz
```

## Updates

Update the container:
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up --build -d

# Or with Docker
docker build -t ai-finance-assistant .
docker stop ai-finance-assistant
docker rm ai-finance-assistant
docker run -d --name ai-finance-assistant ... ai-finance-assistant
```
