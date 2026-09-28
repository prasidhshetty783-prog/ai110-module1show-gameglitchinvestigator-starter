"""Tests for the pure game logic in logic_utils.py.

The first three tests ship with the starter. Everything below them is a
regression test written during Phase 2: each one fails against the original
buggy code and passes against the repaired version.
"""

import pytest

from logic_utils import (
    TROLL_HINTS,
    acrostic,
    check_guess,
    format_clock,
    get_attempt_limit,
    get_range_for_difficulty,
    get_time_limit,
    hint_for,
    hint_message,
    is_time_up,
    narrowed_range,
    parse_guess,
    proximity_band,
    time_remaining,
    update_score,
)

# ---------------------------------------------------------------------------
# Starter tests (unchanged)
# ---------------------------------------------------------------------------


def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    result = check_guess(50, 50)
    assert result == "Win"


def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    result = check_guess(60, 50)
    assert result == "Too High"


def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    result = check_guess(40, 50)
    assert result == "Too Low"


# ---------------------------------------------------------------------------
# Regression tests for the bugs fixed in Phase 2
# ---------------------------------------------------------------------------


def test_hint_text_points_toward_the_secret():
    """Bug 3: the two hint strings were swapped, sending players the wrong way."""
    assert "LOWER" in hint_message("Too High")
    assert "HIGHER" in hint_message("Too Low")


def test_string_secret_does_not_flip_the_comparison():
    """Bug 4: a stringified secret made check_guess compare text, not numbers.

    This is the exact sequence from the bug report: against a secret of 18,
    a guess of 100 reported "Too Low" and a guess of 99 reported "Too High".
    """
    assert check_guess(100, "18") == "Too High"
    assert check_guess(99, "18") == "Too High"
    assert check_guess(5, "18") == "Too Low"


def test_out_of_range_guesses_are_rejected():
    """Bug 5: any integer was accepted, ignoring the stated range."""
    ok_low, _, err_low = parse_guess("-20", 1, 100)
    ok_high, _, err_high = parse_guess("5000", 1, 100)
    assert ok_low is False and "range" in err_low.lower()
    assert ok_high is False and "range" in err_high.lower()


def test_decimals_are_rejected_not_truncated():
    """Bug 5: `int(float("3.9"))` silently scored a guess of 3."""
    ok, guess, err = parse_guess("3.9", 1, 100)
    assert ok is False
    assert guess is None
    assert "decimal" in err.lower()


def test_difficulty_values_match_the_starter():
    """The starter's difficulty values are preserved -- only their storage moved.

    An AI review claimed Hard's narrower range made it the easier setting. The
    arithmetic below says otherwise, so the values were left alone; this test
    pins them so a future 'helpful' refactor cannot quietly rebalance the game.
    """
    assert get_range_for_difficulty("Easy") == (1, 20)
    assert get_range_for_difficulty("Normal") == (1, 100)
    assert get_range_for_difficulty("Hard") == (1, 50)
    assert get_attempt_limit("Easy") == 6
    assert get_attempt_limit("Normal") == 8
    assert get_attempt_limit("Hard") == 5


def test_hard_is_the_only_difficulty_you_cannot_guarantee_winning():
    """Hard really is hardest: it is one guess short of the binary-search floor.

    Optimal play halves the range each turn, so a guaranteed win needs
    ceil(log2(n)) guesses. Easy and Normal each leave one spare; Hard is one
    short, which is what makes it hard -- not the width of its range.
    """
    import math

    spare = {}
    for name in ("Easy", "Normal", "Hard"):
        low, high = get_range_for_difficulty(name)
        needed = math.ceil(math.log2(high - low + 1))
        spare[name] = get_attempt_limit(name) - needed

    assert spare["Easy"] >= 0
    assert spare["Normal"] >= 0
    assert spare["Hard"] < 0, "Hard should not be guaranteed-winnable"
    assert spare["Hard"] < spare["Normal"], "Hard must be harder than Normal"


def test_wrong_guesses_never_add_points():
    """Bug 9: "Too High" added +5 on even attempts, rewarding a wrong guess."""
    for attempt in range(1, 9):
        assert update_score(50, "Too High", attempt) < 50
        assert update_score(50, "Too Low", attempt) < 50


def test_both_wrong_directions_cost_the_same():
    """Bug 9: the two wrong outcomes were scored inconsistently."""
    assert update_score(50, "Too High", 4) == update_score(50, "Too Low", 4)


def test_score_never_goes_negative():
    """Bug 9: there was no floor, so a bad run pushed the score below zero."""
    assert update_score(0, "Too Low", 1) == 0
    assert update_score(3, "Too High", 2) == 0


def test_first_guess_win_is_worth_full_points():
    """Bug 9: `100 - 10 * (attempt_number + 1)` double-penalised an instant win."""
    assert update_score(0, "Win", 1) == 100


# ---------------------------------------------------------------------------
# Stretch Challenge 1: edge cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("raw", ["", "   ", None])
def test_empty_input_is_handled_gracefully(raw):
    """Blank and whitespace-only input should ask for a guess, not crash."""
    ok, guess, err = parse_guess(raw, 1, 100)
    assert ok is False
    assert guess is None
    assert err


@pytest.mark.parametrize("raw", ["abc", "fifty", "1e5", "50; DROP TABLE", "🎮"])
def test_non_numeric_input_is_rejected(raw):
    """Text, scientific notation and emoji must not reach the comparison."""
    ok, guess, err = parse_guess(raw, 1, 100)
    assert ok is False
    assert guess is None
    assert err


def test_boundary_values_are_accepted():
    """Both ends of the range are valid guesses, one step past them is not."""
    assert parse_guess("1", 1, 100)[:2] == (True, 1)
    assert parse_guess("100", 1, 100)[:2] == (True, 100)
    assert parse_guess("0", 1, 100)[0] is False
    assert parse_guess("101", 1, 100)[0] is False


def test_extremely_large_input_is_rejected_without_overflow():
    """A 100-digit number should be rejected cleanly, not hang or crash."""
    ok, guess, err = parse_guess("9" * 100, 1, 100)
    assert ok is False
    assert guess is None
    assert "range" in err.lower()


def test_surrounding_whitespace_is_tolerated():
    """A guess pasted with spaces around it should still work."""
    assert parse_guess("  42  ", 1, 100)[:2] == (True, 42)


def test_unknown_difficulty_falls_back_to_normal():
    """A typo in the difficulty name must not crash the range lookup."""
    assert get_range_for_difficulty("Nightmare") == get_range_for_difficulty("Normal")
    assert get_attempt_limit("Nightmare") == get_attempt_limit("Normal")


# ---------------------------------------------------------------------------
# Feature tests: difficulty-tiered hints and per-difficulty timers
# ---------------------------------------------------------------------------


def test_troll_hints_encode_the_direction_in_their_initials():
    """Every Hard-difficulty taunt must still spell its own direction.

    The joke only works if the acrostic is intact, and a one-word edit would
    silently break it. This test is the guard.
    """
    for taunt in TROLL_HINTS["Too High"]:
        assert acrostic(taunt) == "LOWER", taunt
    for taunt in TROLL_HINTS["Too Low"]:
        assert acrostic(taunt) == "HIGHER", taunt


def test_troll_hints_never_say_the_direction_out_loud():
    """A taunt containing the literal word would give the puzzle away."""
    for taunts in TROLL_HINTS.values():
        for taunt in taunts:
            assert "higher" not in taunt.lower()
            assert "lower" not in taunt.lower()


def test_hint_detail_increases_as_difficulty_drops():
    """Easy should say strictly more than Normal, which says more than Hard."""
    kwargs = dict(outcome="Too High", guess=80, secret=18, low=1, high=100)
    easy = hint_for(difficulty="Easy", **kwargs)
    normal = hint_for(difficulty="Normal", **kwargs)
    hard = hint_for(difficulty="Hard", **kwargs)

    assert "LOWER" in easy and "between" in easy
    assert "LOWER" in normal and "between" not in normal
    assert "LOWER" not in hard
    assert acrostic(hard) == "LOWER"


def test_easy_hint_reports_proximity():
    """Easy tells the player how warm they are, not just which way to go."""
    near = hint_for("Easy", "Too High", 20, 18, 1, 100)
    far = hint_for("Easy", "Too High", 99, 18, 1, 100)
    assert "HOT" in near or "BOILING" in near
    assert "ICE COLD" in far


def test_proximity_is_measured_against_the_range_not_raw_distance():
    """The same raw distance means different things in different ranges.

    Being 5 away is respectable in a 1-100 game and hopeless in a 1-20 one, so
    the band must get colder as the range narrows even though the gap is
    identical. Asserting the ordering rather than two exact band names keeps
    this test about the behaviour instead of the threshold constants.
    """
    order = ["boiling", "hot", "warm", "cool", "cold"]
    wide = proximity_band(15, 10, 1, 100)
    narrow = proximity_band(15, 10, 1, 20)
    assert order.index(narrow) > order.index(wide)


def test_narrowed_range_tightens_and_never_inverts():
    """The bound Easy reports must stay a valid range at the edges."""
    assert narrowed_range(50, "Too High", 1, 100) == (1, 49)
    assert narrowed_range(50, "Too Low", 1, 100) == (51, 100)
    assert narrowed_range(1, "Too High", 1, 100) == (1, 1)
    assert narrowed_range(100, "Too Low", 1, 100) == (100, 100)


def test_time_limits_per_difficulty():
    """Easy is untimed, Normal gets 5 minutes, Hard gets 1."""
    assert get_time_limit("Easy") is None
    assert get_time_limit("Normal") == 300
    assert get_time_limit("Hard") == 60


def test_unknown_difficulty_is_timed_not_untimed():
    """A typo must not accidentally hand the player an untimed round."""
    assert get_time_limit("Nightmare") == get_time_limit("Normal")


def test_round_expires_only_after_the_limit_passes():
    """The clock ends the round at the limit, not before it."""
    start = 1_000.0
    assert is_time_up(start, start + 59, 60) is False
    assert is_time_up(start, start + 60, 60) is True
    assert is_time_up(start, start + 900, 60) is True


def test_untimed_rounds_never_expire():
    """Easy has no limit, so no amount of elapsed time should end it."""
    assert is_time_up(1_000.0, 1_000_000.0, None) is False
    assert time_remaining(1_000.0, 1_000_000.0, None) is None


def test_time_remaining_never_goes_negative():
    """A stale page should read 0:00, not a negative countdown."""
    assert time_remaining(1_000.0, 1_500.0, 60) == 0.0


def test_clock_formatting():
    """The HUD clock is M:SS, and untimed rounds show placeholder dashes."""
    assert format_clock(65) == "1:05"
    assert format_clock(0) == "0:00"
    assert format_clock(300) == "5:00"
    assert format_clock(None) == "--:--"
