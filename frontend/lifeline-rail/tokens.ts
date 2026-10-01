/**
 * Lifeline rail tokens — newsprint-matched tray (mirrors
 * `src/llm_time_machine/ui/theme.py::LIFELINE_ISLAND_CSS`).
 *
 * Same paper/ink/ochre, same serif display + sans body + mono folio, same
 * ticket-stub 2px radii and 3px ink tray top as `.tm-timetable` /
 * `.tm-departure`. Keep the two files in sync; the iframe rail is the
 * visual fallback if this component fails to load.
 *
 * Ported motion + rail logic from evilrabbit/lifeline (MIT).
 */

export const railTokens = {
  bg: "#F7F4EF",
  surface: "#FFFCF8",
  ink: "#1C1B19",
  muted: "#6B6560",
  line: "#D9D2C7",
  lineStrong: "#b9b0a2",
  dash: "#A39A8E",
  accent: "#C47B2D", // shared with newsprint --tm-accent
  accentInk: "#A35F14",
  accentSoft: "#FBF3E8",
  ok: "#2F6F4E",
  danger: "#8B3A2F",
  hole: "#A39A8E",
  font: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", "PingFang SC", "Microsoft YaHei", sans-serif',
  serif: '"Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, "Times New Roman", serif',
  mono: '"SF Mono", ui-monospace, Menlo, Consolas, monospace',
  markerFadeMs: 420,
  railDrawMs: 900,
  staggerMs: 70,
  stopWidthPx: 132,
  shieldWidthPx: 92,
} as const;

export type RailTokens = typeof railTokens;

/**
 * Night paper for the rail island. Mirrors `DARK_ISLAND_VARS` in
 * `src/llm_time_machine/ui/theme.py` — keep the two in sync.
 * Activated by `body.ll-dark` (forced) or `prefers-color-scheme` (auto).
 */
export const railDarkTokens = {
  bg: "#171310",
  surface: "#262017",
  ink: "#F2EBDF",
  muted: "#B4A78F",
  line: "#3E362A",
  lineStrong: "#5A4F3D",
  dash: "#8D8070",
  accent: "#D99945",
  accentInk: "#E5B263",
  accentSoft: "rgba(217, 153, 69, 0.13)",
  ok: "#82BC93",
  danger: "#DA8D7E",
  hole: "#8D8070",
} as const;

export type RailDarkTokens = typeof railDarkTokens;
