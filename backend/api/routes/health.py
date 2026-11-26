from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter(tags=["System Health"])


@router.get("/health")
async def health_check():
    return {
        "success": True,
        "application": "AETHERIQ AI",
        "status": "healthy",
        "backend": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }