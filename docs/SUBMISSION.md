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
- [x] `validate.sh` 38/38, **25/25 tests green**, CI workflow
- [ ] **Submit PR link + questionnaire on the listing  ← only step left (you do this)**

## Paste into the listing form

### Q1. Did you contribute towards existing repos or is it a new idea?
New idea, shipped as our own production-grade repo. It advances one of the gaps the sponsors seeded (position-manager-skill) but is built from scratch as a standalone, installable skill — covering three protocols (Orca Whirlpools, Raydium CLMM, Meteora DLMM) with executable, unit-tested impermanent-loss math, out-of-range alert thresholds, rebalance heuristics, a real read-only Solana RPC position decoder, a runnable DLMM SDK example, an opt-in Claude Code hook, and CI. No existing kit skill covers the CLMM/DLMM position lifecycle end-to-end.

### Q2. What is your closest "competing" skill?
No kit skill covers LP position lifecycle management. Closest references:
- `jup-ag/agent-skills` — Jupiter swaps/lend, not position/range/IL management.
- `sendaifun/skills` — DeFi primitives, not concentrated-LP lifecycle.
- `helius-labs/core-ai` — RPC/infra, not LP analytics.
- Orca/Raydium/Meteora SDK examples — snippet-level fetch code, no IL math, no out-of-range alerts, no rebalance decision framework.
This skill is the first to bundle measure → monitor → rebalance with real concentrated-IL math (unit-tested, incl. the exact λ-amplification formula), real on-chain Position decoding via RPC, and safe-execution rules.

### Q3. Links/proofs showing why you should be the creator of this skill (founder-market fit)
- Standalone repo + PR (links above) — production structure matching `solana-game-skill`: `skill/SKILL.md` lazy router, `agents/`, `commands/`, `rules/`, `install.sh`, MIT.
- **Executable & tested:** `examples/il_math.py` + `examples/fetch_position.py` (real read-only Solana RPC decoding the verified 216-byte Orca Position layout, stdlib only) + `tests/` — **25 unit tests pass** (IL math, v2-amplification cross-check, position decode, base58, CLI smoke).
- **CI green badge** (`.github/workflows/validate.yml`) — validate + tests + installer dry-run on every push/PR. CI lives in the PR diff itself (rare among submissions).
- **Three-protocol coverage** with verified program IDs/SDK (Orca `@orca-so/whirlpools` 8.x incl. `resetPositionRangeInstructions`; Raydium `raydium-sdk-v2` 0.2.55; Meteora `@meteora-ag/dlmm` 1.9.10 incl. atomic `rebalancePosition`) + a runnable DLMM TS example (`examples/dlmm/`).
- **Novel angles:** verified IL-by-range-width benchmark table (λ amplification), and an opt-in Claude Code `Stop` hook for auto-alerts (`hooks/range-alert-hook.sh`) — no other submission uses hooks.
- Verification matrix, comparison vs kit skills, and "When NOT to use" in the README.

## Links to attach
- PR: https://github.com/solanabr/skill-bounty/pull/54
- Repo: https://github.com/yusizer/solana-position-manager-skill

## Contact
Listing contact: @kauenet (Kaue Cano).
