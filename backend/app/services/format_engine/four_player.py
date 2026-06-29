"""四人转引擎：4 人两两搭档，每人与其他 3 人各搭档一次，共 3 轮"""

from app.services.format_engine.base import FormatEngine, MatchSlot

FOUR_PLAYER_MATRIX = [
    # (round_index, [(team_a1, team_a2), (team_b1, team_b2)])
    [[(1, 2), (3, 4)]],
    [[(1, 3), (2, 4)]],
    [[(1, 4), (2, 3)]],
]


class FourPlayerEngine(FormatEngine):
    def generate(self, players: list[int], courts: int) -> list[list[MatchSlot]]:
        if len(players) != 4:
            raise ValueError("四人转需要恰好 4 名球员")
        if courts < 1:
            raise ValueError("场地数至少为 1")

        result = []
        for round_number, template in enumerate(FOUR_PLAYER_MATRIX):
            round_matches = []
            for court_index, ((a1, a2), (b1, b2)) in enumerate(template):
                if court_index >= courts:
                    break
                round_matches.append(MatchSlot(
                    court=court_index + 1,
                    team_a=[players[a1 - 1], players[a2 - 1]],
                    team_b=[players[b1 - 1], players[b2 - 1]],
                ))
            result.append(round_matches)
        return result
