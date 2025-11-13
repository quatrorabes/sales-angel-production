from fastapi import APIRouter
router = APIRouter(prefix="/api/enrichment", tags=["Enrichment"])

@router.get("/status")
async def status():
    return {"status": "enrichment ready"}
