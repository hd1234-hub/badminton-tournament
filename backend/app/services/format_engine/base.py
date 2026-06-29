from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class MatchSlot:
    court: int
    team_a: list[int]
    team_b: list[int]


class FormatEngine(ABC):
    @abstractmethod
    def generate(self, players: list[int], courts: int) -> list[list[MatchSlot]]: ...
