# DLMM reference example — monitor + atomic rebalance

Runnable TypeScript reference for the **Meteora DLMM** parts of `solana-position-manager-skill`, using the verified `@meteora-ag/dlmm` 1.9.x API (see `../../skill/meteora-dlmm.md`). Two scripts:

- **`monitor.ts`** — read-only position monitor with out-of-range + drift alerts. Watches a public wallet; no key, no signing, no auto-rebalance.
- **`rebalance.ts`** — atomic DLMM rebalance (claim + remove + resize + add in one instruction) using `simulateRebalancePositionWithBalancedStrategy` + `rebalancePosition`. **Simulates and prints the quote; never signs** — you sign with your wallet (`../../rules/safe-rebalance.md`).

> This is a *reference* implementation of the skill's measure → monitor → rebalance loop against a real SDK. It is **not** part of the pure-Python `examples/il_*` suite — it needs `npm install` and an RPC endpoint. CI runs `npm run typecheck` (`tsc --noEmit`) on this directory to prove the typed example compiles against the real `@meteora-ag/dlmm` SDK; running `monitor` / `rebalance` needs an RPC endpoint and is not executed in CI.

## Run

```bash
cp .env.example .env       # fill RPC_URL, WATCH_WALLET, POOL_ADDRESS (+ USER_PUBKEY/POSITION_PUBKEY for rebalance)
npm install
npm run monitor:once       # one check, prints signals + fires alerts
npm run monitor            # loop every INTERVAL_S (default 300s)
npm run rebalance -- --position <POSITION_PUBKEY>   # simulate a rebalance, print the quote
npm run typecheck          # tsc --noEmit
```

## What it demonstrates

- **Fetch + freshness:** `DLMM.create`, `pool.getPositionsByUserAndLbPair` returns `{ activeBin, userPositions }`; every run re-fetches (`../../rules/position-data-freshness.md`).
- **In-range by active bin (inclusive):** `lowerBinId <= activeBinId <= upperBinId` — DLMM bounds are inclusive, *not* the strict `<` of Orca/Raydium.
- **Drift signal:** GREEN / YELLOW / RED from the distance of the active bin to the range edges (`../../skill/range-alerts.md`).
- **Dynamic fees:** `pool.getFeeInfo()` — volatility-aware, not a static tier.
- **Atomic rebalance:** `simulateRebalancePositionWithBalancedStrategy` → `rebalancePosition(sim, maxActiveBinSlippage)` → `{ initBinArrayInstructions, rebalancePositionInstruction }`. Strategy `Spot` / `Curve` / `BidAsk`.
- **Safety:** simulate-before-sign, no key custody, freshness re-check, one-line alert contract (`../../skill/monitoring.md`).

## Adapt before real use

- Tune the strategy type, `minBinId`/`maxBinId` window, `topUpAmountX/Y`, `xWithdrawBps`/`yWithdrawBps`, and `MAX_ACTIVE_BIN_SLIPPAGE` to the position (the `rebalance-engineer` agent does this).
- Wire `rebalancePositionInstruction` to your wallet adapter for signing — this file stops at the simulated quote by design.
- For Orca/Raydium, mirror this structure against their SDKs (see `../../skill/whirlpools.md` and `../../skill/raydium-clmm.md`); Orca can shift range in place with `resetPositionRangeInstructions`, Raydium needs close+open.
