#!/bin/bash
set -e

# Default values
SERVICE_NAME=${SERVICE_NAME:-fks_portfolio}
SERVICE_PORT=${SERVICE_PORT:-${PORT:-8012}}
HOST=${HOST:-0.0.0.0}

echo "Starting ${SERVICE_NAME} on ${HOST}:${SERVICE_PORT}"

# Check if running as API server (default) or CLI
if [ "$1" = "cli" ] || [ "$1" = "--help" ]; then
    # Run CLI mode
    exec python src/cli.py "$@"
else
    # Run API server - import app from routes
    exec python -c "from src.api.routes import create_app; import uvicorn; app = create_app(); uvicorn.run(app, host='${HOST}', port=${SERVICE_PORT})"
fi

