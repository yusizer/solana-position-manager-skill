"""
il_math.py — concentrated-liquidity impermanent-loss math.

Pure-Python, zero dependencies. Implements the exact formulas documented in
../skill/impermanent-loss.md so the skill's math is not just prose — it is
executable and unit-tested (see ../tests/test_il.py).

Token convention: token0 is priced in token1, i.e. P = price of token0 in
token1. A position covers the price interval [Pa, Pb] and was opened at P0.
"""

from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass
class ILResult:
    in_range: bool
    v_lp: float          # LP value in token1 units (excl. fees), L-scaled
    v_hodl: float        # HODL value in token1 units, L-scaled
    il: float            # V_LP / V_HODL - 1  (<= 0 in range)
    price_ratio: float   # P / P0

    def as_dict(self) -> dict:
        return {
            "in_range": self.in_range,
            "v_lp": round(self.v_lp, 6),
            "v_hodl": round(self.v_hodl, 6),
            "il_pct": round(self.il * 100, 4),
            "price_ratio": round(self.price_ratio, 6),
        }


def compute_il(Pa: float, Pb: float, P0: float, P: float, L: float = 1.0) -> ILResult:
    """Compute impermanent loss vs HODL for a concentrated-liquidity position.

    Args:
        Pa: lower price bound of the range (token0 in token1).
        Pb: upper price bound of the range.
        P0: price at which the position was opened (rebalance basis).
        P:  current price.
        L:  liquidity (scales values; IL ratio is L-independent).

    Returns:
        ILResult with V_LP, V_HODL, IL, in-range flag, price ratio.
    """
    if Pa <= 0 or Pb <= 0 or P0 <= 0 or P <= 0:
        raise ValueError("prices must be positive")
    if not (Pa < P0 < Pb):
        raise ValueError("open price P0 must be strictly inside (Pa, Pb)")
    if Pa >= Pb:
        raise ValueError("require Pa < Pb")

    x = math.sqrt(P)
    x0 = math.sqrt(P0)
    xa = math.sqrt(Pa)
    xb = math.sqrt(Pb)

    in_range = Pa <= P <= Pb

    if in_range:
        # V_LP(P) = L * (2x - xa - x^2/xb)            [skill/impermanent-loss.md §2]
        v_lp = L * (2 * x - xa - (x * x) / xb)
        # V_HODL(P) = L * (x^2*(1/x0 - 1/xb) + x0 - xa)
        v_hodl = L * (x * x * (1.0 / x0 - 1.0 / xb) + x0 - xa)
    elif P < Pa:
        # Out of range below: 100% token0.
        # token0 = L*(1/xa - 1/xb); V_LP = token0 * P
        v_lp = L * (1.0 / xa - 1.0 / xb) * P
        # HODL keeps the open amounts: token0(P0)*P + token1(P0)
        v_hodl = L * (1.0 / x0 - 1.0 / xb) * P + L * (x0 - xa)
    else:  # P > Pb: out of range above, 100% token1.
        v_lp = L * (xb - xa)
        v_hodl = L * (1.0 / x0 - 1.0 / xb) * P + L * (x0 - xa)

    il = v_lp / v_hodl - 1.0 if v_hodl != 0 else float("nan")
    return ILResult(in_range=in_range, v_lp=v_lp, v_hodl=v_hodl, il=il, price_ratio=P / P0)


def fee_break_even(il: float, fee_ratio: float) -> float:
    """Net return vs HODL once fees are included: fee_ratio - |IL| (in-range, IL<=0)."""
    return fee_ratio + il  # il is negative in range


# --- v2 reference + symmetric amplification (skill/impermanent-loss.md §4) ---

def il_v2(r: float) -> float:
    """Full-range (v2) impermanent loss for price ratio r = P/P0.

    IL_v2(r) = 2*sqrt(r)/(1+r) - 1.  Zero at r=1, negative otherwise.
    """
    if r <= 0:
        raise ValueError("price ratio r must be positive")
    return 2.0 * math.sqrt(r) / (1.0 + r) - 1.0


def amplification_lambda(k: float) -> float:
    """Capital-efficiency / IL-amplification factor for a symmetric range [1/k, k].

    lambda = sqrt(k)/(sqrt(k) - 1).  Full-range (k->inf) -> 1.
    """
    if k <= 1:
        raise ValueError("k must be > 1 for a non-degenerate symmetric range")
    sk = math.sqrt(k)
    return sk / (sk - 1.0)


def il_v3_symmetric(r: float, k: float) -> float:
    """Concentrated IL for a symmetric range [1/k, k] via the amplification identity.

    IL_v3(r) = lambda(k) * IL_v2(r), valid while r in (1/k, k).
    """
    if not (1.0 / k < r < k):
        raise ValueError("r out of symmetric range (1/k, k); use compute_il for out-of-range")
    return amplification_lambda(k) * il_v2(r)


if __name__ == "__main__":
    # Quick self-check matching the worked example in impermanent-loss.md.
    r = compute_il(Pa=140, Pb=210, P0=170, P=200)
    print(r.as_dict())
