from pydantic import ValidationError

from app.schemas import TelegramConnectRequest, TelegramLinkResponse


def test_telegram_connect_request_rejects_non_digit_code():
    try:
        TelegramConnectRequest(code="12AB56", telegram_id="123456")
    except ValidationError as exc:
        assert "code" in str(exc)
    else:
        raise AssertionError("Expected ValidationError")


def test_telegram_link_response_requires_non_negative_ttl():
    try:
        TelegramLinkResponse(code="123456", expires_at="2026-05-17T10:00:00", ttl_seconds=-1)
    except ValidationError as exc:
        assert "ttl_seconds" in str(exc)
    else:
        raise AssertionError("Expected ValidationError")
