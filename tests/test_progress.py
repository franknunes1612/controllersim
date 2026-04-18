import pytest
from components.progress import (
    empty_progress,
    record_score,
    is_module_unlocked,
    mark_module_complete,
    get_readiness_score,
    MODULES,
)


def test_empty_progress_has_all_modules():
    p = empty_progress()
    assert set(p.keys()) == set(MODULES)


def test_empty_progress_all_incomplete():
    p = empty_progress()
    for module in MODULES:
        assert p[module]["completed"] is False
        assert p[module]["scores"] == []


def test_first_module_always_unlocked():
    p = empty_progress()
    assert is_module_unlocked(p, MODULES[0]) is True


def test_second_module_locked_until_first_complete():
    p = empty_progress()
    assert is_module_unlocked(p, MODULES[1]) is False
    p = mark_module_complete(p, MODULES[0])
    assert is_module_unlocked(p, MODULES[1]) is True


def test_record_score_appends_first_score():
    p = empty_progress()
    p = record_score(p, MODULES[0], 0, "pass")
    assert p[MODULES[0]]["scores"] == [1.0]


def test_record_score_overwrites_existing():
    p = empty_progress()
    p = record_score(p, MODULES[0], 0, "pass")
    p = record_score(p, MODULES[0], 0, "fail")
    assert p[MODULES[0]]["scores"] == [0.0]


def test_record_score_partial_is_half():
    p = empty_progress()
    p = record_score(p, MODULES[0], 0, "partial")
    assert p[MODULES[0]]["scores"] == [0.5]


def test_readiness_score_zero_when_empty():
    p = empty_progress()
    assert get_readiness_score(p) == 0


def test_readiness_score_100_all_pass():
    p = empty_progress()
    for i, module in enumerate(MODULES):
        for j in range(3):
            p = record_score(p, module, j, "pass")
    assert get_readiness_score(p) == 100


def test_readiness_score_50_all_partial():
    p = empty_progress()
    for module in MODULES:
        for j in range(3):
            p = record_score(p, module, j, "partial")
    assert get_readiness_score(p) == 50
