---
name: solana-position-manager
description: Manage Solana CLMM/DLMM liquidity positions across Orca Whirlpools, Raydium CLMM, and Meteora DLMM — track impermanent loss, detect out-of-range positions, and decide + execute rebalances. Use when the user asks about liquidity providing, LP positions, concentrated liquidity, impermanent loss, range management, or rebalancing on Solana.
---

# Solana Position Manager Skill

A production-grade, cross-domain skill for managing concentrated-liquidity (CLMM/DLMM) positions on Solana. It turns a coding agent into an expert liquidity manager: **measure → monitor → rebalance**, with real math, current SDK calls, and safe execution rules.

This skill is an **addon** that extends the core `solana-dev-skill` (program/CLI/testing fundamentals). It does not duplicate core dev knowledge — it layers position-management expertise on top.

## When to load this skill

Load the focused files below **only when the task needs them** (progressive, token-efficient loading). Do not read every file upfront.

| Task / intent | Load this | Then this |
|---|---|---|
| "Where are my positions?" / fetch a position | [`whirlpools.md`](whirlpools.md) · [`raydium-clmm.md`](raydium-clmm.md) · [`meteora-dlmm.md`](meteora-dlmm.md) (pick the protocol) | — |
| "Am I in range?" / out-of-range check | the protocol file above | [`range-alerts.md`](range-alerts.md) |
| "What's my impermanent loss?" | [`impermanent-loss.md`](impermanent-loss.md) | the protocol file (for current tick/price) |
| "Should I rebalance?" / rebalance plan | [`rebalance.md`](rebalance.md) | [`range-alerts.md`](range-alerts.md) |
| "Execute the rebalance" | [`rebalance.md`](rebalance.md) | the protocol file (SDK tx order) + [`../rules/safe-rebalance.md`](../rules/safe-rebalance.md) |
| "Set up alerts / monitoring" | [`monitoring.md`](monitoring.md) | [`range-alerts.md`](range-alerts.md) |
| "Backtest this range" / fee APR vs HODL | [`backtest.md`](backtest.md) | [`impermanent-loss.md`](impermanent-loss.md) |
| "Links / SDK packages / program IDs" | [`resources.md`](resources.md) | — |

## Protocols covered

- **Orca Whirlpools** — tick-range CLMM, static tiered fees. → [`whirlpools.md`](whirlpools.md)
- **Raydium CLMM** — tick-range CLMM, Position NFT, static tiered fees. → [`raydium-clmm.md`](raydium-clmm.md)
- **Meteora DLMM** — discrete **bin**-based liquidity, dynamic volatility-aware fees, native limit orders. → [`meteora-dlmm.md`](meteora-dlmm.md)

## Core loop

```
1. FETCH   positions + current pool tick/active bin   (protocol file)
2. MEASURE in-range? IL? accrued fees? fee-to-principal?   (impermanent-loss.md, range-alerts.md)
3. DECIDE  rebalance? widen / move / withdraw?   (rebalance.md heuristics)
4. EXECUTE simulate → sign → confirm, with safety rules   (rebalance.md + rules/safe-rebalance.md)
5. MONITOR set alerts so step 1 runs on a schedule   (monitoring.md)
```

## Agents & commands bundled

- Agents: `position-analyst` (opus — deep IL/strategy), `rebalance-engineer` (sonnet — SDK tx execution). See [`../agents/`](../agents).
- Commands: `/check-positions`, `/il-report`, `/rebalance-suggest`, `/monitor-setup`. See [`../commands/`](../commands).
- Rules (auto-load): [`../rules/safe-rebalance.md`](../rules/safe-rebalance.md), [`../rules/position-data-freshness.md`](../rules/position-data-freshness.md).

## Rules of engagement

- **Never** execute a rebalance without first simulating the transaction (or dry-running the quote). See [`../rules/safe-rebalance.md`](../rules/safe-rebalance.md).
- **Always** confirm price/tick freshness before measuring IL — stale ticks produce wrong IL. See [`../rules/position-data-freshness.md`](../rules/position-data-freshness.md).
- This skill gives **analysis and code**; it does not custody keys or hold positions. All signing stays with the user's wallet.
