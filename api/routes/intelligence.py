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
        "timestamp": datetime.now().isoformat()
    }

@router.post("/full-stack")
async def full_stack_intelligence(request: EnrichmentRequest):
    """Test endpoint for full intelligence pipeline"""
    return {
        "status": "success",
        "message": "Intelligence system connected",
        "request": request.dict(),
        "timestamp": datetime.now().isoformat()
    }
