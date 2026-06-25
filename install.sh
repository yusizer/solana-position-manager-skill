#!/usr/bin/env bash
# install.sh — standard installer for solana-position-manager-skill
# Installs the skill (and optionally agents/commands) into ~/.claude and
# appends a skill reference to ~/.claude/CLAUDE.md.
#
# Usage:
#   ./install.sh            # interactive prompts
#   ./install.sh -y         # non-interactive, defaults, no prompts
#   ./install.sh -y --no-agents   # skill only, skip agents/commands
set -euo pipefail

INTERACTIVE=1
INSTALL_AGENTS=1
CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
SKILL_NAME="solana-position-manager"

for arg in "$@"; do
  case "$arg" in
    -y|--yes) INTERACTIVE=0 ;;
    --no-agents) INSTALL_AGENTS=0 ;;
    --claude-dir=*) CLAUDE_DIR="${arg#*=}" ;;
    -h|--help)
      sed -n '2,11p' "$0"; exit 0 ;;
    *) echo "Unknown flag: $arg" >&2; exit 2 ;;
  esac
done

SKILLS_DIR="$CLAUDE_DIR/skills"
DEST="$SKILLS_DIR/$SKILL_NAME"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

bold() { printf '\033[1m%s\033[0m\n' "$*"; }
warn() { printf '\033[33m! %s\033[0m\n' "$*"; }
ok()   { printf '\033[32m✓ %s\033[0m\n' "$*"; }

command -v git >/dev/null || { warn "git not found on PATH — install git first."; exit 1; }

mkdir -p "$SKILLS_DIR"

# Skill
if [ -d "$DEST" ]; then
  if [ "$INTERACTIVE" -eq 1 ]; then
    read -rp "Skill '$SKILL_NAME' already exists at $DEST. Overwrite? [y/N] " yn
    case "$yn" in y|Y) rm -rf "$DEST";; *) warn "Aborted."; exit 1;; esac
  else
    rm -rf "$DEST"
  fi
fi
cp -r "$SCRIPT_DIR/skill" "$DEST"
ok "Installed skill → $DEST"

# Agents + commands (optional)
if [ "$INSTALL_AGENTS" -eq 1 ]; then
  if [ -d "$SCRIPT_DIR/agents" ]; then mkdir -p "$CLAUDE_DIR/agents"; cp -r "$SCRIPT_DIR/agents/." "$CLAUDE_DIR/agents/"; ok "Installed agents → $CLAUDE_DIR/agents/"; fi
  if [ -d "$SCRIPT_DIR/commands" ]; then mkdir -p "$CLAUDE_DIR/commands"; cp -r "$SCRIPT_DIR/commands/." "$CLAUDE_DIR/commands/"; ok "Installed commands → $CLAUDE_DIR/commands/"; fi
fi

# CLAUDE.md skill reference
CLAUDE_FILE="$CLAUDE_DIR/CLAUDE.md"
mkdir -p "$CLAUDE_DIR"
touch "$CLAUDE_FILE"
MARKER="<!-- solana-position-manager-skill -->"
if ! grep -q "$MARKER" "$CLAUDE_FILE" 2>/dev/null; then
  {
    printf '\n%s\n' "$MARKER"
    printf '## Solana Position Manager skill\n\n'
    printf 'Skill installed at `%s`. Entry point: `skill/SKILL.md` (lazy router).\n' "$DEST"
    printf 'Covers CLMM/DLMM position management: Orca Whirlpools, Raydium CLMM, Meteora DLMM.\n'
    printf 'Commands: /check-positions, /il-report, /rebalance-suggest, /monitor-setup.\n'
    printf '%s\n' "<!-- /solana-position-manager-skill -->"
  } >> "$CLAUDE_FILE"
  ok "Appended skill reference → $CLAUDE_FILE"
else
  ok "CLAUDE.md already references the skill — skipped."
fi

# Core skill presence check (non-fatal)
if [ ! -d "$SKILLS_DIR/solana-dev" ] && [ ! -d "$SKILLS_DIR/ext/solana-dev" ]; then
  warn "Core 'solana-dev-skill' not found in $SKILLS_DIR."
  warn "This addon references it. Install the Solana AI Kit (https://github.com/solanabr/solana-ai-kit) for the core."
fi

bold "Done. Restart Claude Code to pick up the new skill."
