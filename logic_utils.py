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


# ---------------------------------------------------------------------------
# Feature: difficulty-tiered hints (Stretch Challenge 2)
# ---------------------------------------------------------------------------
#
# Easy gives the player everything: direction, how close they are, and the
# range the answer must now sit in. Normal gives direction only. Hard gives a
# sarcastic taunt that appears to help with nothing -- but the first letter of
# each word spells the direction. The joke is that Hard's hint is the most
# informative of the three if you actually read it.

HINT_MODES = {"Easy": "generous", "Normal": "partial", "Hard": "troll"}

# Each taunt's initials spell its direction. test_troll_hints_encode_the
# _direction decodes every one of these, so a typo cannot ship silently.
TROLL_HINTS = {
    "Too High": [
        "Laughably Off. Wildly Extra, Really.",
        "Legends Often Whiff Entire Rounds.",
        "Look, Optimism Won't Erase Reality.",
    ],
    "Too Low": [
        "Hmm. Interesting. Genuinely Hilarious Effort, Rookie.",
        "Historically, Intelligent Guessers Have Educated Reflexes.",
        "Hopeless? Indeed. Great Hustle, Extremely Restrained.",
    ],
}

PROXIMITY_BANDS = (
    (0.02, "boiling"),
    (0.05, "hot"),
    (0.12, "warm"),
    (0.25, "cool"),
)

PROXIMITY_LABELS = {
    "boiling": "BOILING -- you are almost on it",
    "hot": "HOT",
    "warm": "WARM",
    "cool": "COOL",
    "cold": "ICE COLD",
}


def acrostic(message: str) -> str:
    """Return the initials of every word in a message, uppercased.

    Args:
        message: Any sentence, punctuation included.

    Returns:
        The first letter of each whitespace-separated word, e.g.
        ``"Legends Often Whiff Entire Rounds."`` becomes ``"LOWER"``.

    This is the decoder for the Hard-difficulty troll hints, and exists as a
    real function rather than a comment so the tests can verify that every
    taunt still spells what it is supposed to spell.
    """
    return "".join(word[0] for word in message.split() if word).upper()


def proximity_band(guess: int, secret: int, low: int, high: int) -> str:
    """Describe how close a guess is, as a fraction of the whole range.

    Args:
        guess: The player's guess.
        secret: The number being guessed.
        low: Lowest possible secret, inclusive.
        high: Highest possible secret, inclusive.

    Returns:
        One of ``"boiling"``, ``"hot"``, ``"warm"``, ``"cool"`` or ``"cold"``.

    Measuring distance as a fraction of the range keeps the bands fair across
    difficulties: being 5 away means something very different in a 1-20 game
    than in a 1-100 one.
    """
    span = max(high - low, 1)
    ratio = abs(guess - secret) / span
    for threshold, name in PROXIMITY_BANDS:
        if ratio <= threshold:
            return name
    return "cold"


def narrowed_range(guess: int, outcome: str, low: int, high: int) -> tuple[int, int]:
    """Return the range the answer must fall in after a guess.

    Args:
        guess: The guess just made.
        outcome: ``"Too High"`` or ``"Too Low"``.
        low: Current lower bound, inclusive.
        high: Current upper bound, inclusive.

    Returns:
        The tightened ``(low, high)`` bounds, never inverted.
    """
    if outcome == "Too High":
        return low, max(low, guess - 1)
    if outcome == "Too Low":
        return min(high, guess + 1), high
    return low, high


def hint_for(difficulty, outcome, guess, secret, low, high, attempt_number=1):
    """Build the hint shown to the player, scaled to the difficulty.

    Args:
        difficulty: ``"Easy"``, ``"Normal"`` or ``"Hard"``.
        outcome: ``"Win"``, ``"Too High"`` or ``"Too Low"``.
        guess: The guess just made.
        secret: The number being guessed.
        low: Lowest possible secret, inclusive.
        high: Highest possible secret, inclusive.
        attempt_number: Which guess this was, used to rotate the taunts.

    Returns:
        A player-facing hint string.

    Easy states the direction, the proximity band and the remaining range.
    Normal states the direction only. Hard returns a taunt whose initials
    spell the direction -- the information is all there, just hidden.
    """
    if outcome == "Win":
        return hint_message("Win")

    mode = HINT_MODES.get(difficulty, "partial")

    if mode == "troll":
        options = TROLL_HINTS[outcome]
        return options[(attempt_number - 1) % len(options)]

    if mode == "generous":
        band = PROXIMITY_LABELS[proximity_band(guess, secret, low, high)]
        new_low, new_high = narrowed_range(guess, outcome, low, high)
        return f"{hint_message(outcome)}  |  {band}  |  It is between {new_low} and {new_high}."

    return hint_message(outcome)


# ---------------------------------------------------------------------------
# Feature: per-difficulty time limits (Stretch Challenge 2)
# ---------------------------------------------------------------------------

TIME_LIMITS = {"Easy": None, "Normal": 300, "Hard": 60}


def get_time_limit(difficulty: str):
    """Return the round time limit in seconds, or None when untimed.

    Args:
        difficulty: ``"Easy"``, ``"Normal"`` or ``"Hard"``.

    Returns:
        ``None`` for Easy, ``300`` for Normal, ``60`` for Hard. An unknown
        difficulty falls back to Normal rather than running untimed, so a typo
        can never accidentally remove the limit.
    """
    if difficulty not in TIME_LIMITS:
        return TIME_LIMITS[DEFAULT_DIFFICULTY]
    return TIME_LIMITS[difficulty]


def time_remaining(started_at: float, now: float, limit):
    """Return the seconds left in the round.

    Args:
        started_at: Unix timestamp when the round began.
        now: Current unix timestamp.
        limit: Seconds allowed, or ``None`` for an untimed round.

    Returns:
        Seconds remaining, never below zero, or ``None`` when untimed.
    """
    if limit is None:
        return None
    return max(limit - (now - started_at), 0.0)


def is_time_up(started_at: float, now: float, limit) -> bool:
    """Return True when the round's clock has run out.

    Args:
        started_at: Unix timestamp when the round began.
        now: Current unix timestamp.
        limit: Seconds allowed, or ``None`` for an untimed round.

    Returns:
        ``False`` always when untimed, otherwise whether the limit has passed.
    """
    remaining = time_remaining(started_at, now, limit)
    return remaining is not None and remaining <= 0


def format_clock(seconds) -> str:
    """Format a seconds count as M:SS for display.

    Args:
        seconds: Seconds remaining, or ``None`` for an untimed round.

    Returns:
        ``"--:--"`` when untimed, otherwise a ``M:SS`` string.
    """
    if seconds is None:
        return "--:--"
    total = int(seconds)
    return f"{total // 60}:{total % 60:02d}"
