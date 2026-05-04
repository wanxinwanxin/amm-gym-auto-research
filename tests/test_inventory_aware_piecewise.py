"""Tests for `InventoryAwarePiecewiseStrategy`.

Cycle-8 fork of `PiecewiseControllerStrategy` with three new
inventory-skew parameters. The two key invariants we want to lock down:

1. With the three new params at zero, the strategy is behaviourally
   identical to `PiecewiseControllerStrategy` on the exact simple-AMM —
   batch score, edge components, and per-trade fees match within fp
   tolerance. This is what makes warm-start CEM well-defined.
2. With non-zero inventory_skew_to_bid / inventory_skew_to_ask, the
   bid-fee and ask-fee respond in the documented direction when the
   AMM accumulates excess y or excess x.
"""

from __future__ import annotations

import math

from arena_eval.exact_simple_amm import FixedFeeStrategy, run_batch
from arena_policies import (
    InventoryAwarePiecewiseParams,
    InventoryAwarePiecewiseStrategy,
    PiecewiseControllerParams,
    PiecewiseControllerStrategy,
)
from arena_eval.core.types import TradeInfo


def _piecewise_params() -> dict[str, float]:
    return {
        "base_fee": 0.0024,
        "base_spread": 0.0043,
        "signal_decay": 0.55,
        "toxicity_decay": 0.55,
        "small_trade_threshold": 0.0042,
        "large_trade_threshold": 0.010,
        "continuation_small": -0.00012,
        "continuation_medium": 0.0121,
        "continuation_large": 0.020,
        "reversal_small": 0.0163,
        "reversal_medium": 0.0193,
        "reversal_large": 0.0781,
        "continuation_to_same_side": 0.227,
        "continuation_to_cross_side": 0.896,
        "toxicity_to_mid": 0.0124,
        "toxicity_to_side": 0.063,
    }


def test_zero_skew_matches_piecewise_batch_score():
    """Behavioural parity over a multi-seed batch."""
    base = _piecewise_params()
    pw = PiecewiseControllerParams(**base).normalized()
    inv = InventoryAwarePiecewiseParams(
        **base,
        inventory_skew_to_bid=0.0,
        inventory_skew_to_ask=0.0,
        inventory_skew_dead_zone=0.0,
    ).normalized()

    seeds = tuple(range(0, 4))
    pw_batch = run_batch(
        lambda: PiecewiseControllerStrategy(pw),
        seeds,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(0.003, 0.003),
        evaluator_kind="challenge",
    )
    inv_batch = run_batch(
        lambda: InventoryAwarePiecewiseStrategy(inv),
        seeds,
        normalizer_strategy_factory=lambda: FixedFeeStrategy(0.003, 0.003),
        evaluator_kind="challenge",
    )

    assert math.isclose(inv_batch.score, pw_batch.score, rel_tol=0, abs_tol=1e-9), (
        f"score mismatch: inv={inv_batch.score} pw={pw_batch.score}"
    )
    assert math.isclose(inv_batch.edge_mean_submission, pw_batch.edge_mean_submission, abs_tol=1e-9)
    assert math.isclose(
        inv_batch.edge_advantage_mean, pw_batch.edge_advantage_mean, abs_tol=1e-9
    )


def _make_trade(*, is_buy: bool, reserve_x: float, reserve_y: float, amount_y: float = 1.0,
                amount_x: float = 1.0, ts: int = 1) -> TradeInfo:
    return TradeInfo(
        is_buy=is_buy,
        amount_x=amount_x,
        amount_y=amount_y,
        timestamp=ts,
        reserve_x=reserve_x,
        reserve_y=reserve_y,
    )


def test_inventory_skew_responds_in_documented_direction():
    """Excess y must raise bid_fee and lower ask_fee (if both coefs are positive).

    We seed identical state by calling `after_initialize`, then deliver the
    same TradeInfo to two strategies: one with zero skew, one with
    inventory_skew_to_bid = inventory_skew_to_ask = 0.04. The fee diffs
    after one trade with reserve_y > reserve_y_init must satisfy:
        bid_fee_skew  > bid_fee_zero
        ask_fee_skew  < ask_fee_zero
    """
    base = _piecewise_params()
    zero = InventoryAwarePiecewiseParams(
        **base,
        inventory_skew_to_bid=0.0,
        inventory_skew_to_ask=0.0,
        inventory_skew_dead_zone=0.0,
    ).normalized()
    skew = InventoryAwarePiecewiseParams(
        **base,
        inventory_skew_to_bid=0.04,
        inventory_skew_to_ask=0.04,
        inventory_skew_dead_zone=0.0,
    ).normalized()

    s_zero = InventoryAwarePiecewiseStrategy(zero)
    s_skew = InventoryAwarePiecewiseStrategy(skew)
    s_zero.after_initialize(initial_x=1000.0, initial_y=1000.0)
    s_skew.after_initialize(initial_x=1000.0, initial_y=1000.0)

    # First trade: someone bought x with y → AMM has more y than initial.
    trade = _make_trade(is_buy=True, reserve_x=900.0, reserve_y=1100.0)
    bid_zero, ask_zero = s_zero.after_swap(trade)
    bid_skew, ask_skew = s_skew.after_swap(trade)

    # Imbalance > 0 (excess y). Documented direction:
    #   bid_fee skewed UP (discourage further y-in)
    #   ask_fee skewed DOWN (encourage y-out)
    assert bid_skew > bid_zero, f"bid: expected skew > zero, got {bid_skew} vs {bid_zero}"
    assert ask_skew < ask_zero, f"ask: expected skew < zero, got {ask_skew} vs {ask_zero}"


def test_inventory_dead_zone_suppresses_small_imbalance():
    """Dead zone with |imbalance| < dead_zone produces zero skew."""
    base = _piecewise_params()
    skew_no_dz = InventoryAwarePiecewiseParams(
        **base,
        inventory_skew_to_bid=0.04,
        inventory_skew_to_ask=0.04,
        inventory_skew_dead_zone=0.0,
    ).normalized()
    skew_dz = InventoryAwarePiecewiseParams(
        **base,
        inventory_skew_to_bid=0.04,
        inventory_skew_to_ask=0.04,
        inventory_skew_dead_zone=0.30,  # exceed any small imbalance
    ).normalized()

    s_no_dz = InventoryAwarePiecewiseStrategy(skew_no_dz)
    s_dz = InventoryAwarePiecewiseStrategy(skew_dz)
    s_no_dz.after_initialize(initial_x=1000.0, initial_y=1000.0)
    s_dz.after_initialize(initial_x=1000.0, initial_y=1000.0)

    # Tiny imbalance: 1% off in y.
    trade = _make_trade(is_buy=True, reserve_x=995.0, reserve_y=1005.0)
    bid_no_dz, ask_no_dz = s_no_dz.after_swap(trade)
    bid_dz, ask_dz = s_dz.after_swap(trade)

    # With huge dead zone, the skew terms shrink to zero on this trade,
    # so the dz strategy's output should match a strategy with zero skew.
    s_zero = InventoryAwarePiecewiseStrategy(
        InventoryAwarePiecewiseParams(
            **base,
            inventory_skew_to_bid=0.0,
            inventory_skew_to_ask=0.0,
            inventory_skew_dead_zone=0.0,
        ).normalized()
    )
    s_zero.after_initialize(initial_x=1000.0, initial_y=1000.0)
    bid_zero, ask_zero = s_zero.after_swap(trade)

    assert math.isclose(bid_dz, bid_zero, abs_tol=1e-12)
    assert math.isclose(ask_dz, ask_zero, abs_tol=1e-12)
    # Sanity: without dead zone, the skew term is non-zero.
    assert bid_no_dz != bid_zero
    assert ask_no_dz != ask_zero
