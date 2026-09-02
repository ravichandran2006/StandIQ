from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import router as v1_router
from app.infrastructure.database import Database
from app.infrastructure.external_services import LLMClient, PineconeClient
from app.logging_config import configure_logging
from app.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings)
    database = Database(resolved_settings)
    pinecone = PineconeClient(resolved_settings)
    llm = LLMClient(resolved_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        await database.close()

    app = FastAPI(title="StandIQ API", version=resolved_settings.app_version, lifespan=lifespan)
    app.state.settings = resolved_settings
    app.state.database = database

    async def health_checks() -> dict[str, str]:
        return {
            "application": "healthy",
            "database": await database.check(),
            "pinecone": await pinecone.check(),
            "llm": await llm.check(),
        }

    app.state.health_checks = health_checks
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception:
            if resolved_settings.app_env == "production":
                return JSONResponse(status_code=500, content={"detail": "Internal server error"})
            raise
        response.headers["X-Request-ID"] = request_id
        return response

    app.include_router(v1_router)
    return app


app = create_app()
