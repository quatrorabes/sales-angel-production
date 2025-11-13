from fastapi import APIRouter
router = APIRouter(prefix="/api/content", tags=["Content"])

@router.get("/status")
async def status():
    return {"status": "content ready"}
