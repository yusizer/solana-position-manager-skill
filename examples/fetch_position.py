#!/usr/bin/env python3
"""
fetch_position.py — read-only Solana RPC client that fetches and decodes an
Orca Whirlpools CLMM position account, then reports in-range status, drift,
and impermanent loss.

This is the "real executable code touching Solana" counterpart to the pure-math
examples/il_*.py — it does a real getAccountInfo RPC call and decodes the
verified on-chain Position layout (216 bytes, see skill/whirlpools.md) using
ONLY the Python stdlib (no npm, no third-party packages).

Zero dependencies. Read-only. No signing, no private key.

Usage (live RPC):
    python fetch_position.py --position <PUBKEY> --rpc $SOLANA_RPC_URL \
        --current-tick 12345 --open-tick 0

Offline demo (no RPC, uses a built-in fixture):
    python fetch_position.py --offline --current-tick 0 --open-tick 0

Position layout (verified against orca-so/whirlpools state/position.rs, LEN=216):
    [0:8)    discriminator (8)
    [8:40)   whirlpool pubkey (32)
    [40:72)  position_mint pubkey (32)
    [72:88)  liquidity u128 (16, LE)
    [88:92)  tick_lower_index i32 (4, LE signed)
    [92:96)  tick_upper_index i32 (4, LE signed)
    [96:112) fee_growth_checkpoint_a u128
    [112:120) fee_owed_a u64
    [120:136) fee_growth_checkpoint_b u128
    [136:144) fee_owed_b u64
    [144:216) reward_infos [3]
"""

from __future__ import annotations
import argparse
import base64
import json
import math
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from il_math import compute_il  # noqa: E402

ORCA_WHIRLPOOLS_PROGRAM = "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"
POSITION_LEN = 216

_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(b: bytes) -> str:
    n = int.from_bytes(b, "big")
    s = ""
    while n > 0:
        n, r = divmod(n, 58)
        s = _B58[r] + s
    pad = len(b) - len(b.lstrip(b"\x00"))
    return _B58[0] * pad + s


def b58decode(s: str) -> bytes:
    n = 0
    for ch in s:
        n = n * 58 + _B58.index(ch)
    pad = len(s) - len(s.lstrip("1"))
    body = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    return b"\x00" * pad + body


def decode_position(data: bytes) -> dict:
    """Decode an Orca Whirlpools Position account (216 bytes incl. discriminator)."""
    if len(data) < POSITION_LEN:
        raise ValueError(f"account too short: {len(data)} < {POSITION_LEN}")
    d = data
    return {
        "whirlpool": b58encode(d[8:40]),
        "position_mint": b58encode(d[40:72]),
        "liquidity": int.from_bytes(d[72:88], "little"),
        "tick_lower_index": int.from_bytes(d[88:92], "little", signed=True),
        "tick_upper_index": int.from_bytes(d[92:96], "little", signed=True),
        "fee_owed_a": int.from_bytes(d[112:120], "little"),
        "fee_owed_b": int.from_bytes(d[136:144], "little"),
    }


def tick_to_price(tick: int) -> float:
    """Raw (decimal-unscaled) price from a tick index: p = 1.0001^tick.

    Ratios (IL, drift) are decimal-invariant, so unscaled prices are fine here.
    """
    return 1.0001 ** tick


def fetch_account(rpc: str, pubkey: str) -> bytes:
    """getAccountInfo RPC call -> raw account data bytes (or raise)."""
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "getAccountInfo",
        "params": [pubkey, {"encoding": "base64", "commitment": "confirmed"}],
    }).encode()
    req = urllib.request.Request(rpc, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.loads(r.read())
    if resp.get("error"):
        raise RuntimeError(f"RPC error: {resp['error']}")
    val = resp.get("result", {}).get("value")
    if not val:
        raise RuntimeError(f"account not found: {pubkey}")
    return base64.b64decode(val["data"][0])


# A built-in fixture so --offline works without an RPC endpoint (also used by tests).
# Encodes a position: tick_lower=-55440, tick_upper=55440 (a wide range), liquidity 1e6,
# fee_owed_a=750, fee_owed_b=0, whirlpool/position_mint = deterministic pubkeys.
def _build_offline_fixture() -> bytes:
    import struct
    disc = bytes([0] * 8)  # 8-byte discriminator (skipped by decode_position)
    whirlpool = bytes([(i * 7 + 3) % 256 for i in range(32)])
    mint = bytes([(i * 5 + 11) % 256 for i in range(32)])
    liquidity = (1_000_000).to_bytes(16, "little")
    tick_lower = struct.pack("<i", -55440)
    tick_upper = struct.pack("<i", 55440)
    fg_a = (0).to_bytes(16, "little")
    fee_a = (750).to_bytes(8, "little")
    fg_b = (0).to_bytes(16, "little")
    fee_b = (0).to_bytes(8, "little")
    rewards = bytes([0] * 72)
    return disc + whirlpool + mint + liquidity + tick_lower + tick_upper + fg_a + fee_a + fg_b + fee_b + rewards


def analyze(pos: dict, current_tick: int, open_tick: int) -> dict:
    tl, tu = pos["tick_lower_index"], pos["tick_upper_index"]
    in_range = tl < current_tick < tu  # Orca: strict (skill/whirlpools.md)
    span = tu - tl or 1
    drift = (current_tick - tl) / span
    il = None
    if open_tick is not None and tl < open_tick < tu:
        r = compute_il(
            Pa=tick_to_price(tl), Pb=tick_to_price(tu),
            P0=tick_to_price(open_tick), P=tick_to_price(current_tick),
        )
        il = r.as_dict()
    return {
        "in_range": in_range,
        "drift": round(drift, 4),
        "current_tick": current_tick,
        "open_tick": open_tick,
        "il": il,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch + decode an Orca Whirlpools position (read-only).")
    ap.add_argument("--position", help="position account pubkey (required unless --offline)")
    ap.add_argument("--rpc", default=os.environ.get("SOLANA_RPC_URL", ""), help="Solana RPC URL")
    ap.add_argument("--current-tick", type=int, help="pool's current tick index (for in-range/IL)")
    ap.add_argument("--open-tick", type=int, default=None, help="tick at open/last rebalance (for IL)")
    ap.add_argument("--offline", action="store_true", help="use built-in fixture, no RPC")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args()

    if args.offline:
        data = _build_offline_fixture()
        pos = decode_position(data)
        pos["_source"] = "offline-fixture"
    else:
        if not args.position or not args.rpc:
            print("error: --position and --rpc required (or --offline)", file=sys.stderr)
            return 2
        data = fetch_account(args.rpc, args.position)
        pos = decode_position(data)
        pos["_source"] = "rpc"

    out = dict(pos)
    if args.current_tick is not None:
        out["analysis"] = analyze(pos, args.current_tick, args.open_tick)

    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print("Orca Whirlpools position")
        print("=" * 44)
        print("source:        %s" % out["_source"])
        print("whirlpool:     %s" % pos["whirlpool"])
        print("position_mint: %s" % pos["position_mint"])
        print("liquidity:     %s" % pos["liquidity"])
        print("tick range:    [%d, %d]" % (pos["tick_lower_index"], pos["tick_upper_index"]))
        print("fee_owed_a:    %s" % pos["fee_owed_a"])
        print("fee_owed_b:    %s" % pos["fee_owed_b"])
        if args.current_tick is not None:
            a = out["analysis"]
            print("-" * 44)
            print("current_tick:  %d" % a["current_tick"])
            print("in_range:      %s" % ("yes" if a["in_range"] else "NO"))
            print("drift:         %.4f" % a["drift"])
            if a["il"]:
                print("IL:            %+.4f%%" % a["il"]["il_pct"])
        print("=" * 44)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
