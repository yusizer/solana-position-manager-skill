"""
test_il.py — unit tests for the concentrated-IL math in examples/il_math.py.

Run without pytest:
    python tests/test_il.py
Or with pytest (if installed):
    pytest tests/test_il.py

These tests pin the formulas documented in skill/impermanent-loss.md, including
the worked example (SOL/USDC [140,210] opened 170, now 200 -> ~-3.4% IL). If a
future edit to the math drifts, this file fails — that is the point.
"""

from __future__ import annotations
import os
import sys
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "examples"))
from il_math import (  # noqa: E402
    compute_il,
    fee_break_even,
    il_v2,
    amplification_lambda,
    il_v3_symmetric,
)

EPS_IL = 1e-3        # IL tolerance (fraction)
EPS_VAL = 1e-6       # value tolerance (L-scaled)


def test_worked_example_impermanent_loss_md():
    """The exact numbers shown in skill/impermanent-loss.md §5 must hold."""
    r = compute_il(Pa=140, Pb=210, P0=170, P=200)
    # Documented: V_LP = L*2.651, V_HODL = L*2.744, IL ~ -3.4%
    assert abs(r.v_lp - 2.651) < 5e-3, r.v_lp
    assert abs(r.v_hodl - 2.744) < 5e-3, r.v_hodl
    assert abs(r.il - (-0.034)) < EPS_IL, r.il
    assert r.in_range is True


def test_no_move_zero_il():
    r = compute_il(Pa=140, Pb=210, P0=170, P=170)
    assert abs(r.il) < EPS_IL, r.il
    assert r.price_ratio == 1.0


def test_il_non_positive_in_range():
    for P in (150, 160, 180, 200, 205):
        r = compute_il(Pa=140, Pb=210, P0=170, P=P)
        assert r.in_range is True
        assert r.il <= 1e-12, (P, r.il)


def test_il_independent_of_liquidity():
    a = compute_il(Pa=140, Pb=210, P0=170, P=200, L=1.0)
    b = compute_il(Pa=140, Pb=210, P0=170, P=200, L=12345.0)
    assert abs(a.il - b.il) < 1e-12


def test_out_of_range_above_all_token1():
    """P > Pb -> position is 100% token1: V_LP = L*(xb - xa)."""
    r = compute_il(Pa=140, Pb=210, P0=170, P=300)
    xa, xb = math.sqrt(140), math.sqrt(210)
    assert r.in_range is False
    assert abs(r.v_lp - (xb - xa)) < EPS_VAL, r.v_lp


def test_out_of_range_below_all_token0():
    """P < Pa -> position is 100% token0: V_LP = L*(1/xa - 1/xb)*P."""
    r = compute_il(Pa=140, Pb=210, P0=170, P=100, L=1.0)
    xa, xb = math.sqrt(140), math.sqrt(210)
    assert r.in_range is False
    assert abs(r.v_lp - (1.0 / xa - 1.0 / xb) * 100) < EPS_VAL, r.v_lp


def test_hodl_beats_lp_on_pure_move():
    """LP underperforms HODL on any in-range price move (IL <= 0)."""
    for P in (150, 190, 205):
        r = compute_il(Pa=140, Pb=210, P0=170, P=P)
        assert r.v_lp < r.v_hodl, (P, r.v_lp, r.v_hodl)


def test_fee_break_even():
    """Fees must exceed |IL| for net-positive vs HODL."""
    r = compute_il(Pa=140, Pb=210, P0=170, P=200)
    net = fee_break_even(r.il, fee_ratio=0.05)   # 5% fees
    assert net > 0  # 5% fees > 3.4% IL -> net positive
    net0 = fee_break_even(r.il, fee_ratio=0.01)
    assert net0 < 0  # 1% fees < 3.4% IL -> net negative


def test_invalid_inputs_rejected():
    for kwargs in [
        dict(Pa=0, Pb=210, P0=170, P=200),
        dict(Pa=140, Pb=140, P0=170, P=200),
        dict(Pa=210, Pb=140, P0=170, P=200),    # Pa > Pb
        dict(Pa=140, Pb=210, P0=210, P=200),    # P0 not strictly inside
        dict(Pa=140, Pb=210, P0=170, P=-1),
    ]:
        try:
            compute_il(**kwargs)
        except ValueError:
            continue
        raise AssertionError("expected ValueError for %r" % kwargs)


# --- v2 + symmetric amplification (impermanent-loss.md §4) ---

def test_il_v2_zero_at_one():
    assert abs(il_v2(1.0)) < 1e-12
    # symmetric: IL_v2(r) == IL_v2(1/r)
    assert abs(il_v2(1.5) - il_v2(1.0 / 1.5)) < 1e-12


def test_il_v2_known_value():
    # IL_v2(1.21) = 2*1.1/2.21 - 1 = -0.004524...
    assert abs(il_v2(1.21) - (-0.0045249)) < 1e-5


def test_amplification_lambda():
    assert abs(amplification_lambda(2.0) - 3.4142) < 1e-3      # sqrt(2)/(sqrt(2)-1)
    assert abs(amplification_lambda(1.25) - 9.4721) < 1e-3     # tight range
    # full-range: k -> inf converges to 1
    assert abs(amplification_lambda(1e9) - 1.0) < 1e-3


def test_il_v3_symmetric_worked_example():
    # Range [0.5, 2.0], +21% move -> -1.54% (impermanent-loss.md §4)
    v = il_v3_symmetric(1.21, 2.0)
    assert abs(v - (-0.01544)) < 1e-4, v


def test_il_v3_matches_compute_il_cross_check():
    """Two independent formulas must agree on a symmetric range in range."""
    # compute_il path (§2) vs il_v3_symmetric path (§4) for [0.5, 2], P0=1, P=1.21
    r = compute_il(Pa=0.5, Pb=2.0, P0=1.0, P=1.21)
    v = il_v3_symmetric(1.21, 2.0)
    assert abs(r.il - v) < 1e-9, (r.il, v)


def test_il_v3_tighter_range_more_il():
    # Narrower range => larger |IL| for the same move (still in range)
    wide = abs(il_v3_symmetric(1.21, 2.0))      # lambda ~3.4
    tight = abs(il_v3_symmetric(1.21, 1.25))    # lambda ~9.5, price 1.21 still < 1.25
    assert tight > wide


def test_il_v3_out_of_range_rejected():
    for r in (0.4, 2.5):  # outside (1/2, 2)
        try:
            il_v3_symmetric(r, 2.0)
        except ValueError:
            continue
        raise AssertionError("expected ValueError for r=%r" % r)


def _main():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print("ok   %s" % fn.__name__)
        except Exception as e:  # noqa
            failed += 1
            print("FAIL %s: %r" % (fn.__name__, e))
    print("\n%d tests, %d failed" % (len(fns), failed))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    _main()
