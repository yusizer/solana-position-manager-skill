# Demo — solana-position-manager-skill happy path

A verbatim, copy-pasteable transcript of the core flow: **fetch a position →
measure IL → decide a rebalance**. Run offline (synthetic fixture) — no RPC, no
keys. Reproduces the numbers in `docs/EVAL.md`.

## 1. Measure impermanent loss for a position

A SOL/USDC position on Orca Whirlpools, range [140, 210], opened at 170, now at
200.

```bash
$ python examples/il_math.py
{'in_range': True, 'v_lp': 2.651, 'v_hodl': 2.744, 'il_pct': -3.4, 'price_ratio': 1.176}
```

V_LP = 2.651, V_HODL = 2.744 → **IL = −3.40%** vs HODL (matches the worked
example in `skill/impermanent-loss.md` §5 and `tests/test_il.py`).

## 2. Drift level (in-range / near-edge / out-of-range)

```python
>>> from tests.test_eval import skill_level
>>> skill_level(-55440, 55440, 50000)   # drift = 0.90 -> near upper edge
'RED'                                    # YELLOW band is 0.2-0.8; 0.90 is RED-near-edge
>>> skill_level(-1000, 1000, 850)       # drift = 0.925
'YELLOW'
>>> skill_level(-1000, 1000, 0)         # dead center
'GREEN'
```

The skill's three bands (GREEN 0.2–0.8, YELLOW 0.05–0.2 / 0.8–0.95, RED <0.05 /
>0.95 + out) catch a position drifting to a dangerous edge while still
nominally in range — the case a binary in-range check misses.

## 3. Rebalance decision (fee-vs-IL gated)

```python
>>> from tests.test_eval import skill_rebalance
>>> skill_rebalance(-55440, 55440, 60000, il_frac=-0.30, fee_ratio=0.0)
'WITHDRAW'   # out of range + catastrophic IL + fees never cover -> cut
>>> skill_rebalance(-55440, 55440, -52000, il_frac=-0.05, fee_ratio=0.06)
'WIDEN'      # near edge, fees cover IL -> widen
>>> skill_rebalance(-1000, 1000, 960, il_frac=-0.04, fee_ratio=0.01)
'HOLD'       # near edge but fees don't cover IL -> hold (don't widen into a loss)
```

HOLD / WIDEN / MOVE / WITHDRAW gated by whether fees cover |IL| — the decision a
"rebalance whenever near the edge" heuristic gets wrong (it would WIDEN the
last case into a losing position).

## 4. Run the full quantified eval

```bash
$ python tests/test_eval.py
======================================================================
solana-position-manager-skill — quantified eval (offline, reproducible)
======================================================================
suite                          baseline   with_skill   total
--------------------------------------------------------------------
IL computation                        4            6       6
in-range / drift level                7           10      10
rebalance decision                    5            8       8
--------------------------------------------------------------------
TOTAL task correctness               16           24      24

Trigger false-positive: 0/12 false-RED on margin-in-range (target 0) -> PASS
======================================================================
RESULT: with_skill 24/24 vs baseline 16/24 | false-RED 0/12 -> PASS
```

The baseline is a fair ablation (knows symmetric-range concentrated IL, coarse
drift, widen-near-edge); the skill's 8-task edge is the asymmetric-IL formula,
the RED-near-edge band, and the fee-gated WITHDRAW. Full methodology:
[`EVAL.md`](EVAL.md).

## 5. (Optional) Live mainnet decode

```bash
$ SOLANA_RPC_URL=https://api.mainnet-beta.solana.com \
  SOLANA_TEST_POSITION=<a real Orca Position pubkey> \
  python tests/test_fetch.py
```

Fetches and decodes a real 216-byte Orca Position account (read-only, no keys)
and cross-checks the tick range. Skipped in CI without the env vars.
