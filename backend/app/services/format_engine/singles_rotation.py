"""单打轮转引擎：2-8 人循环赛，1v1，每人和其他所有人各打一场"""

from app.services.format_engine.base import FormatEngine, MatchSlot


class SinglesRotationEngine(FormatEngine):
    """单打循环赛：每人和其他所有人各打一场 1v1"""

    def generate(self, players: list[int], courts: int) -> list[list[MatchSlot]]:
        n = len(players)
        if n < 2 or n > 8:
            raise ValueError("单打轮转需要 2-8 名球员")
        if courts < 1:
            raise ValueError("场地数至少为 1")

        # 循环赛算法：固定第一个，旋转其余
        # 如果 n 为奇数，加入轮空（-1）
        circle = list(players)
        if n % 2 == 1:
            circle.append(-1)  # -1 表示轮空
            n_effective = n + 1
        else:
            n_effective = n

        fixed = circle[0]
        rest = circle[1:]
        total_rounds = n_effective - 1

        rounds = []
        for r in range(total_rounds):
            round_matches = []
            court_idx = 0

            # 固定选手 vs 当前对手
            opponent = rest[-1]
            if fixed != -1 and opponent != -1:
                if court_idx < courts:
                    round_matches.append(MatchSlot(
                        court=court_idx + 1,
                        team_a=[fixed],
                        team_b=[opponent],
                    ))
                    court_idx += 1

            # 其余选手配对
            for i in range((n_effective - 2) // 2):
                a = rest[i]
                b = rest[n_effective - 3 - i]
                if a != -1 and b != -1:
                    if court_idx < courts:
                        round_matches.append(MatchSlot(
                            court=court_idx + 1,
                            team_a=[a],
                            team_b=[b],
                        ))
                        court_idx += 1

            rounds.append(round_matches)

            # 旋转：rest 列表循环右移一位
            rest = [rest[-1]] + rest[:-1]

        return rounds
