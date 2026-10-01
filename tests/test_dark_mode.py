"""Dark mode: wiring, token parity, and WCAG contrast floors."""

from __future__ import annotations

import re

from llm_time_machine.ui import theme
from llm_time_machine.ui import timeline as tl
from llm_time_machine.ui.charts import chart_frame, polyline_and_dots
from llm_time_machine.ui.curves import _svg_curve
from llm_time_machine.domain import CurvePoint


def _lum(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))

    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def _ratio(fg: str, bg: str) -> float:
    a, b = _lum(fg), _lum(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


# ── wiring ─────────────────────────────────────────────────────────────


def test_dark_css_modes():
    assert theme.dark_css("light") == ""
    bare = theme.dark_css("dark")
    assert ":root" in bare and "@media" not in bare
    assert "stAlert" in bare  # native widget coverage ships
    assert "stChatInput" in bare and ":not(pre) > code" in bare
    auto = theme.dark_css("auto")
    assert "@media (prefers-color-scheme: dark)" in auto
    assert "stAlert" in auto


def test_no_dead_data_baseweb_selectors():
    """Streamlit 1.64 ships react-aria, not baseweb: the live DOM contains
    zero [data-baseweb] elements. Every rule written against those attributes
    was a no-op, which is how the input boxes stayed white while the CSS
    "covered" them. Anything naming data-baseweb is dead on arrival."""
    for name, css in (("base", theme._css()), ("dark", theme.dark_css("dark"))):
        # strip comments first: the form-fields comment legitimately names the
        # attribute to explain why nothing uses it any more
        rules = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        assert "data-baseweb" not in rules, f"{name} has dead baseweb selectors"


def test_form_fields_use_real_testids_and_are_var_driven():
    """Field surfaces live in the base stylesheet, var()-driven, so one set of
    rules serves light, dark and auto. They must name the real 1.64 test ids
    and carry !important, because Streamlit compiles config.toml's theme into
    emotion at startup and exposes no custom properties to override."""
    css = theme._css()
    for selector in (
        '[data-testid="stTextInputRootElement"]',
        '[data-testid="stTextAreaRootElement"]',
        '[data-testid="stTextInputField"]',
        '[data-testid="stSelectboxVirtualDropdown"]',
        '[data-testid="stSelectbox"] input[role="combobox"]',
        '[data-testid="stAlertContainer"]',
        '[data-testid="stIconMaterial"]',
        # buttons: the hovered/disabled flavours carry their own backgrounds,
        # so a plain base rule still leaves cream flashes on dark paper
        '[data-testid="stBaseButton-secondary"]:hover',
        '[data-testid="stBaseButton-secondary"]:disabled',
        '[data-testid="stBaseButton-primary"]',
        # unchecked radio dots are a light fill in the startup theme
        '[data-testid="stRadioOption"] > div > div > div',
    ):
        assert selector in css, selector
    # not hard-coded colours, and Safari's text fill is handled explicitly
    assert "-webkit-text-fill-color: var(--tm-ink) !important" in css
    assert "var(--tm-paper-2) !important" in css


def test_field_ink_on_field_paper_is_legible_in_both_modes():
    """The exact bug you cannot see while typing: a light-ink textarea on the
    light field box. Guard the pair we actually paint, per mode."""
    for label, paper, ink in (
        ("light", "#EFEAE3", "#1C1B19"),
        ("dark", theme.DARK_VARS["--tm-paper-2"], theme.DARK_VARS["--tm-ink"]),
    ):
        assert _ratio(ink, paper) >= 4.5, f"{label} field text fails contrast"


def test_dark_css_beats_streamlit_emotion():
    """Streamlit themes via emotion, which injects <style data-emotion>
    into <head> AFTER our markdown <style>. Emotion's class-based rules tie
    our selectors on specificity and win on document order, so every shell
    surface must carry !important or the tray flips while the page stays
    paper. This is the regression guard for "toggle does nothing"."""
    bare = theme.dark_css("dark")
    shell = bare.split("text entry")[0]
    for selector in (
        ".stApp",
        '[data-testid="stAppViewContainer"]',
        '[data-testid="stMain"]',
        '[data-testid="stSidebar"]',
    ):
        idx = shell.index(selector)
        rule = shell[idx : shell.index("}", idx)]
        assert "!important" in rule, f"{selector} can lose to emotion"
    assert "color-scheme: dark" in bare


def test_dark_css_does_not_flatten_our_components():
    """A descendant wildcard would erase cards and accent chips."""
    shell = theme.dark_css("dark").split("text entry")[0]
    assert '[data-testid="stMain"] *' not in shell
    assert ".tm-card" not in shell  # our own surfaces keep their own tone

def test_header_chrome_does_not_swallow_clicks():
    """Streamlit's header is a fixed bar over the first content block.

    Left hit-testable it eats clicks on anything at the top of the page — the
    theme toggle appeared dead while its state flipped correctly. AppTest sets
    widget state directly and never hit-tests, so this invariant has to be
    asserted against the stylesheet itself.
    """
    css = theme._css()
    rule = css[css.index('[data-testid="stHeader"],') :]
    rule = rule[: rule.index("}")]
    assert "pointer-events: none" in rule
    # and content is pushed clear of the bar rather than sitting under it
    assert "padding-top: 3.25rem" in css


def test_dark_vars_cover_base_vars():
    base = theme._css()
    for key in theme.DARK_VARS:
        assert key in base, f"{key} has no light counterpart"


def test_resolve_appearance_defaults_auto_without_context():
    assert theme.resolve_appearance() == "auto"


def test_inject_emits_dark_block_per_mode():
    calls: list[str] = []

    class Stub:
        session_state: dict = {}

        def markdown(self, s, unsafe_allow_html=False):
            calls.append(s)

    theme.inject(Stub(), appearance="light")
    assert len(calls) == 2  # base + chart series, no dark
    calls.clear()
    theme.inject(Stub(), appearance="dark")
    assert len(calls) == 3 and "@media" not in calls[2]
    calls.clear()
    theme.inject(Stub(), appearance="auto")
    assert len(calls) == 3 and "prefers-color-scheme" in calls[2]


# ── hero island ────────────────────────────────────────────────────────


def test_island_dark_wiring():
    assert theme.lifeline_island_dark_css("light") == ""
    auto = theme.lifeline_island_dark_css("auto")
    assert "@media (prefers-color-scheme: dark)" in auto and "--ll-ink" in auto
    forced = theme.lifeline_island_dark_css("dark")
    assert "body.ll-dark" in forced and "@media" not in forced


def test_island_dark_vars_cover_light_vars():
    light = theme.lifeline_island_css()
    for key in theme.DARK_ISLAND_VARS:
        assert key in light, f"{key} has no light counterpart"
    # parity with the React tokens file
    from pathlib import Path

    tokens = (Path(__file__).resolve().parents[1] / "frontend" / "lifeline-rail" / "tokens.ts").read_text()
    for _k, v in theme.DARK_ISLAND_VARS.items():
        if v.startswith("#"):
            assert v.lower() in tokens.lower(), v


def test_hero_html_dark_body_class():
    from llm_time_machine.cohort_catalog import CohortCatalog
    from tests.conftest import REPO_ROOT

    cohort = CohortCatalog(REPO_ROOT).load("decade-v0")
    markers = tl.lifeline_markers(cohort)
    dark = tl.hero_rail_html(cohort, markers, appearance="dark")
    assert "ll-dark" in dark and "--ll-ink" in dark
    light = tl.hero_rail_html(cohort, markers, appearance="light")
    assert "ll-dark" not in light and "prefers-color-scheme" not in light


# ── classed charts ─────────────────────────────────────────────────────


def test_curve_svg_uses_classes_not_hardcoded_series():
    pts = [
        CurvePoint(model_id="m1", display_year=2019, ordinal=-1, display_name="M1"),
        CurvePoint(model_id="m2", display_year=2021, ordinal=1, display_name="M2"),
    ]
    svg = _svg_curve(pts)
    assert 'class="tm-chart"' in svg
    assert 'class="s-human"' in svg
    assert 'class="t-lab"' in svg and 'class="t-axis"' in svg
    assert "#2f6f4e" not in svg and "#1a1a1a" not in svg and "#666" not in svg


def test_shared_chart_helpers_emit_series_classes():
    out = polyline_and_dots([(0.0, 0.0, "a"), (10.0, 10.0, "b")], stroke="#2f6f4e")
    assert 'class="s-human"' in out and 'class="t-lab"' in out
    unknown = polyline_and_dots([(0.0, 0.0, "a"), (10.0, 10.0, "b")], stroke="#123456")
    assert "<polyline points=" in unknown  # no invented class
    frame = chart_frame(
        fig=1, title="t", caption="c", a11y_summary="s", legend_items=[], svg_inner="x"
    )
    assert 'class="tm-chart"' in frame


# ── contrast floors (WCAG: text ≥ 4.5, large/graphics ≥ 3) ──────────────


def test_light_text_contrast():
    assert _ratio("#1C1B19", "#F7F4EF") >= 7  # body
    assert _ratio("#6B6560", "#F7F4EF") >= 4.5  # muted
    assert _ratio("#A35F14", "#F7F4EF") >= 4.5  # accent-ink links/labels
    assert _ratio("#2F6F4E", "#FFFCF8") >= 4.5  # ok badges/dots


def test_dark_text_contrast():
    d = theme.DARK_VARS
    assert _ratio(d["--tm-ink"], d["--tm-paper"]) >= 7
    assert _ratio(d["--tm-ink-muted"], d["--tm-paper"]) >= 4.5
    assert _ratio(d["--tm-accent-ink"], d["--tm-paper"]) >= 4.5
    assert _ratio(d["--tm-ink"], d["--tm-card"]) >= 4.5  # stop text on cards
    assert _ratio(d["--tm-accent"], d["--tm-paper"]) >= 3  # rail graphics/large
    assert _ratio(d["--tm-ok"], d["--tm-paper"]) >= 3
    assert _ratio(d["--tm-danger"], d["--tm-paper"]) >= 3
