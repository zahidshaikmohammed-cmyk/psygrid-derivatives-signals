"""Live terminal monitor. Prints decisions, never raw JSON.

Colours (ANSI; enabled on Windows 10+ consoles automatically):
    green = BUY CALL, red = BUY PUT, yellow = WATCH / warnings, normal = NO TRADE.
Use --ascii for consoles without UTF-8 (replaces ✓ ✗ ₹ ═ ● with ASCII).
"""

from __future__ import annotations

import os
import sys

from .signal_engine import CycleResult, IndexDecision
from .signal_state import Signal

RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"
GREEN, RED, YELLOW, CYAN, MAGENTA = "\033[92m", "\033[91m", "\033[93m", "\033[96m", "\033[95m"


def enable_windows_ansi() -> bool:
    if os.name != "nt":
        return True
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        h = k32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if not k32.GetConsoleMode(h, ctypes.byref(mode)):
            return False
        return bool(k32.SetConsoleMode(h, mode.value | 0x0004))
    except Exception:
        return False


def configure_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


class Monitor:
    def __init__(self, color: bool = True, ascii_only: bool = False, clear: bool = True, recent: int = 8,
                 diagnostic: bool = False):
        self.color = color
        self.clear = clear
        self.recent = recent
        self.diagnostic = diagnostic
        if ascii_only:
            self.sym = {"Y": "[+]", "N": "[x]", "~": "[~]", "-": "[-]", "rs": "Rs ", "major": "=",
                        "minor": "-", "dot": "*", "hr": "=", "sep": "-", "arrow": "<-", "to": "->"}
        else:
            self.sym = {"Y": "[✓]", "N": "[✗]", "~": "[~]", "-": "[–]", "rs": "₹", "major": "═",
                        "minor": "─", "dot": "●", "hr": "═", "sep": "─", "arrow": "←", "to": "→"}

    def c(self, text: str, *codes: str) -> str:
        if not self.color or not codes:
            return text
        return "".join(codes) + text + RESET

    # ---------------------------------------------------------------- render
    def render(self, res: CycleResult, recent_events: list) -> str:
        W = 64
        hr = self.sym["hr"] * W
        out = [hr, self.c("PSYGRID OPTIONS ENGINE v1.0", BOLD) + "   (signals only — no orders)",
               f"{res.ref_time:%d-%m-%Y %H:%M:%S} IST   session: {res.phase}", hr]
        if res.clock_note:
            out.append(self.c(res.clock_note, YELLOW))
        summary = []
        for idx, d in res.decisions.items():
            out += self.index_block(d)
            out.append(self.sym["sep"] * W)
            summary.append(self._summary_line(d))
        out.append(self.c("SUMMARY", BOLD))
        out += summary
        if recent_events:
            out.append(self.sym["sep"] * W)
            out.append(self.c("RECENT SIGNAL EVENTS", BOLD))
            for e in recent_events[-self.recent:]:
                out.append(f"  {e.ts:%H:%M:%S} {e.text}")
        out.append(hr)
        return "\n".join(out)

    def show(self, res: CycleResult, recent_events: list) -> None:
        text = self.render(res, recent_events)
        if self.clear:
            sys.stdout.write("\033[2J\033[H" if self.color else "\n" * 3)
        sys.stdout.write(text + "\n")
        sys.stdout.flush()

    def _summary_line(self, d: IndexDecision) -> str:
        label = {"BUY_CALL": "BUY CALL", "BUY_PUT": "BUY PUT", "SIGNAL_ACTIVE": "ACTIVE",
                 "WATCH": "WATCH", "NO_TRADE": "WAIT", "DATA_GATE_BLOCKED": "BLOCKED",
                 "MARKET_CLOSED": "CLOSED", "WARMING_UP": "WARMING UP"}[d.status]
        why = (d.reasons[:1] or d.waiting[:1] or [""])[0]
        if d.status == "NO_TRADE" and d.waiting and why.startswith("no valid setup"):
            why = d.waiting[0]
        if d.signal is not None:
            s = d.signal
            why = (f"{s.strike:,.0f} {s.option_type} @ {s.option_ltp:,.2f}  {s.setup}  Q{s.score:.0f}")
        elif d.status == "SIGNAL_ACTIVE" and d.active:
            why = f"{d.active.direction} {d.active.strike:,.0f} {d.active.option_type} {d.active.state}"
        line = f"  {d.index:<10}: {label:<10} — {why}"
        col = {"BUY_CALL": GREEN, "BUY_PUT": RED, "WATCH": YELLOW, "DATA_GATE_BLOCKED": YELLOW}.get(d.status)
        return self.c(line[:140], col) if col else line[:140]

    # ------------------------------------------------------------ per index
    def index_block(self, d: IndexDecision) -> list[str]:
        px = f"{d.price:,.2f}" if d.price else "n/a"
        out = [self.c(f"{d.index}", BOLD, CYAN) + f"   {px}"
               + (f"   [{d.gate.underlying_source}]" if d.gate and d.gate.underlying_source else "")]
        out += self.feed_lines(d)
        if d.status == "MARKET_CLOSED":
            out.append(self.c("MARKET CLOSED", BOLD) + f" — {d.headline}")
            return out
        if d.status == "DATA_GATE_BLOCKED":
            out.append(self.c("DATA GATE BLOCKED — TRADING AUTHORIZATION = BLOCKED", BOLD, YELLOW))
            for r in d.reasons:
                out.append(f"  reason: {r}")
            return out
        if d.signal is not None:
            out += self.signal_block(d.signal)
            out += self.level_map(d)
            return out
        out += self.level_map(d)
        if d.status == "WARMING_UP":
            out.append(self.c("DATA NOT READY — WARMING UP", BOLD, YELLOW) + f": {'; '.join(d.reasons)}")
            cov = d.coverage
            if cov.get("bars"):
                out.append(f"  bars: {cov['bars']} ({cov.get('feed', 0)} feed, {cov.get('internal', 0)} "
                           f"internally aggregated), first {cov['first']:%H:%M}")
            return out
        if d.status == "SIGNAL_ACTIVE" and d.active and d.signal is None:
            a = d.active
            col = GREEN if a.direction == "CALL" else RED
            out.append(self.c(f"SIGNAL ACTIVE: BUY {a.direction} {a.strike:,.0f} {a.option_type} — {a.state}", BOLD, col))
            out.append(f"  since {a.created:%H:%M:%S}  stop {a.stop:,.2f}  T1 {a.t1:,.2f}  T2 {a.t2:,.2f}"
                       f"  Q{a.score:.0f}")
        elif d.status == "WATCH" and d.best:
            b = d.best
            out.append(self.c(f"WATCH — {b.cand.direction} candidate: {b.cand.setup} "
                              f"(quality {b.score.score:.0f}/100)", BOLD, YELLOW))
            trace = self.trace_lines(d)
            if trace:
                out += trace
            else:
                for r in d.reasons[:3]:
                    out.append(f"  not yet: {r}")
        elif d.status == "NO_TRADE":
            out.append(self.c("NO TRADE", BOLD))
            trace = self.trace_lines(d)
            if trace:
                out += trace
            else:
                for r in d.reasons[:2]:
                    out.append(f"  reason: {r}")
        for w in d.waiting[:3]:
            out.append(f"  waiting for: {w}")
        for c in d.candidates[:3]:
            out.append(self.c(f"  candidate: {c}", DIM))
        return out

    def trace_lines(self, d: IndexDecision) -> list[str]:
        """Renders IndexDecision.trace (diagnostics.py) so a repeated
        NO_TRADE/WATCH is diagnosable ("genuinely no setup" vs "setup
        detected, waiting on confirmation N/M, M points below threshold")
        instead of only a single truncated reason string. Compact by
        default; --diagnostic shows the full per-confirmation breakdown."""
        t = d.trace
        if t is None or not t.setup_detected:
            return []
        out = [f"  {t.direction} SETUP: {t.setup}   Score: {t.score:.0f}/100  Required: {t.signal_threshold:.0f}",
               f"  Confirmations: {len(t.passing)}/{t.confirmations_required}"]
        if self.diagnostic:
            for c in t.confirmations:
                mark = self.sym["Y"] if c.passed else self.sym["N"]
                val = f"{c.value:+.2f}" if c.value is not None else "n/a"
                out.append(f"  {mark} {c.label:<28} {val}  {c.detail[:60]}")
        else:
            if t.passing:
                out.append("  PASS: " + ", ".join(t.passing))
            if t.missing:
                out.append("  MISSING: " + ", ".join(t.missing))
        if t.blocking:
            n = 3 if self.diagnostic else 2
            out.append(self.c("  BLOCKING: " + "; ".join(t.blocking[:n]), DIM)[:200])
        if t.conflicts:
            out.append(self.c("  CONFLICTS: " + ", ".join(t.conflicts), YELLOW))
        if not t.risk_pass and t.risk_reason:
            out.append(self.c(f"  RISK BLOCKED: {t.risk_reason}"[:160], DIM))
        if t.near_miss_points is not None:
            out.append(self.c(f"  NEAR-MISS: {t.near_miss_points:.1f} points below threshold", YELLOW))
        return out

    def feed_lines(self, d: IndexDecision) -> list[str]:
        if d.gate is None:
            return []
        parts = []
        for f, fc in d.gate.feeds.items():
            col = {"OK": GREEN, "DEGRADED": YELLOW, "BLOCKED": RED}[fc.state]
            parts.append(f"{f}:" + self.c(fc.state, col))
        lines = ["  feeds " + "  ".join(parts) + f"   data quality {d.gate.data_quality:.2f}"]
        for f, fc in d.gate.feeds.items():
            if fc.state != "OK" and fc.reasons:
                lines.append(self.c(f"    {f} {fc.state.lower()}: {'; '.join(fc.reasons)}"[:240], DIM))
        return lines

    def level_map(self, d: IndexDecision) -> list[str]:
        lm, st = d.levels, d.structure
        if lm is None:
            return []
        out = []
        zones = lm.display_zones(6)
        above = [z for z in zones if z.low > lm.price]
        below = [z for z in zones if z.high < lm.price]
        inside = [z for z in zones if z.low <= lm.price <= z.high]

        def row(z):
            bar = (self.sym["major"] if z.tier == 1 else self.sym["minor"]) * 9
            tag = f"  {self.sym['arrow']} {z.state}" if z.state not in ("UNTESTED",) else ""
            band = f"{z.low:,.0f}–{z.high:,.0f}" if z.high - z.low >= 1 else f"{z.center:,.0f}"
            return (f"  {z.center:>9,.0f}  {bar}  {z.strength:3.0f}/100  T{z.tier}  {band:<15} "
                    f"{z.role_label}{tag}")

        if above:
            out.append(self.c("  RESISTANCE", RED))
            out += [row(z) for z in sorted(above, key=lambda z: -z.center)]
        if inside:
            out.append(self.c("  AT PRICE", YELLOW))
        for z in inside:
            out.append(self.c(row(z), YELLOW))
        out.append(f"  {lm.price:>9,.2f}  {self.sym['dot']}  PRICE")
        if below:
            out.append(self.c("  SUPPORT", GREEN))
            out += [row(z) for z in sorted(below, key=lambda z: -z.center)]
        if not zones:
            out.append("  (no tier-1/2 levels yet)")
        extras = []
        if st and st.vwap is not None:
            extras.append(f"VWAP {st.vwap:,.1f} ({'above' if lm.price > st.vwap else 'below'})")
        if st and st.ready:
            extras.append(f"trend {st.trend}, momentum {st.momentum:+.1f}")
        if extras:
            out.append("  " + " | ".join(extras))
        for r in lm.relations[:2]:
            out.append(f"  STATE: {r}")
        if lm.unavailable:
            out.append(self.c("  unavailable: " + "; ".join(lm.unavailable[:3]), DIM))
        return out

    def signal_block(self, s: Signal) -> list[str]:
        col = GREEN if s.direction == "CALL" else RED
        rs = self.sym["rs"]
        out = [self.c(f">>> BUY {s.direction} <<<", BOLD, col),
               f"Strike       : {s.strike:,.0f} {s.option_type}",
               f"Option LTP   : {rs}{s.option_ltp:,.2f}  (bid {s.bid:,.2f} / ask {s.ask:,.2f}, "
               f"spread {s.spread_pct:.2f}%)",
               f"Underlying   : {s.underlying:,.2f}",
               f"SETUP        : {s.setup}",
               f"KEY LEVEL    : {s.key_level_price:,.0f}" + (f" ({s.key_level_id})" if s.key_level_id else ""),
               f"LEVEL TYPE   : {s.level_type}",
               f"LEVEL STRENGTH: {s.level_strength:.0f}/100" if s.level_strength is not None else
               "LEVEL STRENGTH: n/a (structural)",
               f"MARKET STATE : {s.market_state}",
               f"Entry        : {rs}{s.entry_low:,.2f}–{s.entry_high:,.2f}",
               f"Invalidation : {s.index} {s.invalidation:,.2f}"
               + (f"  (option est. {rs}{s.option_invalidation:,.2f})" if s.option_invalidation else ""),
               f"Target 1     : {s.index} {s.t1:,.2f}" + (f"  (option est. {rs}{s.option_t1:,.2f})" if s.option_t1 else ""),
               f"Target 2     : {s.index} {s.t2:,.2f}" + (f"  (option est. {rs}{s.option_t2:,.2f})" if s.option_t2 else ""),
               f"R:R (T1)     : {s.reward_risk:.2f}   targets from {s.target_basis}",
               f"EXPECTED HOLD: {s.holding}",
               self.c(f"QUALITY      : {s.score:.0f}/100", BOLD) + "  (confluence score, not a probability)",
               f"Time         : {s.created:%d-%m-%Y %H:%M:%S} IST",
               "CONFIRMATION"]
        for label, mark, detail in s.confirmations:
            out.append(f"{self.sym[mark]} {label:<32} {detail[:60]}")
        out.append("EVIDENCE")
        for e in s.evidence:
            out.append(f"  - {e}")
        out.append("STRIKE SELECTION")
        for r in s.strike_reasons[:5]:
            out.append(f"  - {r}")
        for n in s.notes:
            out.append(self.c(f"  note: {n}", DIM))
        return out
