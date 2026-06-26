# Evaluation report — solana-position-manager-skill

A reproducible, offline evaluation of whether the skill gets LP-lifecycle tasks
right versus a **fair ablation baseline** — a builder who knows the common
textbook cases but misses the CLMM nuance, not a structurally-incapable
strawman. The suite is executable — `python tests/test_eval.py` prints the
scorecard and runs in CI — not a hand-written claim.

> Companion to `tests/test_eval.py`. Re-run any time; the numbers below are the
> deterministic output of that script.

## Methodology

- **Task suite.** LP tasks an agent must get right across the lifecycle:
  concentrated-IL computation, in-range / drift level, rebalance decision, and
  a trigger false-positive check. Each task has a verified reference answer.
  - **IL references** are derived **independently of the skill's eval path**
    (never read out of `compute_il` at runtime), so the IL check is not
    self-referential: the first four are hardcoded from the worked examples in
    `skill/impermanent-loss.md`; `(120,240,170,190)` is hand-computed from the
    §2 closed form (sqrt-space V_LP/V_HODL); `(0.5,2.0,1.0,0.8)` is computed via
    the §4 amplification identity `il_v3 = λ(k)·il_v2(r)` — a *different code
    path* than `skill_il()` uses, i.e. a genuine cross-check.
  - **Drift / rebalance references** encode the documented thresholds
    (`skill/range-alerts.md`) and heuristics (`skill/rebalance.md`): drift
    bands 0.05 / 0.2 / 0.8 / 0.95; HOLD / WIDEN / MOVE / WITHDRAW gated by
    fee-vs-IL.
- **baseline** — a fair "knows some, misses the nuance" ablation, representing
  a builder with *partial* concentrated-liquidity expertise:
  - **IL:** knows concentrated IL for *symmetric* ranges `[1/k, k]` (the common
    textbook case) via the amplification identity; falls back to v2 (ignores
    concentration) for *asymmetric* ranges — the general-CLMM gap.
  - **drift:** 3-level GREEN / YELLOW / OUT with *coarser* thresholds (0.1 /
    0.9); cannot name the RED-near-edge band (0.05 / 0.95) — a position drifting
    to a dangerous edge reads as YELLOW, not RED.
  - **rebalance:** recenter (MOVE) when out of range; WIDEN near either edge;
    HOLD otherwise — but **no fee-vs-IL gate** (widens into losing positions
    where fees do not cover IL) and **no WITHDRAW** (never cuts a catastrophic
    out-of-range position — recenters instead).
- **with_skill** — the skill's models: general concentrated IL (incl.
  asymmetric ranges); GREEN / YELLOW / RED drift with the near-edge band;
  HOLD / WIDEN / MOVE / WITHDRAW gated by whether fees cover |IL|.
- **Pass criterion.** A task is "passed" if the answer matches the reference
  within tolerance (IL: ±0.2pp; drift/decision: exact, with an out-of-range
  RED credited to the baseline's OUT). The suite exits non-zero unless
  with_skill beats baseline, scores 100%, and triggers zero false positives.

## Results

| Suite | baseline | with_skill | tasks |
|---|---:|---:|---:|
| IL computation | 4 / 6 | **6 / 6** | 6 |
| In-range / drift level | 7 / 10 | **10 / 10** | 10 |
| Rebalance decision | 5 / 8 | **8 / 8** | 8 |
| **Total task correctness** | **16 / 24** | **24 / 24** | 24 |
| Trigger false-positive (false-RED on margin-in-range) | — | **0 / 12** | 12 |

**with_skill 24 / 24 vs baseline 16 / 24**, with **0 / 12 false-positive triggers**.

### Where the baseline loses (the CLMM nuance it misses)

| Task | Reference | baseline | with_skill |
|---|---|---|---|
| SOL/USDC [140,210] opened 170, now 200 (asymmetric) | −3.40% | −0.33% ✗ (v2, ignores λ) | −3.40% ✓ |
| Wide [120,240] opened 170, now 190 (asymmetric) | −0.97% | −0.15% ✗ (v2) | −0.97% ✓ |
| Symmetric [0.5,2.0] +21% (λ≈3.4) | −1.54% | −1.54% ✓ (knows symmetric) | −1.54% ✓ |
| Tight [0.8,1.25] +21% (λ≈9.5, symmetric) | −4.28% | −4.29% ✓ (knows symmetric) | −4.29% ✓ |
| Symmetric [0.5,2.0] −20% | −2.11% | −2.11% ✓ | −2.11% ✓ |
| No move (170→170) | 0.00% | 0.00% ✓ | 0.00% ✓ |

The baseline gets every **symmetric** range right (it knows the amplification
identity) and the no-move case — 4/6. It loses on the two **asymmetric** ranges,
where v2 (λ=1) ignores concentration. The drift and rebalance suites show the
same shape: the baseline names GREEN/YELLOW/OUT and HOLD/MOVE/WIDEN, but misses
the **RED-near-edge** band (drift) and **WITHDRAW + the fee-vs-IL gate**
(rebalance) — so it over-rebalances healthy near-edge positions and recenters
catastrophic out-of-range positions instead of cutting them.

This is a fair gap, not an engineered one: the baseline is a competent
textbook-aware builder, and the skill's edge is the general-CLMM math, the
near-edge alert band, and the fee-gated cut decision.

## Reproducibility

```bash
python tests/test_eval.py          # prints the scorecard; exit 0 on PASS
```

CI runs this on every push/PR (`.github/workflows/validate.yml` → "Eval suite").
No network, no RPC, no secrets — the evaluation is fully deterministic.

## Scope & limitations

- **Offline, synthetic positions.** Tasks use constructed tick/price/IL inputs
  with reference answers from documented formulas — not 30 live mainnet
  positions. The point is to measure model correctness against ground truth,
  not to sample the chain.
- **baseline is a fair ablation, not a strawman.** It knows the common
  textbook cases (symmetric-range concentrated IL, coarse drift, widen-near-
  edge); it misses the asymmetric-IL formula, the RED-near-edge band, and the
  fee-vs-IL-gated WITHDRAW decision. The 16/24 reflects that partial
  competence — the skill's 8-task edge is the genuinely-hard CLMM nuance.
- **Trigger eval is with_skill-only.** It verifies the skill fires zero
  false-RED alerts on margin-in-range positions (the false-positive that would
  make an auto-monitor annoying). The baseline's coarser thresholds also
  produce no false-RED on this set, so this is a guardrail on the skill, not a
  differentiator.
- **Live-RPC coverage** lives in `tests/test_fetch.py::test_live_rpc_decode` —
  an opt-in test (set `SOLANA_RPC_URL` + `SOLANA_TEST_POSITION`) that fetches
  and decodes a real mainnet position. CI runs the offline-fixture decode; the
  live test makes the "real read-only RPC" claim truthful rather than asserted.
