from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from datetime import datetime

router = APIRouter(prefix="/api/intelligence", tags=["Intelligence"])

class EnrichmentRequest(BaseModel):
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    vertical: str = "saas"

@router.get("/status")
async def intelligence_status():
    """Check intelligence system status"""
    return {
        "status": "operational",
        "version": "1.0.0",
        "modules": {
            "enrichment": "checking...",
            "scoring": "checking...",
            "content": "checking..."
        }
    }

@router.post("/full-stack")
async def full_stack_intelligence(request: EnrichmentRequest):
    """
    Simplified version for testing - we'll add the real logic after confirming it works
    """
    try:
        # For now, return mock data to test the endpoint
        return {
            "status": "success",
            "contact": request.dict(),
            "enrichment": {
                "profile": f"Mock enrichment for {request.name} at {request.company}",
                "timestamp": datetime.now().isoformat()
            },
            "scoring": {
                "score": 85,
                "tier": "HOT",
                "factors": ["Decision maker", "Budget available", "Recent funding"]
            },
            "content": {
                "email_generated": True,
                "scripts_generated": True
            },
            "message": "Full intelligence pipeline will be activated once modules are confirmed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enrich")
async def enrich_contact(request: EnrichmentRequest):
    """Simplified enrichment endpoint"""
    return {
        "status": "success",
        "enriched": True,
        "data": {
            "name": request.name,
            "company": request.company,
            "enrichment": "Mock enrichment data"
        }
    }
