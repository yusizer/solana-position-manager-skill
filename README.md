# solana-position-manager-skill

![CI](https://github.com/yusizer/solana-position-manager-skill/actions/workflows/validate.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-14f195.svg)
![Tests: 16](https://img.shields.io/badge/tests-16%20passing-9945ff.svg)
![Solana](https://img.shields.io/badge/Solana-CLMM%2FDLMM-14f195.svg)

A Claude Code / Codex skill addon for **managing concentrated-liquidity (CLMM/DLMM) positions on Solana** across **Orca Whirlpools**, **Raydium CLMM**, and **Meteora DLMM**.

<p align="center"><img src="assets/architecture.svg" alt="Position manager skill architecture" width="780"></p>

It extends the core [`solana-dev-skill`](https://github.com/solanabr/solana-dev-skill) with a focused discipline that nobody in the kit covers end-to-end: the **lifecycle of an LP position** — from fetching it, to measuring impermanent loss, to detecting out-of-range drift, to deciding and safely executing a rebalance, to monitoring it on a schedule.

> Solana AI Kit bounty submission. Built to slot cleanly into the standard kit.

## The problem it solves

Concentrated liquidity lets LPs pick a price range and earn far more fees than v2 AMMs — but it turns liquidity providing into an **active management job** that most builders get wrong:

- Positions silently drift **out of range** and stop earning fees (no alerts).
- **Impermanent loss** is larger and non-obvious in concentrated ranges; nobody measures it properly.
- "Rebalancing" is done by feel — too often (burning gas), or too late (missing fees).
- Three protocols with **different models** (Orca/Raydium = tick ranges, Meteora = discrete bins) and different SDKs mean every script is bespoke.

This skill gives an agent the **measurable, repeatable** version: real IL math, current SDK calls, alert thresholds, and rebalance heuristics with the tradeoffs spelled out.

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │  skill/SKILL.md  (routing hub, lazy)     │
                    └───────────────┬─────────────────────────┘
            measure │               │ decide            │ execute
   ┌────────────────┼───────────────┼───────────────────┼───────────────┐
   ▼                ▼               ▼                   ▼               ▼
whirlpools.md   raydium-clmm.md  meteora-dlmm.md   impermanent-loss.md range-alerts.md
   │                │               │                   │               │
   └────────────────┴───────────────┴────────┬──────────┴───────────────┘
                                            ▼
                                      rebalance.md ──► backtest.md
                                            │
                                            ▼
                                  rules/safe-rebalance.md
```

The skill references the core `solana-dev-skill` for program/CLI/testing basics and only loads the file relevant to the current step.

## Skill files

| File | What it gives the agent |
|---|---|
| `skill/SKILL.md` | Entry point. Routes to the right file by intent. |
| `skill/whirlpools.md` | Orca Whirlpools: SDK, program ID, position layout, fetch, in-range check, fees, rebalance tx order. |
| `skill/raydium-clmm.md` | Raydium CLMM: Position NFT layout, SDK, tick math, in-range, fees, rebalance. |
| `skill/meteora-dlmm.md` | Meteora DLMM: bin model, dynamic fees, position layout, SDK, in-range by active bin, rebalance. |
| `skill/impermanent-loss.md` | Concentrated-IL math, worked example, how it differs from v2 IL, how to compute it from tick/price. |
| `skill/benchmarks.md` | Verified IL-by-range-width table (λ amplification) + range-choice decision shortcut. |
| `skill/range-alerts.md` | Out-of-range detection, distance-from-tick thresholds, fee-to-principal ratio alerts. |
| `skill/rebalance.md` | Rebalance decision heuristics: widen vs move vs withdraw; gas-vs-fees tradeoff; anti-over-rebalance. |
| `skill/backtest.md` | Fee APR, IL, return-vs-HODL; historical tick/fee data sources; evaluation metrics. |
| `skill/monitoring.md` | Scheduled fetch + alert wiring (Helius/RPC, webhooks, cron). |
| `skill/resources.md` | SDK packages, program IDs, official docs, data providers. |

## Agents

| Agent | Model | Purpose |
|---|---|---|
| `position-analyst` | opus | Deep position analysis: IL computation, range strategy, rebalance *decision*. |
| `rebalance-engineer` | sonnet | SDK transaction execution: fetch → quote → simulate → sign → confirm. |

## Commands

| Command | Purpose |
|---|---|
| `/check-positions <wallet>` | List all CLMM/DLMM positions for a wallet with in-range status and accrued fees. |
| `/il-report <position>` | Full impermanent-loss report vs HODL for one position. |
| `/rebalance-suggest <position>` | Rebalance recommendation with reasoning and expected fee/IL delta. |
| `/monitor-setup` | Scaffold a scheduled monitor + alert for out-of-range drift. |

## Rules (auto-loading)

- `rules/safe-rebalance.md` — never execute without simulate/dry-run; minimum-cooldown between rebalances; position-size guards.
- `rules/position-data-freshness.md` — require fresh tick/price (<60s) before measuring IL; reject stale quotes.

## Installation

### Automated (defaults)

```bash
curl -fsSL https://raw.githubusercontent.com/yusizer/solana-position-manager-skill/main/install.sh | bash
```

Installs to `~/.claude/skills/solana-position-manager/` and appends the skill reference to `~/.claude/CLAUDE.md`. Assumes the core `solana-dev-skill` is already installed (the kit installs it by default).

### Interactive

```bash
./install-custom.sh
```

Choose install location (`~/.claude/skills/` or `./.claude/skills/` for the current project) and whether to touch `CLAUDE.md`.

### Manual

```bash
git clone https://github.com/yusizer/solana-position-manager-skill.git
cp -r solana-position-manager-skill/skill ~/.claude/skills/solana-position-manager
cp -r solana-position-manager-skill/agents ~/.claude/agents/   # optional
cp -r solana-position-manager-skill/commands ~/.claude/commands/ # optional
```

## Examples & tests (the math is executable, not just prose)

This skill ships runnable artifacts so the IL math and installer are **tested**, not asserted:

- `examples/il_math.py` — pure-Python implementation of the concentrated-IL formulas in `skill/impermanent-loss.md` (zero deps).
- `examples/il_calc.py` — CLI calculator. `python examples/il_calc.py --pa 140 --pb 210 --p0 170 --p 200 --principal 10000 --fees 320`.
- `examples/dlmm/` — runnable TypeScript reference on the real `@meteora-ag/dlmm` SDK: `monitor.ts` (read-only out-of-range alerts) + `rebalance.ts` (atomic rebalance, simulate-only). See `examples/dlmm/README.md`.
- `tests/test_il.py` — unit tests pinning the worked example and edge cases (out-of-range above/below, L-independence, fee break-even, v2-amplification cross-check). `python tests/test_il.py` → 16 passing.
- `.github/workflows/validate.yml` — CI runs `validate.sh` + the tests + an installer dry-run on every push/PR.
- `validate.sh` — structure, required-files, and intra-skill link check.
- `assets/architecture.svg` — the measure → monitor → decide → execute loop, for docs/PRs.

```bash
./validate.sh               # structure + links
python tests/test_il.py     # 9 IL-math tests
```

## Development workflow

- Fork → branch `feat/<topic>` → PR.
- Keep `.md` files **token-efficient**: SKILL.md stays a router; push detail into the focused files.
- Every SDK call in a `.md` must use **real, current** function names. If an API changes, update the file and note the version in `resources.md`.
- Run `./validate.sh` and `python tests/test_il.py` before pushing. CI enforces both.

## License

MIT © 2026 yusizer
