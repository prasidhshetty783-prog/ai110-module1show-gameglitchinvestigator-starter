"""Streamlit UI for the Glitchy Guesser game.

All game rules now live in `logic_utils.py`. This file is responsible only for
drawing the screen and managing Streamlit session state.

Bug fixes applied during Phase 2 are marked with `# FIX:` comments.
"""

import random

import streamlit as st

# FIX: Refactored check_guess, parse_guess, get_range_for_difficulty and
# update_score out of this file and into logic_utils.py, using agent mode.
# Mixing pure rules with UI code was what let the string-coercion bug hide --
# there was no way to call the comparison in a test without booting Streamlit.
from logic_utils import (
    DIFFICULTY_SETTINGS,
    check_guess,
    get_attempt_limit,
    get_range_for_difficulty,
    hint_message,
    parse_guess,
    update_score,
)


def start_new_game(low: int, high: int) -> None:
    """Reset every piece of round state and pick a fresh secret.

    Args:
        low: Lowest possible secret, inclusive.
        high: Highest possible secret, inclusive.

    FIX: The original "New Game" handler reset only `attempts` and `secret`. It
    left `score`, `history` and `status` untouched, so the score and guess list
    carried over and -- after a win -- `status` was still "won", which made the
    guard further down the page call st.stop() and freeze on "You already won."
    It also called random.randint(1, 100) directly, ignoring the difficulty
    range. One function now owns the whole reset.
    """
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0  # FIX: was initialised to 1, costing a guess.
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []


st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game, debugged.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    list(DIFFICULTY_SETTINGS.keys()),
    index=1,
)

low, high = get_range_for_difficulty(difficulty)
attempt_limit = get_attempt_limit(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

if "secret" not in st.session_state:
    start_new_game(low, high)
    st.session_state.difficulty = difficulty

# FIX: the secret used to be generated once and never regenerated, so switching
# difficulty mid-session could leave a secret outside the new range -- a secret
# of 73 with an Easy range of 1-20 is unwinnable. Changing difficulty now
# starts a fresh round.
if st.session_state.get("difficulty") != difficulty:
    st.session_state.difficulty = difficulty
    start_new_game(low, high)
    st.info(f"Difficulty changed to {difficulty}. New round started.")

st.subheader("Make a guess")

attempts_left = attempt_limit - st.session_state.attempts

# FIX: this banner hardcoded "between 1 and 100" on every difficulty, so it lied
# to the player on Easy (1-20) and Hard. It now reads the real range.
st.info(f"Guess a number between {low} and {high}. Attempts left: {attempts_left}")

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

raw_guess = st.text_input("Enter your guess:", key=f"guess_input_{difficulty}")

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    start_new_game(low, high)
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

if submit:
    ok, guess_int, err = parse_guess(raw_guess, low, high)

    # FIX: `attempts += 1` used to run before parsing, so typing "abc" showed an
    # error *and* burned one of your limited guesses. Invalid input is now free.
    if not ok:
        st.error(err)
    else:
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)

        # FIX: the secret was stringified on every even-numbered attempt here,
        # which is what triggered the silent string comparison inside
        # check_guess. It is passed through as an int now.
        outcome = check_guess(guess_int, st.session_state.secret)

        if show_hint:
            st.warning(hint_message(outcome))

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        elif st.session_state.attempts >= attempt_limit:
            st.session_state.status = "lost"
            st.error(
                f"Out of attempts! The secret was {st.session_state.secret}. "
                f"Score: {st.session_state.score}"
            )

st.divider()
st.caption("Rebuilt by a human who read the diff.")
