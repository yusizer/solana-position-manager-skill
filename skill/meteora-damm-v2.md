# Meteora DAMM v2 — constant-product AMM with NFT positions (scope: fetch + fees + claim)

Meteora **DAMM v2** is a **constant-product** AMM (x·y = k) — the "cp-amm" — with **NFT positions**, dynamic fees, and an anti-sniper suite. It is the AMM tokens graduate to from Meteora's Dynamic Bonding Curve. Verified against `@meteora-ag/cp-amm-sdk` 1.4.4 and `github.com/MeteoraAg/damm-v2-sdk` (`docs.md`).

> **Scope note.** DAMM v2 is constant-product, so the concentrated-liquidity parts of this skill (range selection, out-of-range drift, amplified IL) **do not apply** — λ = 1, the full-range case. What *does* apply is the **fetch → fees → claim** slice of the lifecycle. Range/rebalance redirect to the v2 case in [`impermanent-loss.md`](impermanent-loss.md).

## SDK package (2026)

| Package | Version | Notes |
|---|---|---|
| `@meteora-ag/cp-amm-sdk` | 1.4.4 | "SDK for DAMM v2". Class `CpAmm`. Deps: `@coral-xyz/anchor` 0.31.0, `@solana/web3.js` ^1.95.3, `@solana/spl-token` ^0.4.8, `bn.js`, `decimal.js`. |

```bash
npm install @meteora-ag/cp-amm-sdk
```

```ts
import { CpAmm } from "@meteora-ag/cp-amm-sdk";
import { Connection, PublicKey } from "@solana/web3.js";
const cpAmm = new CpAmm(connection);
```

## Program ID (verified)

Same address on Mainnet and Devnet:

```
cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG
```

Do not confuse with DLMM (`LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo`) or the DBC bonding curve (`dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN`).

## Position model — NFT positions on a constant-product curve

A position is an **NFT** (supply-1 SPL token); the holder owns the position. Liquidity is fungible-equivalent (a proportional share of pool liquidity) — there is **no tick/bin range**. A DAMM v2 position is always "full range": it earns fees on every swap and never goes out of range.

Dynamic fees (volatility / time / market-cap schedulers + rate limiter): `getBaseFeeParams`, `getDynamicFeeParams`, `getBaseFeeNumerator`, `getDynamicFeeNumerator`, `bpsToFeeNumerator` / `feeNumeratorToBps`, and the fee-scheduler encoders/decoders (`encodeFeeTimeSchedulerParams`, `encodeFeeMarketCapSchedulerParams`, `encodeFeeRateLimiterParams` + matching decoders).

## Fetch positions + pool state

```ts
// Pool state (sqrt price, liquidity, fees):
const poolState = await cpAmm.fetchPoolState(poolAddress);

// All positions for a user (across DAMM v2 pools):
const positions = await cpAmm.getPositionsByUser(userPublicKey);

// Positions for a user in one pool:
const byPool = await cpAmm.getUserPositionByPool({ pool, user });

// Single position:
const pos = await cpAmm.fetchPositionState(positionNft);

// Pool fees (claimable LP fee):
const fees = await cpAmm.fetchPoolFees(poolAddress);
```

Other state getters: `getAllPositions`, `getAllPositionsByPool`, `getMultiplePositions`, `fetchPoolStatesByTokenAMint`, `getAllPools`, `isPoolExist`, `isLockedPosition` / `isPermanentLockedPosition` / `canUnlockPosition`.

## Fees & rewards — claim

```ts
// Claim accrued LP fees for a position:
await cpAmm.claimPositionFee({ positionNft, payer, ... });   // claimPositionFee2 = newer variant
// Claim liquidity-mining rewards:
await cpAmm.claimReward({ positionNft, rewardIndex, ... });
```

Unclaimed-fee helper: `getUnClaimLpFee(...)`. Rewards do **not** auto-compound — claim manually (same rule as DLMM).

## Why range/rebalance don't apply (the math)

A constant-product position is the full-range case of [`impermanent-loss.md`](impermanent-loss.md):

- Capital efficiency **λ = 1** → `IL_v2(r) = 2·√r/(1+r) − 1` (the un-amplified v2 curve), **not** `λ · IL_v2`.
- No out-of-range state → [`range-alerts.md`](range-alerts.md) has nothing to fire on.
- No range to widen/move/withdraw → [`rebalance.md`](rebalance.md) heuristics are N/A. "Rebalancing" a DAMM v2 position = withdraw + redeposit (close + open) — a gas-vs-fees call, not a range call.

## Lifecycle coverage for DAMM v2

| Step | Applies? | How |
|---|---|---|
| FETCH | ✅ | `fetchPoolState`, `fetchPositionState`, `getPositionsByUser` |
| MEASURE (fees) | ✅ | `fetchPoolFees`, `getUnClaimLpFee`; IL via `IL_v2` (λ=1) |
| MEASURE (in-range) | n/a | always full-range |
| DECIDE rebalance | limited | withdraw+redeposit gas call, not a range decision |
| EXECUTE | ✅ | `removeAllLiquidityAndClosePosition` / `createPositionAndAddLiquidity` — simulate first ([`../rules/safe-rebalance.md`](../rules/safe-rebalance.md)) |
| MONITOR | ✅ | poll `fetchPoolFees` + `fetchPoolState` on a schedule ([`monitoring.md`](monitoring.md)) |

## 2026 notes

- SDK `@meteora-ag/cp-amm-sdk` 1.4.4 (published 2026-04). API surface read from the SDK's own `docs.md`; exact param shapes per method — confirm in `docs.md` before relying on a specific field. The class name (`CpAmm`) and the functions above are taken verbatim from that documentation.
- Position lifecycle extras: `splitPosition` / `splitPosition2`, `mergePosition`, `lockPosition` / `permanentLockPosition`, `refreshVesting`, `closePosition`.
- Quote helpers: `getQuote` / `getQuote2`, `getDepositQuote`, `getWithdrawQuote`, `getLiquidityDelta`, `getPriceImpact`, `getPriceFromSqrtPrice` / `getSqrtPriceFromPrice`, `getMaxAmountWithSlippage` / `getAmountWithSlippage`.
