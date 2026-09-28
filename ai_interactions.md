# AI Interactions Log

Stretch-feature documentation for **Project 1: Game Glitch Investigator**.

Tool used throughout: **Claude (Opus) in Cowork**, with the repository folder
connected so it could read and edit the real files rather than work from pasted
snippets. My working rule was that it could propose anything, but nothing landed
in the repo until I had either reproduced the behaviour in the running app or
watched a test go from red to green.

---

## Agent Workflow (Challenge 2: Feature Expansion)

**What task did I give the agent?**

Two features, given as one multi-step instruction:

> Add difficulty-tiered hints. Easy should give direction, how close the guess
> is, and the remaining range. Normal should give direction only. Hard should
> troll the player -- but the troll message must contain a hidden, decodable
> hint. Then add round timers: no limit on Easy, 5 minutes on Normal, 1 minute
> on Hard. Keep all of it testable, and re-skin the UI as a gamified console
> (PlayStation-style dark) with the Developer Debug panel rendered as an
> in-game terminal.

Before it wrote anything I made it commit to four decisions: how the hidden hint
would be encoded, whether the game would tell the player a hint was hidden, which
theme direction, and what happens when the clock expires. Settling those up front
is what stopped the first draft from being a guess.

**What did the agent do?**

| File | Change |
|---|---|
| `logic_utils.py` | Added `HINT_MODES`, `TROLL_HINTS`, `PROXIMITY_BANDS`, and the functions `acrostic`, `proximity_band`, `narrowed_range`, `hint_for`. Added `TIME_LIMITS`, `get_time_limit`, `time_remaining`, `is_time_up`, `format_clock`. |
| `theme.py` | New file. All CSS and HUD components: header, stat tiles, hint banner, terminal debug console, browser-side countdown. |
| `app.py` | Wired difficulty-aware hints and the clock into the game loop; replaced the plain widgets with the themed HUD. |
| `tests/test_game_logic.py` | 12 new tests covering the acrostics, the hint ladder, proximity, and the timers. |
| `ruff.toml` | New file. Lint configuration (see Challenge 3 below). |

The hidden hint is an **acrostic**: the first letter of each word in the Hard
taunt spells the direction. *"Hmm. Interesting. Genuinely Hilarious Effort,
Rookie."* spells H-I-G-H-E-R. Three taunts per direction, rotating by attempt
number.

**What did I have to verify or fix manually?**

1. **The acrostic needed a machine check, not my eyes.** Reading six words and
   counting initials by hand is exactly the kind of thing that breaks the first
   time someone rewords a taunt. I asked for `acrostic()` to be a real function
   rather than a comment, so a test could decode every entry. A second test
   asserts no taunt contains the literal words "higher" or "lower" -- the joke
   dies if one leaks.

2. **The timer needed a server-side check, and the first draft did not have
   one.** The original version only rendered a JavaScript countdown. That looks
   right and enforces nothing: Streamlit re-renders on interaction, and the
   browser cannot end a round. I had it move expiry into `is_time_up()`, checked
   server-side on submit, and demoted the JS clock to cosmetic. This is the
   change I would point at if asked what I actually contributed.

3. **The unknown-difficulty fallback was backwards.** `get_time_limit()` first
   returned `None` for anything not in the table -- so a typo in a difficulty
   name would silently hand the player an *untimed* round. Unknown now falls
   back to Normal's 5 minutes, and there is a test for it.

4. **Two clocks contradicted each other on screen.** The stat tile showed time
   remaining as of the last page render while the live ticker showed the real
   value, so they drifted apart within seconds. I caught this in a screenshot,
   not in the code. Fixed by giving them different jobs: the tile shows the
   round's budget, the ticker shows what is left.

5. **A proximity test asserted the wrong thing.** The first version asserted
   exact band names, and failed because 5-away in a 1-100 range is 5.05% -- just
   over the "hot" threshold. The test was wrong, not the code. Rewrote it to
   assert the *ordering* (the same gap must read colder in a narrower range),
   which is the behaviour that actually matters and does not break when a
   threshold constant is tuned.

6. **A CSS rule of the agent's broke Streamlit's icons, and I initially let it
   ship.** The theme set `font-family` on `.stApp span`. Streamlit draws the
   expander arrow as a Material Symbols *ligature* -- the span's text content is
   literally `keyboard_arrow_right`, and the icon font is what turns it into a
   chevron. Overriding the font left the ligature unresolved, so the raw word
   painted on top of the panel label. I blamed my offline screenshot environment
   for one round before actually reading my own CSS. Fixed by dropping `span`
   from the rule and pinning the Material family on icon elements.

---

## Test Generation (Challenge 1: Advanced Edge-Case Testing)

**Prompt used:**

```
Here is parse_guess in logic_utils.py. Do not write tests that restate what the
function obviously does. Instead: what inputs would a real player actually type
that could still break this? Give me the edge cases first, with a one-line
reason each, before you write any test code.
```

Asking for the *reasons* before the code was the part that mattered. My first
prompt was just "write edge-case tests for parse_guess" and it produced shallow
tests that re-asserted the happy path.

| Edge case | Why it was chosen | Result |
|---|---|---|
| `""`, `"   "`, `None` | Streamlit hands back an empty string on first render, and a player can hit Submit on a blank or space-only box. Must ask for a guess, not crash. | Passes |
| `"abc"`, `"fifty"` | The most common real mistyping. Must be rejected before it reaches the comparison. | Passes |
| `"1e5"` | Scientific notation. Python's `float()` accepts it, so a naive parser could turn it into 100000 and sail past a range check written for ints. | Passes |
| `"50; DROP TABLE"` | Not a real SQL risk here -- there is no database -- but it proves the parser rejects anything that is not cleanly an integer instead of scraping digits out of a string. | Passes |
| `"🎮"` | Non-ASCII input. Confirms the failure is a clean rejection and not a `UnicodeDecodeError` or an index error on an empty parse. | Passes |
| `"9" * 100` | A 100-digit number. Python ints are unbounded, so this does not overflow -- it must be caught by the range check and rejected cleanly rather than hanging. | Passes |
| `"3.9"` | Decimals. The original silently truncated this to a guess of 3. Must now be rejected out loud. | Passes |
| `"1"`, `"100"`, `"0"`, `"101"` | Range boundaries. Off-by-one at the edges is the classic failure, and both ends must be *inclusive*. | Passes |
| `"  42  "` | A guess pasted with surrounding whitespace. This one should succeed -- rejecting it would be hostile. | Passes |
| `"Nightmare"` as a difficulty | Not player input, but a typo in code must fall back to Normal rather than crash the range lookup. | Passes |

One suggestion I dropped: a test asserting a specific error *string* for each
bad input. That locks the copy to the test, so improving an error message would
break the suite for no reason. The tests assert that an error exists and that it
mentions the right concept ("range", "decimal"), not its exact wording.

---

## Linting & Style (Challenge 3: Professional Documentation and Style)

**Prompts used:**

```
Add Google-style docstrings to every public function in logic_utils.py. For the
functions that fix a bug, the docstring should also state which defect it
addresses and why the fix works -- not just what the arguments are.
```

```
Run ruff over the project and show me the findings grouped by rule. Do not fix
anything yet -- I want to see which of these are real problems and which are
just the default config disagreeing with itself.
```

**Linting output before:**

```
$ ruff check --select E,F,W,I,N,D --ignore D203,D212,D401 . --statistics
30      D213    [*] multi-line-summary-second-line
20      D413    [*] missing-blank-line-after-last-section
10      E501    [ ] line-too-long
 3      D103    [ ] undocumented-public-function
 1      I001    [*] unsorted-imports
Found 64 errors.
```

**What I did with that, and what I refused to do.**

50 of those 64 findings were not real. `D213` wants the docstring summary on the
second line; `D212` wants it on the first. They are mutually exclusive style
conventions, and I had enabled one while silencing the other, so ruff was
flagging every docstring in the project for following the convention I had
chosen. `D413` came from the same confusion. The AI's first instinct was to run
`--fix` and reformat all 30 docstrings. That would have been 30 files' worth of
churn to satisfy a rule I did not want.

Instead I added a `ruff.toml` that states the convention once:

```toml
line-length = 100
[lint]
select = ["E", "F", "W", "I", "N", "D", "UP", "B"]
ignore = ["D203", "D213"]   # these contradict D211/D212
[lint.pydocstyle]
convention = "google"
```

That dropped 64 findings to 2, both genuine:

```
I001  Import block is un-sorted or un-formatted   tests/test_game_logic.py:8
E501  Line too long (134 > 100)                   theme.py:362
Found 2 errors.
```

**Changes applied:**

- `ruff check --fix` sorted the test imports (I had appended new names to the
  end of the list rather than in order).
- Split the over-long line in `theme.py` by hand, extracting the two countdown
  strings into named variables. Ruff cannot auto-fix `E501`, and the result
  reads better than a wrapped ternary.
- Set `line-length = 100` rather than the default 88, and said why in a comment
  in the config: several `# FIX:` comments explain a bug in one sentence and
  read worse wrapped.

```
$ ruff check .
All checks passed!
```

The lesson I am taking from this one: a linter's default configuration is an
opinion, not a specification. The useful work was deciding which 14 of the 64
findings were about my code and which 50 were about my config.
