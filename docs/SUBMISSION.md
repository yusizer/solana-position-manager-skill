# Superteam listing submission — notes

Listing: https://earn.superteam.fun/listings/superteambr/skills
Bounty: "Ship useful agent skills we can add to Solana AI Kit"
Deadline: 2026-07-01
Reward: 3 000 USDG across 10 winners (1–5 = 400, 6–10 = 200)

## Deliverables checklist

- [ ] Public GitHub repo: https://github.com/yusizer/solana-position-manager-skill
- [ ] PR to https://github.com/solanabr/skill-bounty (novel skill)
- [ ] README explains what it does / problem / install  ✓ (in repo)
- [ ] SKILL.md entry point following kit structure  ✓
- [ ] MIT licensed  ✓
- [ ] `validate.sh` + tests green  ✓
- [ ] Submit PR link + questionnaire on the listing

## Questionnaire answers (paste into the listing form)

**Q1. Did you contribute towards existing repos or is it a new idea?**
New idea, shipped as our own production-grade repo. It advances one of the gaps the sponsors seeded (position-manager-skill) but is built from scratch as a standalone, installable skill — covering three protocols (Orca Whirlpools, Raydium CLMM, Meteora DLMM) with executable IL math, alert thresholds, rebalance heuristics, a monitor scaffold, and CI-tested code. No existing kit skill covers the CLMM/DLMM position lifecycle end-to-end.

**Q2. What is your closest "competing" skill?**
No kit skill covers LP position lifecycle management. Closest references:
- `jup-ag/agent-skills` — Jupiter swaps/lend, not position/range/IL management.
- `sendaifun/skills` — DeFi primitives, not concentrated-LP lifecycle.
- Orca/Raydium/Meteora SDK examples — snippet-level fetch code, no IL math, no out-of-range alerts, no rebalance decision framework.
This skill is the first to bundle measure → monitor → rebalance with real concentrated-IL math (unit-tested) and safe-execution rules.

**Q3. Links/proofs showing why you should be the creator of this skill (founder-market fit).**
- Repo + PR (see links above) — production structure matching `solana-game-skill`: `skill/SKILL.md` router, `agents/`, `commands/`, `rules/`, installers, MIT.
- Executable, tested math: `examples/il_math.py` + `tests/test_il.py` (9 passing tests pinning the documented formulas) — the IL section is not prose, it is verified code.
- CI green badge (`.github/workflows/validate.yml`) — structure, links, tests, and an installer dry-run run on every push.
- Three-protocol coverage with protocol-specific position layout, in-range detection, fee mechanics, and rebalance tx order.

## Contact

Listing contact: @kauenet (Kaue Cano).
