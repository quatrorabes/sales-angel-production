from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from datetime import datetime

# Create the FastAPI app
app = FastAPI(
    title="Sales Angel Intelligence API",
    version="2.0.0",
    description="AI-powered sales intelligence and enrichment platform"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Sales Angel Intelligence API",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/api/enrichment",
            "/api/intelligence",
            "/api/analytics",
            "/api/pipeline"
        ]
    }

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Import and register all route modules
try:
    from api.routes import enrichment
    app.include_router(enrichment.router)
    print("✅ Enrichment routes registered")
except Exception as e:
    print(f"❌ Failed to register enrichment routes: {e}")

try:
    from api.routes import intelligence
    app.include_router(intelligence.router)
    print("✅ Intelligence routes registered")
except Exception as e:
    print(f"❌ Failed to register intelligence routes: {e}")

try:
    from api.routes import analytics
    app.include_router(analytics.router)
    print("✅ Analytics routes registered")
except Exception as e:
    print(f"❌ Failed to register analytics routes: {e}")

try:
    from api.routes import pipeline
    app.include_router(pipeline.router)
    print("✅ Pipeline routes registered")
except Exception as e:
    print(f"❌ Failed to register pipeline routes: {e}")

# Fallback test endpoint
@app.post("/api/test")
async def test_endpoint(data: Dict[Any, Any]):
    return {
        "message": "Test successful",
        "received": data,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
