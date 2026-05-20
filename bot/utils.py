import httpx


def extract_api_error(exc: httpx.HTTPStatusError) -> str:
    """Return a human-readable error string from an HTTP error response."""
    try:
        data = exc.response.json()
    except Exception:
        return exc.response.text or "Неизвестная ошибка"

    if isinstance(data, dict):
        if isinstance(data.get("detail"), dict):
            return (
                data["detail"].get("message")
                or data["detail"].get("code")
                or "Неизвестная ошибка"
            )
        message = data.get("message") or data.get("detail") or data.get("code")
        return str(message) if message else "Неизвестная ошибка"
    return str(data) if data else "Неизвестная ошибка"
