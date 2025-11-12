"""
Server entry point for portfolio API
"""
import uvicorn
from .routes import create_app

if __name__ == "__main__":
    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8012,  # Portfolio service port
        log_level="info"
    )

