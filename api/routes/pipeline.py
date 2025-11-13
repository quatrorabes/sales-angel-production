from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline"])

@router.get("/status")
async def status():
    return {"status": "pipeline ready", "timestamp": datetime.now().isoformat()}
