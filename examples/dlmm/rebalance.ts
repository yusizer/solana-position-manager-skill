/**
 * rebalance.ts — atomic DLMM rebalance (claim + remove + resize + add in one instruction).
 *
 * Uses the verified @meteora-ag/dlmm 1.9.x atomic-rebalance API (skill/meteora-dlmm.md):
 *   DLMM.create, pool.getPositionsByUserAndLbPair, pool.simulateRebalancePositionWithBalancedStrategy,
 *   pool.rebalancePosition.
 *
 * SAFETY (skill/rules/safe-rebalance.md):
 *   - SIMULATE BEFORE SIGN. This script builds + simulates + prints the quote; it does NOT sign.
 *   - The user signs with their wallet. This script never holds a private key.
 *   - Freshness: re-fetch pool/active bin immediately before building (skill/rules/position-data-freshness.md).
 *
 * This is a reference implementation. Adapt strategy params (Spot/Curve/BidAsk, topUp amounts,
 * withdrawBps, maxActiveBinSlippage) to the position — the rebalance-engineer agent does this.
 *
 * Run (dry/simulate only — no signing):
 *   cp .env.example .env  # set RPC_URL + USER_PUBKEY + POOL_ADDRESS + POSITION_PUBKEY
 *   npm install && npm run rebalance -- --position <POSITION_PUBKEY>
 */
import DLMM from "@meteora-ag/dlmm";
import { Connection, PublicKey } from "@solana/web3.js";
import BN from "bn.js";
import * as dotenv from "dotenv";

dotenv.config();

async function main() {
  const RPC_URL = process.env.RPC_URL!;
  const POOL_ADDRESS = process.env.POOL_ADDRESS!;
  const POSITION_PUBKEY = process.argv[process.argv.indexOf("--position") + 1] ?? process.env.POSITION_PUBKEY!;
  if (!RPC_URL || !POOL_ADDRESS || !POSITION_PUBKEY) {
    throw new Error("Set RPC_URL, POOL_ADDRESS, and --position (see .env.example)");
  }

  const connection = new Connection(RPC_URL, "confirmed");
  const pool = await DLMM.create(connection, new PublicKey(POOL_ADDRESS), {
    cluster: "mainnet-beta",
  });

  // 1. Fresh fetch of the position + active bin (freshness rule).
  const { activeBin, userPositions } = await pool.getPositionsByUserAndLbPair(
    new PublicKey(process.env.USER_PUBKEY!)
  );
  const position = userPositions.find((p) => p.publicKey.toBase58() === POSITION_PUBKEY);
  if (!position) throw new Error(`position ${POSITION_PUBKEY} not found for user`);

  console.log(`[rebalance] activeBin=${activeBin.binId} ` +
    `range=[${position.positionData.lowerBinId},${position.positionData.upperBinId}]`);

  // 2. Simulate a BALANCED atomic rebalance (claim fees + rewards, recenter with a Spot strategy).
  //    StrategyType: "Spot" | "Curve" | "BidAsk" (skill/meteora-dlmm.md).
  const strategy = {
    minBinId: activeBin.binId - 20,
    maxBinId: activeBin.binId + 20,
    strategyType: "Spot" as const,
  };

  const sim = pool.simulateRebalancePositionWithBalancedStrategy(
    position.publicKey,
    position.positionData,
    strategy,
    /* topUpAmountX */ new BN(0),
    /* topUpAmountY */ new BN(0),
    /* xWithdrawBps  */ new BN(10_000), // 100% withdraw
    /* yWithdrawBps  */ new BN(10_000)
  );

  // 3. Build the rebalance instructions with slippage guard.
  const MAX_ACTIVE_BIN_SLIPPAGE = Number(process.env.MAX_ACTIVE_BIN_SLIPPAGE ?? 5);
  const { initBinArrayInstructions, rebalancePositionInstruction } = pool.rebalancePosition(
    sim,
    MAX_ACTIVE_BIN_SLIPPAGE
  );

  console.log(`[rebalance] SIMULATED quote:`);
  console.log(`  initBinArrayInstructions: ${initBinArrayInstructions.length}`);
  console.log(`  rebalancePositionInstruction: ${!!rebalancePositionInstruction}`);
  console.log(`  new range: [${strategy.minBinId}, ${strategy.maxBinId}] (Spot)`);
  console.log(`  maxActiveBinSlippage: ${MAX_ACTIVE_BIN_SLIPPAGE}`);

  // 4. DO NOT SIGN HERE. Hand the instruction list to the user's wallet for approval.
  //    Example (pseudo — wire to your wallet adapter):
  //    const tx = new VersionedTransaction(...initBinArrayInstructions, rebalancePositionInstruction);
  //    const signed = await wallet.signTransaction(tx);
  //    const sig = await connection.sendRawTransaction(signed.serialize());
  console.log(`[rebalance] review the quote above, then sign with your wallet. Not signing automatically.`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
