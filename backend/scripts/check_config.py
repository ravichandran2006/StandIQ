from app.settings import get_settings


SECRET_FIELDS = {"database_url", "pinecone_api_key", "llm_api_key", "app_secret_key"}


def main() -> int:
    settings = get_settings()
    checks = {
        "DATABASE_URL": settings.database_configured(),
        "PINECONE_API_KEY": bool(settings.pinecone_api_key and settings.pinecone_api_key.get_secret_value().strip()),
        "PINECONE_INDEX_NAME": bool(settings.pinecone_index_name and settings.pinecone_index_name.strip()),
        "LLM_PROVIDER": bool(settings.llm_provider and settings.llm_provider.strip()),
        "LLM_API_KEY": bool(settings.llm_api_key and settings.llm_api_key.get_secret_value().strip()),
        "LLM_MODEL": bool(settings.llm_model and settings.llm_model.strip()),
        "EMBEDDING_PROVIDER": bool(settings.embedding_provider and settings.embedding_provider.strip()),
        "EMBEDDING_MODEL": bool(settings.embedding_model and settings.embedding_model.strip()),
        "APP_SECRET_KEY": bool(settings.app_secret_key and settings.app_secret_key.get_secret_value().strip()),
    }
    for name, configured in checks.items():
        print(f"{'configured' if configured else 'missing'}: {name}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
