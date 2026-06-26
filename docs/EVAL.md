# Evaluation report — solana-position-manager-skill

A reproducible, offline evaluation of whether the skill actually gets LP-lifecycle tasks right versus a naive "no skill" baseline. The suite is executable — `python tests/test_eval.py` prints the scorecard and runs in CI — not a hand-written claim.

> Companion to `tests/test_eval.py`. Re-run any time; the numbers below are the deterministic output of that script.

## Methodology

- **Task suite.** LP tasks an agent must get right across the lifecycle: concentrated-IL computation, in-range / drift level, rebalance decision, and a trigger false-positive check. Each task has a verified reference answer.
  - **IL references** come from the worked examples in `skill/impermanent-loss.md` (derived from first principles and verified by reduction to v2 on full-range) — *not* from the skill's own output, so the IL check is not self-referential.
  - **Drift / rebalance references** encode the documented thresholds (`skill/range-alerts.md`) and heuristics (`skill/rebalance.md`): drift bands 0.05 / 0.2 / 0.8 / 0.95; HOLD / WIDEN / MOVE / WITHDRAW gated by fee-vs-IL.
- **baseline** — a builder without concentrated-liquidity expertise: v2 IL ignoring concentration (λ=1, the full-range curve for *every* range); binary in-range (in vs out, no drift levels); "rebalance when out of range" (HOLD or MOVE only).
- **with_skill** — the skill's models: concentrated IL via λ-amplification; GREEN / YELLOW / RED drift; HOLD / WIDEN / MOVE / WITHDRAW gated by whether fees cover |IL|.
- **Pass criterion.** A task is "passed" if the answer matches the reference within tolerance (IL: ±0.2pp; drift/decision: exact). The suite exits non-zero unless with_skill beats baseline, scores 100%, and triggers zero false positives.

## Results

| Suite | baseline | with_skill | tasks |
|---|---:|---:|---:|
| IL computation | 1 / 6 | **6 / 6** | 6 |
| In-range / drift level | 5 / 10 | **10 / 10** | 10 |
| Rebalance decision | 4 / 8 | **8 / 8** | 8 |
| **Total task correctness** | **10 / 24** | **24 / 24** | 24 |
| Trigger false-positive (false-RED on margin-in-range) | — | **0 / 12** | 12 |

**with_skill 24 / 24 vs baseline 10 / 24**, with **0 / 12 false-positive triggers**.

### Why the baseline fails (the concentrated-liquidity gap)

| Task | Reference | baseline | with_skill |
|---|---|---|---|
| SOL/USDC [140,210] opened 170, now 200 | −3.40% | −0.33% ✗ (v2 ignores λ) | −3.40% ✓ |
| Symmetric [0.5,2.0] +21% (λ≈3.4) | −1.54% | −0.45% ✗ | −1.54% ✓ |
| Tight [0.8,1.25] +21% (λ≈9.5) | −4.28% | −0.45% ✗ | −4.29% ✓ |
| Wide [120,240] opened 170, now 190 | −0.97% | −0.15% ✗ | −0.97% ✓ |
| Symmetric [0.5,2.0] −20% | −2.11% | −0.62% ✗ | −2.11% ✓ |
| No move (170→170) | 0.00% | 0.00% ✓ | 0.00% ✓ |

The baseline gets **only the no-move case right** — every concentrated range exposes the v2-IL error. The drift and rebalance suites show the same pattern: the baseline can name "in range" vs "out of range" but cannot detect a position drifting to a RED edge while still nominally in range, and it cannot distinguish WIDEN / WITHDRAW from a binary "rebalance / don't" — so it over-rebalances healthy near-edge positions and fails to cut a catastrophic out-of-range position.

## Reproducibility

```bash
python tests/test_eval.py          # prints the scorecard; exit 0 on PASS
```

CI runs this on every push/PR (`.github/workflows/validate.yml` → "Eval suite"). No network, no RPC, no secrets — the evaluation is fully deterministic.

## Scope & limitations

- **Offline, synthetic positions.** Tasks use constructed tick/price/IL inputs with reference answers from documented formulas — not 30 live mainnet positions. The point is to measure model correctness against ground truth, not to sample the chain.
- **baseline is deliberately naive** (v2 IL + binary in-range), representing a builder without concentrated-liquidity expertise. A stronger baseline (e.g. one that knows v3 IL but not drift bands) would narrow the gap on IL but still miss the drift/rebalance nuance.
- **Trigger eval is with_skill-only.** It verifies the skill fires zero false-RED alerts on margin-in-range positions (the false-positive that would make an auto-monitor annoying). The baseline's binary in-range logic also produces no false-RED, so this is a guardrail on the skill, not a differentiator.
- **Live-RPC coverage** lives in `tests/test_fetch.py::test_live_rpc_decode` — an opt-in test (set `SOLANA_RPC_URL` + `SOLANA_TEST_POSITION`) that fetches and decodes a real mainnet position. CI runs the offline-fixture decode; the live test makes the "real read-only RPC" claim truthful rather than asserted.
