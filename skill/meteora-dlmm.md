# Meteora DLMM — position management

**Bin-based** dynamic liquidity (not tick-based). Discrete price bins, volatility-aware dynamic fees, native limit orders, and an **atomic rebalance** instruction. Verified against `@meteora-ag/dlmm` and `docs.meteora.ag` (on-chain `lb_clmm` source is closed; account fields are reconstructed from the IDL via the docs).

## SDK packages (2026)

| Package | Version | Notes |
|---|---|---|
| `@meteora-ag/dlmm` | 1.9.10 | TypeScript stable (RC `1.9.10-rc.0`). Deps: `@solana/web3.js`. |
| `commons` (Rust) | 0.3.3 | Not on crates.io — `commons = { path = "../dlmm-sdk/commons" }`. CLI 0.6.3. Anchor 0.31.0, Solana SDK 2.1.0. |

```bash
npm install @meteora-ag/dlmm @solana/web3.js
```

## Program ID

The program is **`lb_clmm`** (DLMM is the product name, not the program). One ID on Mainnet and Devnet:

```
LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo
```

Program version: **lb_clmm 0.12.0**. No separate "DLMM v2" — versioning is per-account (`PositionV2`).

## Position model — discrete bins

Each bin is a single fixed price; swaps fill the active bin at zero slippage, then step to the neighbour. Only one bin is active at a time. Bin price:

```
P_i = (1 + binStep / 10000) ^ i        // binStep up to 400 (bps)
```

SDK: `DLMM.getBinIdFromPrice(price, binStep, min)`, `pool.getBinIdFromPrice(price, min)`, `getPriceOfBinByBinId`. Bins are grouped into **bin arrays of 70** (`MAX_BIN_PER_ARRAY = 70`, `DEFAULT_BIN_PER_POSITION = 70`); array index = `floor(bin_id / 70)`.

Liquidity is added over a contiguous range `[lower_bin_id, upper_bin_id]`. The account is **`PositionV2`**: `lb_pair, owner, fee_owner, lower_bin_id, upper_bin_id, liquidity_shares (inline 70 + extensible), reward_infos (×70, NUM_REWARDS=2), fee_infos (×70: fee_x/y_per_token_complete, fee_x/y_pending), total_claimed_fee_x/y_amount, total_claimed_rewards, last_updated_at, lock_release_point, version, permissionless_operation_bits`. Dynamic positions extend up to **1400 bins** (`MAX_BINS_PER_POSITION`), +91 bins per `increase_position_length`; shrink modes `ShrinkBoth`/`NoShrinkLeft`/`NoShrinkRight`/`NoShrinkBoth`. V1 positions are removed in SDK 1.9.x (migrate via `migrate_position_from_v1`/`_from_v2`). Liquidity share: `liquidity_share = floor(L_in · existing_supply / L_bin)`, `L = P·x + y`.

## Fetch positions + active bin

```ts
import DLMM from "@meteora-ag/dlmm";

const pool = await DLMM.create(connection, poolAddress, { cluster: "mainnet-beta" });
// Multiple pools: DLMM.createMultiple(connection, [addr, ...])

// Positions for a user in this pool (returns activeBin too):
const { activeBin, userPositions } = await pool.getPositionsByUserAndLbPair(userPublicKey);
for (const p of userPositions) {
  p.publicKey;
  p.positionData.lowerBinId;
  p.positionData.upperBinId;
}

// All positions across all DLMM pools for a wallet:
const map = await DLMM.getAllLbPairPositionsByUser(connection, userPubKey, opt?);
// opt: { chunkSize, onChunkFetched, isParallelExecution }

// Single position: pool.getPosition(positionPubKey) -> LbPosition

// Active bin (id + price):
const active = await pool.getActiveBin();   // { binId, price }
```

Other bin queries: `getBinsAroundActiveBin(left, right)`, `getBinsBetweenLowerAndUpperBound(lo, hi)`, `getBinsBetweenMinAndMaxPrice(min, max)`.

## In-range vs out-of-range (inclusive bounds)

```ts
const inRange = userPositions.filter(p => {
  const id = activeBin.binId;
  return id >= p.positionData.lowerBinId && id <= p.positionData.upperBinId; // inclusive
});
// Out of range -> no swap-fee accrual AND no liquidity-mining rewards.
```

Note the **inclusive** bounds — a DLMM position covers both edge bins. Don't apply Orca/Raydium strict-`<` logic here.

## Fees — dynamic, volatility-aware

```
total_fee_rate   = min(base_fee_rate + variable_fee_rate, MAX_FEE_RATE)
base_fee_rate    = base_factor × bin_step × 10 × 10^(base_fee_power_factor)        // precision 1e9
variable_fee_rate= ceil(variable_fee_control × (volatility_accumulator × bin_step)^2 / 1e11)
volatility_accumulator = min(volatility_reference + |index_reference − active_id| × 10000,
                             max_volatility_accumulator)
```

`variable_fee_control = 0` → static mode. Frequent swaps / bin crossings grow `volatility_accumulator` → fee rises; idle periods decay it. Parameters live in `LbPair`: `StaticParameters` (`base_factor`, `base_fee_power_factor`, `bin_step`, `variable_fee_control`, `max_volatility_accumulator`, `protocol_share`, `collect_fee_mode`) and `VariableParameters` (`volatility_accumulator`, `volatility_reference`, `index_reference`). Fees accrue to the bins that participate in a swap.

**Collect Fee Mode** (pool-level): `InputOnly` (fees in the input token) or `OnlyY` (always token Y). Protocol fee = `floor(trading_fee × protocol_share / 10000)`; LP fee = trading_fee − protocol fee.

Read fees: `pool.getFeeInfo()` → `FeeInfo`, `pool.getDynamicFee()` → Decimal; static calc `DLMM.calculateFeeInfo(baseFactor, binStep, protocolShare, baseFeePowerFactor?)`. Claim:

```ts
await pool.claimAllRewardsByPosition({ owner, position });   // fees + LM rewards
// also: claimSwapFee, claimAllSwapFee, claimLMReward, claimAllLMRewards, claimAllRewards
```

Rewards do **not** auto-compound — claim manually.

## Rebalance flow (atomic rebalance is the headline feature)

**Remove + optional close:**

```ts
const txs = await pool.removeLiquidity({
  user, position,
  fromBinId: minBinId, toBinId: maxBinId,
  bps: new BN(10_000),          // 10000 = 100% withdrawal
  shouldClaimAndClose: true,    // claim fee+reward and close the position
  skipUnwrapSOL: false,
});
// underlying: remove_liquidity_by_range2; range trimmed to bins with liquidity/fees
```

**Resize the range** (no full close needed for empty segments):

```ts
increasePositionLength(position, side /* Lower/Upper */, length, funder); // up to POSITION_MAX_LENGTH
decreasePositionLength(position, side, length);                           // only empty segments
```

**Re-add by strategy:**

```ts
await pool.addLiquidityByStrategy({
  positionPubKey, user, totalXAmount, totalYAmount,
  strategy: { minBinId, maxBinId, strategyType },   // Spot | Curve | BidAsk
});
// new position in one step: initializePositionAndAddLiquidityByStrategy(...)
```

Distribution helpers: `calculateSpotDistribution`, `calculateBidAskDistribution`, `calculateNormalDistribution` (Curve), `toAmountsBothSideByStrategy`, `autoFillYByStrategy`/`autoFillXByStrategy`, `singleSidedX?: boolean`.

**Atomic rebalance — claim + remove + resize + add in one instruction** (prefer this; it is what makes DLMM rebalancing cheap and safe):

```ts
// Option A: explicit deposits/withdraws
const sim = pool.simulateRebalancePosition(
  positionAddress, positionData, shouldClaimFees, shouldClaimReward, deposits, withdraws);

// Option B: balanced strategy (recommended for symmetric re-entries)
const sim = pool.simulateRebalancePositionWithBalancedStrategy(
  positionAddress, positionData, strategy, topUpAmountX, topUpAmountY, xWithdrawBps, yWithdrawBps);

const { initBinArrayInstructions, rebalancePositionInstruction } =
  pool.rebalancePosition(sim, maxActiveBinSlippage, rentPayer?, slippage?);
```

Helpers: `BalancedStrategyBuilder`, `SpotStrategyParameterBuilder`, `CurveStrategyParameterBuilder`, `BidAskStrategyParameterBuilder`, `suggestBalancedXParametersFromY`/`suggestBalancedYParametersFromX`. Tx order: init bin arrays (if needed) → rebalance instruction. Seed liquidity: `seedLiquidity(... { curvature, minPrice, maxPrice })`, `seedLiquiditySingleBin(...)`.

## 2026 notes (lb_clmm 0.12.0)

- Limit orders: `place_limit_order` / `cancel_limit_order` / `close_limit_order_if_empty`.
- Collect Fee Mode + permissionless claim: `set_permissionless_operation_bits`, `enablePositionPermissionlessClaimFee`.
- `add_liquidity_by_weight2` (Token-2022 support), `close_bin_array`.
- **Breaking in 0.12.0:** swap-quote logic changed (collect fee mode + limit orders); max bins per swap dropped **280 → 260**; bitmap extension account in `swap`/`swap2` is now **writable**; `FunctionType` default is `Undetermined` (was `LiquidityMining`); SDK removed the v1 `Position` type and `updateBinArray`; `swapExactOutQuoteAtBin.amountIn` now includes the fee.
- The on-chain `lb_clmm` source is closed (verified via the repo listing); account/instruction fields here are reconstructed from the IDL through the docs — accurate, but not read from source.
