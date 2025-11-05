"""
DeepSeek OCR Service - Entry point
"""

import uvicorn
from app.core.config import settings
from app.main import create_app

# Create application instance
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
        log_level="info",
    )
