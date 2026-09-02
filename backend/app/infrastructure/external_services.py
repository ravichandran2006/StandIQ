from typing import Literal

from app.settings import Settings


ServiceStatus = Literal["healthy", "configured", "not_configured", "unavailable"]


class PineconeClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def check(self) -> ServiceStatus:
        if not self._settings.pinecone_configured():
            return "not_configured"
        return "configured"


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def check(self) -> ServiceStatus:
        if not self._settings.llm_configured():
            return "not_configured"
        return "configured"
