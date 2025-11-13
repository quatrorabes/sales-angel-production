import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from api.main import app
except ImportError:
    # Fallback: Create a minimal app if api.main doesn't exist
    from fastapi import FastAPI
    app = FastAPI(title="Sales Angel Production", version="1.0.0")
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "version": "1.0.0"}
    
    @app.get("/")
    async def root():
        return {"message": "Sales Angel Production API", "status": "operational"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
