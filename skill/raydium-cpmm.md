# Raydium CPMM — scope note (constant-product, not concentrated)

Raydium **CPMM** is a separate program from CLMM. It is a **constant-product** AMM (x·y = k) with **fungible LP tokens** — there is no price range, no tick/bin concentration, and no per-position NFT. Verified against `@raydium-io/raydium-sdk-v2` and `docs.raydium.io`.

## Program ID (verified)

| Network | Program ID |
|---|---|
| **Mainnet-beta** | `CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C` |

Do not confuse with CLMM (`CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK`), AMM v4 (`675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8`), or LaunchLab — all separate programs.

## Why this skill does not actively manage CPMM positions

Concentrated-liquidity mechanics — range selection, out-of-range drift, amplified IL — do not apply to a constant-product pool. A CPMM LP position is the degenerate **full-range** case of every formula in [`impermanent-loss.md`](impermanent-loss.md):

- Capital efficiency **λ = 1** (full-range) → IL is the v2 curve `IL_v2(r) = 2·√r/(1+r) − 1`, **not** the amplified `λ · IL_v2`.
- No "out of range" state — the position always earns fees on every swap, so [`range-alerts.md`](range-alerts.md) has nothing to fire on.
- No rebalance decision — there is no range to widen, move, or withdraw ([`rebalance.md`](rebalance.md) heuristics are N/A).

This is the kit-skill's documented "When NOT to use" gate, made concrete: **set-and-forget full-range v2 LP adds little; a position manager's value comes from concentration.**

## If you still need CPMM data

The position is an SPL token balance (an LP token account), not a `Position` account with a range. To inspect:

```ts
// raydium.cpmm facade (constant-product): pool info + your fungible LP balance.
import { Raydium } from "@raydium-io/raydium-sdk-v2";
const raydium = await Raydium.load({ owner, connection, cluster });
const { poolInfo, poolKeys } = await raydium.cpmm.getPoolInfoFromRpc(poolId);
// your liquidity share = yourLpBalance / poolInfo.liquidity (fungible, no tick range).
```

`raydium.cpmm.*` mirrors `raydium.clmm.*` shape but returns fungible-LP state with no tick range. SDK v2 `0.2.55-alpha`. **Unverified:** the exact `raydium.cpmm` method names against the current facade — confirm in `@raydium-io/raydium-sdk-v2` before relying on them. The constant-product conclusion above is what matters for this skill's scope; the exact getter is out of the position-management loop.

## Where it belongs in the AMM landscape

Orca Whirlpools, Raydium CLMM, and Meteora DLMM are the **concentrated** programs this skill manages end-to-end. Raydium CPMM and AMM v4 are **constant-product** baselines (λ = 1) covered by the full-range case in [`impermanent-loss.md`](impermanent-loss.md), not active range management. See the coverage table in [`../README.md`](../README.md) and the routing in [`SKILL.md`](SKILL.md).
