# CLAUDE.md — solana-position-manager-skill

This file activates the position-manager skill, agents, commands, and rules when this repo (or its installed copy) is the active Claude Code project.

## Project

A Solana AI Kit **skill addon** for managing CLMM/DLMM liquidity positions (Orca Whirlpools, Raydium CLMM, Meteora DLMM). See `README.md`.

## Skill routing

The skill entry point is `skill/SKILL.md`. It is a **lazy router** — load focused files only when a task needs them. Do not preload all `.md` files.

Intent → file map is defined inside `skill/SKILL.md`. Follow it.

## Agents

- `agents/position-analyst.md` — opus — analysis & rebalance *decision*.
- `agents/rebalance-engineer.md` — sonnet — SDK tx execution.

## Commands

- `/check-positions` — `commands/check-positions.md`
- `/il-report` — `commands/il-report.md`
- `/rebalance-suggest` — `commands/rebalance-suggest.md`
- `/monitor-setup` — `commands/monitor-setup.md`

## Rules (auto-load on file read)

- `rules/safe-rebalance.md` — gating rules for any rebalance execution.
- `rules/position-data-freshness.md` — freshness required before IL/fee measurement.

## Non-negotiables

1. **Simulate before execute.** No rebalance tx is signed until it is simulated/dry-run and the quote is reviewed. See `rules/safe-rebalance.md`.
2. **Freshness before measurement.** IL and fee numbers are meaningless on a stale tick. See `rules/position-data-freshness.md`.
3. **Real APIs only.** Every SDK function/program ID referenced in a `.md` must be current. If unsure, mark it "unverified" rather than invent one.
4. **User signs.** This skill never custodies keys; all signing is the user's wallet.

## Two-Strike Rule

If the same SDK call or rebalance step fails twice in a row, stop. Present the two errors verbatim and ask the user for guidance. Do not retry a third time blind.
