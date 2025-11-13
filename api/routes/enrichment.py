from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/enrichment", tags=["Enrichment"])

@router.get("/status")
async def status():
    return {"status": "enrichment ready", "timestamp": datetime.now().isoformat()}

@router.post("/enrich")
async def enrich_lead(name: str, company: Optional[str] = None):
    return {"enriched": True, "name": name, "company": company}
