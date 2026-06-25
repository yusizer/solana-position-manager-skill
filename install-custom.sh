#!/usr/bin/env bash
# install-custom.sh — interactive installer with a menu.
# Lets you choose install scope (personal vs project), whether to install
# agents/commands, and whether to touch CLAUDE.md.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_NAME="solana-position-manager"

bold() { printf '\033[1m%s\033[0m\n' "$*"; }
ok()   { printf '\033[32m✓ %s\033[0m\n' "$*"; }
warn() { printf '\033[33m! %s\033[0m\n' "$*"; }

bold "solana-position-manager-skill — interactive installer"
echo

echo "Where should the skill be installed?"
echo "  1) Personal  ~/.claude/skills/   (available in every project)"
echo "  2) Project    ./.claude/skills/   (this repo only)"
read -rp "Choice [1]: " scope
scope="${scope:-1}"

case "$scope" in
  2) CLAUDE_DIR="$PWD/.claude" ;;
  *) CLAUDE_DIR="$HOME/.claude" ;;
esac
SKILLS_DIR="$CLAUDE_DIR/skills"
DEST="$SKILLS_DIR/$SKILL_NAME"
mkdir -p "$SKILLS_DIR"

read -rp "Install bundled agents + commands too? [Y/n]: " ag
case "$ag" in n|N) INSTALL_AGENTS=0;; *) INSTALL_AGENTS=1;; esac

read -rp "Add a skill reference to $CLAUDE_DIR/CLAUDE.md? [Y/n]: " cm
case "$cm" in n|N) TOUCH_CLAUDE=0;; *) TOUCH_CLAUDE=1;; esac

echo
if [ -d "$DEST" ]; then
  read -rp "Destination exists ($DEST). Overwrite? [y/N] " yn
  case "$yn" in y|Y) rm -rf "$DEST";; *) warn "Aborted."; exit 1;; esac
fi
cp -r "$SCRIPT_DIR/skill" "$DEST"
ok "Skill → $DEST"

if [ "$INSTALL_AGENTS" -eq 1 ]; then
  [ -d "$SCRIPT_DIR/agents" ]  && { mkdir -p "$CLAUDE_DIR/agents";  cp -r "$SCRIPT_DIR/agents/."  "$CLAUDE_DIR/agents/";  ok "Agents → $CLAUDE_DIR/agents/"; }
  [ -d "$SCRIPT_DIR/commands" ] && { mkdir -p "$CLAUDE_DIR/commands"; cp -r "$SCRIPT_DIR/commands/." "$CLAUDE_DIR/commands/"; ok "Commands → $CLAUDE_DIR/commands/"; }
fi

if [ "$TOUCH_CLAUDE" -eq 1 ]; then
  CLAUDE_FILE="$CLAUDE_DIR/CLAUDE.md"
  mkdir -p "$CLAUDE_DIR"; touch "$CLAUDE_FILE"
  MARKER="<!-- solana-position-manager-skill -->"
  if ! grep -q "$MARKER" "$CLAUDE_FILE" 2>/dev/null; then
    {
      printf '\n%s\n' "$MARKER"
      printf '## Solana Position Manager skill\n\n'
      printf 'Skill at `%s`. Entry point: `skill/SKILL.md` (lazy router).\n' "$DEST"
      printf 'CLMM/DLMM position management: Orca Whirlpools, Raydium CLMM, Meteora DLMM.\n'
      printf '%s\n' "<!-- /solana-position-manager-skill -->"
    } >> "$CLAUDE_FILE"
    ok "CLAUDE.md → $CLAUDE_FILE"
  else
    ok "CLAUDE.md already references the skill — skipped."
  fi
fi

if [ ! -d "$SKILLS_DIR/solana-dev" ] && [ ! -d "$SKILLS_DIR/ext/solana-dev" ]; then
  warn "Core 'solana-dev-skill' not found. This addon references it — install the Solana AI Kit for the core."
fi

bold "Done. Restart Claude Code to pick up the new skill."
