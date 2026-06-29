from app.services.format_engine.base import FormatEngine, MatchSlot
from app.services.format_engine.eight_player import EightPlayerEngine, generate_eight_player_rotation
from app.services.format_engine.four_player import FourPlayerEngine
from app.services.format_engine.knockout import KnockoutEngine
from app.services.format_engine.singles_rotation import SinglesRotationEngine
from app.services.format_engine.doubles_rotation import DoublesRotationEngine

ENGINES: dict[str, FormatEngine] = {
    "eight_player_rotation": EightPlayerEngine(),
    "four_player_rotation": FourPlayerEngine(),
    "knockout": KnockoutEngine(),
    "singles_rotation": SinglesRotationEngine(),
    "doubles_rotation": DoublesRotationEngine(),
}

__all__ = [
    "FormatEngine", "MatchSlot",
    "EightPlayerEngine", "generate_eight_player_rotation",
    "FourPlayerEngine", "KnockoutEngine",
    "SinglesRotationEngine", "DoublesRotationEngine",
    "get_engine",
]


def get_engine(format_name: str) -> FormatEngine:
    engine = ENGINES.get(format_name)
    if not engine:
        raise ValueError(f"不支持的比赛格式: {format_name}")
    return engine
