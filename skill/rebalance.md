# Rebalance Strategy & Heuristics

A rebalance is **withdraw → (optionally) reopen at a new range → collect fees**. The hard part is not the transaction — it is the *decision*: when to act, and what shape the new range should take. This file gives the decision tree; the protocol file gives the SDK tx order; `../rules/safe-rebalance.md` gates execution.

## 1. The four decisions

| Decision | When | One-liner |
|---|---|---|
| **HOLD** | In range, fees > IL drift, drift < 0.80 | Do nothing. The best rebalance is often no rebalance. |
| **WIDEN** | Approaching an edge, volatility high, fees decent | Withdraw + reopen with a wider range to stay in range longer; accept lower fee APR. |
| **MOVE** | Out of range (or imminent), price trend clear, want to keep tight range | Withdraw + reopen centered on the new price; keeps fee APR high but resets IL basis and pays round-trip cost. |
| **WITHDRAW** | Out of range, fees no longer offsetting IL, or capital needed elsewhere | Close position, collect fees, exit to single-sided or stable. |

## 2. Decision tree

```
1. Is the position OUT OF RANGE (Red) or drift > 0.95?
   yes → go to 3
   no  → go to 2
2. Drift 0.80–0.95 (Yellow)?
   yes → plan only: run /rebalance-suggest, do not execute yet → HOLD unless feeRatio < |IL|
   no  → HOLD
3. Out of range. Is feeRatio over the position life > |IL| + round-trip cost?
   yes → the range served its purpose. WITHDRAW (bank the win) or MOVE to re-engage.
   no  → fees not keeping up.
4. Is the pair still one you want LP exposure to (not a broken thesis)?
   yes → MOVE (re-center) if you expect mean reversion / continued volume;
         WIDEN if you expect high volatility and want fewer rebalances.
   no  → WITHDRAW.
5. Before any non-HOLD: apply ../rules/safe-rebalance.md gates.
```

## 3. Range shape heuristics

- **Center on the current price** for a MOVE; center on your *expected mean* price for a WIDEN (front-run where you think it will sit).
- **Width vs APR:** narrower range → higher fee APR but more frequent rebalances (more gas, more IL resets). Width is a lever between "high APR, high maintenance" and "low APR, set-and-forget".
- **Asymmetric ranges** when you have a directional view: shift the range up/down rather than centering, so you lean long or short of token0. Be explicit that this is a *position*, not just a fee play.
- **DLMM bins:** prefer contiguous bins hugging the active bin for fee capture; leave a few bins of buffer on the side you expect price to drift toward so you don't rebalance on the first wiggle.

## 4. Gas-vs-fees tradeoff (the core equation)

Rebalance only if expected benefit exceeds round-trip cost:

\[
\text{expectedBenefit} = \Delta\text{fees}_{\text{new range over cooldown}} - \Delta|\text{IL}|
\]
\[
\text{roundTripCost} = \text{gas (simulate-read)} + \text{slippage on reinvest} + \text{1 unit of IL-basis-reset risk}
\]

Rebalance iff `expectedBenefit > roundTripCost`. If the margin is thin, HOLD — over-rebalancing is the #1 way concentrated LPs lose to v2.

## 5. Anti-over-rebalance rules

- **Cooldown:** minimum `REBALANCE_COOLDOWN_MIN` (default 240 min) between rebalances of the same position unless fully out of range and earning zero (`../rules/safe-rebalance.md`).
- **Don't chase noise:** a single tick crossing your edge is not a rebalance trigger — require sustained drift (e.g. out of range for > N minutes, or drift past 0.95 with rising volume).
- **Batch:** if multiple positions in the same pair need rebalancing, batch the txs to share the compute budget.
- **Size guard:** positions under `MIN_REBALANCE_USD` (default $250) → HOLD (cost exceeds benefit).

## 6. Execution order (protocol-specific detail lives in the protocol file)

Generic sequence the `rebalance-engineer` follows — exact instructions per protocol:

1. Fetch fresh tick/price + position state (`../rules/position-data-freshness.md`).
2. Withdraw liquidity + collect fees (one or more txs per protocol).
3. (MOVE/WIDEN) Open the new position at the chosen range.
4. Simulate the **whole sequence** as one atomic plan before signing (`../rules/safe-rebalance.md`).
5. On approval, sign + confirm; report new range, in-range status, and post-tx IL basis.

See `whirlpools.md` / `raydium-clmm.md` / `meteora-dlmm.md` for the real SDK calls and the correct account/token ordering.
