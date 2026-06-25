# Rule: safe-rebalance

Auto-loads when any file references rebalance execution. These gates are mandatory; an agent must not execute a rebalance transaction without satisfying every one.

## Gates (all must pass)

1. **Simulate-or-abort.** The full tx sequence (withdraw → optional reopen → collect) must be simulated/dry-run and the quote shown to the user *before* signing. No simulate, no sign.
2. **Minimum cooldown.** Do not rebalance the same position more than once per `REBALANCE_COOLDOWN_MIN` (default 240 minutes / one epoch-ish window) unless the position is fully out of range and earning zero fees. Over-rebalancing burns gas faster than it earns fees.
3. **Position-size guard.** If the position is < `MIN_REBALANCE_USD` (default $250) in value, do not rebalance — gas + slippage will exceed the benefit. Report `HOLD` with a note.
4. **Fee-coverage check.** Expected fee income from the new range over the cooldown window must exceed estimated gas + slippage of the round trip. If it doesn't, report `HOLD`.
5. **Freshness re-check.** The tick/price used to build the tx must be < 60s old at sign time. If the build took longer, re-fetch and re-simulate. See `position-data-freshness.md`.
6. **User signs.** The agent never signs. After a passing simulate, present the quote and wait for explicit user approval.

## Failure handling

- If the same step fails twice in a row (Two-Strike Rule), stop, print both errors verbatim, and ask the user. Do not attempt a third time.
- Never paper over a simulate failure by retrying with different parameters silently — explain what changed and why.
