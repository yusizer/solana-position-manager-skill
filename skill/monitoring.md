# Monitoring & Alerts

How to keep the "measure" step running on a schedule so out-of-range drift and threshold breaches surface without a human watching. Pair with `range-alerts.md` (the signals) and the protocol files (the fetch).

## 1. What a monitor does

On a fixed interval (default: every 5 min for volatile pairs, 15 min for stable/stable):
1. Fetch the wallet's CLMM/DLMM positions (protocol file).
2. Fetch the current tick / active bin + accrued fees — fresh, per `../rules/position-data-freshness.md`.
3. Evaluate signals from `range-alerts.md` (drift, feeRatio, IL).
4. Emit an alert **only** on a state change or threshold breach (not every run — avoid alert fatigue).
5. Persist last-seen state so "state change" is meaningful across runs.

## 2. Data path

- **RPC:** Helius (recommended — generous free tier, DAS + parsed history) or any Solana RPC. URL + key in env. Read-only is sufficient.
- **Price (for USD fee/principal):** Jupiter Price API v3, Birdeye, or GeckoTerminal. Cache 60s max.
- **No key custody.** The monitor reads on-chain state for a *public* wallet pubkey. It never needs a private key.

## 3. Alert targets

Pick one (ask the user in `/monitor-setup`):
- **Webhook** (Slack/Discord/Telegram bot) — POST a one-line JSON per alert.
- **Log file** — append `ts | position | signal | drift | feeRatio | IL%` for local review.
- **stdout** — for a cron job piped to `mail` or a notifier.

Alert format contract (one line, machine-parseable):
```
<iso8601> | <protocol> | <position_id> | <GREEN|YELLOW|RED> | drift=<f> | feeRatio=<f> | IL=<f>% | tickAge=<s>s | next=<cmd>
```

## 4. Schedule

- **cron (system):** `*/5 * * * * cd /path && ./.env/bin/python monitor.py >> monitor.log 2>&1`
- **GitHub Actions (free, no server):** a 5-min schedule with the wallet + RPC key in repo secrets; commit alerts to a log branch or POST to a webhook. Good for "no infra" setups.
- **In-process (long-running):** a single Node/Python process with `setInterval`/`asyncio` — simplest if already running a bot.

Prefer cron/Actions for a set-and-forget monitor; in-process only if something else is already running.

## 5. Env shape (`.env.example`)

```
# RPC
SOLANA_RPC_URL=https://mainnet.helius-rpc.com/?api-key=YOUR_KEY
# Wallet to watch (public key only — no secret)
WATCH_WALLET=
# Price source (optional, for USD figures)
PRICE_PROVIDER=jupiter   # jupiter | birdeye | geckoterminal
# Alert target
ALERT_WEBHOOK=           # https://hooks.slack.com/... or Discord/Telegram
ALERT_LOG=monitor.log    # if no webhook
# Tunables
INTERVAL_SECONDS=300
STALE_TICK_MAX_SECONDS=60
REBALANCE_COOLDOWN_MIN=240
MIN_REBALANCE_USD=250
```

## 6. Failure handling

- **RPC down / 5xx:** retry with backoff (3 tries), then emit a `MONITOR_RPC_DOWN` alert once (not every run) and skip the tick.
- **Stale tick:** do **not** emit a Yellow/Red from stale data — emit `DATA_STALE` per `../rules/position-data-freshness.md`.
- **Position closed between runs:** emit a `POSITION_CLOSED` info line (don't alert as an error).
- **Crash:** the runner (cron/Actions) should not suppress stderr — surface it so a silent failure isn't mistaken for "all green".

## 7. Keep it safe

- Read-only RPC, public wallet watch, no private keys, no auto-execution. The monitor **observes**; any rebalance still goes through `/rebalance-suggest` + `rebalance-engineer` + explicit user sign-off.
