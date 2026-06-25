# Changelog

All notable changes to this skill are documented here. Versions follow the skill's `skill/SKILL.md` `name` lifecycle.

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
