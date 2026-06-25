#!/usr/bin/env python3
"""
il_calc.py — CLI impermanent-loss calculator for concentrated-liquidity positions.

Implements the math from skill/impermanent-loss.md. Useful as a standalone tool
and as a worked, runnable example of the skill (the skill's commands can shell
out to this or reimplement the same logic via the SDK).

Examples:
    python il_calc.py --pa 140 --pb 210 --p0 170 --p 200
    python il_calc.py --pa 140 --pb 210 --p0 170 --p 200 \
        --principal 10000 --fees 320

Output is human-readable; --json emits machine-readable JSON.
"""

from __future__ import annotations
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from il_math import compute_il, fee_break_even  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Concentrated-liquidity IL calculator.")
    ap.add_argument("--pa", type=float, required=True, help="lower price bound (token0 in token1)")
    ap.add_argument("--pb", type=float, required=True, help="upper price bound")
    ap.add_argument("--p0", type=float, required=True, help="price at open / last rebalance")
    ap.add_argument("--p", type=float, required=True, help="current price")
    ap.add_argument("--principal", type=float, default=None, help="principal in token1 (for USD fee ratio)")
    ap.add_argument("--fees", type=float, default=None, help="uncollected fees in token1 (USD)")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args()

    try:
        r = compute_il(Pa=args.pa, Pb=args.pb, P0=args.p0, P=args.p)
    except ValueError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2

    out = r.as_dict()
    out["price_move_pct"] = round((args.p / args.p0 - 1) * 100, 4)

    if args.principal and args.fees is not None:
        fee_ratio = args.fees / args.principal
        net = fee_break_even(r.il, fee_ratio)
        out["fee_ratio_pct"] = round(fee_ratio * 100, 4)
        out["net_vs_hodl_pct"] = round(net * 100, 4)
        out["verdict"] = "net_positive" if net > 0 else "net_negative"

    if args.json:
        print(json.dumps(out, indent=2))
        return 0

    print("Concentrated-liquidity IL report")
    print("=" * 40)
    print("Range:        [%.4f, %.4f]" % (args.pa, args.pb))
    print("Open price:   %.4f" % args.p0)
    print("Now price:    %.4f  (%+.2f%%)" % (args.p, (args.p / args.p0 - 1) * 100))
    print("In range:     %s" % ("yes" if r.in_range else "NO"))
    print("V_LP   (L*):  %.6f" % r.v_lp)
    print("V_HODL (L*):  %.6f" % r.v_hodl)
    print("IL:           %+.4f%%" % (r.il * 100))
    if "fee_ratio_pct" in out:
        print("Fee ratio:    %.4f%%" % out["fee_ratio_pct"])
        print("Net vs HODL:  %+.4f%%  [%s]" % (out["net_vs_hodl_pct"], out["verdict"]))
    print("=" * 40)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
