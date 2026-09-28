"""Streamlit UI for the Glitchy Guesser game.

All game rules live in `logic_utils.py` and all styling lives in `theme.py`.
This file is responsible only for wiring them together and managing Streamlit
session state.

Bug fixes applied during Phase 2 are marked with `# FIX:` comments.
Stretch features are marked with `# FEATURE:` comments.
"""

import random
import time

import streamlit as st

import theme

# FIX: Refactored check_guess, parse_guess, get_range_for_difficulty and
# update_score out of this file and into logic_utils.py using agent mode.
# Mixing pure rules with UI code is what let the string-coercion bug hide --
# there was no way to call the comparison in a test without booting Streamlit.
from logic_utils import (
    DIFFICULTY_SETTINGS,
    check_guess,
    format_clock,
    get_attempt_limit,
    get_range_for_difficulty,
    get_time_limit,
    hint_for,
    is_time_up,
    parse_guess,
    time_remaining,
    update_score,
)


def start_new_game(low, high):
    """Reset every piece of round state and pick a fresh secret.

    Args:
        low: Lowest possible secret, inclusive.
        high: Highest possible secret, inclusive.

    FIX: The original "New Game" handler reset only `attempts` and `secret`.
    It left `score`, `history` and `status` untouched, so the score and guess
    list carried over and -- after a win -- `status` was still "won", which
    made the guard further down call st.stop() and freeze the page on "You
    already won." It also called random.randint(1, 100) directly, ignoring the
    difficulty range. One function now owns the entire reset.
    """
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0  # FIX: was initialised to 1, costing a guess.
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.last_hint = None
    st.session_state.last_outcome = None
    # FEATURE: each round carries its own clock; Easy has no limit.
    st.session_state.started_at = time.time()


st.set_page_config(page_title="Glitch Guesser", page_icon="🎮", layout="centered")
theme.inject_theme()

# ---------------------------------------------------------------------------
# Sidebar: difficulty and the rules that follow from it
# ---------------------------------------------------------------------------

st.sidebar.markdown("### ⚙️ SETTINGS")

difficulty = st.sidebar.selectbox("Difficulty", list(DIFFICULTY_SETTINGS.keys()), index=1)

low, high = get_range_for_difficulty(difficulty)
attempt_limit = get_attempt_limit(difficulty)
time_limit = get_time_limit(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")
st.sidebar.caption(f"Time limit: {'none' if time_limit is None else format_clock(time_limit)}")

# FEATURE: hint quality is part of the difficulty. Easy explains itself, Normal
# gives direction only, Hard is openly hostile -- with the direction hidden in
# the first letters of the taunt. The nudge below is the only clue the player
# gets that the trolling is worth reading.
HINT_BLURB = {
    "Easy": "Hints: generous. Direction, warmth and the remaining range.",
    "Normal": "Hints: partial. Direction only -- the rest is on you.",
    "Hard": "Hints: hostile. Read them closely anyway.",
}
st.sidebar.caption(HINT_BLURB[difficulty])

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "secret" not in st.session_state:
    start_new_game(low, high)
    st.session_state.difficulty = difficulty

# FIX: the secret was generated once and never regenerated, so switching
# difficulty mid-session could leave a secret outside the new range -- a secret
# of 73 with an Easy range of 1-20 is unwinnable. Changing difficulty now
# starts a fresh round, which also resets the clock.
if st.session_state.get("difficulty") != difficulty:
    st.session_state.difficulty = difficulty
    start_new_game(low, high)
    st.toast(f"Difficulty set to {difficulty}. New round started.")

# FEATURE: the clock is authoritative on the server. The browser-side ticker
# below is cosmetic; this is the check that actually ends the round.
if st.session_state.status == "playing" and is_time_up(
    st.session_state.started_at, time.time(), time_limit
):
    st.session_state.status = "timeout"

remaining = time_remaining(st.session_state.started_at, time.time(), time_limit)
attempts_left = attempt_limit - st.session_state.attempts

# ---------------------------------------------------------------------------
# HUD
# ---------------------------------------------------------------------------

theme.header(difficulty)
theme.stat_tiles(
    score=st.session_state.score,
    attempts_left=attempts_left,
    clock=format_clock(time_limit),
    timed=time_limit is not None,
    low_time=remaining is not None and remaining <= time_limit * 0.25,
)

if time_limit is not None and st.session_state.status == "playing":
    theme.live_clock(remaining)

st.caption(f"Guess a number between {low} and {high}.")

if st.session_state.last_hint:
    theme.hint_banner(
        st.session_state.last_hint,
        st.session_state.last_outcome,
        troll=(difficulty == "Hard"),
    )

# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------

raw_guess = st.text_input("Enter your guess", key=f"guess_input_{difficulty}")

col1, col2 = st.columns(2)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")

if new_game:
    start_new_game(low, high)
    st.rerun()

with st.expander("Developer Debug Info"):
    theme.debug_console(
        [
            ("secret", st.session_state.secret),
            ("attempts", f"{st.session_state.attempts}/{attempt_limit}"),
            ("score", st.session_state.score),
            ("difficulty", difficulty),
            ("range", f"{low}-{high}"),
            ("time_left", format_clock(remaining)),
            ("status", st.session_state.status),
            ("history", st.session_state.history or "[]"),
        ]
    )

# ---------------------------------------------------------------------------
# Round end states
# ---------------------------------------------------------------------------

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success(f"You won. The secret was {st.session_state.secret}.")
    elif st.session_state.status == "timeout":
        st.error(f"Out of time. The secret was {st.session_state.secret}.")
    else:
        st.error(f"Out of attempts. The secret was {st.session_state.secret}.")
    st.caption("Press New Game to play again.")
    st.stop()

# ---------------------------------------------------------------------------
# Guess handling
# ---------------------------------------------------------------------------

if submit:
    ok, guess_int, err = parse_guess(raw_guess, low, high)

    # FIX: `attempts += 1` used to run before parsing, so typing "abc" showed an
    # error AND burned one of your limited guesses. Invalid input is now free,
    # and rejected text no longer pollutes the guess history.
    if not ok:
        st.warning(err)
    else:
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)

        # FIX: the secret was stringified on every even-numbered attempt here,
        # which is what triggered the silent string comparison inside
        # check_guess. It is passed straight through as an int now.
        outcome = check_guess(guess_int, st.session_state.secret)

        # FEATURE: the hint is now built per difficulty rather than being one
        # fixed string for everyone.
        st.session_state.last_outcome = outcome
        st.session_state.last_hint = hint_for(
            difficulty=difficulty,
            outcome=outcome,
            guess=guess_int,
            secret=st.session_state.secret,
            low=low,
            high=high,
            attempt_number=st.session_state.attempts,
        )

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.session_state.status = "won"
            st.balloons()
        elif st.session_state.attempts >= attempt_limit:
            st.session_state.status = "lost"

        st.rerun()

st.divider()
st.caption("Rebuilt by a human who read the diff.")
