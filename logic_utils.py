"""Pure game logic for the Glitchy Guesser game.

Every function here is free of Streamlit imports and session state, which means
each one can be called directly from a test without spinning up the UI. That
separation is the point of the refactor: `app.py` decides what to *show*, this
module decides what is *true*.

Bug fixes applied during Phase 2 are marked with `# FIX:` comments.
"""

# FIX: Difficulty settings were scattered across three places in app.py -- a
# range function, a separate attempt-limit dict, and a hardcoded banner string.
# Centralising them here makes it impossible for the three to disagree again.
#
# The VALUES are deliberately unchanged from the starter. An AI review claimed
# Hard's narrower range (1-50 vs Normal's 1-100) made it the easier setting; the
# arithmetic says otherwise. Optimal play needs ceil(log2(n)) guesses: Easy 5 of
# 6 given, Normal 7 of 8, Hard 6 of 5 -- Hard is the only difficulty you cannot
# guarantee winning, so it is already the hardest. Widening it would have been a
# redesign dressed up as a bug fix. See reflection.md, "The AI claim I rejected".
DIFFICULTY_SETTINGS = {
    "Easy": {"low": 1, "high": 20, "attempts": 6},
    "Normal": {"low": 1, "high": 100, "attempts": 8},
    "Hard": {"low": 1, "high": 50, "attempts": 5},
}

DEFAULT_DIFFICULTY = "Normal"


def get_range_for_difficulty(difficulty: str) -> tuple[int, int]:
    """Return the inclusive ``(low, high)`` guessing range for a difficulty.

    Args:
        difficulty: One of ``"Easy"``, ``"Normal"`` or ``"Hard"``. Any
            unrecognised value falls back to ``"Normal"``.

    Returns:
        A ``(low, high)`` tuple of ints, both ends inclusive.

    The ranges themselves are unchanged from the starter; only their storage
    moved into DIFFICULTY_SETTINGS so the range, the attempt limit and the
    on-screen banner can no longer drift apart.
    """
    settings = DIFFICULTY_SETTINGS.get(difficulty, DIFFICULTY_SETTINGS[DEFAULT_DIFFICULTY])
    return settings["low"], settings["high"]


def get_attempt_limit(difficulty: str) -> int:
    """Return how many guesses a player gets on the given difficulty.

    Args:
        difficulty: One of ``"Easy"``, ``"Normal"`` or ``"Hard"``. Any
            unrecognised value falls back to ``"Normal"``.

    Returns:
        The maximum number of guesses allowed, as an int.
    """
    settings = DIFFICULTY_SETTINGS.get(difficulty, DIFFICULTY_SETTINGS[DEFAULT_DIFFICULTY])
    return settings["attempts"]


def parse_guess(raw, low: int, high: int):
    """Turn raw text from the input box into a validated integer guess.

    Args:
        raw: The raw string from the text input. ``None`` and ``""`` are both
            treated as "nothing entered".
        low: Lowest guess the player is allowed to make, inclusive.
        high: Highest guess the player is allowed to make, inclusive.

    Returns:
        A ``(ok, guess, error)`` tuple. On success ``ok`` is ``True``, ``guess``
        is an int and ``error`` is ``None``. On failure ``ok`` is ``False``,
        ``guess`` is ``None`` and ``error`` is a player-facing message.

    FIX: The original accepted any integer it could produce -- ``-20`` and
    ``5000`` both passed even when the range was 1 to 100. It also ran
    ``int(float(raw))``, silently scoring a typed ``3.9`` as a guess of ``3``.
    Out-of-range values and decimals are now rejected with an explicit message.
    """
    if raw is None:
        return False, None, "Enter a guess."

    text = str(raw).strip()
    if text == "":
        return False, None, "Enter a guess."

    # FIX: reject decimals loudly instead of truncating them behind the
    # player's back.
    if "." in text:
        return False, None, "Whole numbers only -- no decimals."

    try:
        value = int(text)
    except ValueError:
        return False, None, "That is not a number."

    # FIX: the range is now actually enforced.
    if value < low or value > high:
        return False, None, f"Out of range. Guess between {low} and {high}."

    return True, value, None


def check_guess(guess: int, secret: int) -> str:
    """Compare a guess against the secret number.

    Args:
        guess: The player's guess.
        secret: The number the player is trying to find.

    Returns:
        ``"Win"``, ``"Too High"`` or ``"Too Low"``.

    FIX: The original wrapped this comparison in a bare ``except TypeError``
    that fell back to comparing the two values as *strings* whenever app.py
    handed it a stringified secret. String comparison goes character by
    character, so ``"99" > "18"`` was True but ``"100" > "18"`` was False --
    producing contradictory hints on alternating turns with no error in the
    console. Both values are now coerced to int up front and the comparison is
    plain integer arithmetic.
    """
    guess = int(guess)
    secret = int(secret)

    if guess == secret:
        return "Win"
    if guess > secret:
        return "Too High"
    return "Too Low"


def hint_message(outcome: str) -> str:
    """Turn an outcome into the sentence shown to the player.

    Args:
        outcome: One of ``"Win"``, ``"Too High"`` or ``"Too Low"``.

    Returns:
        A short player-facing hint string.

    FIX: The original paired ``"Too High"`` with "Go HIGHER!" and ``"Too Low"``
    with "Go LOWER!" -- the two messages were swapped, so the hint always sent
    the player away from the answer. Splitting the wording out of check_guess
    keeps the comparison testable and gives the UI copy one place to live.
    """
    messages = {
        "Win": "🎉 Correct!",
        "Too High": "📉 Too high -- go LOWER.",
        "Too Low": "📈 Too low -- go HIGHER.",
    }
    return messages.get(outcome, "")


def update_score(current_score: int, outcome: str, attempt_number: int) -> int:
    """Apply the result of one guess to the running score.

    Args:
        current_score: Score before this guess.
        outcome: ``"Win"``, ``"Too High"`` or ``"Too Low"``.
        attempt_number: Which guess this was, counting from 1.

    Returns:
        The new score, never below zero.

    FIX: Three separate defects lived here. A ``"Too High"`` guess *added* 5
    points on even-numbered attempts, so being wrong could earn you points; the
    two wrong outcomes were scored inconsistently (``"Too Low"`` always lost 5);
    and there was no floor, so the score could go negative. Wrong guesses now
    cost 5 points regardless of direction or turn, and the score is clamped
    at 0. The win bonus also used ``attempt_number + 1`` on an already
    incremented counter, double-penalising a first-guess win.
    """
    if outcome == "Win":
        # Winning on attempt 1 is worth the full 100; each extra guess costs 10,
        # with a floor of 10 so a slow win still scores something.
        points = 100 - 10 * (attempt_number - 1)
        return current_score + max(points, 10)

    if outcome in ("Too High", "Too Low"):
        return max(current_score - 5, 0)

    return current_score
