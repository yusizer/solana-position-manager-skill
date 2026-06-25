# IL benchmarks by range width

Concrete, **verified** numbers for how range width trades off fee-earning power against impermanent loss. Every value below is produced by `../examples/il_math.py` (`il_v2`, `amplification_lambda`, `il_v3_symmetric`) and is cross-checked by `../tests/test_il.py`. Reproduce with:

```bash
python -c "import sys; sys.path.insert(0,'examples'); from il_math import il_v2, amplification_lambda, il_v3_symmetric; \
print(il_v3_symmetric(1.21, 2.0)*100)"   # -> -1.5449...
```

## Symmetric ranges `[1/k, k]` around the open price

For a symmetric range, concentrated IL = λ · v2-IL, where **λ = √k/(√k−1)** is the capital efficiency (fee-APR multiplier). λ → 1 for full-range (v2). "OOR" = the price move exits the range (position goes single-sided, fees stop).

| k | Range | λ (cap. eff.) | IL @ r=0.9 | IL @ r=1.1 | IL @ r=1.21 | IL @ r=1.5 | IL @ r=2.0 |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1.10 | [0.91, 1.10] | 21.49× | OOR | OOR | OOR | OOR | OOR |
| 1.25 | [0.80, 1.25] | 9.47× | −1.31% | −1.08% | **−4.29%** | OOR | OOR |
| 1.50 | [0.67, 1.50] | 5.45× | −0.76% | −0.62% | −2.47% | OOR | OOR |
| 2.00 | [0.50, 2.00] | 3.41× | −0.47% | −0.39% | −1.55% | **−6.90%** | OOR |
| 3.00 | [0.33, 3.00] | 2.37× | −0.33% | −0.27% | −1.07% | −4.78% | −13.53% |
| 5.00 | [0.20, 5.00] | 1.81× | −0.25% | −0.21% | −0.82% | −3.66% | −10.35% |
| 10.00 | [0.10, 10.00] | 1.46× | −0.20% | −0.17% | −0.66% | −2.96% | −8.36% |

## v2 (full-range) baseline

| r = P/P₀ | 0.9 | 1.1 | 1.21 | 1.5 | 2.0 |
|---|---:|---:|---:|---:|---:|
| IL_v2 | −0.139% | −0.113% | −0.453% | −2.020% | −5.719% |

(The −5.72% at a 2× price move is the canonical v2 IL value — a sanity check on the formulas.)

## How to read this — the core tradeoff

- **λ is the lever, and it cuts both ways.** A 9.47× capital-efficient range (k=1.25) earns ~9.5× more fee APR than full-range — but a +21% move costs 9.5× more IL too (−4.29% vs −0.45%). The same factor multiplies fee income *and* IL.
- **Tight ranges break fast.** k=1.10 (λ=21.5×) exits on almost any move — the fee APR is stellar but you will rebalance constantly (see `rebalance.md` anti-over-rebalance rules) or sit out-of-range earning nothing.
- **Out-of-range is the real risk, not the in-range IL.** Once `r` leaves `[1/k, k]`, fees go to zero and you are holding one token against HODL — no longer an "impermanent" loss, a position decision. Width should be chosen so expected holding time >> time-to-exit.
- **Rule of thumb.** Pick the smallest `k` such that the expected price range over your holding period stays inside `[1/k, k]` with high probability, *and* the resulting IL at the expected move is below the fee income you project (see `backtest.md` for projecting fee income).

## Decision shortcut

| You expect… | Choose | Why |
|---|---|---|
| Low vol, price pinned | small k (1.25–1.5), λ 5–9× | high APR, IL stays small because moves are small |
| Medium vol | k 2–3, λ 2.4–3.4× | balance |
| High vol / unsure | k 5–10, λ 1.5–1.8× | stay in range longer; accept lower APR |

This is the quantitative backbone behind `rebalance.md`'s WIDEN/MOVE/WITHDRAW decision tree.
