"""Shared newspaper chart chrome for human / estimate / pack series."""

from __future__ import annotations

from html import escape

from time_machine.ui import theme

FONT = "-apple-system, 'Helvetica Neue', sans-serif"


def chart_frame(
    *,
    fig: int,
    title: str,
    caption: str,
    a11y_summary: str,
    legend_items: list[tuple[str, str]],
    svg_inner: str,
    width: int = 680,
    height: int = 180,
) -> str:
    legend_html = theme.legend(*legend_items) if legend_items else ""
    return (
        f'<div class="tm-fade">'
        f"{theme.figure_caption(fig, escape(caption))}"
        f"{legend_html}"
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="{FONT}" style="max-width:100%;height:auto;" role="img" '
        f'aria-label="{escape(title, quote=True)}">'
        f"{svg_inner}"
        "</svg>"
        f'<div class="tm-sr">{escape(a11y_summary)}</div>'
        "</div>"
    )


def x_of(year: int, y0: int, y1: int, width: int, pad_l: int = 40, pad_r: int = 16) -> float:
    if y1 == y0:
        y1 = y0 + 1
    return pad_l + (year - y0) / (y1 - y0) * (width - pad_l - pad_r)


def y10(score: float, height: int, pad_t: int = 16, pad_b: int = 28) -> float:
    t = (score - 1) / 9.0
    return pad_t + (1 - t) * (height - pad_t - pad_b)


def y_ord(ord_: float, height: int, pad_t: int = 16, pad_b: int = 28) -> float:
    t = (ord_ + 2) / 4.0
    return pad_t + (1 - t) * (height - pad_t - pad_b)


def human_series(points: list[tuple[int, float]], y_fn) -> str:
    """Deprecated shim — use polyline_and_dots with precomputed coordinates."""
    return ""


def polyline_and_dots(
    points: list[tuple[float, float, str]],
    *,
    stroke: str,
    width: int = 2.5,
    filled: bool = True,
    label_prefix: str = "",
) -> str:
    """points: (x, y, label). Breaks not required if caller splits segments."""
    if not points:
        return ""
    coords = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in points)
    line = (
        f'<polyline points="{coords}" fill="none" stroke="{stroke}" stroke-width="{width}" '
        f'stroke-linejoin="round"/>'
        if len(points) >= 2
        else ""
    )
    dots = []
    for x, y, label in points:
        fill = stroke if filled else "#FFFCF8"
        dots.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
            f'<text x="{x:.1f}" y="{y - 9:.1f}" text-anchor="middle" font-size="11" fill="#1C1B19">'
            f"{label_prefix}{escape(label)}</text>"
        )
    return line + "".join(dots)
