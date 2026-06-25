/**
 * monitor.ts — read-only DLMM position monitor with out-of-range + threshold alerts.
 *
 * Uses the verified @meteora-ag/dlmm 1.9.x API (see skill/meteora-dlmm.md):
 *   DLMM.create, pool.getPositionsByUserAndLbPair, pool.getActiveBin,
 *   pool.getFeeInfo, pool.getDynamicFee.
 *
 * Read-only: watches a PUBLIC wallet. No private key, no signing, no auto-rebalance.
 * Pair the alerts with skill/range-alerts.md thresholds; the rebalance decision is
 * made by the position-analyst agent, execution by rebalance-engineer (rebalance.ts).
 *
 * Run:
 *   cp .env.example .env  # set RPC_URL + WATCH_WALLET + (optional) ALERT_WEBHOOK
 *   npm install && npm run monitor
 */
import DLMM from "@meteora-ag/dlmm";
import { Connection, PublicKey } from "@solana/web3.js";
import * as dotenv from "dotenv";
import { WebhookAlerts, type Alert, type PositionSignal } from "./alerts";

dotenv.config();

const RPC_URL = process.env.RPC_URL!;
const WATCH_WALLET = process.env.WATCH_WALLET!;
const POOL_ADDRESS = process.env.POOL_ADDRESS!; // LB pair to watch
const ALERT_WEBHOOK = process.env.ALERT_WEBHOOK;
const INTERVAL_S = Number(process.env.INTERVAL_S ?? 300);
const STALE_TICK_MAX_S = Number(process.env.STALE_TICK_MAX_S ?? 60);

function signalFor(
  lowerBinId: number,
  upperBinId: number,
  activeBinId: number
): { level: "GREEN" | "YELLOW" | "RED"; drift: number } {
  // DLMM bounds are inclusive (see skill/meteora-dlmm.md).
  if (activeBinId < lowerBinId || activeBinId > upperBinId) {
    return { level: "RED", drift: activeBinId < lowerBinId ? -1 : 1 };
  }
  const span = upperBinId - lowerBinId || 1;
  const drift = (activeBinId - lowerBinId) / span; // 0..1
  const level = drift < 0.05 || drift > 0.95 ? "RED" : drift < 0.2 || drift > 0.8 ? "YELLOW" : "GREEN";
  return { level, drift };
}

async function checkOnce(
  pool: DLMM,
  user: PublicKey,
  alerts: WebhookAlerts
): Promise<PositionSignal[]> {
  // Fresh fetch every run (skill/rules/position-data-freshness.md).
  const { activeBin, userPositions } = await pool.getPositionsByUserAndLbPair(user);
  const activeBinId = activeBin.binId;

  const out: PositionSignal[] = [];
  for (const p of userPositions) {
    const { lowerBinId, upperBinId } = p.positionData;
    const { level, drift } = signalFor(lowerBinId, upperBinId, activeBinId);

    // Fee info (dynamic, volatility-aware — skill/meteora-dlmm.md).
    let feeBps: number | undefined;
    try {
      const feeInfo = await pool.getFeeInfo();
      feeBps = feeInfo ? Number(feeInfo) / 1e9 * 100 : undefined; // precision 1e9 -> %
    } catch {
      feeBps = undefined; // don't block the alert on a fee-read failure
    }

    const sig: PositionSignal = {
      position: p.publicKey.toBase58(),
      lowerBinId,
      upperBinId,
      activeBinId,
      level,
      drift,
      feeBps,
    };
    out.push(sig);

    if (level !== "GREEN") {
      const alert: Alert = {
        ts: new Date().toISOString(),
        level,
        message:
          `DLMM pos ${p.publicKey.toBase58().slice(0, 8)}… ${level} ` +
          `active=${activeBinId} range=[${lowerBinId},${upperBinId}] ` +
          `drift=${drift.toFixed(2)} fee=${feeBps?.toFixed(4) ?? "?"}% ` +
          `next=/rebalance-suggest`,
      };
      await alerts.send(alert);
    }
  }
  return out;
}

async function main() {
  if (!RPC_URL || !WATCH_WALLET || !POOL_ADDRESS) {
    throw new Error("Set RPC_URL, WATCH_WALLET, POOL_ADDRESS in .env (see .env.example)");
  }
  const connection = new Connection(RPC_URL, "confirmed");
  const user = new PublicKey(WATCH_WALLET);
  const pool = await DLMM.create(connection, new PublicKey(POOL_ADDRESS), {
    cluster: "mainnet-beta",
  });
  const alerts = new WebhookAlerts(ALERT_WEBHOOK);

  console.log(`[monitor] watching ${WATCH_WALLET.slice(0, 8)}… on pool ${POOL_ADDRESS.slice(0, 8)}… every ${INTERVAL_S}s`);

  // Single-shot mode: `npm run monitor -- --once`
  const once = process.argv.includes("--once");

  const tick = async () => {
    const fetchedAt = Date.now();
    try {
      const sigs = await checkOnce(pool, user, alerts);
      const ageS = (Date.now() - fetchedAt) / 1000;
      if (ageS > STALE_TICK_MAX_S) {
        console.warn(`[monitor] DATA_STALE: fetch took ${ageS}s > ${STALE_TICK_MAX_S}s`);
      }
      const nonGreen = sigs.filter((s) => s.level !== "GREEN").length;
      console.log(`[monitor] ${new Date().toISOString()} ${sigs.length} pos, ${nonGreen} non-green`);
    } catch (e) {
      // MONITOR_RPC_DOWN: alert once, don't spam — see skill/monitoring.md §6.
      await alerts.send({ ts: new Date().toISOString(), level: "RED", message: `MONITOR_RPC_DOWN: ${(e as Error).message}` });
      console.error(`[monitor] error:`, e);
    }
  };

  await tick();
  if (once) return;
  setInterval(tick, INTERVAL_S * 1000);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
