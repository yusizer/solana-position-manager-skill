# Changelog

All notable changes to this skill are documented here. Versions follow the skill's `skill/SKILL.md` `name` lifecycle.

## [0.3.0] — 2026-06-25

### Added — competitive hardening (vs skill-bounty #49–53)
- `examples/fetch_position.py` — real read-only Solana RPC client (stdlib only): `getAccountInfo` + decode the verified 216-byte Orca Whirlpools `Position` layout, then in-range / drift / IL. `--offline` fixture for tests.
- `tests/test_fetch.py` — 9 tests (Position decode, base58 roundtrip, analyze in/out-of-range, CLI smoke). Total tests now 25.
- `hooks/range-alert-hook.sh` + `skill/hooks.md` — opt-in Claude Code `Stop` hook for auto-alerts on out-of-range drift (no competitor uses hooks). Always exits 0, bounded, read-only.
- `assets/preview-card.svg` — 1200×630 preview card for skill listings.
- README: "Verified program IDs & SDK (2026)" table, "How it compares to kit skills" table, "When NOT to use this skill", "Verification" matrix, "Default stack (2026)" table.
- CI runs `tests/test_fetch.py` + `fetch_position.py --offline` smoke.

### Changed
- `skill/SKILL.md` routing adds "Auto-alert via Claude Code hook" → `hooks.md`.

## [0.2.0] — 2026-06-25

### Added
- `skill/benchmarks.md` — verified IL-by-range-width table (λ amplification, v2 baseline) + range-choice decision shortcut. Numbers produced by `examples/il_math.py`.
- `examples/dlmm/` — runnable TypeScript reference on `@meteora-ag/dlmm` 1.9.x: `monitor.ts` (read-only out-of-range/drift alerts, dynamic-fee read), `rebalance.ts` (atomic rebalance via `simulateRebalancePositionWithBalancedStrategy` + `rebalancePosition`, simulate-only). `package.json`, `tsconfig.json`, `.env.example`, `README.md`.
- `assets/architecture.svg` — measure → monitor → decide → execute diagram, embedded in README.
- README badges (CI, MIT, tests, Solana) + architecture diagram.
- v2 reference + symmetric-amplification math in `skill/impermanent-loss.md` (§4): exact `IL_v3 = λ·IL_v2`, `λ = √k/(√k−1)`, verified worked examples.
- `il_v2`, `amplification_lambda`, `il_v3_symmetric` in `examples/il_math.py` + 7 new tests (cross-check of the two formulas, tighter-range-more-IL, out-of-range rejection). Tests now 16.

### Changed
- `skill/SKILL.md` routing table adds a "which range width / IL by range" row → `benchmarks.md`.
- `.gitignore` adds `dist/`, `*.tsbuildinfo`.

## [0.1.0] — 2026-06-25

### Added
- Initial skill: `skill/SKILL.md` router + 9 focused files (`whirlpools`, `raydium-clmm`, `meteora-dlmm`, `impermanent-loss`, `range-alerts`, `rebalance`, `backtest`, `monitoring`, `resources`).
- `agents/` (position-analyst opus, rebalance-engineer sonnet), `commands/` (`/check-positions`, `/il-report`, `/rebalance-suggest`, `/monitor-setup`), `rules/` (safe-rebalance, position-data-freshness).
- `examples/il_math.py`, `examples/il_calc.py` (pure-Python, zero deps).
- `tests/test_il.py` (9 tests).
- `install.sh`, `install-custom.sh`, `validate.sh`, `CLAUDE.md`, `README.md`, `QUICK-START.md`, `CONTRIBUTING.md`, `LICENSE` (MIT), `.gitignore`, `.gitattributes`, `.github/workflows/validate.yml`.
