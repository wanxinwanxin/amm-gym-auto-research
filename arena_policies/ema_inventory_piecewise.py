"""EMA-inventory piecewise controller for the exact simple-AMM challenge.

Forks `InventoryAwarePiecewiseStrategy` (cycle-8 best, M2=446.6) by
replacing the *instantaneous* reserve-imbalance signal with an
exponential moving average over reserve deviation. Cycle-8 ablation
falsified the instantaneous-imbalance hypothesis (Δ = -0.17 vs zeroed);
the cycle-9 hypothesis is that ChallengeTape one-sided flow is too
intermittent for instantaneous skew to do anything useful, but a slow
EMA may pick up sustained directional pressure.

State: tracks `imbalance_ema` updated each `after_swap` as

    raw_imbalance = 0.5 * (y/y0 - x/x0)
    imbalance_ema = decay * imbalance_ema + (1 - decay) * raw_imbalance

(Larger `decay` -> longer memory.) The dead-zone soft-hinge is then
applied to `imbalance_ema` rather than the raw imbalance. With
`inventory_skew_to_bid = inventory_skew_to_ask = 0` and any decay, the
strategy is behaviourally identical to `PiecewiseControllerStrategy`.

Exposes 20 params: 16 piecewise + 4 inventory (decay, dead-zone, skews).

Cycle 9 deliverable per `research/STATE.md` (M2 priority #3).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from arena_eval.core.types import TradeInfo


MAX_FEE = 0.1


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


@dataclass(frozen=True)
class EMAInventoryPiecewiseParams:
    """Piecewise controller plus 4 EMA-inventory-skew parameters.

    The first 16 params are exactly the `PiecewiseControllerParams` set
    so we can warm-start CEM from the cycle-8 ablation best.
    """

    # --- inherited piecewise params -------------------------------------
    base_fee: float = 0.003
    base_spread: float = 0.0
    signal_decay: float = 0.82
    toxicity_decay: float = 0.9
    small_trade_threshold: float = 0.003
    large_trade_threshold: float = 0.012
    continuation_small: float = 0.002
    continuation_medium: float = 0.004
    continuation_large: float = 0.001
    reversal_small: float = 0.006
    reversal_medium: float = 0.012
    reversal_large: float = 0.02
    continuation_to_same_side: float = 1.0
    continuation_to_cross_side: float = 0.3
    toxicity_to_mid: float = 0.015
    toxicity_to_side: float = 0.03
    # --- new EMA-inventory-skew params ----------------------------------
    inventory_ema_decay: float = 0.9  # how much weight to keep on past imbalance
    inventory_skew_to_bid: float = 0.0
    inventory_skew_to_ask: float = 0.0
    inventory_skew_dead_zone: float = 0.0

    def normalized(self) -> "EMAInventoryPiecewiseParams":
        small = _clamp(self.small_trade_threshold, 1e-4, 0.05)
        large = _clamp(self.large_trade_threshold, small + 1e-4, 0.1)
        return EMAInventoryPiecewiseParams(
            base_fee=_clamp(self.base_fee, 0.0, MAX_FEE),
            base_spread=_clamp(self.base_spread, 0.0, MAX_FEE),
            signal_decay=_clamp(self.signal_decay, 0.0, 0.999),
            toxicity_decay=_clamp(self.toxicity_decay, 0.0, 0.999),
            small_trade_threshold=small,
            large_trade_threshold=large,
            continuation_small=_clamp(self.continuation_small, -0.05, 0.05),
            continuation_medium=_clamp(self.continuation_medium, -0.05, 0.05),
            continuation_large=_clamp(self.continuation_large, -0.05, 0.05),
            reversal_small=_clamp(self.reversal_small, 0.0, 0.08),
            reversal_medium=_clamp(self.reversal_medium, 0.0, 0.08),
            reversal_large=_clamp(self.reversal_large, 0.0, 0.08),
            continuation_to_same_side=_clamp(self.continuation_to_same_side, -4.0, 4.0),
            continuation_to_cross_side=_clamp(self.continuation_to_cross_side, -4.0, 4.0),
            toxicity_to_mid=_clamp(self.toxicity_to_mid, 0.0, 0.5),
            toxicity_to_side=_clamp(self.toxicity_to_side, 0.0, 0.5),
            inventory_ema_decay=_clamp(self.inventory_ema_decay, 0.0, 0.999),
            inventory_skew_to_bid=_clamp(self.inventory_skew_to_bid, -0.05, 0.05),
            inventory_skew_to_ask=_clamp(self.inventory_skew_to_ask, -0.05, 0.05),
            inventory_skew_dead_zone=_clamp(self.inventory_skew_dead_zone, 0.0, 0.5),
        )

    def to_dict(self) -> dict[str, float]:
        return dict(asdict(self.normalized()))


@dataclass
class EMAInventoryPiecewiseState:
    last_timestamp: int = 0
    last_side: int = 0
    bid_signal: float = 0.0
    ask_signal: float = 0.0
    bid_toxicity: float = 0.0
    ask_toxicity: float = 0.0
    initialized: bool = False
    reserve_x_init: float = 0.0
    reserve_y_init: float = 0.0
    reserve_x: float = 0.0
    reserve_y: float = 0.0
    imbalance_ema: float = 0.0


class EMAInventoryPiecewiseStrategy:
    """`PiecewiseControllerStrategy` plus EMA-inventory fee skew.

    With `inventory_skew_to_bid = inventory_skew_to_ask = 0`, the
    strategy is behaviourally identical to `PiecewiseControllerStrategy`
    regardless of the EMA decay value.
    """

    def __init__(self, params: EMAInventoryPiecewiseParams | None = None) -> None:
        self.params = (params or EMAInventoryPiecewiseParams()).normalized()
        self.state = EMAInventoryPiecewiseState()

    def after_initialize(self, initial_x: float, initial_y: float) -> tuple[float, float]:
        self.state = EMAInventoryPiecewiseState(
            initialized=True,
            reserve_x_init=float(initial_x),
            reserve_y_init=float(initial_y),
            reserve_x=float(initial_x),
            reserve_y=float(initial_y),
            imbalance_ema=0.0,
        )
        return self._fees()

    def after_swap(self, trade: TradeInfo) -> tuple[float, float]:
        params = self.params
        state = self.state
        dt = 1 if not state.initialized else max(1, int(trade.timestamp - state.last_timestamp))
        size_ratio = float(trade.amount_y) / max(trade.reserve_y, 1e-9)
        continuation_weight, reversal_weight = self._bucket_weights(size_ratio)
        reversal_scale = 1.0 / float(dt)
        current_side = 1 if trade.is_buy else -1

        state.bid_signal *= params.signal_decay
        state.ask_signal *= params.signal_decay
        state.bid_toxicity *= params.toxicity_decay
        state.ask_toxicity *= params.toxicity_decay

        if current_side == state.last_side:
            if trade.is_buy:
                state.bid_signal += continuation_weight
            else:
                state.ask_signal += continuation_weight
        elif state.last_side != 0:
            if trade.is_buy:
                state.ask_toxicity += reversal_weight * reversal_scale
                state.bid_signal += 0.5 * continuation_weight
            else:
                state.bid_toxicity += reversal_weight * reversal_scale
                state.ask_signal += 0.5 * continuation_weight
        else:
            if trade.is_buy:
                state.bid_signal += 0.5 * continuation_weight
            else:
                state.ask_signal += 0.5 * continuation_weight

        state.last_side = current_side
        state.last_timestamp = int(trade.timestamp)
        state.reserve_x = float(trade.reserve_x)
        state.reserve_y = float(trade.reserve_y)
        # EMA update: imbalance_ema = decay * imbalance_ema + (1-decay) * raw_imbalance
        if state.reserve_x_init > 0.0 and state.reserve_y_init > 0.0:
            raw = 0.5 * (
                state.reserve_y / state.reserve_y_init
                - state.reserve_x / state.reserve_x_init
            )
            state.imbalance_ema = (
                params.inventory_ema_decay * state.imbalance_ema
                + (1.0 - params.inventory_ema_decay) * raw
            )
        state.initialized = True
        return self._fees()

    def _bucket_weights(self, size_ratio: float) -> tuple[float, float]:
        params = self.params
        if size_ratio < params.small_trade_threshold:
            return (params.continuation_small, params.reversal_small)
        if size_ratio < params.large_trade_threshold:
            return (params.continuation_medium, params.reversal_medium)
        return (params.continuation_large, params.reversal_large)

    def _ema_imbalance_softhinged(self) -> float:
        """Dead-zone soft-hinge applied to the EMA, not the raw imbalance."""
        s = self.state
        ema = s.imbalance_ema
        dz = self.params.inventory_skew_dead_zone
        if ema > dz:
            return ema - dz
        if ema < -dz:
            return ema + dz
        return 0.0

    def _fees(self) -> tuple[float, float]:
        params = self.params
        state = self.state
        toxicity_total = state.bid_toxicity + state.ask_toxicity
        base = params.base_fee + 0.5 * params.base_spread + params.toxicity_to_mid * toxicity_total

        imbalance = self._ema_imbalance_softhinged()
        # Positive imbalance (excess y): raise bid_fee, lower ask_fee.
        bid_inv = params.inventory_skew_to_bid * imbalance
        ask_inv = -params.inventory_skew_to_ask * imbalance

        bid_fee = _clamp(
            base
            + params.toxicity_to_side * state.bid_toxicity
            - params.continuation_to_same_side * state.bid_signal
            + params.continuation_to_cross_side * state.ask_signal
            + bid_inv,
            0.0,
            MAX_FEE,
        )
        ask_fee = _clamp(
            base
            + params.toxicity_to_side * state.ask_toxicity
            - params.continuation_to_same_side * state.ask_signal
            + params.continuation_to_cross_side * state.bid_signal
            + ask_inv,
            0.0,
            MAX_FEE,
        )
        return (bid_fee, ask_fee)
