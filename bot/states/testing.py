from aiogram.fsm.state import State, StatesGroup


class TestPassStates(StatesGroup):
    """States for the test-passing FSM."""

    answering = State()
    confirm_retake = State()


class _RetakeStateStorage:
    """In-memory store that keeps pending retake data between messages."""

    def __init__(self) -> None:
        self._pending: dict[int, dict] = {}

    async def set_pending_retake(
        self, user_id: int, test_id: int, questions: list[dict]
    ) -> None:
        self._pending[user_id] = {"test_id": test_id, "questions": questions}

    async def pop_pending_retake(self, user_id: int) -> dict | None:
        return self._pending.pop(user_id, None)


# Singleton used across all handlers
state_storage = _RetakeStateStorage()
