# Quick start

## 1. Install

```bash
curl -fsSL https://raw.githubusercontent.com/yusizer/solana-position-manager-skill/main/install.sh | bash
```

Or, after cloning:

```bash
./install.sh -y
```

This drops the skill into `~/.claude/skills/solana-position-manager/` and adds a reference to `~/.claude/CLAUDE.md`. Restart Claude Code.

## 2. Use the commands

```
/check-positions <wallet>
/il-report <position>
/rebalance-suggest <position>
/monitor-setup
```

Example flow for an LP who drifted out of range:

```
/check-positions 9xQeWv...        → see which positions are ⚠ out of range
/rebalance-suggest <position>     → get a HOLD/WIDEN/MOVE/WITHDRAW call + reasoning
```

If the recommendation is to act, the `rebalance-engineer` agent builds and **simulates** the tx; you sign.

## 3. Try the standalone IL calculator

No Claude Code needed — pure CLI:

```bash
python examples/il_calc.py --pa 140 --pb 210 --p0 170 --p 200 --principal 10000 --fees 320
```

```
IL:           -3.4047%
Fee ratio:    3.2000%
Net vs HODL:  -0.2047%  [net_negative]
```

## 4. Verify

```bash
./validate.sh               # structure + links
python tests/test_il.py     # 9 IL-math tests
```

## 5. Read the skill

Start at `skill/SKILL.md` — it routes to the right file by intent. Don't read all files upfront; that is the point of the lazy hub.
