from app.schemas import ModerateTestRequest


def test_moderate_test_request_requires_comment_on_reject():
    try:
        ModerateTestRequest(action="reject", comment="   ")
    except ValueError as exc:
        assert "комментарий" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError")


def test_moderate_test_request_allows_approve_without_comment():
    payload = ModerateTestRequest(action="approve", comment=None)
    assert payload.action == "approve"
