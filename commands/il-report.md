---
description: Full impermanent-loss report vs HODL for a single CLMM/DLMM position.
argument-hint: <position-pubkey or identifier>
---

Produce a full impermanent-loss report for position `$ARGUMENTS`.

Procedure:
1. Identify the protocol and load its skill file (`skill/whirlpools.md` / `skill/raydium-clmm.md` / `skill/meteora-dlmm.md`).
2. Fetch: entry price (price ratio at open), current price, tick/bin range, liquidity, amounts deposited then vs now.
3. Load `skill/impermanent-loss.md` and compute:
   - **IL%** vs HODL, with the concentrated-liquidity formula (show inputs: price ratio, range).
   - **Value if HODL** vs **value in position** (incl. accrued fees).
   - **Net return** = position value + fees − IL cost.
4. Apply `rules/position-data-freshness.md` — quote the tick/price age.

Output:
- A short table: entry price, current price, price ratio, range, IL%, fees, HODL value, position value, net.
- One paragraph interpreting: is the fee income offsetting IL? At what price ratio does IL exceed collected fees?
