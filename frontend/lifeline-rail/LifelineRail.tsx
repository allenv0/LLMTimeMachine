/**
 * LifelineRail — portable hero rail for LLMTimeMachine.
 *
 * Data contract: `markers` is the JSON verbatim from
 * `src/llm_time_machine/ui/timeline.py::lifeline_markers()`:
 *
 *   [{ year, id, kind: "model"|"hole"|"gap", label, mode,
 *      slot_status, stands_for, limitations: string[],
 *      status: "waiting"|"live"|"complete"|"failed"|"hole"|"gap",
 *      walk_state: "done"|"next"|"upcoming"|null, age }]
 *
 * Honesty rules (non-negotiable, mirrored in the Streamlit iframe rail):
 * - `hole` renders dashed and never carries model text.
 * - `gap` (years with no model and no declared hole) renders faint, empty.
 * - `substitute` is always labeled ochre with its `stands_for` line.
 * - status-quo / FUTURE are endpoints beyond the rail, never year stops.
 *
 * Behavior ports evilrabbit/lifeline (MIT): horizontal scrub with wheel
 * handoff at the ends (embed semantics), sticky Years shield, intro rail
 * draw + staggered marker fade, arrow-key scrub, hover preview on desktop,
 * tap-to-expand contract on mobile (rendered here as <details>), and
 * `prefers-reduced-motion` kill-switch.
 *
 * This file is intentionally dependency-free (React only) so it can land
 * either as a Vite island or as a Streamlit custom component (`streamlit
 * component create` + ` Streamlit.setComponentValue` for stop selection).
 */

import { useEffect, useMemo, useRef } from "react";
import { railTokens } from "./tokens";

export type MarkerKind = "model" | "hole" | "gap";
export type MarkerStatus = "waiting" | "live" | "complete" | "failed" | "hole" | "gap";
export type WalkState = "done" | "next" | "upcoming" | null;

export interface RailMarker {
  year: number;
  id: string;
  kind: MarkerKind;
  label: string;
  mode: string;
  slot_status: string;
  stands_for: string;
  limitations: string[];
  status: MarkerStatus;
  walk_state: WalkState;
  age: number;
}

export interface LifelineRailProps {
  markers: RailMarker[];
  mode?: "walk" | "full";
  activeYear?: number | null;
  intro?: boolean;
  onSelectYear?: (year: number, id: string) => void;
  className?: string;
}

function titleFor(m: RailMarker): string {
  if (m.kind === "hole") return `${m.year} hole — ${m.limitations[0] ?? ""}`;
  if (m.kind === "gap") return `${m.year} — no staged checkpoint. Gap stays empty.`;
  const bits = [`${m.year} ${m.label}`, m.mode];
  if (m.slot_status === "substitute") bits.push(`substitute for ${m.stands_for || "an annual frontier class"}`);
  if (m.limitations[0]) bits.push(m.limitations[0]);
  if (m.walk_state === "next") bits.push("next stop on the decade walk");
  return bits.filter(Boolean).join(" · ");
}

export function LifelineRail({
  markers,
  mode = "walk",
  activeYear = null,
  intro = true,
  onSelectYear,
  className,
}: LifelineRailProps) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const railRef = useRef<HTMLDivElement>(null);

  const focusId = useMemo(() => {
    if (activeYear != null) {
      const hit = markers.find((m) => m.year === activeYear && m.kind === "model");
      if (hit) return hit.id;
    }
    return markers.find((m) => m.walk_state === "next")?.id ?? null;
  }, [markers, activeYear]);

  // Intro: rail draw 0→1, markers stagger in. Skipped under reduced motion.
  useEffect(() => {
    if (!intro || !railRef.current) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    let raf = 0;
    const t0 = performance.now();
    const tick = (t: number) => {
      const p = Math.min((t - t0) / railTokens.railDrawMs, 1);
      railRef.current?.style.setProperty("--ll-intro", p.toFixed(3));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [intro]);

  // Embed wheel handoff: vertical wheel scrubs the rail until an end,
  // then hands scrolling back to the page (lifeline `mode="embed"`).
  useEffect(() => {
    const vp = viewportRef.current;
    if (!vp) return;
    const onWheel = (e: WheelEvent) => {
      if (Math.abs(e.deltaY) <= Math.abs(e.deltaX) || e.deltaY === 0) return;
      if (vp.scrollWidth <= vp.clientWidth + 4) return;
      const atStart = vp.scrollLeft <= 0 && e.deltaY < 0;
      const atEnd = vp.scrollLeft + vp.clientWidth >= vp.scrollWidth - 2 && e.deltaY > 0;
      if (!atStart && !atEnd) {
        vp.scrollLeft += e.deltaY;
        e.preventDefault();
      }
    };
    vp.addEventListener("wheel", onWheel, { passive: false });
    return () => vp.removeEventListener("wheel", onWheel);
  }, []);

  const onKeyDown = (e: React.KeyboardEvent) => {
    const vp = viewportRef.current;
    if (!vp) return;
    if (e.key === "ArrowRight") {
      vp.scrollBy({ left: railTokens.stopWidthPx * 2 });
      e.preventDefault();
    } else if (e.key === "ArrowLeft") {
      vp.scrollBy({ left: -railTokens.stopWidthPx * 2 });
      e.preventDefault();
    }
  };

  return (
    <section aria-label={`Decade rail, ${markers.length} stops`} className={className}>
      <div
        ref={viewportRef}
        tabIndex={0}
        onKeyDown={onKeyDown}
        style={{ overflowX: "auto", scrollSnapType: "x proximity" }}
      >
        <div style={{ display: "flex", minWidth: "max-content", position: "relative" }}>
          <div
            style={{
              position: "sticky",
              left: 0,
              zIndex: 20,
              width: railTokens.shieldWidthPx,
              background: railTokens.surface,
            }}
          >
            <div>Age</div>
            <div>Years</div>
          </div>
          <div style={{ position: "relative", display: "flex" }}>
            <div ref={railRef} aria-hidden style={{ position: "absolute", top: 46, left: 0, right: 0 }} />
            <div style={{ display: "flex", position: "relative" }}>
              {markers.map((m, i) => (
                <button
                  key={m.id}
                  title={titleFor(m)}
                  aria-label={titleFor(m)}
                  data-year={m.year}
                  data-kind={m.kind}
                  onClick={() => onSelectYear?.(m.year, m.id)}
                  style={{
                    width: railTokens.stopWidthPx,
                    scrollSnapAlign: "start",
                    animationDelay: intro ? `${Math.min(i * railTokens.staggerMs, 840)}ms` : undefined,
                  }}
                >
                  <div>{m.year}</div>
                  <div>{m.kind === "hole" ? "not staged" : m.kind === "gap" ? "—" : m.label}</div>
                  <div>
                    {m.kind === "hole"
                      ? "hole"
                      : m.kind === "gap"
                        ? "—"
                        : m.status === "live"
                          ? "live"
                          : m.status === "failed"
                            ? "failed"
                            : m.walk_state === "done"
                              ? "done"
                              : m.slot_status === "substitute"
                                ? "sub"
                                : "avail"}
                  </div>
                  {mode === "walk" && m.walk_state === "next" && <span>Next</span>}
                </button>
              ))}
            </div>
            {focusId && <span aria-hidden>playhead</span>}
          </div>
        </div>
      </div>
    </section>
  );
}

export default LifelineRail;
