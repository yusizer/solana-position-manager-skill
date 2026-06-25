# Contributing

Thanks for considering a contribution to `solana-position-manager-skill`.

## Before you start

This skill is part of the Solana AI Kit bounty scope. The bar is **production-grade**: accurate, current to the 2026 stack, tested, and a clean fit for the kit's lazy-hub structure. Please match that bar.

## Scope of changes

- **Protocol facts** (program IDs, SDK function names, account layouts): must be real and current. Cite the source (official docs or SDK repo) in your PR. If you cannot verify, mark it `unverified` rather than guessing.
- **IL math**: changes to `skill/impermanent-loss.md` must be mirrored in `examples/il_math.py` and covered by `tests/test_il.py`. A docs edit that breaks a test is a bug in the docs, not the test.
- **Heuristics** (`range-alerts.md`, `rebalance.md`): keep them measurable. Prefer a formula or threshold over prose.

## Workflow

1. Fork → branch `feat/<topic>` (or `fix/<topic>`).
2. Make your change. Keep `skill/SKILL.md` a router — push detail into focused files.
3. Verify locally:
   ```bash
   ./validate.sh
   python tests/test_il.py
   ```
4. If you touched the installer, dry-run it:
   ```bash
   ./install.sh -y --claude-dir=/tmp/.claude-test
   ```
5. Open a PR with: what changed, why, and links to any sources you used for protocol facts.

## Style

- Markdown files: token-efficient, scannable tables, code only where it is real API usage.
- Shell scripts: `set -euo pipefail`, POSIX-compatible, no bashisms that break on macOS/Linux.
- Python: zero third-party deps for the math/examples (so CI stays simple); stdlib only.

## Reporting issues

Open an issue with: protocol, SDK version, what you expected vs what the skill produced, and a reproducible snippet.
