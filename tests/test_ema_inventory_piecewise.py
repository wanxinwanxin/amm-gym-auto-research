"""Unit tests for the EMA-inventory piecewise policy.

Three checks:
1. With `inventory_skew_to_bid = inventory_skew_to_ask = 0`, fees are
   identical to `PiecewiseControllerStrategy` for any decay value.
2. EMA actually accumulates: zero decay tracks the latest raw imbalance;
   high decay smooths it.
3. Anchor parity: zero-skew EMA-inventory recovers the cycle-8 ablation
   piecewise score on a small seed slice (within float noise).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from arena_eval.core.types import TradeInfo  # noqa: E402
from arena_eval.exact_simple_amm import FixedFeeStrategy, run_batch  # noqa: E402
from arena_policies import (  # noqa: E402
    EMAInventoryPiecewiseParams,
    EMAInventoryPiecewiseStrategy,
    PiecewiseControllerParams,
    PiecewiseControllerStrategy,
)
from arena_search.simple_amm_search import POLICY_SPECS  # noqa: E402


_PIECEWISE_PARAMS_DICT = {
    "base_fee": 0.0016550408798529576,
    "base_spread": 0.004243130017056316,
    "signal_decay": 0.6710204554398381,
    "toxicity_decay": 0.5359985273747493,
    "small_trade_threshold": 0.0035434960848610567,
    "large_trade_threshold": 0.010026395287212322,
    "continuation_small": -0.0002902772323995477,
    "continuation_medium": 0.007132694969980573,
    "continuation_large": 0.01823001527951129,
    "reversal_small": 0.01193099991680676,
    "reversal_medium": 0.02189557268220984,
    "reversal_large": 0.07594344828226333,
    "continuation_to_same_side": 0.12260500653949676,
    "continuation_to_cross_side": 1.3580492898846743,
    "toxicity_to_mid": 0.009952017339294478,
    "toxicity_to_side": 0.06882714964266168,
}


def _trade(*, ts, is_buy, amount_y, reserve_x, reserve_y):
    return TradeInfo(
        is_buy=is_buy,
        amount_x=0.0,  # ignored by piecewise/ema; not used for sizing
        amount_y=amount_y,
        timestamp=ts,
        reserve_x=reserve_x,
        reserve_y=reserve_y,
    )


@pytest.mark.parametrize("decay", [0.0, 0.5, 0.95, 0.99])
def test_zero_skew_matches_piecewise(decay: float) -> None:
    """Zero skew + any decay => identical fees to PiecewiseController."""
    pw_params = PiecewiseControllerParams(**_PIECEWISE_PARAMS_DICT).normalized()
    ema_params = EMAInventoryPiecewiseParams(
        **_PIECEWISE_PARAMS_DICT,
        inventory_ema_decay=decay,
        inventory_skew_to_bid=0.0,
        inventory_skew_to_ask=0.0,
        inventory_skew_dead_zone=0.0,
    ).normalized()

    pw = PiecewiseControllerStrategy(pw_params)
    ema = EMAInventoryPiecewiseStrategy(ema_params)
    pw_fees = [pw.after_initialize(1.0e6, 1.0e3)]
    ema_fees = [ema.after_initialize(1.0e6, 1.0e3)]

    # Drive 30 alternating-and-then-one-sided trades through both.
    rng_pattern = [True, True, False, True, True, True, False, False] * 4
    rx, ry = 1.0e6, 1.0e3
    for i, is_buy in enumerate(rng_pattern[:30]):
        amount_y = 1.0 + 0.05 * (i % 3)
        if is_buy:
            ry += amount_y
            rx -= 800.0
        else:
            ry -= amount_y
            rx += 800.0
        t = _trade(
            ts=i + 1, is_buy=is_buy, amount_y=amount_y, reserve_x=rx, reserve_y=ry
        )
        pw_fees.append(pw.after_swap(t))
        ema_fees.append(ema.after_swap(t))

    for i, (a, b) in enumerate(zip(pw_fees, ema_fees, strict=True)):
        assert a == pytest.approx(b, rel=0, abs=1e-12), (
            f"step {i}: piecewise={a} ema={b}"
        )


def test_decay_zero_tracks_instantaneous() -> None:
    """decay=0 => imbalance_ema equals latest raw imbalance after each trade."""
    params = EMAInventoryPiecewiseParams(
        **_PIECEWISE_PARAMS_DICT,
        inventory_ema_decay=0.0,
        inventory_skew_to_bid=0.01,
        inventory_skew_to_ask=0.01,
        inventory_skew_dead_zone=0.0,
    ).normalized()
    strat = EMAInventoryPiecewiseStrategy(params)
    strat.after_initialize(1.0e6, 1.0e3)
    rx, ry = 1.0e6, 1.0e3
    for i in range(5):
        # Pull y up (buy x — wait, "is_buy" semantics here: amount_y goes IN
        # to AMM on a buy. Increase y, decrease x.).
        ry += 1.0
        rx -= 800.0
        strat.after_swap(_trade(ts=i + 1, is_buy=True, amount_y=1.0,
                                reserve_x=rx, reserve_y=ry))
        expected_raw = 0.5 * (ry / 1.0e3 - rx / 1.0e6)
        assert strat.state.imbalance_ema == pytest.approx(expected_raw, rel=0, abs=1e-9)


def test_high_decay_smooths_imbalance() -> None:
    """decay=0.9 => ema is well below the latest raw imbalance after a single trade."""
    params = EMAInventoryPiecewiseParams(
        **_PIECEWISE_PARAMS_DICT,
        inventory_ema_decay=0.9,
        inventory_skew_to_bid=0.0,
        inventory_skew_to_ask=0.0,
        inventory_skew_dead_zone=0.0,
    ).normalized()
    strat = EMAInventoryPiecewiseStrategy(params)
    strat.after_initialize(1.0e6, 1.0e3)
    rx = 1.0e6 - 800.0
    ry = 1.0e3 + 1.0
    strat.after_swap(_trade(ts=1, is_buy=True, amount_y=1.0,
                            reserve_x=rx, reserve_y=ry))
    raw = 0.5 * (ry / 1.0e3 - rx / 1.0e6)
    expected_ema = 0.9 * 0.0 + 0.1 * raw
    assert strat.state.imbalance_ema == pytest.approx(expected_ema, rel=0, abs=1e-9)
    # And the ema is much smaller than raw.
    assert abs(strat.state.imbalance_ema) < abs(raw)


def test_zero_skew_recovers_cycle8_baseline() -> None:
    """Anchor parity: zero-skew EMA-inv on 32 cycle-8 test seeds == bare piecewise."""
    spec_pw = POLICY_SPECS["piecewise"]
    spec_ema = POLICY_SPECS["ema_inventory_piecewise"]

    pw_params = spec_pw.params_cls(**_PIECEWISE_PARAMS_DICT).normalized()
    ema_params = spec_ema.params_cls(
        **_PIECEWISE_PARAMS_DICT,
        inventory_ema_decay=0.5,
        inventory_skew_to_bid=0.0,
        inventory_skew_to_ask=0.0,
        inventory_skew_dead_zone=0.0,
    ).normalized()

    seeds = tuple(range(2000, 2032))
    norm = lambda: FixedFeeStrategy(0.003, 0.003)  # noqa: E731
    pw_batch = run_batch(
        lambda: spec_pw.strategy_cls(pw_params),
        seeds,
        normalizer_strategy_factory=norm,
        evaluator_kind="challenge",
    )
    ema_batch = run_batch(
        lambda: spec_ema.strategy_cls(ema_params),
        seeds,
        normalizer_strategy_factory=norm,
        evaluator_kind="challenge",
    )
    # Equal up to float noise — the ema state has zero coupling to fees.
    assert ema_batch.score == pytest.approx(pw_batch.score, rel=0, abs=1e-6), (
        f"piecewise={pw_batch.score} ema={ema_batch.score}"
    )
