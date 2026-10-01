"""LLMTimeMachine visual language — newsprint masthead × time-machine timetable.

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
    --tm-danger-soft: #FBF0EE;
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
    /* Clear Streamlit's fixed header bar (see pointer-events note below).
       Without this the first block sits underneath the header. */
    padding-top: 3.25rem !important;
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
  /* Streamlit's header is a fixed, full-width bar painted ON TOP of the first
     block of content. We make it transparent but, left hit-testable, it
     silently swallows clicks on anything at the top of the page — the theme
     toggle looked dead while its state logic worked fine. We hide the toolbar
     anyway, so the chrome should not intercept pointer events at all. */
  [data-testid="stHeader"],
  [data-testid="stToolbar"],
  [data-testid="stDecoration"] { pointer-events: none !important; }
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
  /* Stop notes: ledger of stations — year gutter + breathing room.
     Rules used to sit under every grid cell, so they never lined up across
     the two columns. Now separation comes from whitespace; only quarantined
     endpoints keep a rule. Each note is one idea: year, name, what it stands
     for, its limits — stacked, never run on. */
  .tm-stop-notes {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
    width: 100%;
    margin: 0.6rem 0 1rem;
    max-width: 70rem;
  }
  @media (min-width: 960px) {
    .tm-stop-notes {
      grid-template-columns: 1fr 1fr;
      gap: 1.1rem 2.5rem;
    }
    .tm-stop-notes > .tm-note-wide {
      grid-column: 1 / -1;
    }
  }
  .tm-stop-note {
    display: grid;
    grid-template-columns: 3.4rem minmax(0, 1fr);
    gap: 0 0.8rem;
    align-items: start;
    min-width: 0;
  }
  .tm-stop-note-year {
    font-family: var(--tm-serif);
    font-variant-numeric: tabular-nums;
    font-size: 1.3rem;
    font-weight: 700;
    line-height: 1.15;
    color: var(--tm-ink);
  }
  .tm-stop-note.is-hole .tm-stop-note-year {
    color: var(--tm-hole);
    font-weight: 600;
  }
  .tm-stop-note-body {
    min-width: 0;
    font-size: 0.92rem;
    line-height: 1.55;
  }
  .tm-stop-note-name {
    font-weight: 650;
    color: var(--tm-ink);
  }
  .tm-stop-note.is-hole .tm-stop-note-name {
    font-weight: 500;
    font-style: italic;
    color: var(--tm-ink-muted);
  }
  .tm-stop-note-chips {
    display: inline-flex;
    flex-wrap: wrap;
    gap: 0.25rem;
    margin-left: 0.45rem;
    vertical-align: middle;
  }
  .tm-stop-note-sub {
    color: var(--tm-ink-muted);
    font-size: 0.82rem;
    line-height: 1.55;
    margin-top: 0.3rem;
  }
  .tm-stop-note-sub + .tm-stop-note-sub {
    margin-top: 0.2rem;
  }
  .tm-stop-note-sub strong {
    color: var(--tm-ink);
    font-weight: 600;
  }
  .tm-stop-note.is-hole .tm-stop-note-sub strong {
    color: var(--tm-ink-muted);
  }
  /* Legacy single-line classes (kept working, no longer emitted). */
  .tm-hole-line {
    color: var(--tm-ink-muted);
    font-size: 0.88rem;
    line-height: 1.55;
  }
  .tm-model-line {
    font-size: 0.92rem;
    line-height: 1.55;
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
  [data-testid="stTabs"] [role="tablist"] {
    gap: 0.15rem;
    border-bottom: 2px solid var(--tm-ink);
  }
  [data-testid="stTabs"] [role="tab"] {
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

  /* ——— form fields ———
     Streamlit compiles config.toml's theme into emotion at STARTUP and
     exposes no custom properties for it, so the only lever on its own widget
     surfaces is CSS that out-specifies emotion — hence !important everywhere
     in this section. The selectors are the real Streamlit 1.64 test ids;
     there are no [data-baseweb] attributes in this version (that was the
     old baseweb build, and every rule written against it was dead).
     Everything here is var()-driven, so fields follow the palette in light,
     dark and auto without a second copy. */
  [data-testid="stTextInputRootElement"],
  [data-testid="stTextAreaRootElement"] {
    background-color: var(--tm-paper-2) !important;
    border: 1px solid var(--tm-line) !important;
    border-radius: var(--tm-radius-sm) !important;
  }
  /* the editable elements themselves: transparent so the field box shows
     through, and ink text so typing is legible on the box's own value. */
  [data-testid="stTextInputField"],
  [data-testid="stTextAreaRootElement"] textarea,
  [data-testid="stChatInput"] textarea,
  [data-testid="stSidebar"] textarea {
    background-color: transparent !important;
    color: var(--tm-ink) !important;
    /* Safari resolves -webkit-text-fill-color ahead of `color`; without this
       the caret text can stay the startup theme's ink on a dark field. */
    -webkit-text-fill-color: var(--tm-ink) !important;
    caret-color: var(--tm-accent) !important;
  }
  [data-testid="stTextInputField"]::placeholder,
  [data-testid="stTextAreaRootElement"] textarea::placeholder,
  [data-testid="stChatInput"] textarea::placeholder {
    color: var(--tm-ink-muted) !important;
    -webkit-text-fill-color: var(--tm-ink-muted) !important;
    opacity: 1 !important;
  }
  /* focus is the state you actually see while typing: keep the field dark and
     ring it in ochre instead of letting emotion repaint the box. */
  [data-testid="stTextInputRootElement"]:focus-within,
  [data-testid="stTextAreaRootElement"]:focus-within {
    background-color: var(--tm-paper-2) !important;
    border-color: var(--tm-accent) !important;
    box-shadow: 0 0 0 2px var(--tm-accent-soft) !important;
  }
  [data-testid="stTextInputField"]:focus,
  [data-testid="stTextAreaRootElement"] textarea:focus {
    background-color: transparent !important;
    color: var(--tm-ink) !important;
    -webkit-text-fill-color: var(--tm-ink) !important;
    outline: none !important;
  }
  /* selectbox: control box, then the dropdown, which is portaled to <body>
     and therefore outside .stApp — it needs its own rule. */
  [data-testid="stSelectbox"] > div > div {
    background-color: var(--tm-paper-2) !important;
    border: 1px solid var(--tm-line) !important;
    border-radius: var(--tm-radius-sm) !important;
  }
  [data-testid="stSelectbox"] input[role="combobox"] {
    background-color: transparent !important;
    color: var(--tm-ink) !important;
    -webkit-text-fill-color: var(--tm-ink) !important;
    caret-color: var(--tm-accent) !important;
  }
  [data-testid="stSelectbox"] input[role="combobox"]::placeholder {
    color: var(--tm-ink-muted) !important;
    -webkit-text-fill-color: var(--tm-ink-muted) !important;
  }
  [data-testid="stSelectbox"] svg { fill: var(--tm-ink-muted) !important; }
  [data-testid="stSelectboxVirtualDropdown"] {
    background-color: var(--tm-paper) !important;
    border: 1px solid var(--tm-line) !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35) !important;
  }
  [data-testid="stSelectboxVirtualDropdown"] [role="listbox"],
  [data-testid="stSelectboxVirtualDropdown"] [role="option"] {
    background-color: transparent !important;
    color: var(--tm-ink) !important;
    -webkit-text-fill-color: var(--tm-ink) !important;
  }
  [data-testid="stSelectboxVirtualDropdown"] [role="option"]:hover,
  [data-testid="stSelectboxVirtualDropdown"] [role="option"][aria-selected="true"] {
    background-color: var(--tm-paper-2) !important;
  }
  /* radio + checkbox discs (react-aria hides the real input in a clipped span,
     so :has() is how we reach the checked state) */
  /* the disc is three nested divs: outer > ring > dot. The unselected dot is
     a light fill in the startup theme, so an unchecked radio reads as a pale
     blob on dark paper — style the ring and hollow the dot when unchecked. */
  [data-testid="stRadioOption"] > div {
    background-color: var(--tm-card) !important;
    border-color: var(--tm-ink-muted) !important;
  }
  [data-testid="stRadioOption"] > div > div {
    background-color: transparent !important;
    border-color: var(--tm-ink-muted) !important;
  }
  [data-testid="stRadioOption"] > div > div > div {
    background-color: transparent !important;
  }
  [data-testid="stRadioOption"]:has(input:checked) > div {
    background-color: var(--tm-card) !important;
    border-color: var(--tm-accent) !important;
  }
  [data-testid="stRadioOption"]:has(input:checked) > div > div {
    background-color: transparent !important;
    border-color: var(--tm-accent) !important;
  }
  [data-testid="stRadioOption"]:has(input:checked) > div > div > div {
    background-color: var(--tm-accent) !important;
  }
  [data-testid="stCheckbox"] label:has(input:checked) > div {
    background-color: var(--tm-accent) !important;
    border-color: var(--tm-accent) !important;
  }
  [data-testid="stCheckbox"] label:has(input:checked) > div svg {
    fill: var(--tm-paper) !important;
  }
  [data-testid="stRadioOption"] [data-testid="stMarkdownContainer"] p,
  [data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] p,
  [data-testid="stWidgetLabel"] { color: var(--tm-ink) !important; }
  /* helper/info icons ship the startup theme's ink, invisible on dark paper */
  [data-testid="stIconMaterial"],
  [data-testid="stTooltipIcon"] { color: var(--tm-ink-muted) !important; }
  [data-testid="stCaptionContainer"] { color: var(--tm-ink-muted) !important; }
  [data-testid="stAlertContainer"] {
    background-color: var(--tm-paper-2) !important;
    color: var(--tm-ink) !important;
    border: 1px solid var(--tm-line) !important;
  }
  [data-testid="stAlertContentInfo"],
  [data-testid="stAlertContentWarning"],
  [data-testid="stAlertContentSuccess"],
  [data-testid="stAlertContentError"],
  [data-testid="stAlertContent"] {
    background-color: transparent !important;
    color: var(--tm-ink) !important;
    -webkit-text-fill-color: var(--tm-ink) !important;
  }
  /* Buttons. Secondary is emitted in two flavours (plain and form-submit) and
     the hovered/active states carry their own backgrounds, so each state needs
     its own rule or a hovered button flashes cream on dark paper. */
  [data-testid="stBaseButton-secondary"] {
    background-color: var(--tm-card) !important;
    color: var(--tm-ink) !important;
    border: 1px solid var(--tm-line) !important;
  }
  [data-testid="stBaseButton-secondary"]:hover,
  [data-testid="stBaseButton-secondary"]:active,
  [data-testid="stBaseButton-secondary"]:focus-visible {
    background-color: var(--tm-paper-2) !important;
    color: var(--tm-ink) !important;
    border-color: var(--tm-accent) !important;
  }
  [data-testid="stBaseButton-secondary"]:disabled,
  [data-testid="stBaseButton-secondary"][disabled] {
    background-color: var(--tm-paper-2) !important;
    color: var(--tm-hole) !important;
    border-color: var(--tm-line) !important;
  }
  [data-testid="stBaseButton-primary"] {
    background-color: var(--tm-accent) !important;
    color: var(--tm-paper) !important;
    border: 1px solid var(--tm-accent) !important;
  }
  [data-testid="stBaseButton-primary"] p,
  [data-testid="stBaseButton-secondary"] p { color: inherit !important; }
  /* header/menu buttons are icon-only and carry no background, so only the
     glyph colour needs restating */
  [data-testid="stBaseButton-header"],
  [data-testid="stBaseButton-headerNoPadding"],
  [data-testid="stMainMenuButton"],
  [data-testid="stSidebarCollapseButton"] {
    color: var(--tm-ink) !important;
  }
  [data-testid="stBaseButton-header"]:hover,
  [data-testid="stMainMenuButton"]:hover { background-color: var(--tm-paper-2) !important; }
  [data-testid="stAlertContentInfo"] { border-left: 3px solid var(--tm-accent) !important; }
  [data-testid="stAlertContentWarning"] { border-left: 3px solid var(--tm-accent) !important; }
  [data-testid="stAlertContentSuccess"] { border-left: 3px solid var(--tm-ok) !important; }
  [data-testid="stAlertContentError"] { border-left: 3px solid var(--tm-danger) !important; }

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
    background: var(--tm-danger-soft);
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


# ── chart series colors (single source; was hardcoded per-builder) ──
# Light values preserve the original hexes exactly. Dark variants are
# brightened for contrast on the night paper. Builders emit classes
# (s-human / s-est / s-pack / s-band / s-grid / t-lab / t-axis) and no fills.
CHART_CSS = """
<style>
  .tm-chart .s-grid { stroke: #D9D2C7; }
  .tm-chart .s-human { stroke: #2F6F4E; }
  .tm-chart circle.s-human, .tm-chart polygon.s-human { fill: #2F6F4E; }
  .tm-chart .s-est { stroke: #6B4C9A; }
  .tm-chart circle.s-est { fill: #6B4C9A; }
  .tm-chart .s-pack { stroke: #9B7BB8; }
  .tm-chart circle.s-hollow { fill: #FFFCF8; }
  .tm-chart .s-band { fill: #CBB8E8; fill-opacity: 0.35; }
  .tm-chart text.t-lab { fill: #1C1B19; }
  .tm-chart text.t-axis { fill: #6B6560; }
  .tm-legend i.est { background: #6B4C9A; }
  .tm-legend i.pack { background: #9B7BB8; opacity: 0.7; height: 1px; }
</style>
"""

# Newsprint after dark. Ink becomes warm paper, paper becomes warm ink;
# ochre brightens so it keeps its job (substitutes, playheads, CTAs) at
# ≥4.5:1. Semantic hues soften instead of inverting: danger blushes,
# ok mints, judge violet lifts. Same rules, new variables — the system
# doesn't change shape at night, only lamplight.
DARK_VARS = {
    "--tm-paper": "#171310",
    "--tm-paper-2": "#211B14",
    "--tm-card": "#262017",
    "--tm-ink": "#F2EBDF",
    "--tm-ink-muted": "#B4A78F",
    "--tm-line": "#3E362A",
    "--tm-accent": "#D99945",
    "--tm-accent-soft": "rgba(217, 153, 69, 0.13)",
    "--tm-accent-ink": "#E5B263",
    "--tm-hole": "#8D8070",
    "--tm-danger": "#DA8D7E",
    "--tm-danger-soft": "#38211C",
    "--tm-ok": "#82BC93",
}

# Everything native Streamlit paints from its own (light) theme, restyled
# here so widgets don't glow white at night. Scoped to the same dark
# activation as the variables (bare `:root` when forced, `@media` when auto).
DARK_WIDGET_CSS = """
  /* ── 0. Shell override. Streamlit themes itself with emotion (CSS-in-JS),
        which injects <style data-emotion> into <head> AFTER any markdown
        <style> we emit. Emotion's rules are class-based, so they tie our
        selector on specificity and win on document order — which is why a
        plain variable flip looked like it did nothing: the tray went dark,
        the page stayed paper. `!important` is the only reliable way to win
        against a runtime-injected sheet, so the shell is forced explicitly
        rather than trusting cascade order. Also sets `color-scheme` so
        native form controls, scrollbars, and focus rings follow. */
  :root { color-scheme: dark; }
  html, body,
  .stApp,
  [data-testid="stAppViewContainer"],
  [data-testid="stMain"],
  [data-testid="stMainBlockContainer"],
  [data-testid="stSidebar"],
  [data-testid="stHeader"],
  [data-testid="stToolbar"],
  [data-testid="stBottom"],
  [data-testid="stStatusWidget"],
  [data-testid="stDecoration"] {
    background-color: var(--tm-paper) !important;
    color: var(--tm-ink) !important;
  }
  /* deliberately NOT a descendant wildcard: our own components (cards,
     accent chips, endpoints) carry explicit backgrounds and emotion never
     styles them, so blanket-ing the tree would erase the design. */
  html, body { background: var(--tm-paper) !important; }
  [data-testid="stSidebar"],
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
  [data-testid="stBottom"],
  [data-testid="stStatusWidget"] {
    background-color: var(--tm-paper-2) !important;
  }
  [data-testid="stHeader"],
  [data-testid="stToolbar"],
  [data-testid="stDecoration"] {
    background-color: transparent !important;
  }
  .stApp a { color: var(--tm-accent-ink) !important; }
  ::-webkit-scrollbar-thumb { background: var(--tm-line) !important; }
  /* every text-bearing surface follows the token, not emotion's light set */
  .stApp p, .stApp span, .stApp label, .stApp li, .stApp h1, .stApp h2,
  .stApp h3, .stApp h4, .stApp td, .stApp th, .stApp small {
    color: inherit;
  }
  [data-testid="stCaptionContainer"], .stCaption {
    color: var(--tm-ink-muted) !important;
  }
  /* containers we own keep their surface tone */
  [data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--tm-card) !important;
    border-color: var(--tm-line) !important;
    color: var(--tm-ink) !important;
  }
  [data-testid="stExpander"] {
    background: var(--tm-paper) !important;
    border-color: var(--tm-line) !important;
    color: var(--tm-ink) !important;
  }
  /* Text entry, menus, tags, radio/checkbox and alerts are all handled in the
     base "form fields" section: that layer is var()-driven, so it already
     follows the dark palette from here. What remains below is only what
     genuinely needs a night-specific value. */
  [data-testid="stAlert"] {
    background: var(--tm-card) !important;
    border: 1px solid var(--tm-line) !important;
    color: var(--tm-ink) !important;
  }
  [data-testid="stAlert"] p, [data-testid="stAlert"] li { color: var(--tm-ink) !important; }
  /* chat input bar (playground chat) */
  [data-testid="stChatInput"] > div {
    background: var(--tm-card) !important;
    border-color: var(--tm-line) !important;
  }
  [data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--tm-ink) !important;
    caret-color: var(--tm-accent) !important;
  }
  [data-testid="stChatInput"] textarea::placeholder { color: var(--tm-ink-muted) !important; }
  [data-testid="stChatInput"] button svg { fill: var(--tm-accent-ink) !important; }
  [data-testid="stChatInput"] button:disabled svg { fill: var(--tm-hole) !important; }
  /* inline code pills in markdown (blocks under pre: are untouched) */
  .stApp :not(pre) > code {
    background: var(--tm-paper-2) !important;
    border: 1px solid var(--tm-line) !important;
    color: var(--tm-ink) !important;
  }
  /* radio + checkbox discs are var-driven in the base form-fields section */
  /* alerts keep their icon hue, gain night paper */
  [data-testid="stAlert"] {
    background: var(--tm-card) !important;
    border: 1px solid var(--tm-line) !important;
    color: var(--tm-ink) !important;
  }
  [data-testid="stAlert"] p, [data-testid="stAlert"] li { color: var(--tm-ink) !important; }
  /* code / json / tables */
  [data-testid="stJson"] {
    background: var(--tm-paper-2) !important;
    border: 1px solid var(--tm-line) !important;
  }
  [data-testid="stDataFrame"], [data-testid="stTable"] { border: 1px solid var(--tm-line); }
  /* dividers, spinners, progress */
  [data-testid="stDivider"] hr, hr { border-color: var(--tm-line) !important; }
  [data-testid="stSpinner"] > div { border-top-color: var(--tm-accent) !important; }
  [data-testid="stProgressBar"] > div > div { background: var(--tm-accent) !important; }
  /* expanders already var-driven except the chevron */
  [data-testid="stExpander"] svg { fill: var(--tm-ink-muted) !important; }
  /* our chart series at night */
  .tm-chart .s-grid { stroke: #3E362A; }
  .tm-chart .s-human { stroke: #82BC93; }
  .tm-chart circle.s-human, .tm-chart polygon.s-human { fill: #82BC93; }
  .tm-chart .s-est { stroke: #A78BDB; }
  .tm-chart circle.s-est { fill: #A78BDB; }
  .tm-chart .s-pack { stroke: #B79AD9; }
  .tm-chart circle.s-hollow { fill: #262017; }
  .tm-chart .s-band { fill: #A78BDB; fill-opacity: 0.22; }
  .tm-chart text.t-lab { fill: #F2EBDF; }
  .tm-chart text.t-axis { fill: #B4A78F; }
  .tm-legend i.est { background: #A78BDB; }
  .tm-legend i.pack { background: #B79AD9; }
  .tm-legend i.human { background: #82BC93; }
"""


def _dark_block() -> str:
    vars_css = "\n".join(f"    {k}: {v};" for k, v in DARK_VARS.items())
    return f":root {{\n{vars_css}\n  }}\n{DARK_WIDGET_CSS}"


def dark_css(appearance: str) -> str:
    """Dark stylesheet for an appearance mode: auto (media-wrapped), dark (bare), else empty."""
    if appearance == "dark":
        return f"<style>\n{_dark_block()}\n</style>"
    if appearance == "auto":
        return f"<style>\n@media (prefers-color-scheme: dark) {{\n{_dark_block()}\n}}\n</style>"
    return ""


APPEARANCE_CHOICES = ("auto", "light", "dark")


def resolve_appearance(default: str = "auto") -> str:
    """Read the sidebar Appearance choice; safe without a Streamlit context (tests, stubs)."""
    try:
        import streamlit as st

        value = st.session_state.get("appearance", default)
    except Exception:
        return default
    return value if value in APPEARANCE_CHOICES else default


def inject(st, appearance: str | None = None) -> None:
    """Apply the shared stylesheet once per render, plus dark mode per appearance."""
    st.markdown(_css(), unsafe_allow_html=True)
    st.markdown(CHART_CSS, unsafe_allow_html=True)
    mode = appearance or resolve_appearance()
    css = dark_css(mode)
    if css:
        st.markdown(css, unsafe_allow_html=True)


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


# ── Lifeline hero-rail island (newsprint-matched tray) ──
# Ported motion + rail logic from evilrabbit/lifeline (MIT). The island lives
# in an iframe (st.components.v1.html), so this CSS is self-contained — but
# every token below mirrors the newsprint system above (paper/ink/ochre,
# serif display, ticket-stub 2px radii, 3px ink tray top). The rail reads as
# the same timetable family as `.tm-timetable` and `.tm-departure`, not a
# foreign zinc module. Honesty encoding is unchanged: hole dashed, sub ochre,
# avail ink, gaps faint.
LIFELINE_ISLAND_CSS = """
  :root {
    --ll-bg: #F7F4EF;
    --ll-surface: #FFFCF8;
    --ll-ink: #1C1B19;
    --ll-muted: #6B6560;
    --ll-line: #D9D2C7;
    --ll-line-strong: #b9b0a2;
    --ll-dash: #A39A8E;
    --ll-accent: #C47B2D;
    --ll-accent-ink: #A35F14;
    --ll-accent-soft: #FBF3E8;
    --ll-ok: #2F6F4E;
    --ll-danger: #8B3A2F;
    --ll-hole: #A39A8E;
    --ll-font: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    --ll-serif: "Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, 'Times New Roman', serif;
    --ll-mono: 'SF Mono', ui-monospace, Menlo, Consolas, monospace;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0;
    background: var(--ll-bg);
    color: var(--ll-ink);
    font-family: var(--ll-font);
    -webkit-font-smoothing: antialiased;
  }
  .ll-shell { padding: 14px 16px 12px; }
  .ll-top {
    display: flex; align-items: baseline; gap: 10px;
    margin-bottom: 10px;
  }
  .ll-title {
    font-family: var(--ll-serif);
    font-size: 15px; font-weight: 700; letter-spacing: 0.01em;
  }
  .ll-sub {
    font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--ll-muted); font-weight: 600;
    margin-left: auto; white-space: nowrap;
  }
  .ll-legend {
    display: flex; flex-wrap: wrap; gap: 6px 14px;
    font-size: 10.5px; letter-spacing: 0.06em; text-transform: uppercase;
    color: var(--ll-muted); font-weight: 600;
    margin: 0 0 10px;
  }
  .ll-legend i {
    display: inline-block; width: 18px; height: 2px;
    background: var(--ll-ink); vertical-align: middle; margin-right: 5px;
  }
  .ll-legend i.sub { background: var(--ll-accent); height: 3px; }
  .ll-legend i.hole { background: transparent; border-top: 2px dashed var(--ll-hole); height: 0; }
  .ll-legend i.gap { background: var(--ll-line-strong); }
  .ll-legend i.live { background: var(--ll-accent); height: 3px; }
  .ll-viewport {
    overflow-x: auto; overflow-y: hidden;
    scroll-snap-type: x proximity;
    border: 1px solid var(--ll-line);
    border-top: 3px solid var(--ll-ink);
    background: var(--ll-surface);
    border-radius: 0;
  }
  .ll-track {
    display: flex; align-items: stretch;
    min-width: max-content; position: relative;
    padding: 0;
  }
  .ll-shield {
    position: sticky; left: 0; z-index: 20;
    width: 92px; min-width: 92px;
    background: var(--ll-surface);
    border-right: 1px solid var(--ll-line);
    padding: 12px 10px;
    display: flex; flex-direction: column; gap: 2px;
  }
  .ll-shield .age {
    font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--ll-muted); font-weight: 700;
  }
  .ll-shield .years {
    font-family: var(--ll-serif); font-weight: 700; font-size: 13px;
  }
  .ll-shield .hint { font-size: 10.5px; color: var(--ll-muted); line-height: 1.4; }
  .ll-rail-wrap { position: relative; display: flex; }
  .ll-rail {
    position: absolute; left: 0; right: 0; top: 46px; height: 0;
    border-top: 1px solid var(--ll-ink);
    opacity: 0.35;
    transform-origin: left center;
  }
  .ll-rail.solid { border-top-style: solid; opacity: 0.35; }
  .ll-markers { display: flex; align-items: stretch; position: relative; }
  .ll-stop {
    scroll-snap-align: start;
    width: 132px; min-width: 132px; max-width: 132px;
    padding: 14px 10px 12px;
    text-align: left; position: relative;
    border: 0; border-right: 1px solid var(--ll-line);
    background: transparent; cursor: default;
    font-family: var(--ll-font);
  }
  .ll-stop:last-child { border-right: 0; }
  .ll-stop:focus-visible { outline: 2px solid var(--ll-accent); outline-offset: -2px; }
  .ll-stop .tick { width: 1px; height: 10px; background: var(--ll-ink); margin: 0 0 4px 2px; }
  .ll-stop.is-hole .tick { background: transparent; border-left: 1px dashed var(--ll-hole); width: 0; }
  .ll-stop.is-gap .tick { background: var(--ll-line-strong); }
  .ll-dot {
    width: 10px; height: 10px; border-radius: 2px;
    border: 1.5px solid var(--ll-ink); background: var(--ll-surface);
    margin: 0 0 8px 0;
  }
  .ll-stop.is-sub .ll-dot { border-color: var(--ll-accent); background: var(--ll-accent-soft); }
  .ll-stop.is-hole .ll-dot { border-style: dashed; border-color: var(--ll-hole); background: transparent; border-radius: 50%; }
  .ll-stop.is-gap .ll-dot { border-color: var(--ll-line-strong); background: var(--ll-bg); border-radius: 50%; width: 8px; height: 8px; }
  .ll-stop.is-now .ll-dot, .ll-stop.is-next .ll-dot { background: var(--ll-accent); border-color: var(--ll-accent-ink); }
  .ll-stop.is-done .ll-dot { background: var(--ll-ok); border-color: var(--ll-ok); }
  .ll-stop.is-live .ll-dot { background: var(--ll-accent); border-color: var(--ll-accent-ink); animation: ll-pulse 1.1s ease-in-out infinite; }
  .ll-stop.is-failed .ll-dot { background: var(--ll-danger); border-color: var(--ll-danger); }
  @keyframes ll-pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.35); } }
  .ll-year {
    font-family: var(--ll-serif); font-variant-numeric: tabular-nums;
    font-size: 14px; font-weight: 700; line-height: 1.1;
  }
  .ll-stop.is-hole .ll-year, .ll-stop.is-gap .ll-year { color: var(--ll-hole); font-weight: 600; }
  .ll-name {
    font-size: 11.5px; font-weight: 650; line-height: 1.3;
    margin-top: 3px; min-height: 2.6em;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  }
  .ll-stop.is-hole .ll-name { color: var(--ll-muted); font-weight: 500; font-style: italic; }
  .ll-stop.is-gap .ll-name { color: var(--ll-dash); font-weight: 500; }
  .ll-meta {
    font-size: 9.5px; letter-spacing: 0.07em; text-transform: uppercase;
    color: var(--ll-muted); font-weight: 700; margin-top: 4px;
  }
  .ll-flag {
    display: inline-block; font-size: 9px; font-weight: 800; letter-spacing: 0.08em;
    text-transform: uppercase; padding: 1px 5px; border-radius: 2px; margin-top: 6px;
  }
  .ll-flag.next { background: var(--ll-ink); color: var(--ll-bg); }
  .ll-flag.done { background: transparent; border: 1px solid var(--ll-ok); color: var(--ll-ok); }
  .ll-flag.live { background: var(--ll-accent); color: var(--ll-bg); }
  .ll-flag.failed { background: transparent; border: 1px solid var(--ll-danger); color: var(--ll-danger); }
  .ll-preview {
    font-size: 11px; color: var(--ll-muted); line-height: 1.45; margin-top: 6px;
    display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
  }
  .ll-stop:hover .ll-name, .ll-stop:focus .ll-name { color: var(--ll-accent-ink); }
  .ll-playhead {
    position: absolute; top: 0; bottom: 0; width: 0;
    border-left: 1.5px dashed var(--ll-accent);
    pointer-events: none; z-index: 5;
  }
  .ll-playhead span {
    position: absolute; top: 4px; left: 5px;
    font-size: 9px; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--ll-accent-ink); font-weight: 800; white-space: nowrap;
    background: var(--ll-surface); padding: 0 4px;
  }
  .ll-rail-intro { transform: scaleX(var(--ll-intro, 0)); }
  .ll-marker-intro { opacity: 0; animation: ll-marker-in 420ms cubic-bezier(0.22,1,0.36,1) forwards; }
  @keyframes ll-marker-in { from { opacity: 0; transform: translate3d(0,6px,0); } to { opacity: 1; transform: none; } }
  .ll-labels-intro { opacity: 0; animation: ll-labels-in 600ms cubic-bezier(0.22,1,0.36,1) forwards; }
  @keyframes ll-labels-in { from { opacity: 0; } to { opacity: 1; } }
  .ll-foot {
    display: flex; flex-wrap: wrap; gap: 4px 12px;
    font-family: var(--ll-mono); font-size: 10.5px; color: var(--ll-muted);
    margin-top: 8px;
  }
  .ll-endpoint {
    border-left: 3px solid var(--ll-accent);
    background: var(--ll-accent-soft);
    padding: 6px 9px; font-size: 11.5px; margin-top: 8px; border-radius: 0 2px 2px 0;
  }
  .ll-endpoint.muted { border-left-color: var(--ll-hole); border-left-style: dashed; background: transparent; }
  @media (max-width: 640px) {
    .ll-track { min-width: 0; }
    .ll-shield { display: none; }
    .ll-viewport { overflow-x: hidden; }
    .ll-rail-wrap { width: 100%; }
    .ll-markers { flex-direction: column; width: 100%; }
    .ll-stop { width: 100%; min-width: 0; max-width: none; border-right: 0; border-bottom: 1px solid var(--ll-line); }
    .ll-rail { display: none; }
    .ll-playhead { display: none; }
  }
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation: none !important; transition: none !important; }
    .ll-marker-intro, .ll-labels-intro { opacity: 1 !important; }
    .ll-rail-intro { transform: none !important; }
    .ll-stop.is-live .ll-dot { animation: none !important; }
  }
"""


def lifeline_island_css() -> str:
    """Standalone <style> for the hero-rail iframe island."""
    return f"<style>{LIFELINE_ISLAND_CSS}</style>"


# Night paper for the hero rail island. Same shape, lamplight palette —
# mirrors DARK_VARS under the island's own --ll-* names.
DARK_ISLAND_VARS = {
    "--ll-bg": "#171310",
    "--ll-surface": "#262017",
    "--ll-ink": "#F2EBDF",
    "--ll-muted": "#B4A78F",
    "--ll-line": "#3E362A",
    "--ll-line-strong": "#5A4F3D",
    "--ll-dash": "#8D8070",
    "--ll-accent": "#D99945",
    "--ll-accent-ink": "#E5B263",
    "--ll-accent-soft": "rgba(217, 153, 69, 0.13)",
    "--ll-ok": "#82BC93",
    "--ll-danger": "#DA8D7E",
    "--ll-hole": "#8D8070",
}


def lifeline_island_dark_css(appearance: str) -> str:
    """Island dark styles: media-wrapped for auto, body.ll-dark-scoped for forced dark."""
    vars_css = "\n".join(f"    {k}: {v};" for k, v in DARK_ISLAND_VARS.items())
    if appearance == "dark":
        return f"<style>\n  body.ll-dark {{\n{vars_css}\n  }}\n</style>"
    if appearance == "auto":
        return f"<style>\n  @media (prefers-color-scheme: dark) {{\n    :root {{\n{vars_css}\n    }}\n  }}\n</style>"
    return ""
