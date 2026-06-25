# Claude Code hooks integration

This skill ships an **opt-in Claude Code hook** that checks your CLMM/DLMM positions for out-of-range drift when a Claude Code session stops, and surfaces an alert if any position left its range. None of the other kit skills use hooks — this is a native, zero-interrupt way to keep position health visible while you work.

> Hooks run in your Claude Code harness, not in the model. They are opt-in: nothing runs unless you wire it up in `settings.json`.

## What it does

`hooks/range-alert-hook.sh` is a `Stop` hook. When Claude Code finishes a turn, the harness calls it with a small JSON payload on stdin. If you've set `SOLANA_RPC_URL` + `WATCH_WALLET`, it does a **read-only** position sweep (reusing `examples/fetch_position.py` / the protocol files' fetch logic) and:

- prints a one-line alert to stderr if any position is out of range or past a drift threshold (visible in the session transcript);
- appends the same line to `${POSITION_ALERT_LOG:-position-alerts.log}`;
- exits `0` **always** — a monitor failure never blocks or fails your Claude Code turn.

If the env vars are unset, the hook is a no-op (so it's safe to install globally and ignore until you need it).

## Install (opt-in)

Add to your project or user `settings.json` (see `../CLAUDE.md` for the skill's config):

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/range-alert-hook.sh\"" }
        ]
      }
    ]
  }
}
```

Then set env (e.g. in `.env` or your shell):

```
SOLANA_RPC_URL=https://mainnet.helius-rpc.com/?api-key=YOUR_KEY
WATCH_WALLET=<your wallet pubkey>
POSITION_ALERT_LOG=position-alerts.log   # optional
```

Copy the hook next to your config:

```bash
mkdir -p .claude/hooks && cp hooks/range-alert-hook.sh .claude/hooks/
```

## Safety properties

- **Read-only RPC, public wallet.** No private key, no signing. The hook never executes a rebalance — it only *alerts*. Execution still goes through `/rebalance-suggest` + `rebalance-engineer` + your sign-off (`../rules/safe-rebalance.md`).
- **Never blocks.** Exit code is always 0; a timeout or RPC failure is logged, not raised.
- **Bounded time.** The hook self-timeouts (default 25s) so a slow RPC can't stall your session.
- **Freshness.** Each run fetches fresh state (`../rules/position-data-freshness.md`); it never caches the tick across turns.

## Tuning

The hook reads the same thresholds as `range-alerts.md` (drift RED < 5% from an edge, or out of range). To adjust, set `DRIFT_RED` (default `0.05`) and `DRIFT_YELLOW` (default `0.20`) in the environment before the hook runs.
