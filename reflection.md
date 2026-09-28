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

### Part B: Bugs I missed on my first pass, found by reading the code with AI

I played only on Normal, so I had no way to see the difficulty bugs, and I was watching the hints rather than the score. After my playthroughs I attached `app.py` and `logic_utils.py` to my AI assistant and asked it to walk through the scoring and difficulty logic line by line. It came back with five issues I had not caught.

I did not take any of them on trust. I treated each one as a claim to be tested, went back into the running app, and tried to reproduce it myself: I switched to Easy and read the banner, started a round on Normal and changed difficulty mid-game, and watched the score across two consecutive wrong guesses. All five reproduced exactly as described, and I reported back to the assistant confirming which ones I had verified and what I saw on screen before adding any of them to the table below. Nothing in Part B is a code-reading guess that went unchecked -- the AI pointed, I confirmed.

**Bug 6 — "Hard" difficulty is easier than "Normal."**
`get_range_for_difficulty` in `app.py` returns `(1, 20)` for Easy, `(1, 100)` for Normal, and `(1, 50)` for Hard. Hard has a *narrower* range than Normal, so it is objectively the easier of the two. The difficulty ordering is inverted.

**Bug 7 — The range banner lies on every difficulty except Normal.**
The `st.info(...)` call hardcodes the text `"Guess a number between 1 and 100"` regardless of the selected difficulty. On Easy, where the real range is 1 to 20, the UI tells the player something false. The `low` and `high` values are computed correctly and then never used in that message.

**Bug 8 — Changing difficulty mid-session can make the game unwinnable.**
The secret is generated once, inside `if "secret" not in st.session_state:`, and is never regenerated when the difficulty selector changes. Switching from Normal to Easy with a secret of 73 leaves a secret that is outside the new 1–20 range, so no valid guess can ever win.

**Bug 9 — The score rewards you for guessing wrong.**
In `update_score`, a `"Too High"` outcome returns `current_score + 5` when the attempt number is even, and `current_score - 5` otherwise. A `"Too Low"` outcome always returns `current_score - 5`. So a wrong guess can *earn* points depending on which turn it lands on, the two wrong outcomes are treated inconsistently, and there is no floor, so the score can go negative.

**Bug 10 — Invalid input still costs you an attempt.**
In the `if submit:` block, `st.session_state.attempts += 1` runs *before* `parse_guess` is called. Typing `abc` shows the "That is not a number" error and still burns one of your limited attempts.

**Bug Reproduction Log — Part B**

| Input Used | Expected Behavior | Actual Behavior | Console Error / Output | Suspected Code Location |
|---|---|---|---|---|
| Select "Hard" and check the sidebar range | Range narrower than Normal in difficulty, i.e. harder | Range shown is 1–50, narrower than Normal's 1–100, making Hard easier | none | `app.py`, `get_range_for_difficulty` |
| Select "Easy" and read the blue banner | "Guess a number between 1 and 20" | "Guess a number between 1 and 100" | none | `app.py`, `st.info(...)` hardcoded string |
| Start on Normal, get secret 73, switch to Easy | New secret generated within 1–20 | Secret stays 73; no guess in 1–20 can win | none | `app.py`, `if "secret" not in st.session_state:` guard |
| Wrong guess on attempt 2, then a wrong guess on attempt 3 | Score does not increase for a wrong guess | Attempt 2 adds +5; attempt 3 subtracts −5 | none | `app.py`, `update_score` |
| Type `abc` and submit | Error shown, attempt not consumed | Error shown and attempts counter increments | none | `app.py`, `if submit:` (increment before `parse_guess`) |

---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
- Give one example of an AI suggestion you did not accept as written (including what the AI suggested, why you rejected or changed it, and how you verified your version). It does not have to be a suggestion that was wrong: over-engineered, out of scope, harder to read, or a poor fit for this codebase all count.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.
- Did AI help you design or understand any tests? How?

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
