"""Presentation layer for the Glitchy Guesser: theme CSS and HUD components.

Kept out of app.py so the game flow stays readable. Nothing in here touches
game state -- every function takes plain values and returns markup.

The look is console-dark (PlayStation-style): near-black field, cool blue-grey
panels, electric-blue accents, geometric type. The Developer Debug panel
deliberately breaks that language and renders as a green-on-black terminal,
the way an in-game developer console does.
"""

import html

import streamlit as st

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
  --bg-deep: #05070c;
  --bg-panel: #121a27;
  --bg-panel-2: #0d1420;
  --stroke: #24334a;
  --accent: #4d8dff;
  --accent-dim: #2e6cf6;
  --text: #e8eefb;
  --muted: #8b9ab3;
  --good: #3ddc97;
  --warn: #ffb454;
  --bad: #ff5d6c;
  --term: #33ff9f;
  --font-ui: 'Chakra Petch', 'Eurostile', 'Bahnschrift', 'DIN Alternate',
             'Segoe UI Semibold', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Cascadia Mono', Consolas,
               ui-monospace, monospace;
}

.stApp {
  background:
    radial-gradient(1100px 620px at 50% -12%, #16223a 0%, transparent 62%),
    var(--bg-deep);
  color: var(--text);
  font-family: var(--font-ui);
}

header[data-testid="stHeader"],
.stAppHeader,
[data-testid="stHeader"] {
  background: transparent !important;
  background-color: transparent !important;
}
div[data-testid="stToolbar"] { right: 8px; }
div[data-testid="stDecoration"] { display: none; }

.stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp label, .stApp span {
  font-family: var(--font-ui);
}

section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0d1420 0%, #070b12 100%);
  border-right: 1px solid var(--stroke);
}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
  color: #a9b8cf; font-size: .82rem;
}

/* ---- HUD header ---- */
.gg-header {
  border: 1px solid var(--stroke);
  border-radius: 14px;
  padding: 18px 22px;
  margin-bottom: 18px;
  background: linear-gradient(135deg, #16223a 0%, #0d1420 100%);
  box-shadow: 0 0 0 1px rgba(77,141,255,.08), 0 18px 40px -24px rgba(77,141,255,.55);
}
.gg-title {
  font-size: 1.85rem; font-weight: 700; letter-spacing: .06em;
  text-transform: uppercase; margin: 0; line-height: 1.1;
}
.gg-title span { color: var(--accent); }
.gg-sub { color: var(--muted); font-size: .9rem; margin: 6px 0 0; letter-spacing: .04em; }

/* ---- stat tiles ---- */
.gg-tiles { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.gg-tile {
  flex: 1 1 140px; min-width: 130px;
  border: 1px solid var(--stroke); border-radius: 12px;
  background: var(--bg-panel); padding: 12px 16px;
}
.gg-tile-label {
  font-size: .68rem; letter-spacing: .18em; text-transform: uppercase;
  color: var(--muted); margin-bottom: 4px;
}
.gg-tile-value {
  font-size: 1.7rem; font-weight: 700; line-height: 1;
  font-variant-numeric: tabular-nums;
}
.gg-tile.is-danger .gg-tile-value { color: var(--bad); }
.gg-tile.is-warn .gg-tile-value { color: var(--warn); }
.gg-tile.is-good .gg-tile-value { color: var(--good); }

/* ---- hint banner ---- */
.gg-hint {
  border-radius: 12px; padding: 16px 20px; margin: 4px 0 16px;
  border-left: 4px solid var(--accent);
  background: var(--bg-panel); font-size: 1.05rem; line-height: 1.5;
}
.gg-hint.is-win   { border-left-color: var(--good); background: #10251d; }
.gg-hint.is-high  { border-left-color: var(--warn); }
.gg-hint.is-low   { border-left-color: var(--accent); }
.gg-hint.is-troll {
  border-left-color: var(--bad); background: #21131a;
  font-style: italic; letter-spacing: .02em;
}
.gg-hint-tag {
  display: block; font-size: .64rem; letter-spacing: .2em;
  text-transform: uppercase; color: var(--muted); margin-bottom: 6px;
}

/* ---- terminal console ---- */
.gg-term {
  background: #04070a;
  border: 1px solid #12351f;
  border-radius: 8px;
  padding: 14px 16px;
  font-family: var(--font-mono);
  font-size: .82rem; line-height: 1.65;
  color: var(--term);
  text-shadow: 0 0 6px rgba(51,255,159,.35);
  overflow-x: auto;
}
.gg-term .t-bar {
  color: #5f7a6b; border-bottom: 1px solid #12351f;
  padding-bottom: 8px; margin-bottom: 10px; letter-spacing: .06em;
}
.gg-term .t-cmd { color: #7fd1ff; }
.gg-term .t-key { color: #5f7a6b; }
.gg-term .t-val { color: var(--term); font-weight: 700; }
.gg-term .t-cursor {
  display: inline-block; width: 8px; height: 14px;
  background: var(--term); vertical-align: -2px;
  animation: gg-blink 1.05s steps(2, start) infinite;
}
@keyframes gg-blink { to { visibility: hidden; } }

/* ---- controls ---- */
.stButton > button {
  width: 100%;
  font-family: var(--font-ui); font-weight: 700;
  letter-spacing: .08em; text-transform: uppercase;
  border-radius: 10px; border: 1px solid var(--stroke);
  background: linear-gradient(180deg, #1b2740 0%, #121a27 100%);
  color: var(--text); padding: .6rem 1rem; transition: all .15s ease;
}
.stButton > button:hover {
  border-color: var(--accent); color: #fff;
  box-shadow: 0 0 0 1px var(--accent), 0 0 22px -6px var(--accent);
}
.stTextInput input {
  background: #0a111c; color: var(--text);
  border: 1px solid var(--stroke); border-radius: 10px;
  font-family: var(--font-mono); font-size: 1.1rem;
}
.stTextInput input:focus { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }
</style>
"""


def inject_theme():
    """Write the theme stylesheet into the page. Call once, before anything else."""
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def header(difficulty):
    """Render the HUD title bar.

    Args:
        difficulty: The active difficulty name, shown as the loaded mode.
    """
    st.markdown(
        f"""
        <div class="gg-header">
          <p class="gg-title">GLITCH <span>GUESSER</span></p>
          <p class="gg-sub">MODE: {html.escape(difficulty).upper()} &nbsp;//&nbsp; SYSTEM ONLINE</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stat_tiles(score, attempts_left, clock, timed, low_time):
    """Render the score / attempts / timer row.

    Args:
        score: Current score.
        attempts_left: Guesses remaining.
        clock: Pre-formatted ``M:SS`` string, or ``"--:--"`` when untimed.
        timed: Whether this difficulty has a time limit.
        low_time: Whether the clock is in its final quarter.
    """
    attempt_state = "is-danger" if attempts_left <= 1 else ""
    if not timed:
        clock_state = ""
    elif low_time:
        clock_state = "is-danger"
    else:
        clock_state = "is-good"

    st.markdown(
        f"""
        <div class="gg-tiles">
          <div class="gg-tile is-good">
            <div class="gg-tile-label">Score</div>
            <div class="gg-tile-value">{score}</div>
          </div>
          <div class="gg-tile {attempt_state}">
            <div class="gg-tile-label">Attempts Left</div>
            <div class="gg-tile-value">{attempts_left}</div>
          </div>
          <div class="gg-tile {clock_state}">
            <div class="gg-tile-label">{'Round Limit' if timed else 'Timer'}</div>
            <div class="gg-tile-value">{clock if timed else 'OFF'}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hint_banner(message, outcome, troll):
    """Render the hint panel, styled by outcome.

    Args:
        message: The hint text to show.
        outcome: ``"Win"``, ``"Too High"`` or ``"Too Low"``.
        troll: True on Hard, which gets the hostile red-tinted treatment.
    """
    if outcome == "Win":
        variant, tag = "is-win", "Result"
    elif troll:
        variant, tag = "is-troll", "Transmission // unhelpful?"
    elif outcome == "Too High":
        variant, tag = "is-high", "Hint"
    else:
        variant, tag = "is-low", "Hint"

    st.markdown(
        f"""
        <div class="gg-hint {variant}">
          <span class="gg-hint-tag">{tag}</span>{html.escape(message)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def debug_console(rows):
    """Render the developer debug panel as an in-game terminal.

    Args:
        rows: Ordered ``(key, value)`` pairs to print as console output.
    """
    lines = "".join(
        f'<div><span class="t-key">  {html.escape(str(k)).ljust(12, ".")}</span> '
        f'<span class="t-val">{html.escape(str(v))}</span></div>'
        for k, v in rows
    )
    st.markdown(
        f"""
        <div class="gg-term">
          <div class="t-bar">glitch_guesser.exe &mdash; developer console &mdash; build 1.1.0</div>
          <div><span class="t-cmd">&gt; status --verbose</span></div>
          {lines}
          <div><span class="t-cmd">&gt; </span><span class="t-cursor"></span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def live_clock(seconds_left):
    """Render a client-side ticking countdown.

    Args:
        seconds_left: Seconds remaining at page render time.

    Streamlit only re-renders on interaction, so the server-rendered clock
    freezes between guesses. This little component keeps ticking in the
    browser. It is cosmetic only -- the authoritative expiry check runs
    server-side in app.py when a guess is submitted.
    """
    st.components.v1.html(
        f"""
        <div id="gg-clock" style="
             font-family:'JetBrains Mono','Cascadia Mono',Consolas,monospace;
             font-size:.74rem;letter-spacing:.18em;color:#8b9ab3;
             text-transform:uppercase;padding:2px 2px 0;">
        </div>
        <script>
          let left = {max(int(seconds_left), 0)};
          const el = document.getElementById('gg-clock');
          function paint() {{
            const m = Math.floor(left / 60), s = String(left % 60).padStart(2, '0');
            el.textContent = left > 0 ? `\u25b8 time remaining  ${{m}}:${{s}}` : '\u25b8 time remaining  0:00  --  submit to confirm';
            el.style.color = left <= 15 ? '#ff5d6c' : '#8b9ab3';
            if (left > 0) {{ left -= 1; setTimeout(paint, 1000); }}
          }}
          paint();
        </script>
        """,
        height=28,
    )
