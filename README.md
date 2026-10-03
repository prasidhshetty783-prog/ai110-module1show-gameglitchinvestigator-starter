# 🎮 Glitch Guesser — Game Glitch Investigator

A Streamlit number-guessing game that an AI wrote badly, and that I debugged,
repaired, tested and extended.

**CodePath AI110 · Project 1 · Prasidh Shetty**

---

## 🎯 What the game does

You guess a hidden number inside a range. After each guess the game tells you
whether you were too high or too low, tracks your score, and ends the round when
you either win, run out of attempts, or run out of time. Difficulty controls the
range, the attempt limit, the time limit, and — new in this version — how much
the hints are willing to help you.

| Difficulty | Range | Attempts | Time limit | Hints |
|---|---|---|---|---|
| Easy | 1–20 | 6 | none | Direction, warmth, and the remaining range |
| Normal | 1–100 | 8 | 5:00 | Direction only |
| Hard | 1–50 | 5 | 1:00 | Openly hostile — with the answer hidden inside |

## 🛠️ Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

Run the tests with `pytest` from the project root.

---

## 📝 Document Your Experience

This section covers the three things the project asks for: the game's purpose
(above, under "What the game does"), every bug found, and every fix applied.

### 🐛 The bugs I found

The starter code shipped nine real defects. Full reproduction tables, with
inputs, expected versus actual behaviour and code locations, are in
[`reflection.md`](reflection.md) section 1.

**Found by playing the game:**

1. **Attempt counter off by one** — the sidebar promised 8 guesses on Normal and
   the game cut you off after 7. `attempts` was initialised to `1` instead of `0`.
2. **"New Game" did nothing** — the handler reset the secret and counter but left
   `score`, `history` and `status` behind. After a win, `status` was still
   `"won"`, so the guard below hit `st.stop()` and froze the page.
3. **Hint messages swapped** — `"Too High"` was paired with "Go HIGHER!", so every
   hint pointed away from the answer.
4. **Hints contradicted themselves on alternate turns** — `app.py` stringified the
   secret on every even attempt, `check_guess` threw a `TypeError` comparing an
   int to a str, and a bare `except` silently fell back to comparing them as
   *text*. Against a secret of 18, a guess of 100 read as "too low" because
   `"100" < "18"` character by character. Nothing appeared in the console.
5. **No input validation** — `-20` and `5000` were accepted in a 1–100 game, and
   `3.9` was silently scored as a guess of `3`.

**Found by reading the code with AI, then reproduced by me:**

6. **The range banner lied** — hardcoded "between 1 and 100" on every difficulty,
   so Easy (1–20) told the player something false.
7. **Switching difficulty could make the round unwinnable** — the secret was
   generated once and never regenerated, so Normal → Easy could strand a secret
   of 73 in a 1–20 round.
8. **The score rewarded wrong guesses** — `"Too High"` *added* 5 points on
   even-numbered attempts, the two wrong outcomes were scored inconsistently,
   and there was no floor, so the score could go negative.
9. **Invalid input burned an attempt** — the counter incremented before parsing,
   so typing `abc` cost you a turn.

**One reported bug I withdrew.** The AI review also claimed Hard was *easier*
than Normal because its range is narrower, and I accepted it — it was written up,
fixed, tested and committed before anyone questioned it. It came apart when I
asked for the change to be explained in plain language, which forced the range to
be put next to the attempt limit: optimal play needs `ceil(log2(n))` guesses, and
Hard is the only difficulty that gives fewer than that, so it was already the
hardest. I reverted the change and withdrew the claim. Written up in
[`reflection.md`](reflection.md) section 2.

### 🔧 The fixes

All game rules moved out of `app.py` into `logic_utils.py` first, as a separate
commit with no behaviour change, so every later fix reads as a clean diff. That
refactor is also what made the bugs catchable: `check_guess` could not be
imported into a test while it lived inside a Streamlit script.

- `check_guess` coerces both values to `int` and the swallowing `except TypeError`
  is gone. A visible crash beats a silent wrong answer.
- Hint wording moved into `hint_message()`, unswapped, which also lets
  `check_guess` return the bare outcome string the starter tests expect.
- `parse_guess` takes the active bounds, enforces them, and rejects decimals
  instead of truncating them.
- One `start_new_game()` owns the whole reset and respects the active range.
- Difficulty ranges, attempt limits and time limits live in one
  `DIFFICULTY_SETTINGS` table, so the range, the limit and the banner cannot
  drift apart.
- Wrong guesses cost 5 points regardless of direction, the score floors at 0,
  and the win bonus no longer double-penalises a first-guess win.

Every fix carries a `# FIX:` comment naming the defect and why the change works.

---

## 📸 Demo Walkthrough

A full round on **Normal** (range 1–100, 8 attempts, 5-minute clock):

1. The HUD shows **Score 0**, **Attempts Left 8**, **Round Limit 5:00**, and a
   live countdown ticking below the tiles.
2. User enters **50**. The game returns *"📉 Too high — go LOWER."* Attempts Left
   drops to 7, score drops to 0 (already floored).
3. User enters **25**. The game returns *"📈 Too low — go HIGHER."* Attempts Left
   drops to 6.
4. User enters **37**. The game returns *"📉 Too high — go LOWER."* Attempts Left
   drops to 5.
5. User enters **31**, the secret. The game shows *"🎉 Correct!"*, the status
   banner reads **"You won. The secret was 31."**, and the score jumps to **60**
   (100 minus 10 per extra guess, floored at 10).
6. Pressing **New Game 🔁** clears the score, the history and the clock, and
   picks a fresh secret inside the current range — including after a win, which
   the starter could not do.

The same round on **Easy** replaces step 2's hint with
*"📉 Too high — go LOWER. | ICE COLD | It is between 1 and 49."*

On **Hard**, step 2's hint is instead *"Laughably Off. Wildly Extra, Really."* —
which looks like pure sarcasm until you read the first letter of each word.

## 🧪 Test Results

37 tests: the 3 starter tests kept verbatim, 10 regression tests (one per bug
fixed, each written to fail against the original code), and 24 edge-case and
feature assertions.

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0 -- D:\CodePath\Project 1\ai110-module1show-gameglitchinvestigator-starter\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\CodePath\Project 1\ai110-module1show-gameglitchinvestigator-starter
plugins: anyio-4.15.1
collecting ... collected 37 items

tests/test_game_logic.py::test_winning_guess PASSED                      [  2%]
tests/test_game_logic.py::test_guess_too_high PASSED                     [  5%]
tests/test_game_logic.py::test_guess_too_low PASSED                      [  8%]
tests/test_game_logic.py::test_hint_text_points_toward_the_secret PASSED [ 10%]
tests/test_game_logic.py::test_string_secret_does_not_flip_the_comparison PASSED [ 13%]
tests/test_game_logic.py::test_out_of_range_guesses_are_rejected PASSED  [ 16%]
tests/test_game_logic.py::test_decimals_are_rejected_not_truncated PASSED [ 18%]
tests/test_game_logic.py::test_difficulty_values_match_the_starter PASSED [ 21%]
tests/test_game_logic.py::test_hard_is_the_only_difficulty_you_cannot_guarantee_winning PASSED [ 24%]
tests/test_game_logic.py::test_wrong_guesses_never_add_points PASSED     [ 27%]
tests/test_game_logic.py::test_both_wrong_directions_cost_the_same PASSED [ 29%]
tests/test_game_logic.py::test_score_never_goes_negative PASSED          [ 32%]
tests/test_game_logic.py::test_first_guess_win_is_worth_full_points PASSED [ 35%]
tests/test_game_logic.py::test_empty_input_is_handled_gracefully[] PASSED [ 37%]
tests/test_game_logic.py::test_empty_input_is_handled_gracefully[   ] PASSED [ 40%]
tests/test_game_logic.py::test_empty_input_is_handled_gracefully[None] PASSED [ 43%]
tests/test_game_logic.py::test_non_numeric_input_is_rejected[abc] PASSED [ 45%]
tests/test_game_logic.py::test_non_numeric_input_is_rejected[fifty] PASSED [ 48%]
tests/test_game_logic.py::test_non_numeric_input_is_rejected[1e5] PASSED [ 51%]
tests/test_game_logic.py::test_non_numeric_input_is_rejected[50; DROP TABLE] PASSED [ 54%]
tests/test_game_logic.py::test_non_numeric_input_is_rejected[\U0001f3ae] PASSED [ 56%]
tests/test_game_logic.py::test_boundary_values_are_accepted PASSED       [ 59%]
tests/test_game_logic.py::test_extremely_large_input_is_rejected_without_overflow PASSED [ 62%]
tests/test_game_logic.py::test_surrounding_whitespace_is_tolerated PASSED [ 64%]
tests/test_game_logic.py::test_unknown_difficulty_falls_back_to_normal PASSED [ 67%]
tests/test_game_logic.py::test_troll_hints_encode_the_direction_in_their_initials PASSED [ 70%]
tests/test_game_logic.py::test_troll_hints_never_say_the_direction_out_loud PASSED [ 72%]
tests/test_game_logic.py::test_hint_detail_increases_as_difficulty_drops PASSED [ 75%]
tests/test_game_logic.py::test_easy_hint_reports_proximity PASSED        [ 78%]
tests/test_game_logic.py::test_proximity_is_measured_against_the_range_not_raw_distance PASSED [ 81%]
tests/test_game_logic.py::test_narrowed_range_tightens_and_never_inverts PASSED [ 83%]
tests/test_game_logic.py::test_time_limits_per_difficulty PASSED         [ 86%]
tests/test_game_logic.py::test_unknown_difficulty_is_timed_not_untimed PASSED [ 89%]
tests/test_game_logic.py::test_round_expires_only_after_the_limit_passes PASSED [ 91%]
tests/test_game_logic.py::test_untimed_rounds_never_expire PASSED        [ 94%]
tests/test_game_logic.py::test_time_remaining_never_goes_negative PASSED [ 97%]
tests/test_game_logic.py::test_clock_formatting PASSED                   [100%]

============================= 37 passed in 0.05s ==============================
```

Lint is clean too — `ruff check .` reports `All checks passed!`. Config is in
`ruff.toml`, full report in `lint_report.txt`.

---

## 🚀 Stretch Features

### Challenge 1 — Advanced edge-case testing

24 edge-case and feature assertions beyond the regression suite: blank and
whitespace-only input, non-numeric text, scientific notation (`1e5`), emoji, a
100-digit number, both range boundaries, surrounding whitespace, and an unknown
difficulty name. Prompts and the reasoning behind each case are in
[`ai_interactions.md`](ai_interactions.md).

### Challenge 2 — Feature expansion via agent mode

**Difficulty-tiered hints.** Easy states the direction, a proximity band and the
remaining range. Normal states the direction only. Hard returns a taunt — and the
first letter of each word spells the direction. *"Hmm. Interesting. Genuinely
Hilarious Effort, Rookie."* spells **HIGHER**. Three taunts per direction,
rotating by attempt number. Hard's hint is the most informative of the three if
you actually read it, which is the joke.

Two tests protect the mechanic: `test_troll_hints_encode_the_direction_in_their
_initials` decodes every taunt with the `acrostic()` helper, and
`test_troll_hints_never_say_the_direction_out_loud` fails if one leaks the word.

**Round timers.** Easy untimed, Normal 5 minutes, Hard 1 minute. Expiry is
enforced server-side in `is_time_up()` when a guess is submitted; the countdown
ticking in the browser is cosmetic, because Streamlit only re-renders on
interaction and a JavaScript clock cannot end a round. An unrecognised difficulty
falls back to a *timed* round, so a typo can never hand out a free untimed game.

Agent workflow, files touched, and the six things I had to correct manually are
documented in [`ai_interactions.md`](ai_interactions.md).

### Challenge 3 — Professional documentation and style

Google-style docstrings on every public function in `logic_utils.py`, each
naming the defect it addresses and why the fix works. Ruff configured via
`ruff.toml` and now passing clean. The interesting part was that 50 of the first
64 findings came from two mutually contradictory docstring rules rather than from
my code — write-up in [`ai_interactions.md`](ai_interactions.md).

### Challenge 4 — Enhanced game UI

Re-skinned as a console-dark HUD, PlayStation-style: near-black field, cool
blue-grey panels, electric-blue accents, geometric type with a fallback stack
(`Chakra Petch` → `Eurostile` → `Bahnschrift` → `DIN Alternate`) so it degrades
well if the webfont is blocked.

| Element | Function | What it does |
|---|---|---|
| HUD header | `theme.header()` | Title bar with the active mode |
| Stat tiles | `theme.stat_tiles()` | Score, attempts left, round limit; turns red as attempts or time run low |
| Hint banner | `theme.hint_banner()` | Colour-coded by outcome — amber too-high, blue too-low, green win, red italic for a Hard taunt, tagged *"TRANSMISSION // UNHELPFUL?"* |
| Debug console | `theme.debug_console()` | The Developer Debug panel rendered as an in-game terminal: green-on-black monospace, a `> status --verbose` prompt, dot-leader alignment and a blinking cursor |
| Live clock | `theme.live_clock()` | Browser-side ticking countdown, red under 15 seconds |

All presentation lives in `theme.py`, keeping `app.py` about game flow — the same
separation argument as moving the rules into `logic_utils.py`.

One bug worth recording, because it was mine: the theme originally set
`font-family` on `.stApp span`, which broke Streamlit's expander arrow. Streamlit
draws it as a Material Symbols *ligature* whose span text content is literally
`keyboard_arrow_right`, so replacing the font left the word painting on top of
the panel label. Fixed by scoping the font rule and pinning the icon family; the
arrow was also moved to the right of the header row.

---

## 📁 Project structure

```
app.py                     Streamlit UI and session state
logic_utils.py             All game rules — pure functions, no Streamlit
theme.py                   CSS and HUD components
conftest.py                Puts the project root on sys.path for pytest
tests/test_game_logic.py   37 tests
reflection.md              Bug logs and AI collaboration reflection
ai_interactions.md         Stretch-feature documentation
lint_report.txt            Ruff output, before and after
test_results.txt           Full pytest output
ruff.toml                  Lint configuration
```
