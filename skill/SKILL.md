---
name: solana-position-manager
description: Manage Solana concentrated-liquidity (CLMM/DLMM) LP positions across Orca Whirlpools, Raydium CLMM, and Meteora DLMM, plus the constant-product baselines (Raydium CPMM, Meteora DAMM v2). Track impermanent loss, detect out-of-range positions, and decide + execute rebalances. Use when the user asks about liquidity providing, LP positions, concentrated liquidity, impermanent loss, range management, or rebalancing on Solana.
license: MIT
compatibility: claude-code, codex
metadata:
  orca-whirlpools: "@orca-so/whirlpools 8.x"
  raydium-clmm: "raydium-sdk-v2 0.2.55"
  meteora-dlmm: "@meteora-ag/dlmm 1.9.10"
  meteora-damm-v2: "@meteora-ag/cp-amm-sdk 1.4.4"
  verified: 2026-06-26
---

# Solana Position Manager Skill

A production-grade, cross-domain skill for managing concentrated-liquidity (CLMM/DLMM) positions on Solana. It turns a coding agent into an expert liquidity manager: **measure → monitor → rebalance**, with real math, current SDK calls, and safe execution rules.

This skill is an **addon** that extends the core `solana-dev-skill` (program/CLI/testing fundamentals). It does not duplicate core dev knowledge — it layers position-management expertise on top.

> **Verify before you author.** Solana SDKs and program IDs drift. Do not author SDK calls, account layouts, or program IDs from memory — re-read the relevant protocol file below and confirm the version/ID against the upstream repo before generating code. If a value cannot be confirmed, mark it `UNVERIFIED` rather than inventing one.

## What this skill is NOT

- **Not a swap / aggregation skill** — it does not trade; use the kit's `jupiter`/`orca` swap skills for swaps. This skill manages *positions* (range, IL, rebalance), not routing.
- **Not a static security auditor** — it gives rebalance *decisions* and execution *recipes*, not program audits. Use the kit's auditor skills for security review.
- **Not a tx-landing / priority-fee tool** — it builds rebalance transactions; landing them is the kit's tx-landing skill's job.
- **Does not actively manage constant-product pools** — Raydium CPMM and Meteora DAMM v2 are λ=1 (no concentration → no range/rebalance value). This skill covers their fetch/fees/claim lifecycle and redirects range/rebalance questions to the v2 case. See `impermanent-loss.md` §4.
- This skill gives **analysis and code**; it does not custody keys or hold positions. All signing stays with the user's wallet.

## When to load this skill

Load the focused files below **only when the task needs them** (progressive, token-efficient loading). Do not read every file upfront.

| Task / intent | Load this | Then this |
|---|---|---|
| "Where are my positions?" / fetch a position | [`whirlpools.md`](whirlpools.md) · [`raydium-clmm.md`](raydium-clmm.md) · [`meteora-dlmm.md`](meteora-dlmm.md) · [`meteora-damm-v2.md`](meteora-damm-v2.md) (pick the protocol) | — |
| "Am I in range?" / out-of-range check | the protocol file above | [`range-alerts.md`](range-alerts.md) |
| "What's my impermanent loss?" | [`impermanent-loss.md`](impermanent-loss.md) | the protocol file (for current tick/price) |
| "Which range width? / IL by range" | [`benchmarks.md`](benchmarks.md) | [`impermanent-loss.md`](impermanent-loss.md) |
| "Should I rebalance?" / rebalance plan | [`rebalance.md`](rebalance.md) | [`range-alerts.md`](range-alerts.md) |
| "Execute the rebalance" | [`rebalance.md`](rebalance.md) | the protocol file (SDK tx order) + [`../rules/safe-rebalance.md`](../rules/safe-rebalance.md) |
| "Set up alerts / monitoring" | [`monitoring.md`](monitoring.md) | [`range-alerts.md`](range-alerts.md) |
| "Auto-alert via Claude Code hook" | [`hooks.md`](hooks.md) | [`monitoring.md`](monitoring.md) |
| "Backtest this range" / fee APR vs HODL | [`backtest.md`](backtest.md) | [`impermanent-loss.md`](impermanent-loss.md) |
| "Links / SDK packages / program IDs" | [`resources.md`](resources.md) | — |
| "Is this AMM concentrated?" / CPMM · DAMM v2 | [`raydium-cpmm.md`](raydium-cpmm.md) · [`meteora-damm-v2.md`](meteora-damm-v2.md) | [`impermanent-loss.md`](impermanent-loss.md) (λ=1 v2 case) |

## Protocols covered — the full Solana AMM landscape

**Concentrated (fetch + measure + rebalance-decide for all three; executable rebalance for DLMM, SDK-correct recipes for Orca/Raydium):**

- **Orca Whirlpools** — tick-range CLMM, static tiered fees. → [`whirlpools.md`](whirlpools.md)
- **Raydium CLMM** — tick-range CLMM, Position NFT, static tiered fees. → [`raydium-clmm.md`](raydium-clmm.md)
- **Meteora DLMM** — discrete **bin**-based liquidity, dynamic volatility-aware fees, native limit orders. → [`meteora-dlmm.md`](meteora-dlmm.md)

**Constant-product (scope-clarified — the v2 baseline, λ = 1):**

- **Raydium CPMM** — constant-product, fungible LP, no concentration; the full-range case of every formula. → [`raydium-cpmm.md`](raydium-cpmm.md)
- **Meteora DAMM v2** — constant-product, NFT positions; fetch / fees / claim in scope, range/rebalance redirect to the v2 case. → [`meteora-damm-v2.md`](meteora-damm-v2.md)

> A position manager's value comes from concentration (λ > 1). CPMM and DAMM v2 are λ = 1, so this skill covers their fetch/fees/claim lifecycle but does not pretend range management applies. See [`impermanent-loss.md`](impermanent-loss.md) §4.

## Core loop

```
1. FETCH   positions + current pool tick/active bin   (protocol file)
2. MEASURE in-range? IL? accrued fees? fee-to-principal?   (impermanent-loss.md, range-alerts.md)
3. DECIDE  rebalance? widen / move / withdraw?   (rebalance.md heuristics)
4. EXECUTE simulate → sign → confirm, with safety rules   (rebalance.md + rules/safe-rebalance.md)
5. MONITOR set alerts so step 1 runs on a schedule   (monitoring.md)
```

## The math (the one thing to get right)

The same factor that boosts fee APR boosts IL. For a symmetric range `[1/k, k]`:

```python
# examples/il_math.py — two independent paths that must agree (test_il.py cross-checks)
IL_v2(r) = 2*sqrt(r)/(1+r) - 1                 # full-range; r = P/P0
lambda(k) = sqrt(k)/(sqrt(k) - 1)              # capital-efficiency = IL multiplier
IL_v3(r) = lambda(k) * IL_v2(r)                # concentrated (valid while r in (1/k, k))
```

Range `[0.5, 2.0]` (λ≈3.4) on a +21% move → −1.54% IL; tight `[0.8, 1.25]` (λ≈9.5) on the same move → −4.28% IL. Implemented in `examples/il_math.py` and pinned by `tests/test_il.py` (incl. a `compute_il`-vs-`il_v3_symmetric` cross-check so the two paths cannot silently diverge).

## Expected output shape

A position report or rebalance plan from this skill should be structured as:

- **Positions table**: protocol · range · current tick/price · in-range (GREEN/YELLOW/RED) · accrued fees · fee-to-principal.
- **IL**: V_LP / V_HODL / IL% vs HODL, with the price ratio and whether the position is in range.
- **Decision**: HOLD / WIDEN / MOVE / WITHDRAW, with the reason (drift band + fee-vs-IL gate).
- **Execution recipe** (if rebalancing): the SDK instruction order for the protocol, flagged simulate-only until the user signs.
- **Caveats**: data freshness, assumptions, open questions.

## Agents & commands bundled

- Agents: `position-analyst` (opus — deep IL/strategy), `rebalance-engineer` (sonnet — SDK tx execution). See [`../agents/`](../agents).
- Commands: `/check-positions`, `/il-report`, `/rebalance-suggest`, `/monitor-setup`. See [`../commands/`](../commands).
- Rules (auto-load): [`../rules/safe-rebalance.md`](../rules/safe-rebalance.md), [`../rules/position-data-freshness.md`](../rules/position-data-freshness.md).

## Rules of engagement

- **Never** execute a rebalance without first simulating the transaction (or dry-running the quote). See [`../rules/safe-rebalance.md`](../rules/safe-rebalance.md).
- **Always** confirm price/tick freshness before measuring IL — stale ticks produce wrong IL. See [`../rules/position-data-freshness.md`](../rules/position-data-freshness.md).
- This skill gives **analysis and code**; it does not custody keys or hold positions. All signing stays with the user's wallet.

## Provenance

- SDK versions + program IDs in the frontmatter and [`resources.md`](resources.md) were verified against each protocol's repo on 2026-06-26. If a version/ID drifts, update it and bump the `verified:` date — do not author from memory.
- Math: [`impermanent-loss.md`](impermanent-loss.md) (first-principles derivation, verified by reduction to v2 on full-range); executable in [`../examples/il_math.py`](../examples/il_math.py); pinned by [`../tests/test_il.py`](../tests/test_il.py) + the quantified eval [`../tests/test_eval.py`](../tests/test_eval.py) (see [`../docs/EVAL.md`](../docs/EVAL.md)).
