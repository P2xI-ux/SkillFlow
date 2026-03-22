from abc import ABC, abstractmethod


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


class RatingStrategyFactory:
    @staticmethod
    def build(difficulty: int) -> RatingStrategy:
        if difficulty >= 5:
            return BonusStrategy()
        if difficulty == 4:
            return TournamentStrategy()
        return StandardStrategy()
