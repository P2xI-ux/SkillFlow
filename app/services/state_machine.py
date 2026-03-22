from dataclasses import dataclass
from datetime import datetime

from app.models.enums import TestStatus


_ALLOWED_TRANSITIONS = {
    TestStatus.DRAFT: {"submit": TestStatus.PENDING_MODERATION, "archive": TestStatus.ARCHIVED},
    TestStatus.PENDING_MODERATION: {"approve": TestStatus.PUBLISHED, "reject": TestStatus.DRAFT},
    TestStatus.PUBLISHED: {"archive": TestStatus.ARCHIVED},
    TestStatus.ARCHIVED: {},
}


@dataclass
class TestStateMachine:
    current_state: TestStatus

    def transition(self, action: str) -> TestStatus:
        transitions = _ALLOWED_TRANSITIONS[self.current_state]
        if action not in transitions:
            raise ValueError(f"Переход {self.current_state} -> {action} недопустим")
        return transitions[action]

    def apply(self, test, action: str):
        new_state = self.transition(action)
        test.status = new_state
        if new_state == TestStatus.PUBLISHED:
            test.published_at = datetime.utcnow()
        return test
