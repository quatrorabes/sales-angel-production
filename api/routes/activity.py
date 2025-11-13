from fastapi import APIRouter
router = APIRouter(prefix="/api/activity", tags=["Activity"])

@router.get("/status")
async def status():
    return {"status": "activity ready"}
