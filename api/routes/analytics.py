from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/status")
async def status():
    return {"status": "analytics ready", "timestamp": datetime.now().isoformat()}
