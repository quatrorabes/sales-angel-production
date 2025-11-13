from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import sys

# Add the parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(
    title="Sales Angel Intelligence API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Sales Angel Production API",
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }

# Import and register routes
from api.routes import intelligence, enrichment, analytics, pipeline

app.include_router(intelligence.router)
app.include_router(enrichment.router)
app.include_router(analytics.router)
app.include_router(pipeline.router)

print("✅ All routes registered successfully")
