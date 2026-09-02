import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.settings import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        cors_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    )


@pytest.mark.asyncio
async def test_health_is_available_without_external_credentials(settings: Settings) -> None:
    app = create_app(settings)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "standiq-api",
        "version": "v1",
        "components": {
            "application": "healthy",
            "database": "not_configured",
            "pinecone": "not_configured",
            "llm": "not_configured",
        },
    }
    assert response.headers["x-request-id"]


def test_cors_is_restricted(settings: Settings) -> None:
    app = create_app(settings)
    cors = next(m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware")
    assert cors.kwargs["allow_origins"] == ["http://localhost:5173", "http://127.0.0.1:5173"]
    assert cors.kwargs["allow_origins"] != ["*"]


def test_settings_never_require_external_services_for_import(settings: Settings) -> None:
    assert settings.database_configured() is False
    assert settings.pinecone_configured() is False
    assert settings.llm_configured() is False
