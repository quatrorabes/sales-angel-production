from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import os

app = FastAPI(
    title="Sales Angel Intelligence API",
    version="2.0.0",
    description="AI-powered sales intelligence platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ROOT ENDPOINTS ====================

@app.get("/")
async def root():
    return {
        "message": "Sales Angel Production API",
        "status": "operational",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/api/intelligence/status",
            "/api/intelligence/full-stack",
            "/api/enrichment/status",
            "/docs"
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ==================== INTELLIGENCE ENDPOINTS ====================

class EnrichmentRequest(BaseModel):
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    vertical: str = "saas"

@app.get("/api/intelligence/status")
async def intelligence_status():
    """Check intelligence system status"""
    return {
        "status": "operational",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "modules": {
            "enrichment": "ready",
            "scoring": "ready",
            "content": "ready"
        }
    }

@app.post("/api/intelligence/full-stack")
async def full_stack_intelligence(request: EnrichmentRequest):
    """Full intelligence pipeline endpoint"""
    return {
        "status": "success",
        "message": "Intelligence system connected successfully!",
        "request": request.dict(),
        "enrichment": {
            "profile": f"Mock enrichment for {request.name} at {request.company}",
            "timestamp": datetime.now().isoformat()
        },
        "scoring": {
            "score": 85,
            "tier": "HOT",
            "factors": ["Decision maker", "Budget available", "Recent funding"]
        },
        "next_steps": "Ready to integrate real enrichment modules"
    }

# ==================== ENRICHMENT ENDPOINTS ====================

@app.get("/api/enrichment/status")
async def enrichment_status():
    return {
        "status": "enrichment ready",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/enrichment/enrich")
async def enrich_lead(name: str, company: Optional[str] = None):
    return {
        "enriched": True,
        "name": name,
        "company": company,
        "timestamp": datetime.now().isoformat()
    }

# ==================== ANALYTICS ENDPOINTS ====================

@app.get("/api/analytics/status")
async def analytics_status():
    return {
        "status": "analytics ready",
        "timestamp": datetime.now().isoformat()
    }

# ==================== PIPELINE ENDPOINTS ====================

@app.get("/api/pipeline/status")
async def pipeline_status():
    return {
        "status": "pipeline ready",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ==================== ENRICHMENT ENDPOINTS ====================

@app.post("/api/enrichment/profile")
async def enrich_profile(
    name: str,
    company: Optional[str] = None,
    email: Optional[str] = None
):
    """Enrich a contact profile with additional information"""
    
    return {
        "status": "success",
        "profile": {
            "name": name,
            "company": company,
            "email": email,
            "enriched": True,
            "title": "Mock Title",
            "linkedin": "https://linkedin.com/in/mock",
            "decision_maker": True
        },
        "timestamp": datetime.now().isoformat()
    }

# ==================== CONTENT GENERATION ENDPOINTS ====================

@app.post("/api/content/email")
async def generate_email(
    prospect_name: str,
    company: str,
    tone: str = "professional"
):
    """Generate personalized email content"""
    
    return {
        "status": "success",
        "email": {
            "subject": f"Quick question about {company}'s growth",
            "body": f"""Hi {prospect_name},

I noticed {company} is making impressive strides in the market. 

I help companies like yours accelerate their sales processes through intelligent automation.

Would you be open to a brief 15-minute call next week to explore how we could help {company} achieve similar results?

Best regards,
[Your Name]""",
            "tone": tone
        },
        "timestamp": datetime.now().isoformat()
    }

