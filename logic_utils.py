"""Pure game logic for the Glitchy Guesser game.

Moved verbatim out of app.py so the rules can be tested without booting
Streamlit. No behaviour is changed in this commit -- the bugs come out next.
"""


def get_range_for_difficulty(difficulty: str):
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw, low, high):
    # FIX: the original accepted any integer it could produce -- -20 and 5000
    # both passed even when the range was 1 to 100 -- and ran int(float(raw)),
    # silently scoring a typed "3.9" as a guess of 3. Range is now enforced and
    # decimals are rejected out loud.
    if raw is None:
        return False, None, "Enter a guess."

    text = str(raw).strip()
    if text == "":
        return False, None, "Enter a guess."

    if "." in text:
        return False, None, "Whole numbers only -- no decimals."

    try:
        value = int(text)
    except ValueError:
        return False, None, "That is not a number."

    if value < low or value > high:
        return False, None, f"Out of range. Guess between {low} and {high}."

    return True, value, None


def check_guess(guess, secret):
    # FIX: the original wrapped this in a bare `except TypeError` that fell back
    # to comparing the two values as STRINGS whenever app.py handed it a
    # stringified secret. String comparison goes character by character, so
    # "99" > "18" was True but "100" > "18" was False -- contradictory hints on
    # alternating turns, with nothing in the console. Both values are coerced to
    # int up front and the comparison is now plain integer arithmetic.
    guess = int(guess)
    secret = int(secret)

    if guess == secret:
        return "Win"
    if guess > secret:
        return "Too High"
    return "Too Low"


def hint_message(outcome):
    # FIX: the original paired "Too High" with "Go HIGHER!" and "Too Low" with
    # "Go LOWER!" -- the two messages were swapped, so the hint always sent the
    # player away from the answer. Splitting the wording out of check_guess also
    # lets check_guess return a single outcome string, which is what the starter
    # tests assert against.
    messages = {
        "Win": "\U0001F389 Correct!",
        "Too High": "\U0001F4C9 Too high -- go LOWER.",
        "Too Low": "\U0001F4C8 Too low -- go HIGHER.",
    }
    return messages.get(outcome, "")


def update_score(current_score: int, outcome: str, attempt_number: int):
    if outcome == "Win":
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points

    if outcome == "Too High":
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5

    if outcome == "Too Low":
        return current_score - 5

    return current_score
