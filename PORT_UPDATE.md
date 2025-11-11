# Portfolio Service Port Update

**Date**: 2025-01-XX  
**Change**: Port updated from 8001 to 8012

## Reason

Port 8001 was already in use by `fks_api` service. To avoid conflicts, portfolio service has been assigned port **8012**.

## Files Updated

1. **Service Registry**: `repo/main/config/service_registry.json`
   - Added `fks_portfolio` service entry
   - Port: 8012
   - Dependencies: fks_data, fks_ai

2. **Docker Compose**: `repo/portfolio/docker-compose.yml`
   - Updated port mapping: `8012:8012`

3. **Entrypoint Script**: `repo/portfolio/entrypoint.sh`
   - Updated uvicorn port: `--port 8012`

4. **README**: `repo/portfolio/README.md`
   - Updated port documentation: `8012`

## Service Registry Entry

```json
{
  "fks_portfolio": {
    "name": "fks_portfolio",
    "port": 8012,
    "base_url": "http://fks_portfolio:8012",
    "health_url": "http://fks_portfolio:8012/health",
    "dependencies": [
      "fks_data",
      "fks_ai"
    ]
  }
}
```

## Testing

After updating, test the service:

```bash
# Start the service
cd repo/portfolio
docker-compose up -d

# Check health
curl http://localhost:8012/health

# Check API docs
curl http://localhost:8012/docs
```

## Next Steps

1. ✅ Port conflict resolved
2. ✅ Service registry updated
3. ⏳ Update start.sh/stop.sh scripts if needed
4. ⏳ Test service startup
5. ⏳ Update documentation references

