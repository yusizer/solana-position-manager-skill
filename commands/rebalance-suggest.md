---
description: Recommend a rebalance action (hold/widen/move/withdraw) for a CLMM/DLMM position, with reasoning and expected fee/IL delta.
argument-hint: <position-pubkey or identifier>
---

Recommend a rebalance decision for position `$ARGUMENTS`.

Procedure:
1. Delegate the **measure + decide** work to the `position-analyst` agent (it loads the protocol file, `skill/impermanent-loss.md`, `skill/range-alerts.md`, `skill/rebalance.md`).
2. Produce a recommendation in exactly one of: `HOLD`, `WIDEN`, `MOVE`, `WITHDRAW`.
3. For non-HOLD recommendations, sketch the proposed new range (or withdraw target) and the expected deltas:
   - Expected fee accrual change (APR up/down, rationale).
   - Expected IL change.
   - Estimated gas / round-trip cost in USD.
4. Cite the heuristic from `skill/rebalance.md` that drove the decision.
5. If the recommendation is to execute, end with: *"Run `/check-positions` then ask the rebalance-engineer to execute, or approve here."*

Never skip `rules/safe-rebalance.md` and `rules/position-data-freshness.md`. If data is stale or the analysis fails twice, stop and surface the errors.
