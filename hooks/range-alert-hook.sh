#!/usr/bin/env sh
# range-alert-hook.sh — opt-in Claude Code Stop hook.
# Checks a CLMM/DLMM position for out-of-range drift when a Claude Code turn ends,
# and surfaces a one-line alert if the position left its range. ALWAYS exits 0 so a
# monitor failure never blocks or fails the session.
#
# Wire-up: see skill/hooks.md. Env (all optional — unset => no-op):
#   SOLANA_RPC_URL   RPC endpoint (read-only)
#   POSITION_PUBKEY  Orca Whirlpools position account to check
#   CURRENT_TICK     pool's current tick index (if known); without it only the range is decoded
#   DRIFT_RED        drift threshold for RED (default 0.05)
#   POSITION_ALERT_LOG  log file (default ./position-alerts.log)
#
# For a full wallet sweep across Orca/Raydium/Meteora, run examples/dlmm/monitor.ts
# (it fetches the active bin itself); this hook covers the single-position, no-npm path.

# Consume the Stop hook's stdin payload (we don't use it).
cat >/dev/null 2>&1 || true

LOG="${POSITION_ALERT_LOG:-position-alerts.log}"
DRIFT_RED="${DRIFT_RED:-0.05}"
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HOOK_DIR/.." && pwd)"
PY="${PYTHON:-python3}"

alert() {
  # $1 = message
  printf '[position-alert] %s\n' "$1" >&2
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date)" "$1" >>"$LOG" 2>/dev/null || true
}

# No-op unless explicitly enabled.
if [ -z "$SOLANA_RPC_URL" ] || [ -z "$POSITION_PUBKEY" ]; then
  exit 0
fi

# Bounded: never stall the session. 25s ceiling.
(
  if [ -z "$CURRENT_TICK" ]; then
    # Only decode the range (no in-range verdict without the current tick).
    "$PY" "$REPO_ROOT/examples/fetch_position.py" \
      --position "$POSITION_PUBKEY" --rpc "$SOLANA_RPC_URL" --json 2>/dev/null
  else
    "$PY" "$REPO_ROOT/examples/fetch_position.py" \
      --position "$POSITION_PUBKEY" --rpc "$SOLANA_RPC_URL" \
      --current-tick "$CURRENT_TICK" --open-tick "${OPEN_TICK:-$CURRENT_TICK}" --json 2>/dev/null
  fi
) >"/tmp/.pos-hook.$$" 2>/dev/null &
PID=$!
i=0
while [ $i -lt 25 ]; do
  kill -0 "$PID" 2>/dev/null || break
  sleep 1; i=$((i+1))
done
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID" 2>/dev/null || true
  alert "DATA_STALE: position check timed out (>25s)"
  rm -f "/tmp/.pos-hook.$$"
  exit 0
fi

OUT="$(cat "/tmp/.pos-hook.$$" 2>/dev/null)"
rm -f "/tmp/.pos-hook.$$"

if [ -z "$OUT" ]; then
  alert "MONITOR_RPC_DOWN: no response from RPC (check SOLANA_RPC_URL)"
  exit 0
fi

if [ -n "$CURRENT_TICK" ]; then
  in_range="$(printf '%s' "$OUT" | "$PY" -c 'import sys,json;
try: print(json.load(sys.stdin)["analysis"]["in_range"])
except Exception: print("ERR")' 2>/dev/null)"
  drift="$(printf '%s' "$OUT" | "$PY" -c 'import sys,json;
try: print(json.load(sys.stdin)["analysis"]["drift"])
except Exception: print("ERR")' 2>/dev/null)"
  if [ "$in_range" = "False" ]; then
    alert "RED out-of-range: position $POSITION_PUBKEY drift=$drift — run /rebalance-suggest"
  elif [ "$in_range" = "True" ] && [ "$drift" != "ERR" ] && [ "$drift" != "" ]; then
    # drift is 0..1; RED if within DRIFT_RED of either edge
    near_edge="$(awk -v d="$drift" -v r="$DRIFT_RED" 'BEGIN{ if (d<r || d>1-r) print 1; else print 0 }')"
    if [ "$near_edge" = "1" ]; then
      alert "YELLOW near edge: position $POSITION_PUBKEY drift=$drift (RED<=$DRIFT_RED)"
    fi
  fi
fi

exit 0
