#!/usr/bin/env python3
"""
SALES ANGEL - UNIFIED API SERVER
Master FastAPI application combining all services

Port: 8000
Swagger Docs: http://localhost:8000/docs
WebSocket: ws://localhost:8000/ws
"""

import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import asyncio
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import route modules
from api.routes import enrichment, content, pipeline, cadence, activity, analytics
from api.websocket import ConnectionManager
from api.models import HealthCheck, SystemStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = PROJECT_ROOT / "sales_angel.db"

# Global connection manager for WebSocket
manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 Sales Angel API starting up...")
    logger.info(f"📂 Database: {DB_PATH}")
    logger.info(f"📊 Swagger Docs: http://localhost:8000/docs")
    logger.info(f"🔌 WebSocket: ws://localhost:8000/ws")
    
    # Verify database exists
    if not DB_PATH.exists():
        logger.error(f"❌ Database not found at {DB_PATH}")
        logger.error("   Run upgrade_db_pipeline.py first!")
        sys.exit(1)
    
    yield
    
    logger.info("👋 Sales Angel API shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Sales Angel API",
    description="Complete sales intelligence and outreach automation platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = PROJECT_ROOT / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Templates
templates_dir = PROJECT_ROOT / "templates"
if templates_dir.exists():
    templates = Jinja2Templates(directory=str(templates_dir))

# ============================================================================
# CORE ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """API Homepage"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sales Angel API</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                padding: 40px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            h1 { font-size: 3em; margin: 0 0 20px 0; }
            .status { color: #4ade80; font-weight: bold; }
            a {
                color: #4ade80;
                text-decoration: none;
                font-weight: bold;
            }
            a:hover { text-decoration: underline; }
            .endpoints {
                margin-top: 30px;
                background: rgba(0, 0, 0, 0.3);
                padding: 20px;
                border-radius: 10px;
            }
            .endpoint {
                margin: 10px 0;
                padding: 10px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Sales Angel API</h1>
            <p class="status">✅ System Online</p>
            <p>Complete sales intelligence and outreach automation platform</p>
            
            <div class="endpoints">
                <h2>📚 Available Endpoints</h2>
                <div class="endpoint">
                    <a href="/docs">📖 Interactive API Docs (Swagger)</a>
                </div>
                <div class="endpoint">
                    <a href="/redoc">📄 API Documentation (ReDoc)</a>
                </div>
                <div class="endpoint">
                    <a href="/health">❤️ Health Check</a>
                </div>
                <div class="endpoint">
                    <a href="/status">📊 System Status</a>
                </div>
            </div>
            
            <div class="endpoints" style="margin-top: 20px;">
                <h2>🔧 API Routes</h2>
                <div class="endpoint">
                    <strong>/api/enrich</strong> - Contact enrichment (68 citations)
                </div>
                <div class="endpoint">
                    <strong>/api/content</strong> - Content generation (emails, scripts, LinkedIn)
                </div>
                <div class="endpoint">
                    <strong>/api/pipeline</strong> - Pipeline management
                </div>
                <div class="endpoint">
                    <strong>/api/cadence</strong> - Cadence automation
                </div>
                <div class="endpoint">
                    <strong>/api/activity</strong> - Activity tracking
                </div>
                <div class="endpoint">
                    <strong>/api/analytics</strong> - Real-time analytics
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="2.0.0"
    )

@app.get("/status", response_model=SystemStatus)
async def system_status():
    """System status with database info"""
    import sqlite3
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM contacts")
        total_contacts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE enriched = 1")
        enriched_contacts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM outreach_activities")
        total_activities = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contact_cadence_assignments WHERE status = 'active'")
        active_cadences = cursor.fetchone()[0]
        
        conn.close()
        
        return SystemStatus(
            status="operational",
            database="connected",
            total_contacts=total_contacts,
            enriched_contacts=enriched_contacts,
            total_activities=total_activities,
            active_cadences=active_cadences,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Echo back for testing
            await websocket.send_json({
                "type": "echo",
                "message": data,
                "timestamp": datetime.utcnow().isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

# Enrichment endpoints
app.include_router(
    enrichment.router,
    prefix="/api/enrich",
    tags=["Enrichment"]
)

# Content generation endpoints
app.include_router(
    content.router,
    prefix="/api/content",
    tags=["Content Generation"]
)

# Pipeline management endpoints
app.include_router(
    pipeline.router,
    prefix="/api/pipeline",
    tags=["Pipeline"]
)

# Cadence automation endpoints
app.include_router(
    cadence.router,
    prefix="/api/cadence",
    tags=["Cadence"]
)

# Activity tracking endpoints
app.include_router(
    activity.router,
    prefix="/api/activity",
    tags=["Activity"]
)

# Analytics endpoints
app.include_router(
    analytics.router,
    prefix="/api/analytics",
    tags=["Analytics"]
)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url)
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 80)
    print("🚀 SALES ANGEL UNIFIED API")
    print("=" * 80)
    print(f"\n📂 Database: {DB_PATH}")
    print(f"🌐 Server: http://localhost:8000")
    print(f"📊 Swagger Docs: http://localhost:8000/docs")
    print(f"🔌 WebSocket: ws://localhost:8000/ws")
    print("\n" + "=" * 80 + "\n")
    
    uvicorn.run(
        "sales_angel_unified_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
