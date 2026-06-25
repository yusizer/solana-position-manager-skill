---
description: Scaffold a scheduled monitor that alerts when a CLMM/DLMM position drifts out of range or hits a fee/IL threshold.
argument-hint: [wallet-pubkey]
---

Scaffold an out-of-range + threshold monitor for `$ARGUMENTS`.

Procedure:
1. Load `skill/monitoring.md` and `skill/range-alerts.md`.
2. Produce a ready-to-run monitor (cron or scheduled job) that, on an interval:
   - Fetches the wallet's CLMM/DLMM positions (protocol file per `skill/SKILL.md`).
   - Checks in-range status + fee-to-principal ratio + IL against thresholds from `skill/range-alerts.md`.
   - Fires an alert (webhook / log / Telegram — ask the user which) when a position leaves the range or a threshold is crossed.
3. Emit:
   - A `monitor.ts` (or `.py`) file using the official SDK + an RPC endpoint (Helius by default; read key from env).
   - A `.env.example` with the required keys (RPC URL, wallet, alert target).
   - The cron/schedule line and a one-command runner.
4. Respect `rules/position-data-freshness.md` — the monitor must fetch fresh state each run, never cache the tick across runs.

Keep it dependency-light and safe (no key custody, read-only on RPC). Ask before writing files into the user's project.
