# Range & Threshold Alerts

When to flag a position. These heuristics turn raw tick/bin state into a small set of actionable signals. Pair with the protocol file (for how to read current tick / active bin) and `impermanent-loss.md` (for the IL number).

## 1. In-range vs out-of-range

**Tick model (Orca Whirlpools, Raydium CLMM):** a position with range \([t_l, t_u]\) (tick indices) is **in range** while the pool's current tick \(t_c\) satisfies \(t_l \le t_c < t_u\). Out of range the moment \(t_c\) leaves that interval — the position holds only one token and earns **zero** trading fees.

**Bin model (Meteora DLMM):** a position spanning bins \([b_l, b_u]\) is earning fees only on the **active bin** \(b_a\); it is "out of range" when \(b_a < b_l\) or \(b_a > b_u\). Within range but far from \(b_a\), only the bins near the active one earn.

## 2. Distance-from-edge (drift) alert

Don't wait for a full exit — alert as the position approaches an edge so a rebalance can be planned, not emergency-executed.

- **Green:** current tick/bin in the middle 60% of the range.
- **Yellow:** within the outer 20% of either edge → plan a rebalance (run `/rebalance-suggest`), no rush.
- **Red:** within the outer 5% of an edge, or already out of range → act now (fees about to stop / already stopped).

Compute drift as the fraction of the range between current and nearest edge:

\[
\text{drift} = \frac{t_c - t_l}{t_u - t_l} \in [0,1]\quad(\text{tick model})
\]

`drift < 0.05` or `> 0.95` → Red. `0.05–0.20` or `0.80–0.95` → Yellow.

## 3. Fee-to-principal ratio alert

The single best "is this position still worth it?" number:

\[
\text{feeRatio} = \frac{\text{uncollected fees (USD)}}{\text{principal value (USD)}}
\]

- Compare `feeRatio` against the position's IL (from `impermanent-loss.md`).
- **Net-positive flag:** `feeRatio + expected_near_term_fees > |IL|` → keep.
- **Net-negative flag:** `feeRatio < |IL|` **and** out-of-range-imminent → strong candidate to withdraw or rebalance.

Alert thresholds (tune per pool volatility):
- `feeRatio < 0.5%` after >7 days in a volatile pool → underperforming; review.
- `feeRatio` growing < IL growth over the last interval → fees not keeping up; review.

## 4. Zero-fee-while-in-range alert

A position that is **in range but accruing no fees** over a meaningful window (e.g. >1h on an active pool) signals stale data or a broken fetch — not a market condition. Treat as `DATA_STALE` (`../rules/position-data-freshness.md`), not as a rebalance trigger.

## 5. Out-of-range-but-still-earning (DLMM only)

On Meteora DLMM, bins adjacent to the active bin still earn when volatility sweeps the active bin back and forth. A "technically out of range" position with bins hugging the active bin may still accrue fees. Before flagging Red on DLMM, check **actual fee accrual over the last N slots**, not just bin index distance.

## 6. Alert output contract

Every alert carries: position id, protocol, signal (Green/Yellow/Red + which), `drift`, `feeRatio`, `IL%`, tick/bin age, and the recommended next command (`/il-report`, `/rebalance-suggest`, or nothing). Keep it one line per position so a monitor (`monitoring.md`) can emit a clean stream.
