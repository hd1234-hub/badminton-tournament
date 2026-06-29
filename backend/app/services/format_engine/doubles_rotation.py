"""双打轮转引擎：4/6/8 人，每轮更换搭档，每个球员和其他所有人都搭档一次"""

from app.services.format_engine.base import FormatEngine, MatchSlot


class DoublesRotationEngine(FormatEngine):
    """双打轮转换搭档：使用循环构造法，每人每轮换搭档，最终与所有人都合作一次"""

    def generate(self, players: list[int], courts: int) -> list[list[MatchSlot]]:
        n = len(players)
        if n not in (4, 6, 8):
            raise ValueError("双打轮转需要 4、6 或 8 名球员")
        if courts < 1:
            raise ValueError("场地数至少为 1")

        total_rounds = n - 1
        fixed = players[0]  # 固定第一个球员
        circle = players[1:]  # 其余形成圆圈

        rounds = []
        for r in range(total_rounds):
            # 生成当前轮的所有配对
            pairs = []
            # 固定球员搭档：0 号搭档 circle 的最后一个
            pairs.append((fixed, circle[-1]))

            # 其余球员配对：从前和后向中间取
            m = (n - 2) // 2  # 剩余可配对数
            for i in range(m):
                pairs.append((circle[i], circle[n - 3 - i]))

            # max_matches = 1 for N=4,6 | 2 for N=8
            max_matches = min(courts, n // 4)
            round_matches = []

            for match_idx in range(max_matches):
                pair_a = pairs[match_idx * 2]
                pair_b = pairs[match_idx * 2 + 1]
                round_matches.append(MatchSlot(
                    court=match_idx + 1,
                    team_a=[pair_a[0], pair_a[1]],
                    team_b=[pair_b[0], pair_b[1]],
                ))

            rounds.append(round_matches)

            # 旋转圆圈：循环右移一位（circle[-1] 变成 circle[0]）
            circle = [circle[-1]] + circle[:-1]

        return rounds
