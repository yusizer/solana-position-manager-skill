#!/usr/bin/env bash
# validate.sh — structural integrity check for the skill repo.
# Verifies required files exist, SKILL.md has frontmatter, and every
# intra-skill markdown link resolves. Exits non-zero on any problem.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

pass=0; fail=0
ok()   { printf '\033[32m✓ %s\033[0m\n' "$*"; pass=$((pass+1)); }
bad()  { printf '\033[31m✗ %s\033[0m\n' "$*"; fail=$((fail+1)); }

# 1. Required files
for f in skill/SKILL.md README.md LICENSE CLAUDE.md install.sh install-custom.sh; do
  [ -f "$f" ] && ok "present: $f" || bad "missing: $f"
done

# 2. SKILL.md frontmatter
if [ -f skill/SKILL.md ]; then
  head -1 skill/SKILL.md | grep -q '^---' && ok "SKILL.md frontmatter open" || bad "SKILL.md missing frontmatter opening ---"
  awk 'NR==1&&/^---/{f=1;next} f&&/^---/{print "close";exit}' skill/SKILL.md | grep -q close && ok "SKILL.md frontmatter close" || bad "SKILL.md frontmatter not closed"
  grep -q '^name:' skill/SKILL.md && ok "SKILL.md has name:" || bad "SKILL.md missing name:"
  grep -q '^description:' skill/SKILL.md && ok "SKILL.md has description:" || bad "SKILL.md missing description:"
fi

# 3. Intra-skill link resolution (skill/*.md -> skill/*.md)
# NOTE: process substitution (not a pipe) so fail-count mutates in this shell.
if [ -d skill ]; then
  for md in skill/*.md; do
    while IFS= read -r link; do
      [ -z "$link" ] && continue
      case "$link" in
        http*|//*) continue ;;            # external, skip
        \#*) continue ;;                  # anchor, skip
      esac
      base="$(dirname "$md")"
      target="$base/$link"
      if [ -f "$target" ]; then
        ok "link ok: $md -> $link"
      else
        bad "broken link: $md -> $link"
      fi
    done < <(grep -oE '\]\([^)]+\.md\)' "$md" | sed -E 's/^\]\(//; s/\)$//')
  done
fi

# 4. Agent / command / rule dirs
for d in agents commands rules; do
  [ -d "$d" ] && ok "dir present: $d" || bad "missing dir: $d"
done

echo
printf 'Result: \033[32m%d passed\033[0m, \033[31m%d failed\033[0m\n' "$pass" "$fail"
[ "$fail" -eq 0 ] && exit 0 || exit 1
