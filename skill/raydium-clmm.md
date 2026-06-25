# Raydium CLMM — position management

Tick-range CLMM, **NFT-bound** positions, static tiered fees (with optional dynamic fee). Verified against `@raydium-io/raydium-sdk-v2` and `docs.raydium.io` as of the 2026 SDK v2. Unconfirmed items marked **unverified**.

## SDK packages (2026)

| Package | Version | Notes |
|---|---|---|
| `@raydium-io/raydium-sdk-v2` | 0.2.55-alpha | TypeScript, GPL-3.0. Deps: `@solana/web3.js ^1.95.3`, `@solana/spl-token ^0.4.8`. |
| `raydium_amm_v3` (Rust, CPI) | git only | No crates.io publish. `raydium_amm_v3 = { git = "https://github.com/raydium-io/raydium-clmm", features = ["cpi"] }` |

```bash
yarn add @raydium-io/raydium-sdk-v2
```

Load the facade: `const raydium = await Raydium.load({ owner, connection, cluster, ... })`, then use `raydium.clmm.*`.

## Program ID (CLMM only)

| Network | Program ID |
|---|---|
| **Mainnet-beta** | `CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK` |
| **Devnet** | `DRayAUgENGQBKVaX8owNhgzkEDyoHTGVEGHVJT1E9pfH` |

Do not confuse with AMM v4 (`675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8`), CPMM (`CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C`), or LaunchLab (`LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj`) — those are separate programs.

## Position model (NFT-bound)

Opening a position mints a supply-1 SPL token (the CLMM program is the mint authority); the holder of the token account owns the position. The position PDA `PersonalPositionState` is derived from the NFT mint. Two open variants: `OpenPosition` (SPL) and `OpenPositionWithToken22Nft` (Token-2022).

`PersonalPositionState` (on-chain):

```
bump, nft_mint, pool_id, tick_lower_index (i32), tick_upper_index (i32), liquidity (u128),
fee_growth_inside_0_last_x64 (u128), fee_growth_inside_1_last_x64 (u128),
token_fees_owed_0 (u64), token_fees_owed_1 (u64), reward_infos: [PositionRewardInfo; 3]
```

SDK layout (`PersonalPositionLayout`, camelCase, **A/B suffix instead of 0/1**):

```
nftMint, poolId, tickLower (s32), tickUpper (s32), liquidity (u128),
feeGrowthInsideLastX64A, feeGrowthInsideLastX64B,
tokenFeesOwedA (u64), tokenFeesOwedB (u64), rewardInfos
```

Pool (`PoolInfoLayout`): `mintA/mintB, tickSpacing, liquidity, sqrtPriceX64, tickCurrent, feeGrowthGlobalX64A/B, protocolFeesTokenA/B, fundFeesTokenA/B, tickArrayBitmap, dynamicFeeInfo`. `TickArrayState` holds `start_tick_index` + `ticks: [TickState; 60]` (`TICK_ARRAY_SIZE = 60`). `ProtocolPositionState` is deprecated.

## Fetch positions + pool price/tick

```ts
// All CLMM positions owned by a wallet (fetches token accounts, filters amount===1 NFTs,
// derives PDAs, decodes):
const positions = await raydium.clmm.getOwnerPositionInfo({ programId }); // defaults to CLMM_PROGRAM_ID

// Pool state (current tick, sqrt price, decoded price):
const { rpcPoolInfo, poolInfo, poolKeys, computePoolInfo, tickData, tickArrays } =
  await raydium.clmm.getPoolInfoFromRpc(poolId);
const tickCurrent = rpcPoolInfo.tickCurrent;     // BN
const sqrtPriceX64 = rpcPoolInfo.sqrtPriceX64;   // BN
const price = poolInfo.price;                    // decoded Decimal
```

Utilities: `TickUtils.getPriceAndTick(poolInfo, price, baseIn)`, `TickUtil.sqrtPriceX64ToPrice(...)`, `PoolUtils.getLiquidityAmountOutFromAmountIn(...)`.

- Locked (Burn&Earn) positions: `raydium.clmm.getOwnerLockedPositionInfo({ programId: CLMM_LOCK_PROGRAM_ID })` → pairs `{ position, lockInfo }`.
- `raydium.clmm.getPositionInfo({ nftMint })` appears in `code-demos.md` but is **unverified** in the current `clmm.ts` — use `getOwnerPositionInfo`, or derive manually via `getPdaPersonalPositionAddress(programId, mint)` + `PersonalPositionLayout.decode`.

## In-range vs out-of-range

```ts
const inRange = position.tickLower <= tickCurrent && tickCurrent < position.tickUpper;
// Only in-range positions contribute to PoolState.liquidity and earn swap fees.
// Out of range -> 100% one token (token1 if below, token0 if above), no fee accrual.
```

Bounds are multiples of `tick_spacing`. `MIN_TICK = -443636`, `MAX_TICK = 443636`, `p(i) = 1.0001^i`.

## Fees (static tiers + optional dynamic)

Four `AmmConfig` tiers:

| Index | trade_fee_rate | Fee | Tick spacing |
|:-:|:-:|:-:|:-:|
| 0 | 100 | 0.01% | 1 |
| 1 | 500 | 0.05% | 10 |
| 2 | 2_500 | 0.25% | 60 |
| 3 | 10_000 | 1.00% | 120 |

`trade_fee_rate` is in units of 1/1_000_000 of volume. From each swap: protocol fee `floor(step_fee·protocol_fee_rate/1e6)` → `protocol_fees_token_{input}` (collected via `CollectProtocolFee`); fund fee → `fund_fees_token_{input}` (`CollectFundFee`); remainder = LP. LP accrual: globally `fee_growth_global_{0,1}_x64 += step_lp·2^64/liquidity`; on touch, `fee_growth_inside_{0,1}_x64` is recomputed and `delta × liquidity/2^64` lands in `token_fees_owed_{0,1}`. Tokens move only on `DecreaseLiquidity`/`CollectFees`; **"collect only" = `DecreaseLiquidity` with `liquidity = 0`**.

Dynamic fee (per-pool `DynamicFeeInfo` + `DynamicFeeConfig`: `filter_period`, `decay_period`, `reduction_factor`, `max_volatility_accumulator`) is enabled via `CreateCustomizablePool`.

## Rebalance flow (NFT-bound: range change = close + open)

Mutating methods return a builder `{ execute, builder, transaction, innerTransactions, extInfo }` with a `txVersion` (V0 recommended).

```ts
// 1. Withdraw liquidity (and optionally collect + close). For "collect only": liquidity = new BN(0).
const { execute } = await raydium.clmm.decreaseLiquidity({
  poolInfo, poolKeys, ownerPosition,
  liquidity,            // full BN to withdraw all
  amountMinA, amountMinB,
  closePosition,        // true to also burn the NFT and close
  txVersion,
});

// 2. (If moving range) open a new position at the new tick bounds:
const { execute } = await raydium.clmm.openPositionFromBase({
  poolInfo, poolKeys,
  tickLower, tickUpper,
  base, baseAmount, otherAmountMax,
  ownerInfo, txVersion,
});
// or openPositionFromLiquidity / increasePositionFromBase / increasePositionFromLiquidity
```

- Rewards (3 streams, no farm program needed): `raydium.clmm.harvestAllRewards({ ownerInfo, allPoolInfo, allPositions, txVersion })` (batches `CollectReward`); or targeted `collectReward`/`collectRewards`.
- Close + burn NFT: `closePosition: true` in `decreaseLiquidity`, or `raydium.clmm.closePosition({...})`. The docs warn: do **not** close liquidity and the position in separate calls — the program reverts.
- **A live position's range cannot be changed in place** (unlike Orca's `resetPositionRange`). A range move = withdraw/close → open a new NFT.
- All amounts are `BN`, never `number`. **Re-fetch `getPoolInfoFromRpc` immediately before building the tx** (`../rules/position-data-freshness.md`).

## 2026 notes

- SDK v2 `0.2.55-alpha` (published 2026-06-24) — frequent releases; pin a version.
- Recent CLMM extensions: limit orders (`openLimitOrder`/`increaseLimitOrder`/.../`closeAllLimitOrder`), single-sided fee mode (`fee_on`: FromInput / Token0Only / Token1Only), dynamic fee via `CreateCustomizablePool`.
- Product line: AMM v4 (constant-product, fungible LP), CPMM (separate program, fungible LP, **not** a CLMM replacement — no concentration), CLMM (tick-based, NFT positions, up to 3 built-in reward streams).
