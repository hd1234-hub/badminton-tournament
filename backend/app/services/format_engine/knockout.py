"""淘汰赛引擎：支持 4/8/16 人单淘汰赛"""

import math
from app.services.format_engine.base import FormatEngine, MatchSlot


class KnockoutEngine(FormatEngine):
    """单淘汰赛引擎。根据人数生成对阵树。"""

    def generate(self, players: list[int], courts: int) -> list[list[MatchSlot]]:
        n = len(players)
        if n < 2 or (n & (n - 1)) != 0:
            raise ValueError("淘汰赛人数必须是 2 的幂（2/4/8/16）")
        if courts < 1:
            raise ValueError("场地数至少为 1")

        total_rounds = int(math.log2(n))
        result = []

        # 第一轮：所有选手两两配对
        current_pairs = []
        for i in range(0, n, 2):
            current_pairs.append(((players[i],), (players[i + 1],)))

        for round_idx in range(total_rounds):
            round_matches = []
            for court_idx, (team_a, team_b) in enumerate(current_pairs):
                round_matches.append(MatchSlot(
                    court=(court_idx % courts) + 1,
                    team_a=list(team_a),
                    team_b=list(team_b),
                ))
            result.append(round_matches)

            # 下一轮的选手是这一轮的胜者（用占位符 -1）
            next_count = len(current_pairs) // 2
            current_pairs = [((-1,), (-1,)) for _ in range(next_count)]

        return result
