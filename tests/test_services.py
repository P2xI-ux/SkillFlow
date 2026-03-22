from app.models.enums import TestStatus
from app.services.event_bus import EventBus
from app.services.rating_strategy import BonusStrategy, RatingStrategyFactory, StandardStrategy, TournamentStrategy
from app.services.state_machine import TestStateMachine


class DummyTest:
    def __init__(self, status):
        self.status = status
        self.published_at = None


def test_state_machine_allows_expected_transition():
    test = DummyTest(TestStatus.DRAFT)
    TestStateMachine(test.status).apply(test, "submit")
    assert test.status == TestStatus.PENDING_MODERATION


def test_state_machine_blocks_invalid_transition():
    test = DummyTest(TestStatus.DRAFT)
    try:
        TestStateMachine(test.status).apply(test, "approve")
    except ValueError as exc:
        assert "недопустим" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_rating_strategy_factory_picks_expected_implementation():
    assert isinstance(RatingStrategyFactory.build(2), StandardStrategy)
    assert isinstance(RatingStrategyFactory.build(4), TournamentStrategy)
    assert isinstance(RatingStrategyFactory.build(5), BonusStrategy)


def test_event_bus_collects_messages_from_subscribers():
    bus = EventBus()
    bus.subscribe("TEST_COMPLETED", lambda event: ["earned"])
    assert bus.publish("TEST_COMPLETED", {"student_id": 1}) == ["earned"]
