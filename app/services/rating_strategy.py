from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RatingContext:
    score: int
    difficulty: int
    is_first_attempt: bool = False
    is_tournament: bool = False


class RatingStrategy(ABC):
    @abstractmethod
    def calculate(self, score: int, difficulty: int) -> int:
        raise NotImplementedError


class StandardStrategy(RatingStrategy):
    def calculate(self, score: int, difficulty: int) -> int:
        return score


class BonusStrategy(RatingStrategy):
    def calculate(self, score: int, difficulty: int) -> int:
        return int(score * 1.5)


class TournamentStrategy(RatingStrategy):
    def calculate(self, score: int, difficulty: int) -> int:
        return score * 2


class FirstAttemptStrategy(RatingStrategy):
    def calculate(self, score: int, difficulty: int) -> int:
        return score + 50


class RatingStrategyFactory:
    @staticmethod
    def build(context: RatingContext) -> RatingStrategy:
        if context.is_first_attempt:
            return FirstAttemptStrategy()
        if context.is_tournament:
            return TournamentStrategy()
        if context.difficulty >= 5:
            return BonusStrategy()
        return StandardStrategy()
