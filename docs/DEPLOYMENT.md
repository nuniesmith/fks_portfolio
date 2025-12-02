# Portfolio Service - Deployment Guide

**Date**: 2025-01-XX  
**Status**: Ready for Deployment

---

## 🚀 Deployment Overview

This guide covers deploying the portfolio service in development and production environments.

---

## 📋 Prerequisites

### Required Services
- **Docker** and **Docker Compose**
- **Python 3.9+** (for local development)
- **PostgreSQL** (optional, for production)
- **Redis** (optional, for caching)

### Environment Variables
```bash
# Portfolio Service
PORT=8012
LOG_LEVEL=INFO
DATA_DIR=/app/data

# API Keys (optional)
POLYGON_API_KEY=your_key
ALPHA_VANTAGE_API_KEY=your_key
BINANCE_API_KEY=your_key
COINMARKETCAP_API_KEY=your_key

# Service URLs
FKS_AI_BASE_URL=http://fks_ai:8007
FKS_DATA_BASE_URL=http://fks_data:8003
```

---

## 🐳 Docker Deployment

### Quick Start
```bash
# Build and run with Docker Compose
cd repo/portfolio
docker-compose up -d

# Check logs
docker-compose logs -f portfolio

# Stop service
docker-compose down
```

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8012

# Run application
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8012"]
```

### Docker Compose
```yaml

services:
  portfolio:
    build: .
    container_name: fks_portfolio
    ports:
      - "8012:8012"
    volumes:
      - ./src:/app/src
      - ./data:/app/data
    environment:
      - LOG_LEVEL=INFO
      - DATA_DIR=/app/data
      - PORT=8012
    command: uvicorn src.api.server:app --host 0.0.0.0 --port 8012
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8012/health').raise_for_status()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## 🔧 Local Development

### Setup
```bash
# Clone repository
cd repo/portfolio

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run service
uvicorn src.api.server:app --host 0.0.0.0 --port 8012 --reload
```

### Development Server
```bash
# Run with auto-reload
uvicorn src.api.server:app --reload --port 8012

# Run with specific log level
uvicorn src.api.server:app --log-level debug --port 8012
```

---

## 🌐 Production Deployment

### Environment Setup
```bash
# Set environment variables
export PORT=8012
export LOG_LEVEL=INFO
export DATA_DIR=/app/data
export FKS_AI_BASE_URL=http://fks_ai:8007
```

### Gunicorn (Production WSGI Server)
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn src.api.server:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8012 \
    --timeout 120
```

### Systemd Service
```ini
[Unit]
Description=FKS Portfolio Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/app/portfolio
Environment="PATH=/app/portfolio/venv/bin"
ExecStart=/app/portfolio/venv/bin/uvicorn src.api.server:app --host 0.0.0.0 --port 8012
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 🔒 Security

### API Keys
- Store API keys in environment variables
- Never commit API keys to git
- Use `.env.example` as template
- Rotate API keys regularly

### Network Security
- Use HTTPS in production
- Restrict access to service
- Use firewall rules
- Enable CORS only for trusted domains

### Data Security
- Encrypt sensitive data
- Use secure database connections
- Regular backups
- Access control

---

## 📊 Monitoring

### Health Checks
```bash
# Health check
curl http://localhost:8012/health

# Readiness check
curl http://localhost:8012/ready
```

### Logging
```bash
# View logs
docker logs fks_portfolio

# Follow logs
docker logs -f fks_portfolio

# Check log files
tail -f data/logs/*.log
```

### Metrics
- Response times
- Error rates
- Request counts
- Service availability

---

## 🧪 Testing

### Integration Tests
```bash
# Run integration tests
./scripts/test_integration.sh

# Run pytest tests
pytest tests/ -v
```

### Demo Workflow
```bash
# Run demo workflow
./scripts/demo_workflow.sh
```

---

## 🔄 Updates and Maintenance

### Updating Service
```bash
# Pull latest code
git pull

# Rebuild Docker image
docker-compose build

# Restart service
docker-compose up -d
```

### Database Migrations
```bash
# Run migrations (if using database)
# Currently using SQLite, no migrations needed
```

### Backup
```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Backup database
cp data/historical/portfolio.db backup/portfolio-$(date +%Y%m%d).db
```

---

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check Docker logs
docker logs fks_portfolio

# Check port availability
netstat -tuln | grep 8012

# Check dependencies
docker-compose ps
```

### API Errors
```bash
# Check API response
curl -v http://localhost:8012/health

# Check error logs
tail -f data/logs/*.log
```

### Performance Issues
```bash
# Check resource usage
docker stats fks_portfolio

# Check response times
curl -w "@curl-format.txt" http://localhost:8012/api/dashboard/overview
```

---

## 📚 Additional Resources

### Documentation
- API Documentation: `API_DOCUMENTATION.md`
- Integration Guide: `INTEGRATION_TESTING.md`
- Architecture: `docs/ARCHITECTURE.md`

### Support
- Service Registry: `repo/main/config/service_registry.json`
- Health Dashboard: `http://localhost:8000/services/fks_portfolio/`

---

**Status**: Ready for Deployment  
**Next**: Deploy and test in target environment

