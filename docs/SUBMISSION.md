# Superteam listing submission — final

Listing: https://earn.superteam.fun/listings/superteambr/skills
Bounty: "Ship useful agent skills we can add to Solana AI Kit"
Deadline: 2026-07-01
Reward: 3 000 USDG across 10 winners (1–5 = 400, 6–10 = 200)

## Deliverables (all done)

- [x] Public GitHub repo: https://github.com/yusizer/solana-position-manager-skill (default branch `main`)
- [x] PR to https://github.com/solanabr/skill-bounty — **#54**: https://github.com/solanabr/skill-bounty/pull/54
- [x] README (what / problem / install)
- [x] SKILL.md entry point following kit structure (lazy router)
- [x] MIT licensed
- [x] `validate.sh` 38/38, **26/26 tests green** + quantified **eval 24/24 vs baseline 10/24**, CI workflow (incl. DLMM `tsc` typecheck)
- [x] Live GitHub Pages landing (`docs/index.html` + `deploy-pages.yml`)
- [ ] **Submit PR link + questionnaire on the listing  ← only step left (you do this)**

## Paste into the listing form

### Q1. Did you contribute towards existing repos or is it a new idea?
New idea, shipped as our own production-grade repo. It advances one of the gaps the sponsors seeded (position-manager-skill) but is built from scratch as a standalone, installable skill — covering the full Solana AMM landscape: three concentrated protocols managed end-to-end (Orca Whirlpools, Raydium CLMM, Meteora DLMM) plus the two constant-product baselines scope-clarified (Raydium CPMM, Meteora DAMM v2 — the λ=1 v2 case). It ships executable, unit-tested impermanent-loss math (incl. the exact λ-amplification formula), out-of-range alert thresholds, rebalance heuristics, a read-only Solana RPC position decoder (offline-fixture tested in CI + opt-in live-RPC test), a runnable DLMM SDK TypeScript example (`tsc`-clean, typechecked in CI), an opt-in Claude Code hook, a quantified eval suite (24/24 vs 10/24 baseline), a live GitHub Pages landing, and CI. No existing kit skill covers the CLMM/DLMM position lifecycle end-to-end.

### Q2. What is your closest "competing" skill?
No kit skill covers LP position lifecycle management. Closest references:
- `jup-ag/agent-skills` — Jupiter swaps/lend, not position/range/IL management.
- `sendaifun/skills` — DeFi primitives, not concentrated-LP lifecycle.
- `helius-labs/core-ai` — RPC/infra, not LP analytics.
- Orca/Raydium/Meteora SDK examples — snippet-level fetch code, no IL math, no out-of-range alerts, no rebalance decision framework.
This skill is the first to bundle measure → monitor → rebalance with real concentrated-IL math (unit-tested, incl. the exact λ-amplification formula λ = √k/(√k−1) — capital efficiency = IL multiplier), on-chain Position decoding via a read-only RPC decoder (offline-fixture tested in CI + opt-in live-RPC test), a quantified eval suite (with-skill 24/24 vs naive baseline 10/24, 0/12 false-positive triggers), a `tsc`-clean DLMM SDK example, and safe-execution rules.

### Q3. Links/proofs showing why you should be the creator of this skill (founder-market fit)
- Standalone repo + PR (links above) — production structure matching `solana-game-skill`: `skill/SKILL.md` lazy router, `agents/`, `commands/`, `rules/`, `install.sh`, MIT.
- **Executable & tested:** `examples/il_math.py` + `examples/fetch_position.py` (read-only Solana RPC decoder of the verified 216-byte Orca Position layout, stdlib only; offline-fixture tested in CI + opt-in live-RPC test) + `tests/` — **26 unit tests pass** (IL math, v2-amplification cross-check, position decode, base58, CLI smoke). Plus `tests/test_eval.py` — **quantified eval: with-skill 24/24 vs baseline 10/24, 0/12 false-positive triggers** (runs in CI).
- **CI green badge** (`.github/workflows/validate.yml`) — validate + IL + decode + **eval** + DLMM **`tsc` typecheck** + installer dry-run on every push/PR. CI lives in the PR diff itself (rare among submissions).
- **Full Solana AMM coverage (5 programs):** three concentrated managed end-to-end with verified program IDs/SDK (Orca `@orca-so/whirlpools` 8.x incl. `resetPositionRangeInstructions`; Raydium `raydium-sdk-v2` 0.2.55; Meteora `@meteora-ag/dlmm` 1.9.10 incl. atomic `rebalancePosition`) + two constant-product scope-clarified (Raydium CPMM `CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C`; Meteora DAMM v2 `cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG` via `@meteora-ag/cp-amm-sdk` 1.4.4) — the skill knows what it does *and* does not actively manage (λ=1 vs λ>1).
- **Runnable typed example:** `examples/dlmm/` TS on the real `@meteora-ag/dlmm` SDK — `tsc --noEmit` clean, typechecked in CI (monitor + atomic rebalance, simulate-only).
- **Live site:** GitHub Pages landing (`docs/index.html` + `deploy-pages.yml`).
- **Novel angles:** the exact concentrated-IL λ-amplification formula (capital efficiency = IL multiplier) with verified worked examples, an IL-by-range-width benchmark table, and an opt-in Claude Code `Stop` hook for auto-alerts (`hooks/range-alert-hook.sh`) — no other submission uses hooks.
- Verification matrix, comparison vs kit skills, and "When NOT to use" in the README; full eval report in `docs/EVAL.md`.

## Links to attach
- PR: https://github.com/solanabr/skill-bounty/pull/54
- Repo: https://github.com/yusizer/solana-position-manager-skill
- Live site: https://yusizer.github.io/solana-position-manager-skill/ (live — GitHub Pages)
- Eval report: https://github.com/yusizer/solana-position-manager-skill/blob/main/docs/EVAL.md

## Contact
Listing contact: @kauenet (Kaue Cano).
