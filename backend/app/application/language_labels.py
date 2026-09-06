"""User-facing language labels in native script."""

LANGUAGE_DISPLAY_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "हिन्दी",
    "ta": "தமிழ்",
    "ml": "മലയാളം",
}


def language_display_name(code: str | None) -> str:
    if not code:
        return "English"
    return LANGUAGE_DISPLAY_NAMES.get(code, code)
