from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse, summary="Check API availability")
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="ai-aion-api")
