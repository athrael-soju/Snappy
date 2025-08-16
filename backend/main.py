import os
import uvicorn
from api.app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    try:
        port = int(os.getenv("PORT", "8000"))
    except Exception:
        raise ValueError("Invalid PORT")
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    uvicorn.run(
        "main:app", host=host, port=port, log_level=log_level, reload=True
    )
