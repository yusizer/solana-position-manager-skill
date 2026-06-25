# Impermanent Loss for Concentrated Liquidity

Impermanent loss (IL) is the gap between holding a position in an AMM and simply holding the deposited tokens (HODL). In **concentrated liquidity** (CLMM/DLMM) IL is **amplified** versus v2-style full-range LPing, because the same capital is spread over a narrower range — the position reacts more sharply to price moves. This file gives the exact math, a worked example, and how to compute it from on-chain state.

> Pair this file with the protocol file (`whirlpools.md` / `raydium-clmm.md` / `meteora-dlmm.md`) for the current price/tick, and with `range-alerts.md` for thresholds.

## 1. Setup

A position covers the price interval \([P_a, P_b]\) (for DLMM, convert the active bin range to a price interval — see `meteora-dlmm.md`). It was opened at price \(P_0\) and the current price is \(P\).

Work in **sqrt-price** space — it linearises the AMM math. Define:

\[
x = \sqrt{P},\quad x_0 = \sqrt{P_0},\quad x_a = \sqrt{P_a},\quad x_b = \sqrt{P_b}
\]

The position's liquidity is \(L\). At any in-range price \(P \in [P_a, P_b]\), the held amounts are:

\[
\text{token0}(P) = L\left(\frac{1}{x} - \frac{1}{x_b}\right),\qquad
\text{token1}(P) = L\,(x - x_a)
\]

(token0 is the "base" token priced in token1, i.e. \(P\) = price of token0 in token1.)

## 2. Value of the LP position vs HODL

Value everything in token1.

**LP value** (in range):

\[
V_{LP}(P) = \text{token0}(P)\cdot P + \text{token1}(P)
           = L\Bigl(2x - x_a - \frac{x^2}{x_b}\Bigr)
\]

**HODL value** (the open amounts held idle):

\[
V_{HODL}(P) = \text{token0}(P_0)\cdot P + \text{token1}(P_0)
            = L\Bigl(x^2\Bigl(\frac{1}{x_0} - \frac{1}{x_b}\Bigr) + x_0 - x_a\Bigr)
\]

**Impermanent loss** (excluding fees):

\[
\boxed{\;\text{IL}(P) = \frac{V_{LP}(P)}{V_{HODL}(P)} - 1\;}
\]

This is always \(\le 0\) (LP underperforms HODL on pure price moves). Fees are what must overcome it — see `backtest.md`.

## 3. Out of range

If \(P < P_a\): the position is 100% token0, \(V_{LP} = L\,(1/x_a - 1/x_b)\cdot P\). IL vs HODL is then the full move.
If \(P > P_b\): 100% token1, \(V_{LP} = L\,(x_b - x_a)\). The position has "sold" all token0 into token1 at the top of the range — IL is the missed upside.

## 4. Why concentrated IL is larger — the amplification (exact)

Compress liquidity into a narrower range and the same price move shifts more of your inventory. There is an **exact** relationship to v2 IL (basis: the Uniswap v3 value function; verified by reduction to v2 on full-range).

v2 (full-range) IL as a function of price ratio \(r = P/P_0\):

\[
\text{IL}_{v2}(r) = \frac{2\sqrt{r}}{1+r} - 1
\]

General concentrated case, normalise \(P_0 = 1\), \(a = P_a/P_0\), \(b = P_b/P_0\), \(r = P/P_0\), price in range:

\[
\boxed{\;\text{IL}_{v3}(r) = \text{IL}_{v2}(r)\cdot\frac{r+1}{(r+1) - r/\sqrt{b} - \sqrt{a}}\;}
\]

**Symmetric range** \([1/k,\, k]\) (geometrically centred on \(P_0\), i.e. \(a\cdot b = 1\)) simplifies to:

\[
\boxed{\;\text{IL}_{v3}(r) = \lambda\cdot\text{IL}_{v2}(r),\qquad
\lambda = \frac{\sqrt{k}}{\sqrt{k}-1}\;}
\]

\(\lambda\) is the **capital efficiency** of the range — how many times more fee-generating liquidity you get per unit of capital vs full-range. The same factor that boosts your fee APR boosts your IL. Checks: full-range \(k\to\infty \Rightarrow \lambda\to 1 \Rightarrow \text{IL}_{v3}=\text{IL}_{v2}\) ✓.

### Worked example (symmetric, verified two ways)

Range \([0.5,\, 2.0]\) around \(P_0 = 1\); price moves to \(1.21\) (\(+21\%\), still in range).
- \(\lambda = \sqrt{2}/(\sqrt{2}-1) = 1.4142/0.4142 = 3.414\)
- \(\text{IL}_{v2}(1.21) = 2\cdot1.1/2.21 - 1 = -0.452\%\)
- \(\text{IL}_{v3} = 3.414 \cdot (-0.452\%) = -1.54\%\)

Direct check from §2 (\(L=1\)): open amounts \(x_0 = y_0 = 0.2929\); at \(P=1.21\), \(V_{LP}=0.6374\), \(V_{HODL}=0.6473\), IL \(= 0.6374/0.6473 - 1 = -1.54\%\) ✓.

**Tighter = riskier.** Range \([0.8,\, 1.25]\) (\(k=1.25\), \(\lambda = 9.47\)): the same \(+21\%\) move (price 1.21, still in range) → \(\text{IL}_{v3} = 9.47\cdot(-0.452\%) = -4.28\%\). A narrow range multiplies **both** fee APR **and** IL by \(\lambda\) — but only while the price stays in range; crossing an edge zeroes the fee stream and leaves you single-sided.

> These formulas are implemented and unit-tested in `../examples/il_math.py` (`il_v2`, `amplification_lambda`, `il_v3_symmetric`) — see `../tests/test_il.py`.

## 5. Worked example (verified by the §2 formula)

Position: SOL/USDC, range \([P_a, P_b] = [140,\,210]\) USDC/SOL. Opened at \(P_0 = 170\). Now \(P = 200\).

- \(x_a=\sqrt{140}\approx 11.832,\; x_b=\sqrt{210}\approx 14.491,\; x_0=\sqrt{170}\approx 13.038,\; x=\sqrt{200}\approx 14.142\)
- \(V_{LP}(200) = L\,(2\cdot14.142 - 11.832 - 14.142^2/14.491)\)
  - \(14.142^2 = 200,\; 200/14.491 \approx 13.801\)
  - \(= L\,(28.284 - 11.832 - 13.801) = L\cdot 2.651\)
- \(V_{HODL}(200) = L\,(200\,(1/13.038 - 1/14.491) + 13.038 - 11.832)\)
  - \(1/13.038\approx 0.07670,\; 1/14.491\approx 0.06901,\; \Delta\approx 0.00769\)
  - \(200\cdot 0.00769 \approx 1.538,\; +1.206 \approx 2.744\)
  - \(= L\cdot 2.744\)
- \(\text{IL} = 2.651 / 2.744 - 1 \approx -3.4\%\)

So a +17.6% SOL move (170→200) inside a [140,210] range costs ~3.4% IL **before fees**. If the position has collected >3.4% of principal in fees, the LP is net-positive vs HODL; otherwise HODL won. That threshold is the single most useful number — see `range-alerts.md` and `backtest.md`.

## 6. How to compute it from on-chain state

1. Read \(P\) (current sqrt-price / active bin price) and \(L\) from the pool/position account — protocol file.
2. Read \(P_a, P_b\) from the position's tick/bin range — protocol file.
3. You need \(P_0\): either store it when the position is opened, or **reconstruct** it from the open amounts (deposit transaction) — fetch the deposit tx and solve the §2 amounts for \(x_0\). For rebalance decisions, \(P_0\) = price at last rebalance.
4. Plug into §2. Always pair with the freshness rule (`../rules/position-data-freshness.md`) — a stale \(P\) gives a wrong IL.

## 7. Gotchas

- **Fees are not IL.** Always report IL and fee income separately; net return = fees − |IL|.
- **Rebalancing resets \(P_0\).** After a rebalance, IL is measured from the new open price — do not carry the old basis.
- **Bin vs tick.** For Meteora DLMM the "range" is a set of bins; convert to a \([P_a, P_b]\) interval using the bin price formula before applying §2.
- **Token ordering matters.** Confirm which token is token0 in the pool; flipping it inverts \(P\) and breaks the signs.
