from fastapi import APIRouter
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/status")
async def status():
    return {"status": "analytics ready"}
