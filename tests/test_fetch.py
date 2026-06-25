"""
test_fetch.py — tests for examples/fetch_position.py (Position decode + analysis).

Run without pytest:  python tests/test_fetch.py
With pytest:         pytest tests/test_fetch.py
"""

from __future__ import annotations
import os
import struct
import sys
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "examples"))
import fetch_position as fp  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLES = os.path.join(HERE, "..", "examples")


def _make_position(tick_lower=-55440, tick_upper=55440, liquidity=1_000_000,
                   fee_a=750, fee_b=0) -> bytes:
    disc = bytes([0] * 8)
    whirlpool = bytes([(i * 7 + 3) % 256 for i in range(32)])
    mint = bytes([(i * 5 + 11) % 256 for i in range(32)])
    return (
        disc + whirlpool + mint
        + liquidity.to_bytes(16, "little")
        + struct.pack("<i", tick_lower)
        + struct.pack("<i", tick_upper)
        + (0).to_bytes(16, "little") + fee_a.to_bytes(8, "little")
        + (0).to_bytes(16, "little") + fee_b.to_bytes(8, "little")
        + bytes([0] * 72)
    )


def test_decode_position_fields():
    data = _make_position(tick_lower=-1000, tick_upper=2000, liquidity=42, fee_a=99, fee_b=7)
    p = fp.decode_position(data)
    assert p["tick_lower_index"] == -1000
    assert p["tick_upper_index"] == 2000
    assert p["liquidity"] == 42
    assert p["fee_owed_a"] == 99
    assert p["fee_owed_b"] == 7
    assert len(p["whirlpool"]) >= 32  # base58 pubkey string
    assert len(p["position_mint"]) >= 32


def test_decode_position_length_check():
    try:
        fp.decode_position(b"\x00" * 100)
    except ValueError:
        return
    raise AssertionError("expected ValueError for short account")


def test_offline_fixture_decodes():
    p = fp.decode_position(fp._build_offline_fixture())
    assert p["tick_lower_index"] == -55440
    assert p["tick_upper_index"] == 55440
    assert p["liquidity"] == 1_000_000
    assert p["fee_owed_a"] == 750
    assert p["fee_owed_b"] == 0


def test_b58_roundtrip():
    for s in ["whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",
              "11111111111111111111111111111111",
              "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"]:
        assert fp.b58encode(fp.b58decode(s)) == s


def test_analyze_in_range_middle():
    pos = {"tick_lower_index": -55440, "tick_upper_index": 55440}
    a = fp.analyze(pos, current_tick=0, open_tick=0)
    assert a["in_range"] is True
    assert abs(a["drift"] - 0.5) < 1e-9


def test_analyze_out_of_range_above():
    pos = {"tick_lower_index": -100, "tick_upper_index": 100}
    a = fp.analyze(pos, current_tick=999, open_tick=0)
    assert a["in_range"] is False


def test_analyze_il_returns_dict():
    pos = {"tick_lower_index": -55440, "tick_upper_index": 55440}
    a = fp.analyze(pos, current_tick=1000, open_tick=0)
    assert a["il"] is not None
    assert "il_pct" in a["il"]


def test_analyze_no_il_without_open_tick():
    pos = {"tick_lower_index": -100, "tick_upper_index": 100}
    a = fp.analyze(pos, current_tick=0, open_tick=None)
    assert a["il"] is None


def test_cli_offline_smoke():
    r = subprocess.run(
        [sys.executable, os.path.join(EXAMPLES, "fetch_position.py"),
         "--offline", "--current-tick", "0", "--open-tick", "0", "--json"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    import json
    out = json.loads(r.stdout)
    assert out["tick_lower_index"] == -55440
    assert out["analysis"]["in_range"] is True


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
