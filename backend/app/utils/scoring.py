"""羽毛球 21 分制比分校验（20 平后延分，领先 2 分获胜，封顶 30）."""


def is_final_score(score_a: int, score_b: int) -> bool:
    """是否为合法的一局终局比分。"""
    w = max(score_a, score_b)
    l = min(score_a, score_b)
    d = w - l
    return (
        (w == 21 and l <= 19)
        or (22 <= w <= 29 and d == 2)
        or (w == 30 and 28 <= l <= 29)
    )


def validate_score_pair(score_a: int, score_b: int) -> None:
    """校验比分在规则下是否可达（含进行中与终局）。"""
    if score_a < 0 or score_b < 0 or score_a > 30 or score_b > 30:
        raise ValueError("比分范围 0-30")

    w = max(score_a, score_b)
    l = min(score_a, score_b)
    d = w - l

    # 21 分制直接胜出（如 21-15，分差可大于 2）
    if w == 21 and l <= 19:
        return

    if w < 21:
        return

    if w == 21 and l == 20:
        return

    if d > 2:
        raise ValueError("无效比分：分差不能超过 2 分")

    if l < 20:
        raise ValueError("无效比分")

    if w == 30:
        if l not in (28, 29):
            raise ValueError("无效比分：30 分时对方须为 28 或 29 分")
        return

    if d <= 2:
        return

    raise ValueError("无效比分")


def validate_direct_score(score_a: int, score_b: int) -> None:
    """直接录入比分：须为合法终局，或为进行中的合法中间分。"""
    validate_score_pair(score_a, score_b)

    if is_final_score(score_a, score_b):
        return

    w = max(score_a, score_b)
    l = min(score_a, score_b)
    d = w - l

    if w < 21:
        return

    if w == 21 and l == 20:
        return

    if d == 0 and l >= 20:
        return

    if d == 1 and w >= 22:
        raise ValueError("无效比分：请录入完整终局比分（如 23-21、26-24），或使用 +1 逐分计分")

    raise ValueError("无效比分")
