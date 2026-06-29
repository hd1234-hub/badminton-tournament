import pytest

from app.utils.scoring import is_final_score, validate_direct_score, validate_score_pair


@pytest.mark.parametrize("a,b", [
    (21, 19), (21, 15), (21, 23), (24, 26), (30, 28), (30, 29),
    (20, 18), (21, 20), (20, 20), (22, 22), (22, 21),
])
def test_valid_score_pairs(a, b):
    validate_score_pair(a, b)


@pytest.mark.parametrize("a,b", [
    (30, 0), (21, 24), (25, 22), (30, 27), (22, 19),
])
def test_invalid_score_pairs(a, b):
    with pytest.raises(ValueError):
        validate_score_pair(a, b)


@pytest.mark.parametrize("a,b", [
    (21, 19), (21, 23), (24, 26), (30, 28),
])
def test_valid_direct_scores(a, b):
    validate_direct_score(a, b)


@pytest.mark.parametrize("a,b", [
    (21, 22), (21, 24), (22, 21), (30, 0),
])
def test_invalid_direct_scores(a, b):
    with pytest.raises(ValueError):
        validate_direct_score(a, b)


def test_is_final_score():
    assert is_final_score(21, 19)
    assert is_final_score(21, 23)
    assert is_final_score(26, 24)
    assert not is_final_score(21, 20)
    assert not is_final_score(22, 21)
