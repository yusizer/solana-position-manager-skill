# Resources — SDKs, program IDs, docs, data

Quick lookup. All program IDs and package versions verified against official SDK repos and docs as of 2026; items not confirmed in-source are marked **unverified**.

## Program IDs

| Protocol | Network | Program ID |
|---|---|---|
| Orca Whirlpools | Mainnet **and** Devnet | `whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc` |
| Raydium CLMM | Mainnet-beta | `CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK` |
| Raydium CLMM | Devnet | `DRayAUgENGQBKVaX8owNhgzkEDyoHTGVEGHVJT1E9pfH` |
| Meteora DLMM (`lb_clmm`) | Mainnet **and** Devnet | `LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo` |

Do **not** confuse Raydium CLMM with AMM v4 `675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8`, CPMM `CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C`, or LaunchLab `LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj`.

## SDK packages

| Protocol | TS package | Version | Rust |
|---|---|---|---|
| Orca | `@orca-so/whirlpools` (+ `_client`, `_core`) | 8.0.1 / 7.0.0 / 3.1.0 | `orca_whirlpools` 8.0.0 (crates.io) |
| Orca (legacy) | `@orca-so/whirlpools-sdk` (web3.js) | 0.21.0 | — |
| Raydium | `@raydium-io/raydium-sdk-v2` (GPL-3.0) | 0.2.55-alpha | `raydium_amm_v3` (git, CPI) |
| Meteora | `@meteora-ag/dlmm` | 1.9.10 | `commons` 0.3.3 (path) |

Orca's new SDK is on `@solana/kit` (web3.js moved to legacy). Meteora's on-chain `lb_clmm` source is closed; the SDK ships the IDL.

## Official docs (llms.txt indexes)

- Orca: `https://docs.orca.so/llms.txt`
  - Concepts: `…/liquidity/concepts/ticks-and-fees`, `…/trading-fees`, `…/adaptive-fees`
  - SDK: `…/developers/sdks/positions/monitor-positions`, `…/open-position`, `…/harvest`, `…/close-position`; `…/sdks/pools/monitor-pools`
  - Architecture: `…/developers/architecture/price-and-ticks`, `…/tokenized-positions`, `…/tick-arrays`
- Raydium: `https://docs.raydium.io/llms.txt`
  - `…/products/clmm/{overview,accounts,instructions,ticks-and-positions,fees,math,code-demos}.md`
  - `…/sdk-api/typescript-sdk.md`, `…/rust-cpi.md`; addresses `…/reference/program-addresses.md`
  - User flows: `…/user-flows/{add-remove-liquidity,claim-rewards,burn-and-earn}.md`
- Meteora: `https://docs.meteora.ag/llms.txt`
  - `…/core-products/dlmm/{what-is-dlmm,dynamic-positions,formulas,collect-fee-mode,liquidity-mining}.md`
  - `…/developer-guides/dlmm/program/{accounts,instructions,events}.md`, `…/typescript-sdk/{getting-started,reference,examples}.md`, `…/changelog.md`

## Key SDK functions (cheat sheet)

**Orca** (`@orca-so/whirlpools-client` / `@orca-so/whirlpools`):
`fetchPositionsForOwner`, `fetchPositionsInWhirlpool`, `fetchWhirlpool`, `fetchConcentratedLiquidityPool`, `decreaseLiquidityInstructions`, `harvestPositionInstructions`, `resetPositionRangeInstructions`, `increaseLiquidityInstructions`, `closePositionInstructions`. Rust: `fetch_positions_for_owner`, `fetch_whirlpool`.

**Raydium** (`raydium.clmm.*`):
`getOwnerPositionInfo`, `getOwnerLockedPositionInfo`, `getPoolInfoFromRpc`, `decreaseLiquidity`, `closePosition`, `harvestAllRewards`, `openPositionFromBase`, `openPositionFromLiquidity`, `increasePositionFromBase`, `increasePositionFromLiquidity`. Utils: `TickUtils.getPriceAndTick`, `TickUtil.sqrtPriceX64ToPrice`, `PoolUtils.getLiquidityAmountOutFromAmountIn`, `getPdaPersonalPositionAddress`, `PersonalPositionLayout.decode`.

**Meteora** (`@meteora-ag/dlmm`):
`DLMM.create`, `DLMM.createMultiple`, `DLMM.getAllLbPairPositionsByUser`, `pool.getPositionsByUserAndLbPair`, `pool.getPosition`, `pool.getActiveBin`, `pool.getFeeInfo`, `pool.getDynamicFee`, `pool.removeLiquidity`, `pool.addLiquidityByStrategy`, `pool.initializePositionAndAddLiquidityByStrategy`, `pool.simulateRebalancePosition`, `pool.simulateRebalancePositionWithBalancedStrategy`, `pool.rebalancePosition`, `increasePositionLength`, `decreasePositionLength`, `pool.claimAllRewardsByPosition`, `DLMM.calculateFeeInfo`. Strategy builders: `BalancedStrategyBuilder`, `Spot/Curve/BidAskStrategyParameterBuilder`.

## Tick / bin math reference

- Orca & Raydium (tick model): `p(i) = 1.0001^i`, usable range **[-443636, 443636]**. Orca `TICKS_PER_ARRAY = 88`; Raydium `TICK_ARRAY_SIZE = 60`. Position bounds are multiples of `tick_spacing`.
  - Orca tick spacings: 1, 2, 4, 8, 16, 64, 96, 128, 256.
  - Raydium tick spacings: 1, 10, 60, 120.
- Meteora (bin model): `P_i = (1 + binStep/10000)^i`, `binStep` up to 400 bps. `MAX_BIN_PER_ARRAY = 70`. Active bin is unique; position bounds inclusive.
- In-range: Orca strict `tickLower < tickCurrent < tickUpper`; Raydium `tickLower <= tickCurrent < tickUpper`; Meteora `lowerBinId <= activeBinId <= upperBinId` (inclusive).

## Historical data / backtest sources

- **Helius RPC** (`https://www.helius.dev/docs`): `getSignaturesForAddress` (limit 1–1000, paginate `before`/`until`); REST `GET /v0/addresses/{address}/transactions` (limit 1–100, `before-signature`/`after-signature`, slot/time filters, parsed/enhanced); `getTransaction` for full detail. Apply to the pool account to reconstruct swap/fee history.
- **Birdeye** (`https://docs.birdeye.so`, has llms.txt): `GET /defi/ohlcv` (max 1000), `GET /defi/v3/ohlcv` (max 5000, 1s/15s/30s), `GET /defi/v3/ohlcv/pair`, `GET /defi/history_price`. Solana via chain param/header.
- **GeckoTerminal** (`https://api.geckoterminal.com/api/v2`, free ~10 req/min): Solana network id `solana` (ids prefixed `solana_`). `GET /networks/solana/pools`, `GET /networks/solana/pools/{pool}/ohlcv/{minute|hour|day}?aggregate=&limit=&before_timestamp=` → `data.attributes.ohlcv_list = [ts, o, h, l, c, v]`, `GET /networks/solana/trending_pools`.
- **Jupiter Price API v3** — spot price for USD fee/principal conversion.

See `backtest.md` for how to combine these into a replay.

## Unverified / caveats

- **Orca:** `PositionDecoder` and a dedicated fetch-by-mint helper are not confirmed in the current monorepo (names from the legacy/standalone SDK). The "128 / 32896" dual value for the 1% fee tier is verbatim from docs, reason undocumented.
- **Raydium:** `raydium.clmm.getPositionInfo({ nftMint })` from `code-demos.md` is absent in current `clmm.ts` — use `getOwnerPositionInfo`. No testnet addresses documented (mainnet/devnet only).
- **Meteora:** on-chain `lb_clmm` source is closed; account/instruction fields are reconstructed from the IDL via docs (accurate, not from source).
- Cross-protocol alert thresholds and rebalance cadences are practical synthesis, not a single standard — calibrate to pool volatility and tx cost.
