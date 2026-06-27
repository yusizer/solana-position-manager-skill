# Orca Whirlpools — position management

Tick-range CLMM with static tiered fees. Verified against the `orca-so/whirlpools` monorepo (Rust + TypeScript) and `docs.orca.so` as of the 2026 v8 SDK. Anything not confirmed in the current monorepo is marked **unverified**.

## SDK packages (2026)

The SDK is split into three tiers, all on `@solana/kit` (web3.js is legacy only):

| Package | Version | Use |
|---|---|---|
| `@orca-so/whirlpools` | 8.0.1 | High-level instructions (open/withdraw/shift/close). |
| `@orca-so/whirlpools-client` | 7.0.0 | Fetch + decoders (`fetchWhirlpool`, `fetchPositionsForOwner`). |
| `@orca-so/whirlpools-core` | 3.1.0 | Types + math (`CollectFeesQuote`). |
| `@orca-so/whirlpools-sdk` | 0.21.0 | Legacy web3.js API (`WhirlpoolContext`, `collectFeesQuote`). |
| `orca_whirlpools` (Rust, crates.io) | 8.0.0 | Rust high-level; plus `orca_whirlpools_client`/`_core`. |

```bash
npm install @orca-so/whirlpools @orca-so/whirlpools-client @orca-so/whirlpools-core @solana/kit
```

## Program ID

```
whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc
```

Same on Mainnet and Devnet (`declare_id!` in `programs/whirlpool/src/lib.rs`). `FeeTier`, `Whirlpool`, `Position`, `TickArray`, `PositionBundle`, `TokenBadge`, `WhirlpoolsConfig`, `WhirlpoolsConfigExtension` are PDAs inside this one program — no companion program IDs.

## Position model (on-chain account)

`Position` is a PDA derived from the Program ID + the Position Mint (an NFT). Account size **216 bytes**. Fields (from `state/position.rs`):

```rust
pub struct Position {
    pub whirlpool: Pubkey,                    // 32  pool this position belongs to
    pub position_mint: Pubkey,                // 32  NFT mint identifying the position
    pub liquidity: u128,                      // 16
    pub tick_lower_index: i32,                // 4
    pub tick_upper_index: i32,                // 4
    pub fee_growth_checkpoint_a: u128,        // 16  Q64.64
    pub fee_owed_a: u64,                      // 8   uncollected fees, token A
    pub fee_growth_checkpoint_b: u128,        // 16  Q64.64
    pub fee_owed_b: u64,                      // 8   uncollected fees, token B
    pub reward_infos: [PositionRewardInfo; 3],// 72
}
```

Pool (`Whirlpool`) fields you need: `tick_spacing: u16`, `fee_rate: u16` (hundredths of bps), `liquidity: u128`, `sqrt_price: u128` (Q64.64), `tick_current_index: i32`, `fee_growth_global_a/b: u128`.

## Fetch positions + pool price/tick

```ts
import { fetchPositionsForOwner, fetchWhirlpool } from "@orca-so/whirlpools-client";

// All positions owned by a wallet (scans token accounts, decodes):
const positions: PositionData[] = await fetchPositionsForOwner(rpc, owner, whirlpoolDeployment);

// Pool state (price, current tick, liquidity, fee rate):
const pool = await fetchWhirlpool(rpc, poolAddress);
const { sqrtPrice, tickCurrentIndex, liquidity, feeRate, tickSpacing } = pool.data;
// price = (sqrtPrice / 2^64)^2, rescaled by token decimals
```

- By-pool positions: `fetchPositionsInWhirlpool(rpc, poolAddress, deployment)` → `HydratedPosition[]`.
- Pool by token pair: `fetchConcentratedLiquidityPool(rpc, mintA, mintB, tickSpacing, deployment)`.
- Rust equivalents: `fetch_positions_for_owner`, `fetch_positions_in_whirlpool`, `fetch_whirlpool`.
- Fetch a single position by its NFT mint: derive the Position PDA from the mint and decode via `@orca-so/whirlpools-client` (a dedicated high-level by-mint helper is **unverified** in the current monorepo — filter `fetchPositionsForOwner` by mint if needed).

## In-range vs out-of-range

```ts
const inRange =
  position.tickLowerIndex <= tickCurrentIndex && tickCurrentIndex < position.tickUpperIndex;
// lower-INCLUSIVE, upper-exclusive (matches Orca docs: active + earning fees).
// Below range (tickCurrent < tickLower) -> 100% token B.
// At/above upper (tickCurrent >= tickUpper) -> 100% token A. Fees stop accruing.
```

Tick math: `p(i) = 1.0001^i`, usable tick range **[-443636, 443636]**. `TICKS_PER_ARRAY = 88`. Position bounds must be multiples of `tick_spacing` (use `getInitializableTickIndex` for rounding).

## Fees (static, tiered)

Each (pair, tick_spacing) is its own pool with a fixed tier. Swap fee split: **87% LP, 12% protocol treasury, 1% climate fund**.

| Tick spacing | Base fee | LP share (87%) |
|---|---|---|
| 256 | 2% | 1.74% |
| 128 / 32896 | 1% | 0.87% |
| 96 | 0.65% | 0.5655% |
| 64 | 0.3% | 0.261% |
| 16 | 0.16% | 0.1392% |
| 8 | 0.08% | 0.0696% |
| 4 | 0.04% | 0.0348% |
| 2 | 0.02% | 0.0174% |
| 1 | 0.01% | 0.0087% |

(The "128 / 32896" double value is verbatim from the docs; reason undocumented.)

**Adaptive-fee pools:** effective fee = base tier + a dynamic component that rises with price movement/volatility. On-chain: pool holds `fee_rate` + `fee_growth_global_a/b` (Q64.64); position holds `fee_growth_checkpoint_a/b` + `fee_owed_a/b` (u64, accumulated uncollected). Read `fee_owed_a/b` directly from the account; the exact claimable amount comes from a quote (legacy `collectFeesQuote` from `@orca-so/whirlpools-core`/legacy-sdk).

## Rebalance flow (2026 — cheap range shift)

The modern SDK can **shift a position's range without close+reopen**, which avoids rent overhead on a new NFT:

```ts
// 1. Withdraw all liquidity (REQUIRED before resetPositionRange: position.liquidity must be 0)
const { quote: decQuote, instructions: decIx } = await decreaseLiquidityInstructions(
  rpc, positionMint, { liquidity: position.liquidity }, config);

// 2. Harvest accrued fees + rewards
const { feesQuote, rewardsQuote, instructions: harvIx } =
  await harvestPositionInstructions(rpc, positionMint, config);

// 3. Shift the range in place (one instruction, rewrites tickLower/UpperIndex)
const { instructions: resetIx } = await resetPositionRangeInstructions(
  rpc, positionMint, newLowerPrice, newUpperPrice, config);

// 4. Re-add liquidity at the new range
const { instructions: incIx } = await increaseLiquidityInstructions(
  rpc, positionMint, { tokenA, tokenB } /* or liquidity */, config);
```

- `decreaseLiquidityInstructions` accepts `{ liquidity } | { tokenA } | { tokenB }` (a `DecreaseLiquidityQuoteParam`).
- `resetPositionRangeInstructions` → `getResetPositionRangeInstruction`; prices are converted via `priceToTickIndex` + `getInitializableTickIndex` rounding. **Precondition: `position.liquidity === 0n`.**
- Classic close+open path: `closePositionInstructions` (internally collects fees → rewards → decreases liquidity → closes; low-level close on a non-empty position fails with `ClosePositionNotEmpty` = 0x1775). Open: `openConcentratedPosition`, `openPositionInstructionsWithTickBounds`, `openFullRangePositionInstructions`.
- Many positions: `PositionBundle` packs up to 256 positions under one NFT.

**Always** re-fetch the pool (`fetchWhirlpool`) immediately before building the tx, and simulate the full sequence before signing (`../rules/safe-rebalance.md`).

## 2026 notes

- `@orca-so/whirlpools` 8.0.1 / Rust `orca_whirlpools` 8.0.0 (crates.io, 2026-05-14).
- `resetPositionRange` is the key 2026 capability for cheap rebalances — prefer it over close+open.
- Position NFTs use Token-2022 (MetadataPointer + TokenMetadata); mint authority is burned at open.
- There is no separate "Whirlpools v2" program — extensions ship via `WhirlpoolsConfigExtension` + new instructions on the same Program ID.
- `PositionDecoder` (a name from the old standalone SDK) is **unverified** in the current monorepo; decoding is exposed via `fetchWhirlpool`/`fetchPositionsForOwner` `.data` (`WhirlpoolData`/`PositionData`).
