from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Sales Angel Production API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Sales Angel Production API", "status": "operational"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# Import and include routers if they exist
try:
    from api.routes import enrichment
    app.include_router(enrichment.router)
except:
    pass

try:
    from api.routes import content
    app.include_router(content.router)
except:
    pass

try:
    from api.routes import pipeline
    app.include_router(pipeline.router)
except:
    pass

try:
    from api.routes import cadence
    app.include_router(cadence.router)
except:
    pass

try:
    from api.routes import activity
    app.include_router(activity.router)
except:
    pass

try:
    from api.routes import analytics
    app.include_router(analytics.router)
except:
    pass

# Import all route modules
from api.routes import enrichment, intelligence, analytics, pipeline

# Include all routers
app.include_router(enrichment.router)
app.include_router(intelligence.router)
app.include_router(analytics.router)
app.include_router(pipeline.router)
