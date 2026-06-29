from app.services.format_engine.base import FormatEngine, MatchSlot

EIGHT_PLAYER_MATRIX = [
    [[(1, 2), (3, 4)], [(5, 6), (7, 8)]],
    [[(1, 3), (5, 7)], [(2, 4), (6, 8)]],
    [[(1, 4), (6, 7)], [(2, 3), (5, 8)]],
    [[(1, 5), (2, 6)], [(3, 7), (4, 8)]],
    [[(1, 6), (4, 5)], [(2, 7), (3, 8)]],
    [[(1, 7), (2, 8)], [(3, 5), (4, 6)]],
    [[(1, 8), (3, 6)], [(4, 7), (2, 5)]],
]


class EightPlayerEngine(FormatEngine):
    def generate(self, players: list[int], courts: int) -> list[list[MatchSlot]]:
        if len(players) != 8:
            raise ValueError("需要恰好 8 名球员")
        if courts not in (1, 2, 4):
            raise ValueError("场地数必须是 1、2 或 4")

        result = []
        for round_number, round_template in enumerate(EIGHT_PLAYER_MATRIX):
            round_matches = []
            max_matches = min(courts, 2)
            for court_index, ((a1, a2), (b1, b2)) in enumerate(round_template):
                if court_index >= max_matches:
                    break
                round_matches.append(MatchSlot(
                    court=court_index + 1,
                    team_a=[players[a1 - 1], players[a2 - 1]],
                    team_b=[players[b1 - 1], players[b2 - 1]],
                ))
            result.append(round_matches)
        return result


def generate_eight_player_rotation(players: list[int], courts: int) -> list[list[dict]]:
    if len(players) != 8:
        raise ValueError("需要恰好 8 名球员")
    if courts not in (1, 2, 4):
        raise ValueError("场地数必须是 1、2 或 4")

    result = []
    for round_number, round_template in enumerate(EIGHT_PLAYER_MATRIX):
        round_matches = []
        # 八人转每轮只有 2 场双打，4 场地 = 2 场双打（每场占 2 个半场）
        max_matches = min(courts, 2)
        for court_index, ((a1, a2), (b1, b2)) in enumerate(round_template):
            if court_index >= max_matches:
                break
            round_matches.append({
                "court": court_index + 1,
                "round_number": round_number + 1,
                "team_a": [players[a1 - 1], players[a2 - 1]],
                "team_b": [players[b1 - 1], players[b2 - 1]],
            })
        result.append(round_matches)
    return result
