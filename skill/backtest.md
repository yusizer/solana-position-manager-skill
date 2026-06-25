# Backtest & Evaluation

How to evaluate whether a range (or a rebalance policy) was actually good. Backtesting concentrated LP is about comparing three curves over a historical window: **LP value with fees**, **HODL**, and **fees-only cumulative**. This file gives the metrics and the data sources; the math is in `impermanent-loss.md`.

## 1. The three curves

Over a window \([t_0, t_n]\) at a fixed cadence (e.g. every 5 min):
- \(V_{LP}(t)\) — position value (in range amounts, §2 of `impermanent-loss.md`) **plus** cumulative collected fees.
- \(V_{HODL}(t)\) — the open amounts held idle, valued at the price at \(t\).
- \(F(t)\) — cumulative fees collected (USD), the income stream.

## 2. Core metrics

| Metric | Definition | Use |
|---|---|---|
| **Return vs HODL** | \(V_{LP}(t_n)/V_{HODL}(t_n) - 1\) | Did LPing beat holding? The bottom line. |
| **Fee APR** | \(F(t_n) / \text{principal} \times (365/\text{days})\) | Income rate; compare across ranges. |
| **Realised IL** | \(\min_t (V_{LP,\text{excl fees}}/V_{HODL} - 1)\) or end-of-window IL | The cost side. |
| **Time in range** | fraction of window the position was in range | High APR but low time-in-range ⇒ you rebalanced too late. |
| **Rebalance cost ratio** | total gas+slippage / total fees | >15% ⇒ over-rebalancing. |
| **Max drawdown vs HODL** | worst \(V_{LP}/V_{HODL} - 1\) in window | Risk gauge for a range. |

A good range: Return vs HODL > 0, fee APR competitive, rebalance cost ratio < 10%, time-in-range > 80%.

## 3. Decision-quality, not just range-quality

Backtest the **policy**, not just one static range:
- Replay a rebalance rule (e.g. "MOVE when drift > 0.95") over history and compare total return + rebalance count vs a static range.
- Sweep thresholds (0.90 / 0.95 / 0.98) and widths to find the policy that maximises return-vs-HODL per rebalance.

## 4. Historical data sources

- **On-chain ticks/price history:** Helius RPC (getSignaturesFor + parsed tx logs, or `getTokenLargestAccounts`/price via DAS) — reconstruct tick series from swap events. Helius also exposes parsed transaction history.
- **Price series (aggregated):** Birdeye, GeckoTerminal, Jupiter Price API v3 — for token0/token1 price at each timestamp.
- **Fee accrual:** parse the pool's `feeGrowthGlobal` deltas between snapshots (Orca/Raydium tick-level; Meteora per-bin) — see protocol files for field names.
- **Slot/time alignment:** anchor every sample by Solana slot, then map to UTC via `blockTime`.

## 5. A minimal backtest skeleton

```
for t in cadence(t0, tn):
    price[t]  = fetch_price(token0, token1, slot=t)          # Birdeye/Helius
    tick[t]   = fetch_pool_tick(pool, slot=t)                 # RPC snapshot
    in_range  = tick[t] in [tl, tu]
    fees[t]   = feeGrowth_delta(t) * liquidity_share         # protocol-specific
    V_LP[t]   = lp_value(price[t], tick[t], range) + cum_fees
    V_HODL[t] = hodl_value(open_amounts, price[t])
report: return_vs_hodl, fee_apr, time_in_range, max_dd, rebalance_count
```

Caveat: past fee/IL performance is a weak predictor for a different volatility regime — report the window's realised volatility alongside the metrics so the user can sanity-check regime fit.

## 6. Common pitfalls

- **Survivorship:** a range that looked great because price sat still will look great in backtest but earn nothing in a real volatile regime. Always pair APR with time-in-range and realised vol.
- **Ignoring rebalance costs** in the replay — the static-range curve always wins unless you charge the round-trip.
- **Stale-price leakage** — sampling price and tick from different sources at "the same" timestamp can misattribute IL. Align by slot.
