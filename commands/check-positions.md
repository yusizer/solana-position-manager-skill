---
description: List all CLMM/DLMM liquidity positions for a Solana wallet with in-range status and accrued fees.
argument-hint: <wallet-pubkey>
---

Inventory every concentrated-liquidity position owned by wallet `$ARGUMENTS` across Orca Whirlpools, Raydium CLMM, and Meteora DLMM.

Procedure:
1. Load `skill/SKILL.md` routing, then each protocol file as needed (`skill/whirlpools.md`, `skill/raydium-clmm.md`, `skill/meteora-dlmm.md`).
2. For every position found, fetch current pool tick / active bin and accrued fees (respect `rules/position-data-freshness.md`).
3. Determine in-range vs out-of-range per `skill/range-alerts.md`.

Output a single table:

| Protocol | Position | Pair | Range (tick/bin) | Current | In-range | Accrued fees | Fee/principal | IL% |

Append a one-line summary: total positions, count out-of-range, total accrued fees (USD if price available). Flag any out-of-range position with ⚠.
