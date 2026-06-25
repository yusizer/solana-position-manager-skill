# PR body — solanabr/skill-bounty

Title: `Add solana-position-manager-skill`

## What

A new Solana AI Kit skill for managing concentrated-liquidity (CLMM/DLMM) positions across **Orca Whirlpools**, **Raydium CLMM**, and **Meteora DLMM** — the full LP position lifecycle: measure → monitor → rebalance.

It advances the `position-manager-skill` seed idea from the listing into a production-grade, standalone skill.

## Problem it solves

Concentrated liquidity turns LPing into an active management job that most builders get wrong: positions silently drift out of range and stop earning; IL is larger and non-obvious in narrow ranges; rebalancing is done by feel (too often or too late); and three protocols with different models (tick ranges vs discrete bins) make every script bespoke. No existing kit skill covers the LP position lifecycle end-to-end.

## Structure (matches solana-game-skill)

```
solana-position-manager/
├── skill/SKILL.md          # lazy routing hub
├── skill/{whirlpools,raydium-clmm,meteora-dlmm,impermanent-loss,
│          range-alerts,rebalance,backtest,monitoring,resources}.md
├── agents/                 # position-analyst (opus), rebalance-engineer (sonnet)
├── commands/               # /check-positions, /il-report, /rebalance-suggest, /monitor-setup
├── rules/                  # safe-rebalance, position-data-freshness
├── examples/               # il_math.py (pure-Python IL math), il_calc.py (CLI)
├── tests/                  # 16 unit tests pinning the documented formulas
├── install.sh / install-custom.sh / validate.sh
├── CLAUDE.md / README.md / QUICK-START.md / CONTRIBUTING.md
├── .github/workflows/validate.yml   # CI: validate + tests + install dry-run
└── LICENSE (MIT)
```

## Why it's production-grade

- **Accurate & current to 2026:** program IDs and SDK function names verified against the official SDK repos/docs (Orca `@orca-so/whirlpools` 8.x incl. `resetPositionRangeInstructions`; Raydium `raydium-sdk-v2` 0.2.55-alpha; Meteora `@meteora-ag/dlmm` 1.9.10 incl. atomic `rebalancePosition`). Unverified items are marked, not invented.
- **Tested:** the IL math in `skill/impermanent-loss.md` is implemented in `examples/il_math.py` and pinned by `tests/test_il.py` (16 tests, including a cross-check of the v2-amplification formula against the direct value-function formula). CI runs them on every push.
- **Token-efficient:** `SKILL.md` is a router; detail lives in focused files loaded on demand.
- **Safe:** `rules/safe-rebalance.md` gates every rebalance (simulate-before-sign, cooldown, size guard, freshness re-check); the skill never custodies keys.

## Judging criteria

- **Usefulness:** recurring LP pain (out-of-range, IL, when-to-rebalance) across the 3 dominant Solana CLMM/DLMM protocols.
- **Novelty:** no kit skill covers LP position lifecycle management; includes the exact concentrated-IL amplification formula (λ = capital efficiency = IL multiplier) with verified worked examples.
- **Quality:** verified SDK calls, executable + unit-tested math, CI, working installer, clean lazy-hub structure.
- **Fit:** mirrors `solana-game-skill` shape; installs via `install.sh`; MIT.

## Install

```bash
git clone https://github.com/yusizer/solana-position-manager-skill.git
cd solana-position-manager-skill
./validate.sh && python tests/test_il.py
./install.sh -y
```

## Bounty submission

- Listing: https://earn.superteam.fun/listings/superteambr/skills
- Standalone repo: https://github.com/yusizer/solana-position-manager-skill
- License: MIT
