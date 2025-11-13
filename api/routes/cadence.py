from fastapi import APIRouter
router = APIRouter(prefix="/api/cadence", tags=["Cadence"])

@router.get("/status")
async def status():
    return {"status": "cadence ready"}
