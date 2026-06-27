# Rubric checklist — solana-position-manager-skill

Maps each bounty judging criterion to the concrete evidence in this repo, so a
reviewer can verify every claim in two clicks. Bounty criteria (from the
Superteam Brasil listing): **Usefulness · Novelty · Quality · Fit**.

## Usefulness — solves a real, important problem for builders

- `README.md` → "The problem" — concentrated-LP lifecycle is an active mgmt job most builders get wrong; no kit skill covers it end-to-end.
- `skill/SKILL.md` → "Core loop" — measure → monitor → rebalance.
- `commands/` → `/check-positions`, `/il-report`, `/rebalance-suggest`, `/monitor-setup` (4 user-invocable commands).
- `examples/fetch_position.py` → read-only Solana RPC position decoder (216-byte Orca Position, stdlib only).
- `examples/il_math.py` → executable concentrated-IL math.
- `examples/dlmm/rebalance.ts` → runnable atomic-rebalance example.
- `hooks/range-alert-hook.sh` → opt-in Claude Code `Stop` hook for auto-alerts.

## Novelty — fills a genuine gap in the ecosystem

- `docs/EVAL.md` → "Where the baseline loses" + the gap analysis: the kit's sendai orca/meteora/raydium skills ship position CRUD + fee claim, **not** IL-measurement / drift-alert / rebalance-decision / monitoring.
- `examples/il_math.py` + `tests/test_il.py::test_il_v3_matches_compute_il_cross_check` → the exact λ-amplification formula via **two independent computation paths** (§2 `compute_il` + §4 `il_v3_symmetric`) — a genuine cross-check, not a single implemented formula.
- `skill/SKILL.md` → "What this skill does NOT manage" — CPMM/DAMM v2 λ=1 scope clarification (the skill knows what it does *not* actively manage).
- Honest differentiation vs other position-manager submissions (`docs/SUBMISSION.md` Q2).

## Quality — production-grade, accurate, tested, well-documented

- `tests/test_il.py` → **16 IL-math tests** (worked examples, v2-amplification cross-check, out-of-range, invalid inputs).
- `tests/test_fetch.py` → **10 decode + analysis tests** (+ opt-in live-RPC test).
- `tests/test_eval.py` → **quantified eval: with-skill 24/24 vs fair ablation 16/24, 0/12 false-positive triggers**; references derived independently of the skill's eval path (not self-referential).
- `examples/dlmm/` → `tsc --noEmit` clean vs real `@meteora-ag/dlmm` (typechecked in CI).
- `validate.sh` → 60/60 structure + intra-skill link checks.
- `.github/workflows/validate.yml` → CI: validate + IL + decode + **eval** + DLMM **tsc** + installer real-install test.
- `skill/*.md` → 11 reference docs; program IDs verified against `declare_id!`/SDK docs.
- `docs/EVAL.md` → full methodology + scope & limitations (honest about offline/synthetic).

## Fit — follows the kit structure, coexists with other skills

- `skill/SKILL.md` → lazy router (the kit's progressive-disclosure pattern).
- `agents/`, `commands/`, `rules/` → bundled (kit convention).
- `install.sh` → kit-style install into `.claude/`.
- `CLAUDE.md` → skill activation + non-negotiables + two-strike rule.
- `skill/SKILL.md` → "When to load this skill" intent→file table (routes away from adjacent skills).
- Negative-scope: CPMM/DAMM v2 redirect to the λ=1 v2 case; routes execution to protocol skills after explicit approval.

## Verification commands (reproduce in <1 min)

```bash
python tests/test_il.py        # 16/16
python tests/test_fetch.py     # 10/10
python tests/test_eval.py      # 24/24 vs 16/24, exit 0
bash install.sh --dry-run      # structure OK
```
