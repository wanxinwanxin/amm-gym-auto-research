"""
Ladder5ControllerStrategy — k=5 bucket extension of the cycle-26 4-bucket
LadderControllerStrategy.

Design.
  Mirrors the 4-bucket ladder exactly but splits the tiny bucket into
  ultra_tiny + tiny. Adds 3 new dims: ultra_tiny_trade_threshold,
  continuation_ultra_tiny, reversal_ultra_tiny. Total 22 dims (vs
  the 4-bucket ladder's 19, vs piecewise's 16).

  Identity warm-start from piecewise. Initializing
      ultra_tiny_threshold = small_threshold * 0.25
      tiny_threshold       = small_threshold * 0.5
      small_threshold      = small_threshold
      continuation_{ultra_tiny, tiny, small} = continuation_small (piecewise)
      reversal_{ultra_tiny, tiny, small}     = reversal_small (piecewise)
  produces *exactly* the piecewise-controller behaviour at warm start.
  CEM is then free to separate ultra_tiny / tiny / small bucket params.

  This is the "6-bucket (one extra small-bucket)" candidate from the
  cycle-27 active hypothesis. The author labelled it 6-bucket but the
  description ("split the tiny bucket from cycle-26's 4-bucket into
  tiny+ultra-tiny") describes a 1-bucket addition (4 → 5). We
  follow the description; see cycle-27 LOG entry for the labelling
  note.

  Note. The 4-bucket ladder warm-started directly from piecewise
  (cycle 26). For apples-to-apples, this 5-bucket strategy also
  warm-starts directly from piecewise — *not* from the cycle-26
  4-bucket-best — so the cycle-27 lift over piecewise is comparable
  to the cycle-26 lift over piecewise on the same anchor.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from arena_eval.core.types import TradeInfo


MAX_FEE = 0.1


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


@dataclass(frozen=True)
class Ladder5ControllerParams:
    """5-bucket ladder: ultra_tiny / tiny / small / medium / large."""

    base_fee: float = 0.003
    base_spread: float = 0.0
    signal_decay: float = 0.82
    toxicity_decay: float = 0.9
    ultra_tiny_trade_threshold: float = 0.00075
    tiny_trade_threshold: float = 0.0015
    small_trade_threshold: float = 0.003
    large_trade_threshold: float = 0.012
    continuation_ultra_tiny: float = 0.001
    continuation_tiny: float = 0.001
    continuation_small: float = 0.002
    continuation_medium: float = 0.004
    continuation_large: float = 0.001
    reversal_ultra_tiny: float = 0.003
    reversal_tiny: float = 0.003
    reversal_small: float = 0.006
    reversal_medium: float = 0.012
    reversal_large: float = 0.02
    continuation_to_same_side: float = 1.0
    continuation_to_cross_side: float = 0.3
    toxicity_to_mid: float = 0.015
    toxicity_to_side: float = 0.03

    def normalized(self) -> "Ladder5ControllerParams":
        ut = _clamp(self.ultra_tiny_trade_threshold, 1e-6, 0.04)
        tiny = _clamp(self.tiny_trade_threshold, ut + 1e-6, 0.05)
        small = _clamp(self.small_trade_threshold, tiny + 1e-5, 0.06)
        large = _clamp(self.large_trade_threshold, small + 1e-5, 0.1)
        return Ladder5ControllerParams(
            base_fee=_clamp(self.base_fee, 0.0, MAX_FEE),
            base_spread=_clamp(self.base_spread, 0.0, MAX_FEE),
            signal_decay=_clamp(self.signal_decay, 0.0, 0.999),
            toxicity_decay=_clamp(self.toxicity_decay, 0.0, 0.999),
            ultra_tiny_trade_threshold=ut,
            tiny_trade_threshold=tiny,
            small_trade_threshold=small,
            large_trade_threshold=large,
            continuation_ultra_tiny=_clamp(self.continuation_ultra_tiny, -0.05, 0.05),
            continuation_tiny=_clamp(self.continuation_tiny, -0.05, 0.05),
            continuation_small=_clamp(self.continuation_small, -0.05, 0.05),
            continuation_medium=_clamp(self.continuation_medium, -0.05, 0.05),
            continuation_large=_clamp(self.continuation_large, -0.05, 0.05),
            reversal_ultra_tiny=_clamp(self.reversal_ultra_tiny, -0.05, 0.1),
            reversal_tiny=_clamp(self.reversal_tiny, -0.05, 0.1),
            reversal_small=_clamp(self.reversal_small, -0.05, 0.1),
            reversal_medium=_clamp(self.reversal_medium, -0.05, 0.1),
            reversal_large=_clamp(self.reversal_large, -0.05, 0.1),
            continuation_to_same_side=_clamp(self.continuation_to_same_side, -5.0, 5.0),
            continuation_to_cross_side=_clamp(self.continuation_to_cross_side, -5.0, 5.0),
            toxicity_to_mid=_clamp(self.toxicity_to_mid, -0.05, 0.05),
            toxicity_to_side=_clamp(self.toxicity_to_side, 0.0, 0.2),
        )


# Match the 4-bucket ladder bounds plus the new ultra_tiny dims.
LADDER5_PARAM_RANGES: dict[str, tuple[float, float]] = {
    "base_fee": (0.0, 0.01),
    "base_spread": (0.0, 0.01),
    "signal_decay": (0.0, 0.999),
    "toxicity_decay": (0.0, 0.999),
    "ultra_tiny_trade_threshold": (0.00005, 0.005),
    "tiny_trade_threshold": (0.0001, 0.01),
    "small_trade_threshold": (0.0005, 0.01),
    "large_trade_threshold": (0.005, 0.05),
    "continuation_ultra_tiny": (-0.01, 0.01),
    "continuation_tiny": (-0.01, 0.01),
    "continuation_small": (-0.01, 0.01),
    "continuation_medium": (-0.01, 0.01),
    "continuation_large": (-0.01, 0.05),
    "reversal_ultra_tiny": (-0.01, 0.1),
    "reversal_tiny": (-0.01, 0.1),
    "reversal_small": (-0.01, 0.1),
    "reversal_medium": (-0.01, 0.1),
    "reversal_large": (-0.01, 0.1),
    "continuation_to_same_side": (-2.0, 2.0),
    "continuation_to_cross_side": (-2.0, 2.0),
    "toxicity_to_mid": (-0.05, 0.05),
    "toxicity_to_side": (0.0, 0.2),
}


@dataclass
class Ladder5ControllerState:
    last_side: int = 0
    last_timestamp: int = 0
    bid_signal: float = 0.0
    ask_signal: float = 0.0
    bid_toxicity: float = 0.0
    ask_toxicity: float = 0.0
    initialized: bool = False


class Ladder5ControllerStrategy:
    """5-bucket ladder controller mirroring the 4-bucket ladder."""

    def __init__(self, params: Ladder5ControllerParams | None = None) -> None:
        self.params = (params or Ladder5ControllerParams()).normalized()
        self.state = Ladder5ControllerState()

    def after_initialize(self, initial_x: float, initial_y: float) -> tuple[float, float]:
        self.state = Ladder5ControllerState(initialized=True)
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
        state.initialized = True
        return self._fees()

    def _bucket_weights(self, size_ratio: float) -> tuple[float, float]:
        params = self.params
        if size_ratio < params.ultra_tiny_trade_threshold:
            return (params.continuation_ultra_tiny, params.reversal_ultra_tiny)
        if size_ratio < params.tiny_trade_threshold:
            return (params.continuation_tiny, params.reversal_tiny)
        if size_ratio < params.small_trade_threshold:
            return (params.continuation_small, params.reversal_small)
        if size_ratio < params.large_trade_threshold:
            return (params.continuation_medium, params.reversal_medium)
        return (params.continuation_large, params.reversal_large)

    def _fees(self) -> tuple[float, float]:
        params = self.params
        state = self.state
        toxicity_total = state.bid_toxicity + state.ask_toxicity
        base = params.base_fee + 0.5 * params.base_spread + params.toxicity_to_mid * toxicity_total
        bid_fee = _clamp(
            base
            + params.toxicity_to_side * state.bid_toxicity
            - params.continuation_to_same_side * state.bid_signal
            + params.continuation_to_cross_side * state.ask_signal,
            0.0,
            MAX_FEE,
        )
        ask_fee = _clamp(
            base
            + params.toxicity_to_side * state.ask_toxicity
            - params.continuation_to_same_side * state.ask_signal
            + params.continuation_to_cross_side * state.bid_signal,
            0.0,
            MAX_FEE,
        )
        return (bid_fee, ask_fee)
