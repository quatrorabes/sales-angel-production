from fastapi import APIRouter
router = APIRouter(prefix="/api/pipeline", tags=["Pipeline"])

@router.get("/status")
async def status():
    return {"status": "pipeline ready"}
