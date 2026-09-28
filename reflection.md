# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

The first time I ran the app it looked finished. The layout was clean, the sidebar had difficulty settings, and there was a debug panel showing the secret number. Then I actually played it, and almost nothing behaved the way the UI promised. The hints sent me in the wrong direction, the attempt counter did not match what the sidebar said, and the "New Game" button appeared to do nothing at all. I recorded two full playthroughs on Normal difficulty before touching any code, then read `app.py` and `logic_utils.py` to connect each symptom to a line.

I am splitting this section into two parts on purpose. The first group is what I caught by playing. The second group is what I only caught afterwards, by reading the source with my AI assistant. Keeping them separate is more honest than pretending I spotted everything live, and the gap between the two lists is itself the interesting part.

### Part A: Bugs I found by playing the game

**Bug 1 — The attempt counter is off by one.**
The sidebar says "Attempts allowed: 8" on Normal, but the game cut me off after 7 guesses. My history list in the debug panel confirmed it: 7 entries, then game over. The cause is in the session-state setup in `app.py`, where `st.session_state.attempts` is initialised to `1` instead of `0`. That single line causes two symptoms — the "Attempts left" banner starts one short, and the loss check `attempts >= attempt_limit` triggers a guess early.

**Bug 2 — "New Game" does not start a new game.**
Clicking it left my score and my guess history exactly where they were. The `if new_game:` block in `app.py` resets `attempts` and picks a new `secret`, but never resets `score`, `history`, or `status`. Worse, if you have already won or lost, `status` is still `"won"` or `"lost"`, so the block immediately below runs `st.stop()` and freezes the page on "You already won." The same block also calls `random.randint(1, 100)` directly, ignoring whatever difficulty range is selected.

**Bug 3 — The hints point the wrong way.**
This is the one that made the game unplayable. In `check_guess` in `app.py`, the outcome `"Too High"` is returned alongside the message `"📈 Go HIGHER!"`, and `"Too Low"` alongside `"📉 Go LOWER!"`. The two message strings are simply swapped, so the on-screen hint always tells you to move away from the answer.

**Bug 4 — The hint direction also flips every other turn, for a different reason.**
Separately from the swapped text, my guesses of 100 and then 99 against a secret of 18 produced "Go LOWER" and then "Go HIGHER" — contradicting each other. The cause is in `app.py`, just before `check_guess` is called: on every even-numbered attempt the code does `secret = str(st.session_state.secret)`, converting the secret to text. `check_guess` then tries `guess > secret`, which raises `TypeError` when comparing an int to a str. The bare `except TypeError` catches it and silently falls back to comparing the two values as **strings**. String comparison goes character by character, so `"99" > "18"` is true but `"100" > "18"` is false, because `"1"` ties with `"1"` and then `"0"` loses to `"8"`. Nothing is printed to the console, which is what made this so hard to see from the UI alone.

**Bug 5 — Guesses are never checked against the valid range, and decimals are silently truncated.**
`parse_guess` in `app.py` accepts any integer it can produce. There is no bounds check at all, so `-20` and `5000` are both accepted as valid guesses even when the stated range is 1 to 100. It also converts decimals with `int(float(raw))`, so typing `3.9` is silently scored as a guess of `3` with no warning to the player.

**Bug Reproduction Log — Part A**

| Input Used | Expected Behavior | Actual Behavior | Console Error / Output | Suspected Code Location |
|---|---|---|---|---|
| Play 8 guesses on Normal without winning | 8 guesses allowed, as the sidebar states | Game ends after the 7th guess; history shows 7 entries | none | `app.py`, session-state init (`st.session_state.attempts = 1`) |
| Click "New Game 🔁" mid-game | Score resets to 0, history clears, fresh secret | Score and history unchanged; only the secret changes | none | `app.py`, `if new_game:` block |
| Click "New Game 🔁" after winning | A new round starts | Page freezes on "You already won. Start a new game to play again." | none | `app.py`, `if new_game:` block (never resets `status`) |
| Guess of 60 on odd attempt, secret 18 | Hint reads "Go LOWER" | Hint reads "📈 Go HIGHER!" | none | `app.py`, `check_guess` (messages swapped) |
| Guess of 100 then 99, secret 18 | "Go LOWER" both times | 100 → "Go LOWER", 99 → "Go HIGHER" (contradictory) | none — `TypeError` is silently swallowed | `app.py`, even-attempt `secret = str(...)` + bare `except TypeError` in `check_guess` |
| Guess of `5000`, then `-20`, then `3.9` | Rejected as out of range / invalid | All accepted; `3.9` is silently scored as `3` | none | `app.py`, `parse_guess` (no bounds check, `int(float(raw))`) |

### Part B: Bugs I missed on my first pass, surfaced by AI and then verified by me

I played only on Normal, so I had no way to see the difficulty bugs, and I was watching the hints rather than the score. After my playthroughs I attached `app.py` and `logic_utils.py` to my AI assistant and asked it to walk through the scoring and difficulty logic line by line. It came back with five issues I had not caught.

I did not take any of them on trust. I treated each one as a claim to be tested, went back into the running app, and tried to reproduce it myself. **Four held up. One did not, and I withdrew it** -- see the rejected claim at the end of this section. I reported back to the assistant on each one, confirming what I had verified and what I actually saw on screen, before adding anything to the table below. The AI pointed; I confirmed or refused.

**Bug 6 -- The range banner lies on every difficulty except Normal.**
The `st.info(...)` call hardcodes the text `"Guess a number between 1 and 100"` regardless of the selected difficulty. On Easy, where the real range is 1 to 20, the UI tells the player something false. The `low` and `high` values are computed correctly just above and then never used in that message.

**Bug 7 -- Changing difficulty mid-session can make the game unwinnable.**
The secret is generated once, inside `if "secret" not in st.session_state:`, and is never regenerated when the difficulty selector changes. Switching from Normal to Easy with a secret of 73 leaves a secret outside the new 1-20 range, so no valid guess can ever win.

**Bug 8 -- The score rewards you for guessing wrong.**
In `update_score`, a `"Too High"` outcome returns `current_score + 5` when the attempt number is even, and `current_score - 5` otherwise. A `"Too Low"` outcome always returns `current_score - 5`. So a wrong guess can *earn* points depending on which turn it lands on, the two wrong outcomes are treated inconsistently, and there is no floor, so the score can go negative.

**Bug 9 -- Invalid input still costs you an attempt.**
In the `if submit:` block, `st.session_state.attempts += 1` runs *before* `parse_guess` is called. Typing `abc` shows the "That is not a number" error and still burns one of your limited attempts.

**Bug Reproduction Log -- Part B**

| Input Used | Expected Behavior | Actual Behavior | Console Error / Output | Suspected Code Location |
|---|---|---|---|---|
| Select "Easy" and read the blue banner | "Guess a number between 1 and 20" | "Guess a number between 1 and 100" | none | `app.py`, `st.info(...)` hardcoded string |
| Start on Normal, get secret 73, switch to Easy | New secret generated within 1-20 | Secret stays 73; no guess in 1-20 can win | none | `app.py`, `if "secret" not in st.session_state:` guard |
| Wrong guess on attempt 2, then a wrong guess on attempt 3 | Score does not increase for a wrong guess | Attempt 2 adds +5; attempt 3 subtracts -5 | none | `app.py`, `update_score` |
| Type `abc` and submit | Error shown, attempt not consumed | Error shown and attempts counter increments | none | `app.py`, `if submit:` (increment before `parse_guess`) |

### One claim I rejected

The fifth issue the assistant raised was that Hard's narrower range (1-50 vs Normal's 1-100) made it the easier setting. I checked the arithmetic instead of trusting it, found the opposite, and did not fix it -- so it is not in the table above. The full write-up is in section 2, "The suggestion I did not accept."

---

## 2. How did you use AI as a teammate?

I used Claude (Opus) inside Cowork as my pair programmer for the whole project, with the repo folder connected so it could read and edit the real files rather than guess at them. I did the playing, the reproducing and the deciding; it did the code reading, the first drafts and the arguing back. The rule I set myself early was that it could propose anything, but nothing landed in the repo until I had either reproduced the behaviour in the running app or watched a test go from red to green.

### The suggestion I accepted: the silent string comparison

**What the AI suggested.** I described the glitch from my recording -- against a secret of 18, a guess of 100 said "go lower" and a guess of 99 said "go higher" -- and asked why. It pointed at two lines I had not connected. First, in `app.py`, on every even-numbered attempt the code ran `secret = str(st.session_state.secret)`, turning the number `18` into the text `"18"`. Second, `check_guess` wrapped its comparison in a bare `except TypeError` that, on failure, converted the guess to text and compared the two as strings. It proposed deleting the `except` block entirely, coercing both values with `int()` at the top of the function, and removing the stringify line from `app.py`.

**Why it was correct.** The explanation predicted my exact symptom, which is what convinced me. String comparison works character by character, like dictionary order: `"99"` beats `"18"` on the first character, but `"100"` ties on the first (`1` vs `1`) and then loses on the second (`0` vs `8`). So 100 really was "smaller" than 18 as far as that code was concerned. It also explained why I saw nothing in the console -- the `TypeError` was caught and swallowed, so the program never reported that anything had gone wrong. A wrong answer with no error is far worse than a crash, because there is nothing to notice.

**How I verified it.** I wrote the failing case into a test before trusting the fix:

```python
def test_string_secret_does_not_flip_the_comparison():
    assert check_guess(100, "18") == "Too High"
    assert check_guess(99, "18") == "Too High"
    assert check_guess(5, "18") == "Too Low"
```

It failed against the original code and passed after the change. I then ran the app and played a full round on Normal, watching the debug panel's secret against every hint, and the hints tracked the secret correctly on both odd and even turns for the first time.

### The suggestion I did not accept: "Hard is easier than Normal"

**What the AI suggested.** While reviewing the difficulty logic, it flagged that `get_range_for_difficulty` returns `(1, 50)` for Hard -- a narrower range than Normal's `(1, 100)` -- and concluded that Hard was therefore the easier of the two settings. It proposed widening Hard to `(1, 200)` and raising its attempt limit from 5 to 8, and wrote the change up as a bug fix. I nearly accepted it. It was specific, it named the right function, and the reasoning sounded obvious.

**Why I rejected it.** Before writing it into my bug table I tried to work out how I would reproduce it, and realised I could not -- "the range is narrower" is something you read, not something you observe while playing. So I did the arithmetic myself. Difficulty in a guessing game is not the size of the range on its own; it is the range measured against the number of guesses you get. Playing well means halving the remaining numbers every turn, so a guaranteed win needs `ceil(log2(n))` guesses:

| Difficulty | Numbers | Guesses needed | Guesses given | Guaranteed win? |
|---|---|---|---|---|
| Easy | 20 | 5 | 6 | Yes, one spare |
| Normal | 100 | 7 | 8 | Yes, one spare |
| Hard | 50 | 6 | 5 | **No -- one short** |

Hard is the only setting where perfect play still is not enough, which makes it genuinely the hardest of the three. The AI had looked at one number and never checked it against the one sitting next to it. The odd-looking range progression (20, then 50, then 100) is inconsistent and reads strangely, but an inconsistent-looking number is not a bug.

Accepting it would have cost me twice. The "fix" would have made Hard *guaranteed winnable* -- quietly redesigning the game while claiming to repair it -- and I would have published a false bug in my own report. I reverted the change and withdrew the claim from my bug list, taking Part B from five findings down to four.

**How I verified my version.** I put the reasoning into a test so the decision cannot be silently undone later:

```python
def test_hard_is_the_only_difficulty_you_cannot_guarantee_winning():
    spare = {}
    for name in ("Easy", "Normal", "Hard"):
        low, high = get_range_for_difficulty(name)
        needed = math.ceil(math.log2(high - low + 1))
        spare[name] = get_attempt_limit(name) - needed
    assert spare["Hard"] < 0
    assert spare["Hard"] < spare["Normal"]
```

A second test pins all three difficulties to the starter's original values, so a future refactor cannot rebalance the game by accident. I also played a Hard round to confirm the sidebar still reads "Range: 1 to 50 / Attempts allowed: 5" after the revert.

This is the moment the project actually taught me something. The AI was fluent, specific, confident and wrong, and the only thing standing between that and my submitted work was me checking a number.

---

## 3. Debugging and testing your fixes

**How I decided a bug was really fixed.** I used three gates, and a fix only counted when it cleared all three: a test that failed before the change and passed after it, the behaviour visibly correct in the running Streamlit app, and the full suite still green so I had not broken something else while fixing this.

The middle gate caught things the tests could not. My New Game fix passed its logic check immediately, but playing the app showed the page still frozen on "You already won" -- because `status` was one of three pieces of session state the original handler never reset, and no unit test of a pure function was ever going to see that. Streamlit state bugs only show up when you actually click the button.

**The tests I ran.** The suite is in `tests/test_game_logic.py` and grew to 25 tests: the 3 starter tests, 10 regression tests (one per bug fixed, each written to fail against the original code), and 12 edge-case assertions for the stretch challenge. Running `pytest -v`:

```
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-9.1.1, pluggy-1.6.0
collected 25 items

tests/test_game_logic.py::test_winning_guess PASSED                      [  4%]
tests/test_game_logic.py::test_guess_too_high PASSED                     [  8%]
tests/test_game_logic.py::test_guess_too_low PASSED                      [ 12%]
tests/test_game_logic.py::test_hint_text_points_toward_the_secret PASSED [ 16%]
tests/test_game_logic.py::test_string_secret_does_not_flip_the_comparison PASSED [ 20%]
tests/test_game_logic.py::test_out_of_range_guesses_are_rejected PASSED  [ 24%]
tests/test_game_logic.py::test_decimals_are_rejected_not_truncated PASSED [ 28%]
tests/test_game_logic.py::test_difficulty_values_match_the_starter PASSED [ 32%]
tests/test_game_logic.py::test_hard_is_the_only_difficulty_you_cannot_guarantee_winning PASSED [ 36%]
tests/test_game_logic.py::test_wrong_guesses_never_add_points PASSED     [ 40%]
tests/test_game_logic.py::test_both_wrong_directions_cost_the_same PASSED [ 44%]
tests/test_game_logic.py::test_score_never_goes_negative PASSED          [ 48%]
tests/test_game_logic.py::test_first_guess_win_is_worth_full_points PASSED [ 52%]
tests/test_game_logic.py::test_empty_input_is_handled_gracefully[] PASSED [ 56%]
tests/test_game_logic.py::test_empty_input_is_handled_gracefully[   ] PASSED [ 60%]
tests/test_game_logic.py::test_empty_input_is_handled_gracefully[None] PASSED [ 64%]
tests/test_game_logic.py::test_non_numeric_input_is_rejected[abc] PASSED [ 68%]
tests/test_game_logic.py::test_non_numeric_input_is_rejected[fifty] PASSED [ 72%]
tests/test_game_logic.py::test_non_numeric_input_is_rejected[1e5] PASSED [ 76%]
tests/test_game_logic.py::test_non_numeric_input_is_rejected[50; DROP TABLE] PASSED [ 80%]
tests/test_game_logic.py::test_boundary_values_are_accepted PASSED       [ 88%]
tests/test_game_logic.py::test_extremely_large_input_is_rejected_without_overflow PASSED [ 92%]
tests/test_game_logic.py::test_surrounding_whitespace_is_tolerated PASSED [ 96%]
tests/test_game_logic.py::test_unknown_difficulty_falls_back_to_normal PASSED [100%]

============================== 25 passed in 0.11s ==============================
```

The single most useful test was `test_string_secret_does_not_flip_the_comparison`, because it turned a glitch I could only demonstrate by recording my screen into three lines that either pass or fail in a tenth of a second. Before the refactor that test was impossible to write at all -- `check_guess` lived inside `app.py`, so importing it meant booting Streamlit. Moving the logic into `logic_utils.py` was what made the bug catchable, which is the real argument for separating rules from UI.

**How AI helped with the tests.** I asked it to generate the first regression tests and they were reasonable but shallow -- mostly re-asserting what the fixed function obviously did. The useful move was asking a different question: "what inputs would still break this?" That produced the edge cases I would not have thought of on my own -- scientific notation like `1e5`, an emoji, a 100-digit number, and whitespace around a valid guess. I kept the ones that described a plausible player and dropped the rest. I also made a habit of writing the failing test *before* applying a fix, so I could watch it go red then green; that turned "the AI says this is fixed" into something I had seen with my own eyes.

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
