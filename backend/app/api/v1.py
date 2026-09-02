from fastapi import APIRouter, Request
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    components: dict[str, str]


router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    checks = await request.app.state.health_checks()
    return HealthResponse(
        status="healthy",
        service=request.app.state.settings.app_name,
        version=request.app.state.settings.app_version,
        components=checks,
    )
