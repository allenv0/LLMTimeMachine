"""Old Weights visual language — newsprint masthead × time-machine timetable.

Palette: warm paper, near-black ink, one ochre accent.
Feel: old newspaper (masthead, rules, serif display, dense captions)
     + time machine (timetable spine, playhead, departure board).
No gradients, no heavy shadows.
"""

from __future__ import annotations

PAPER = "#F7F4EF"
PAPER_2 = "#EFEAE3"
CARD = "#FFFCF8"
INK = "#1C1B19"
INK_MUTED = "#6B6560"
LINE = "#D9D2C7"
ACCENT = "#C47B2D"
ACCENT_SOFT = "#FBF3E8"
ACCENT_INK = "#A35F14"
HOLE = "#A39A8E"
DANGER = "#8B3A2F"
OK = "#2F6F4E"

SERIF = (
    '"Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", '
    "Georgia, 'Times New Roman', serif"
)
SANS = (
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', "
    "'PingFang SC', 'Microsoft YaHei', sans-serif"
)
MONO = "'SF Mono', ui-monospace, Menlo, Consolas, monospace"

CSS = """
<style>
  :root {
    --tm-paper: #F7F4EF;
    --tm-paper-2: #EFEAE3;
    --tm-card: #FFFCF8;
    --tm-ink: #1C1B19;
    --tm-ink-muted: #6B6560;
    --tm-line: #D9D2C7;
    --tm-accent: #C47B2D;
    --tm-accent-soft: #FBF3E8;
    --tm-accent-ink: #A35F14;
    --tm-hole: #A39A8E;
    --tm-danger: #8B3A2F;
    --tm-ok: #2F6F4E;
    --tm-serif: __SERIF__;
    --tm-sans: __SANS__;
    --tm-mono: __MONO__;
    --tm-radius-sm: 6px;
    --tm-radius-md: 8px;
    --tm-radius-lg: 10px;
  }

  /* ——— base newsprint + layout rhythm ——— */
  .stApp {
    background: var(--tm-paper);
    color: var(--tm-ink);
    font-family: var(--tm-sans);
    letter-spacing: -0.01em;
  }
  /* Let the paper sheet use the wide layout — avoid Streamlit's narrow text column */
  [data-testid="stMain"] > div,
  [data-testid="stMainBlockContainer"] {
    max-width: 100% !important;
    width: 100% !important;
  }
  [data-testid="stMainBlockContainer"] {
    padding-left: 1.25rem !important;
    padding-right: 1.25rem !important;
    gap: 0.85rem !important;
  }
  .block-container {
    max-width: 100% !important;
    padding-top: 1rem !important;
    padding-bottom: 2.5rem !important;
  }
  [data-testid="stVerticalBlock"] {
    gap: 0.75rem !important;
    width: 100% !important;
  }
  [data-testid="stVerticalBlockBorderWrapper"] {
    width: 100% !important;
  }
  h1, h2, h3, h4 {
    color: var(--tm-ink) !important;
    letter-spacing: -0.02em;
  }
  h1 {
    font-family: var(--tm-serif) !important;
    font-weight: 700 !important;
    font-size: 2.35rem !important;
    letter-spacing: 0.02em !important;
    text-transform: uppercase;
    margin: 0.1rem 0 0.2rem 0 !important;
    line-height: 1.05 !important;
  }
  h2 {
    font-family: var(--tm-serif) !important;
    font-size: 1.2rem !important;
    font-weight: 700 !important;
  }
  h3 {
    font-family: var(--tm-sans) !important;
    font-size: 0.98rem !important;
    font-weight: 650 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  p, label, li { line-height: 1.55; }
  .stCaption, [data-testid="stCaptionContainer"] {
    color: var(--tm-ink-muted) !important;
    font-size: 0.8rem !important;
  }
  [data-testid="stSidebar"] {
    background: var(--tm-paper-2);
    border-right: 1px solid var(--tm-line);
  }
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.84rem;
  }
  [data-testid="stHeader"] { background: transparent; }
  [data-testid="stToolbar"] { display: none; }

  /* ——— masthead (old newspaper) ——— */
  .tm-masthead {
    border-top: 3px solid var(--tm-ink);
    border-bottom: 1px solid var(--tm-ink);
    padding: 0.55rem 0 0.45rem 0;
    margin: 0 0 0.35rem 0;
  }
  .tm-masthead-rule {
    height: 1px;
    background: var(--tm-ink);
    margin: 0.18rem 0;
  }
  .tm-masthead-rule.thin { background: var(--tm-line); height: 1px; }
  .tm-dateline {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 0.35rem 1rem;
    font-family: var(--tm-sans);
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--tm-ink-muted);
    padding: 0.15rem 0 0.25rem 0;
  }
  .tm-dateline strong { color: var(--tm-ink); font-weight: 600; }
  .tm-deck {
    font-family: var(--tm-serif);
    font-size: 1.05rem;
    font-style: italic;
    color: var(--tm-ink);
    margin: 0.35rem 0 0.15rem 0;
    max-width: 40rem;
  }
  .tm-claim {
    color: var(--tm-ink-muted);
    font-size: 0.88rem;
    margin: 0 0 0.85rem 0;
    max-width: 42rem;
    line-height: 1.5;
  }
  .tm-claim strong {
    color: var(--tm-ink);
    font-weight: 600;
  }

  .tm-kicker {
    font-family: var(--tm-sans);
    font-size: 0.7rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--tm-ink-muted);
    margin: 0 0 0.3rem 0;
    font-weight: 600;
  }
  .tm-section {
    display: flex;
    align-items: baseline;
    gap: 0.65rem;
    margin: 1.1rem 0 0.65rem 0;
    border-bottom: 1px solid var(--tm-ink);
    padding-bottom: 0.3rem;
    width: 100%;
  }
  .tm-section-title {
    font-family: var(--tm-serif);
    font-size: 0.98rem;
    font-weight: 700;
    letter-spacing: 0.01em;
  }
  .tm-section-note {
    font-family: var(--tm-sans);
    font-size: 0.72rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--tm-ink-muted);
    margin-left: auto;
  }

  /* ——— badges / chips ——— */
  .tm-badge {
    display: inline-block;
    font-family: var(--tm-sans);
    font-size: 0.65rem;
    font-weight: 650;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 0.1rem 0.4rem;
    border: 1px solid var(--tm-line);
    border-radius: 2px;
    background: var(--tm-paper);
    color: var(--tm-ink-muted);
    vertical-align: middle;
    line-height: 1.35;
  }
  .tm-badge-accent {
    border-color: var(--tm-accent);
    color: var(--tm-accent-ink);
    background: var(--tm-accent-soft);
  }
  .tm-badge-ink {
    border-color: var(--tm-ink);
    color: var(--tm-ink);
  }
  .tm-badge-hole {
    border-style: dashed;
    border-color: var(--tm-hole);
    color: var(--tm-ink-muted);
    background: transparent;
  }
  .tm-badge-danger {
    border-color: var(--tm-danger);
    color: var(--tm-danger);
    background: transparent;
  }
  .tm-badge-ok {
    border-color: var(--tm-ok);
    color: var(--tm-ok);
    background: transparent;
  }

  /* ——— time-machine timetable spine ——— */
  .tm-timetable {
    border: 1px solid var(--tm-line);
    border-top: 3px solid var(--tm-ink);
    border-radius: 0;
    background: var(--tm-paper-2);
    padding: 0.85rem 1.5rem 0.7rem;
    margin: 0.65rem 0 0.85rem 0;
    overflow-x: auto;
    width: 100%;
  }
  .tm-track {
    display: flex;
    flex-wrap: wrap;
    align-items: stretch;
    gap: 0.35rem 0.15rem;
    min-width: min-content;
    width: 100%;
    position: relative;
    padding-top: 0.85rem;
  }
  .tm-track::before {
    content: "";
    position: absolute;
    left: 8px;
    right: 8px;
    top: 22px;
    height: 1px;
    background: var(--tm-ink);
    opacity: 0.35;
    z-index: 0;
  }
  .tm-stop {
    position: relative;
    z-index: 1;
    flex: 1 1 7.5rem;
    min-width: 7.25rem;
    max-width: 11rem;
    padding: 0 0.35rem 0.2rem;
    text-align: center;
  }
  .tm-stop-tick {
    width: 1px;
    height: 10px;
    background: var(--tm-ink);
    margin: 0 auto;
  }
  .tm-stop.is-hole .tm-stop-tick {
    background: var(--tm-hole);
    border-left: 1px dashed var(--tm-hole);
    background: transparent;
    width: 0;
  }
  .tm-stop-dot {
    width: 9px;
    height: 9px;
    border: 1.5px solid var(--tm-ink);
    background: var(--tm-card);
    margin: 2px auto 0;
    border-radius: 1px;
  }
  .tm-stop.is-sub .tm-stop-dot {
    border-color: var(--tm-accent);
    background: var(--tm-accent-soft);
  }
  .tm-stop.is-hole .tm-stop-dot {
    border-style: dashed;
    border-color: var(--tm-hole);
    background: transparent;
    border-radius: 50%;
  }
  .tm-stop.is-now .tm-stop-dot {
    background: var(--tm-accent);
    border-color: var(--tm-accent-ink);
  }
  .tm-stop-year {
    font-family: var(--tm-serif);
    font-variant-numeric: tabular-nums;
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--tm-ink);
    margin-top: 0.2rem;
  }
  .tm-stop.is-hole .tm-stop-year { color: var(--tm-hole); }
  .tm-stop-name {
    font-family: var(--tm-sans);
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--tm-ink);
    line-height: 1.25;
    margin-top: 0.18rem;
    min-height: 2.4em;
    word-break: break-word;
  }
  .tm-stop.is-hole .tm-stop-name {
    color: var(--tm-ink-muted);
    font-weight: 500;
    font-style: italic;
  }
  .tm-stop-meta {
    font-family: var(--tm-sans);
    font-size: 0.6rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--tm-ink-muted);
    margin-top: 0.15rem;
  }
  .tm-playhead {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 0;
    border-left: 1.5px dashed var(--tm-accent);
    z-index: 2;
    pointer-events: none;
  }
  .tm-playhead span {
    position: absolute;
    top: -2px;
    left: 4px;
    font-size: 0.58rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--tm-accent-ink);
    white-space: nowrap;
    font-weight: 700;
    background: var(--tm-paper-2);
    padding: 0 0.15rem;
  }
  .tm-endpoints {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
    margin: 0.75rem 0 0.5rem;
    padding-top: 0.55rem;
    border-top: 1px solid var(--tm-line);
    width: 100%;
  }
  .tm-endpoints > .tm-endpoint {
    flex: 1 1 18rem;
    margin-top: 0;
  }

  /* ——— catalog / editorial cards ——— */
  [data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--tm-line) !important;
    border-radius: var(--tm-radius-md) !important;
    border-top: 2px solid var(--tm-ink) !important;
    background: var(--tm-card) !important;
    box-shadow: none !important;
  }
  [data-testid="stExpander"] {
    border-color: var(--tm-line) !important;
    border-radius: var(--tm-radius-sm) !important;
    background: var(--tm-paper) !important;
  }
  .tm-card-head {
    display: flex;
    align-items: baseline;
    gap: 0.75rem;
    border-bottom: 1px solid var(--tm-line);
    padding-bottom: 0.35rem;
    margin-bottom: 0.55rem;
  }
  .tm-card-year {
    font-family: var(--tm-serif);
    font-variant-numeric: tabular-nums;
    font-size: 1.65rem;
    font-weight: 700;
    color: var(--tm-ink-muted);
    line-height: 1;
    min-width: 3.4rem;
  }
  .tm-card-name {
    font-family: var(--tm-serif);
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--tm-ink);
  }
  .tm-card-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem 0.65rem;
    align-items: center;
  }
  .tm-output {
    font-size: 0.95rem;
    line-height: 1.55;
    color: var(--tm-ink);
  }
  .tm-meta {
    color: var(--tm-ink-muted);
    font-size: 0.78rem;
  }
  .tm-endpoint {
    margin-top: 0.45rem;
    padding: 0.5rem 0.65rem;
    border-left: 3px solid var(--tm-accent);
    background: var(--tm-accent-soft);
    font-size: 0.84rem;
  }
  .tm-endpoint.is-muted {
    border-left-color: var(--tm-hole);
    background: transparent;
    border-left-style: dashed;
  }
  .tm-hole-line {
    color: var(--tm-ink-muted);
    font-size: 0.88rem;
    width: 100%;
    max-width: none;
    line-height: 1.45;
    margin: 0 0 0.15rem;
  }
  .tm-model-line {
    font-size: 0.95rem;
    width: 100%;
    max-width: none;
    line-height: 1.45;
    margin: 0 0 0.15rem;
  }

  /* Stop notes: full-width editorial rows in a 2-col newspaper grid when wide */
  .tm-stop-notes {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0.55rem 1.75rem;
    width: 100%;
    margin: 0.35rem 0 0.85rem;
  }
  @media (min-width: 960px) {
    .tm-stop-notes {
      grid-template-columns: 1fr 1fr;
      gap: 0.65rem 2rem;
    }
    .tm-stop-notes > .tm-note-wide {
      grid-column: 1 / -1;
    }
  }
  .tm-stop-notes > div {
    min-width: 0;
    padding-bottom: 0.45rem;
    border-bottom: 1px solid var(--tm-line);
  }
  .tm-stop-notes > div:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }

  /* ——— departure board (progress) ——— */
  .tm-departure {
    border: 1px solid var(--tm-line);
    border-top: 3px solid var(--tm-ink);
    background: var(--tm-card);
    padding: 0.35rem 0;
  }
  .tm-dep-row {
    display: grid;
    grid-template-columns: 4.2rem 1fr 7rem 2.5rem;
    gap: 0.5rem;
    align-items: center;
    padding: 0.35rem 0.75rem;
    border-bottom: 1px solid var(--tm-line);
    font-size: 0.84rem;
  }
  .tm-dep-row:last-child { border-bottom: none; }
  .tm-dep-row.is-active {
    background: var(--tm-accent-soft);
  }
  .tm-dep-year {
    font-family: var(--tm-serif);
    font-variant-numeric: tabular-nums;
    font-weight: 700;
  }
  .tm-dep-status {
    font-family: var(--tm-sans);
    font-size: 0.68rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 650;
  }
  .tm-dep-status.waiting { color: var(--tm-ink-muted); }
  .tm-dep-status.loading,
  .tm-dep-status.generating { color: var(--tm-accent-ink); }
  .tm-dep-status.complete { color: var(--tm-ok); }
  .tm-dep-status.failed { color: var(--tm-danger); }
  .tm-dep-track {
    height: 2px;
    background: var(--tm-line);
    position: relative;
  }
  .tm-dep-track i {
    display: block;
    height: 100%;
    background: var(--tm-accent);
  }

  /* ——— stage plates (progress arc) ——— */
  .tm-stages {
    display: grid;
    grid-template-columns: 1fr auto 1fr auto 1fr;
    gap: 0.4rem;
    align-items: stretch;
    margin: 0.5rem 0 0.35rem;
  }
  .tm-stage {
    border: 1px solid var(--tm-line);
    border-top: 2px solid var(--tm-ink);
    background: var(--tm-card);
    padding: 0.55rem 0.65rem;
    min-width: 0;
  }
  .tm-stage-label {
    font-family: var(--tm-sans);
    font-size: 0.65rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--tm-ink-muted);
    font-weight: 700;
  }
  .tm-stage-year {
    font-family: var(--tm-serif);
    font-size: 1.35rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }
  .tm-stage-name {
    font-family: var(--tm-serif);
    font-size: 0.95rem;
    font-weight: 700;
  }
  .tm-stage-note {
    font-size: 0.75rem;
    color: var(--tm-ink-muted);
    margin: 0.15rem 0 0.35rem;
  }
  .tm-stage-body {
    font-size: 0.84rem;
    line-height: 1.45;
    max-height: 8.5rem;
    overflow: hidden;
  }
  .tm-arrow {
    display: flex;
    align-items: center;
    color: var(--tm-accent);
    font-family: var(--tm-serif);
    font-size: 1.2rem;
    padding: 0 0.1rem;
    font-weight: 700;
  }

  /* ——— controls ——— */
  .stButton > button[kind="primary"],
  .stButton > button[data-testid="baseButton-primary"] {
    background: var(--tm-accent);
    border: 1px solid var(--tm-accent-ink);
    color: var(--tm-card);
    border-radius: var(--tm-radius-sm);
    font-weight: 650;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 0.8rem;
  }
  .stButton > button {
    border-radius: var(--tm-radius-sm);
    border-color: var(--tm-line);
  }
  [data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 0.15rem;
    border-bottom: 2px solid var(--tm-ink);
  }
  [data-testid="stTabs"] [data-baseweb="tab"] {
    height: 2.35rem;
    background: transparent;
    border: none;
    border-radius: 0;
    color: var(--tm-ink-muted);
    font-family: var(--tm-sans);
    font-size: 0.78rem;
    font-weight: 650;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
  [data-testid="stTabs"] [aria-selected="true"] {
    color: var(--tm-ink) !important;
    background: var(--tm-accent-soft) !important;
    border-bottom: 2px solid var(--tm-accent) !important;
    margin-bottom: -2px;
  }

  pre, code {
    font-family: var(--tm-mono) !important;
    font-size: 0.78rem !important;
    border-radius: var(--tm-radius-sm) !important;
  }
  [data-testid="stCode"] {
    border: 1px solid var(--tm-line);
    background: var(--tm-paper-2);
  }
  [data-testid="stAlert"] {
    border-radius: var(--tm-radius-sm);
    border-width: 1px;
  }

  .tm-rule {
    border: none;
    border-top: 1px solid var(--tm-line);
    margin: 0.9rem 0;
  }
  .tm-rule-heavy {
    border: none;
    border-top: 2px solid var(--tm-ink);
    margin: 1rem 0 0.65rem;
  }
  .tm-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem 0.7rem;
    align-items: center;
    color: var(--tm-ink-muted);
    font-size: 0.8rem;
  }
  .tm-note {
    border: 1px solid var(--tm-line);
    border-left: 3px solid var(--tm-ink);
    background: var(--tm-card);
    padding: 0.55rem 0.75rem;
    font-size: 0.86rem;
    margin: 0.4rem 0 0.75rem;
  }
  .tm-note li { margin: 0.15rem 0; }
  .tm-note ul { margin: 0.2rem 0 0.15rem 1.1rem; padding: 0; }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      transition: none !important;
      animation: none !important;
    }
  }
  button:focus-visible,
  [role="tab"]:focus-visible,
  input:focus-visible,
  textarea:focus-visible,
  select:focus-visible {
    outline: 2px solid var(--tm-accent);
    outline-offset: 2px;
  }

  /* stack stage plates on narrow widths */
  @media (max-width: 800px) {
    .tm-stages { grid-template-columns: 1fr; }
    .tm-arrow { display: none; }
    .tm-dep-row { grid-template-columns: 3.5rem 1fr; }
    .tm-stop { flex: 1 1 6.5rem; min-width: 6.5rem; }
    .tm-card-year { min-width: 2.8rem; font-size: 1.35rem; }
  }

  /* ——— P1 masthead craft (minimal) ——— */
  .tm-masthead {
    border-top: 2px solid var(--tm-ink);
    border-bottom: 2px solid var(--tm-ink);
    padding: 0.55rem 0 0.35rem;
    margin: 0.15rem 0 0.55rem;
  }
  .tm-masthead h1 {
    text-align: center;
    margin: 0.15rem 0 0.35rem !important;
  }
  .tm-volume {
    font-family: var(--tm-sans);
    font-size: 0.62rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--tm-ink-muted);
    text-align: center;
    margin: 0 0 0.1rem;
    font-weight: 650;
  }
  .tm-dateline {
    justify-content: center;
    gap: 0.35rem 0.85rem;
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    border: none;
  }
  .tm-deck {
    text-align: center;
    max-width: none;
    border: none;
    padding: 0.35rem 0 0.1rem;
    margin: 0.25rem 0 0;
    font-family: var(--tm-serif);
    font-style: italic;
    font-size: 1rem;
    color: var(--tm-ink);
    font-weight: 400;
  }

  /* ticket-stub CTAs */
  .stButton > button[kind="primary"],
  .stButton > button[data-testid="baseButton-primary"] {
    background: var(--tm-accent);
    border: 1px solid var(--tm-accent-ink);
    box-shadow: inset 0 0 0 1px var(--tm-card);
    color: var(--tm-card);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-family: var(--tm-sans);
    font-size: 0.78rem;
    font-weight: 700;
    border-radius: 2px;
  }
  .stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]) {
    border-radius: 2px;
    border: 1px solid var(--tm-ink);
    background: var(--tm-card);
    color: var(--tm-ink);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-family: var(--tm-sans);
    font-size: 0.75rem;
    font-weight: 650;
  }

  /* ——— P2 film perforation on timetable tray ——— */
  .tm-timetable {
    border-left: none;
    border-right: none;
    border-radius: 0;
    background:
      linear-gradient(var(--tm-paper-2), var(--tm-paper-2)) padding-box,
      repeating-linear-gradient(
        to bottom,
        var(--tm-ink) 0 4px,
        transparent 4px 10px
      ) left 4px top 8px / 4px calc(100% - 16px) no-repeat border-box,
      repeating-linear-gradient(
        to bottom,
        var(--tm-ink) 0 4px,
        transparent 4px 10px
      ) right 4px top 8px / 4px calc(100% - 16px) no-repeat border-box;
    padding-left: 1.35rem;
    padding-right: 1.35rem;
  }
  .tm-stop { cursor: help; }
  .tm-stop:hover .tm-stop-name { color: var(--tm-accent-ink); }

  /* ——— P3 dispatch density ——— */
  .tm-folio {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem 0.75rem;
    font-family: var(--tm-mono);
    font-size: 0.68rem;
    color: var(--tm-ink-muted);
    border-top: 1px solid var(--tm-line);
    margin-top: 0.35rem;
    padding-top: 0.3rem;
    letter-spacing: 0.01em;
    width: 100%;
  }
  .tm-output.clamp {
    display: -webkit-box;
    -webkit-line-clamp: 8;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .tm-erratum {
    border: 1px solid var(--tm-danger);
    border-left: 3px solid var(--tm-danger);
    background: #FBF0EE;
    padding: 0.45rem 0.65rem;
    color: var(--tm-danger);
    font-family: var(--tm-sans);
    font-size: 0.75rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-weight: 650;
    margin: 0.35rem 0 0.5rem;
  }
  .tm-dirty-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem 1rem;
    align-items: center;
    border: 1px solid var(--tm-accent);
    background: var(--tm-accent-soft);
    padding: 0.4rem 0.65rem;
    margin: 0.55rem 0;
    font-family: var(--tm-sans);
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 700;
    color: var(--tm-accent-ink);
  }
  .tm-empty {
    border: 1px dashed var(--tm-hole);
    background: transparent;
    padding: 1.1rem 1rem;
    text-align: center;
    color: var(--tm-ink-muted);
    font-family: var(--tm-serif);
    font-style: italic;
    font-size: 0.95rem;
    margin: 0.4rem 0 0.75rem;
  }

  /* ——— P4 departure / stages ——— */
  .tm-dep-row {
    grid-template-columns: 4.2rem 1fr 7.5rem 2.75rem 2.5rem;
  }
  .tm-dep-row.is-active {
    box-shadow: inset 3px 0 0 var(--tm-accent);
  }
  .tm-dep-track i {
    position: relative;
    overflow: hidden;
  }
  .tm-dep-row.is-active .tm-dep-track i::after {
    content: "";
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(
      90deg,
      transparent 0 6px,
      rgba(255, 252, 248, 0.45) 6px 10px
    );
    animation: tm-stripe 0.8s linear infinite;
  }
  @keyframes tm-stripe {
    from { transform: translateX(-10px); }
    to { transform: translateX(0); }
  }
  .tm-stage {
    border-style: solid;
    background:
      linear-gradient(var(--tm-card), var(--tm-card)) padding-box;
  }
  .tm-dep-status {
    font-variant-numeric: tabular-nums;
    text-align: right;
  }

  /* ——— P5 figure captions / legend ——— */
  .tm-fig {
    font-family: var(--tm-sans);
    font-size: 0.72rem;
    color: var(--tm-ink-muted);
    margin: 0.15rem 0 0.55rem;
  }
  .tm-fig strong {
    font-family: var(--tm-serif);
    font-weight: 700;
    color: var(--tm-ink);
  }
  .tm-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem 1rem;
    font-family: var(--tm-sans);
    font-size: 0.7rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--tm-ink-muted);
    margin: 0 0 0.25rem;
    font-weight: 650;
  }
  .tm-legend i {
    display: inline-block;
    width: 1.1rem;
    height: 2px;
    vertical-align: middle;
    margin-right: 0.25rem;
    background: var(--tm-ink);
  }
  .tm-legend i.human { background: #2F6F4E; height: 3px; }
  .tm-legend i.est { background: #6B4C9A; }
  .tm-legend i.pack { background: #9B7BB8; opacity: 0.7; height: 1px; }
  .tm-coverage {
    display: flex;
    height: 8px;
    border: 1px solid var(--tm-line);
    background: var(--tm-paper-2);
    margin: 0.35rem 0 0.5rem;
  }
  .tm-coverage .scored { background: var(--tm-accent); }
  .tm-coverage .refused {
    background: repeating-linear-gradient(
      45deg,
      var(--tm-hole) 0 2px,
      transparent 2px 5px
    );
  }

  /* ——— P6 letters / slips ——— */
  .tm-letter {
    font-family: var(--tm-serif);
    font-size: 1.75rem;
    font-weight: 700;
    line-height: 1;
    color: var(--tm-ink);
    border: 1px solid var(--tm-ink);
    width: 2.1rem;
    height: 2.1rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-right: 0.5rem;
    background: var(--tm-card);
  }
  .tm-slip {
    border: 1px solid var(--tm-line);
    border-left: 3px solid var(--tm-ink);
    background: var(--tm-card);
    padding: 0.5rem 0.7rem;
    margin: 0.3rem 0;
    font-size: 0.9rem;
  }
  .tm-slip.user {
    border-left-color: var(--tm-accent);
    background: var(--tm-accent-soft);
  }
  .tm-holdings {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem 1.5rem;
    margin: 0.35rem 0 0.65rem;
  }
  .tm-holdings b {
    display: block;
    font-family: var(--tm-serif);
    font-size: 1.55rem;
    font-variant-numeric: tabular-nums;
    font-weight: 700;
    line-height: 1.05;
  }
  .tm-holdings span {
    font-family: var(--tm-sans);
    font-size: 0.65rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--tm-ink-muted);
    font-weight: 650;
  }
  .tm-colophon {
    border-top: 1px solid var(--tm-line);
    margin-top: 0.55rem;
    padding-top: 0.35rem;
    font-family: var(--tm-serif);
    font-style: italic;
    font-size: 0.8rem;
    color: var(--tm-ink-muted);
  }

  /* ——— P7 motion / a11y ——— */
  .tm-fade {
    animation: tm-fade 120ms ease-out;
  }
  @keyframes tm-fade {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      transition: none !important;
      animation: none !important;
    }
    .tm-dep-row.is-active .tm-dep-track i::after { display: none; }
  }
  .tm-sr {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
  }
</style>
"""


def _css() -> str:
    return (
        CSS.replace("__SERIF__", SERIF)
        .replace("__SANS__", SANS)
        .replace("__MONO__", MONO)
    )


def inject(st) -> None:
    """Apply the shared stylesheet once per render."""
    st.markdown(_css(), unsafe_allow_html=True)


def kicker(text: str) -> str:
    return f'<div class="tm-kicker">{text}</div>'


def section(title: str, note: str = "") -> str:
    note_html = f'<span class="tm-section-note">{note}</span>' if note else ""
    return (
        f'<div class="tm-section">'
        f'<span class="tm-section-title">{title}</span>{note_html}'
        f"</div>"
    )


def badge(label: str, variant: str = "") -> str:
    cls = "tm-badge"
    mapping = {
        "accent": " tm-badge-accent",
        "ink": " tm-badge-ink",
        "hole": " tm-badge-hole",
        "danger": " tm-badge-danger",
        "ok": " tm-badge-ok",
    }
    cls += mapping.get(variant, "")
    return f'<span class="{cls}">{label}</span>'


def claim(text: str) -> str:
    return f'<p class="tm-claim">{text}</p>'


def rule(heavy: bool = False) -> str:
    return '<hr class="tm-rule-heavy" />' if heavy else '<hr class="tm-rule" />'


def row(*parts: str) -> str:
    return f'<div class="tm-row">{"".join(parts)}</div>'


def masthead(title: str, dateline_parts: list[str], deck: str = "", volume: str = "") -> str:
    """Minimal newsprint masthead: wordmark, thin dateline, one deck line."""
    meta = " · ".join(p for p in dateline_parts if p)
    volume_html = f'<div class="tm-volume">{volume}</div>' if volume else ""
    deck_html = f'<p class="tm-deck">{deck}</p>' if deck else ""
    meta_html = f'<div class="tm-dateline">{meta}</div>' if meta else ""
    return (
        '<div class="tm-masthead tm-fade">'
        f"{volume_html}"
        f"<h1>{title}</h1>"
        f"{meta_html}"
        f"{deck_html}"
        "</div>"
    )


def empty_state(text: str) -> str:
    return f'<div class="tm-empty">{text}</div>'


def folio(*parts: str) -> str:
    return f'<div class="tm-folio">{"".join(parts)}</div>'


def erratum(text: str) -> str:
    return f'<div class="tm-erratum">Erratum · {text}</div>'


def dirty_bar(label: str = "Unsaved notes") -> str:
    return f'<div class="tm-dirty-bar">● {label}</div>'


def figure_caption(n: int, text: str) -> str:
    return f'<div class="tm-fig"><strong>Fig. {n}</strong> — {text}</div>'


def legend(*items: tuple[str, str]) -> str:
    """items: (css_class, label)"""
    bits = "".join(f'<span><i class="{cls}"></i>{label}</span>' for cls, label in items)
    return f'<div class="tm-legend">{bits}</div>'


def coverage_bar(scored: int, refused: int) -> str:
    total = max(scored + refused, 1)
    s = (scored / total) * 100
    r = (refused / total) * 100
    return (
        f'<div class="tm-coverage" title="scored {scored} / refused {refused}">'
        f'<div class="scored" style="width:{s:.1f}%"></div>'
        f'<div class="refused" style="width:{r:.1f}%"></div>'
        f"</div>"
    )


def letter_badge(label: str) -> str:
    return f'<span class="tm-letter">{label}</span>'


def slip(text: str, role: str = "assistant") -> str:
    from html import escape

    cls = "tm-slip user" if role == "user" else "tm-slip"
    return f'<div class="{cls}">{escape(text)}</div>'


def holdings(*pairs: tuple[str, str]) -> str:
    bits = "".join(f"<div><b>{n}</b><span>{label}</span></div>" for n, label in pairs)
    return f'<div class="tm-holdings">{bits}</div>'


def colophon(text: str) -> str:
    return f'<div class="tm-colophon">{text}</div>'


def note_block(html_body: str) -> str:
    return f'<div class="tm-note">{html_body}</div>'


def card_head(year: str, name: str, *chips: str) -> str:
    return (
        '<div class="tm-card-head">'
        f'<div class="tm-card-year">{year}</div>'
        f'<div class="tm-card-name">{name}</div>'
        f'<div class="tm-card-meta">{"".join(chips)}</div>'
        "</div>"
    )
