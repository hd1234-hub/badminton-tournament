import pytest
from app.services.format_engine.eight_player import generate_eight_player_rotation


def test_生成7轮():
    players = [1, 2, 3, 4, 5, 6, 7, 8]
    rounds = generate_eight_player_rotation(players, courts=2)
    assert len(rounds) == 7


def test_2场地每轮2场():
    players = [1, 2, 3, 4, 5, 6, 7, 8]
    rounds = generate_eight_player_rotation(players, courts=2)
    for rnd in rounds:
        assert len(rnd) == 2


def test_每轮所有球员都上场():
    players = [1, 2, 3, 4, 5, 6, 7, 8]
    rounds = generate_eight_player_rotation(players, courts=2)
    for rnd in rounds:
        in_round = []
        for m in rnd:
            in_round.extend(m["team_a"])
            in_round.extend(m["team_b"])
        assert sorted(in_round) == players


def test_每人搭档恰好一次():
    players = list(range(1, 9))
    rounds = generate_eight_player_rotation(players, courts=2)
    partners = {}
    for rnd in rounds:
        for m in rnd:
            for side in [m["team_a"], m["team_b"]]:
                p1, p2 = sorted(side)
                partners.setdefault(p1, {})[p2] = partners.get(p1, {}).get(p2, 0) + 1
    for p in range(1, 9):
        for q in range(p + 1, 9):
            assert partners[p].get(q, 0) == 1, f"球员 {p} 和 {q} 搭档了 {partners[p].get(q, 0)} 次"


def test_每轮每人至少打一场():
    players = list(range(1, 9))
    rounds = generate_eight_player_rotation(players, courts=2)
    for rnd in rounds:
        appeared = set()
        for m in rnd:
            appeared.update(m["team_a"])
            appeared.update(m["team_b"])
        assert appeared == set(range(1, 9))


def test_人数不对报错():
    with pytest.raises(ValueError, match="需要恰好 8 名球员"):
        generate_eight_player_rotation([1, 2, 3], courts=2)


def test_场地数不对报错():
    with pytest.raises(ValueError):
        generate_eight_player_rotation(list(range(1, 9)), courts=3)


def test_4场地每轮2场():
    players = list(range(1, 9))
    rounds = generate_eight_player_rotation(players, courts=4)
    assert len(rounds) == 7
    for rnd in rounds:
        assert len(rnd) == 2
