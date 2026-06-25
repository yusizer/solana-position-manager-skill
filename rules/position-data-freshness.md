# Rule: position-data-freshness

Auto-loads when any file measures IL, fees, or in-range status. IL and fee numbers are meaningless on a stale tick — enforce freshness.

## Requirements

1. **Max age 60 seconds.** The current pool tick / active bin / price used in any measurement (IL, in-range, fee-to-principal) must be fetched within the last 60 seconds. If older, re-fetch before computing.
2. **Record the age.** Every report must state the age of the tick/price it used, e.g. `tick age: 12s (fetched <source> @ <slot>)`.
3. **Slot, not wall-clock.** Prefer Solana slot as the freshness clock when available; fall back to RPC `blockTime`. Do not trust a cached tick from a previous session.
4. **Stale ⇒ reject.** If the freshest available tick is older than 60s (RPC lag, endpoint down), do not emit IL/in-range numbers. Report `DATA_STALE` and the last known age.
5. **Post-build re-check.** For execution, re-verify freshness immediately before signing — see `safe-rebalance.md` gate 5.
