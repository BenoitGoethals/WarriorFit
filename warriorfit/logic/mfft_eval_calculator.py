"""MFFT Eval scoring calculator.

The Eval MFFT is scored across 8 events. Six are higher-is-better counts
(reps or meters); the last two are timed and lower-is-better. The scale
depends on the soldier's cluster (and age, and for OPS_SP / TER_SP, sex):

    COMBAT      - Gender & age neutral. Four tiers: GOLD/SILVER/BRONZE/FIT.
                  A tier is validated when >= 6 of 8 events reach that
                  tier AND no event is UNFIT.
    ENABLER     - Gender neutral, age-bracketed single threshold.
    OPS_SP      - Age + sex bracketed single threshold.
    TER_SP      - Age + sex bracketed single threshold (same shape as OPS_SP).
    NON_DEP     - No official scale. The calculator still reports an
                  informational COMBAT-equivalent tier.

Tuple layout for every threshold row::

    (pull_ups, burpees_step_over, farmer_walk_m, push_ups_release,
     casualty_drag_m, sandbag_carry_m, combat_run_seconds,
     combat_swim_seconds)

Higher is better for indices 0..5; lower is better for 6..7 (timed).
Thresholds are taken from the official scoring matrix.
"""

from __future__ import annotations

from dataclasses import dataclass

from warriorfit.core.cluster import Cluster
from warriorfit.core.Gender import Gender
from warriorfit.core.mfft_level import MfftLevel
from warriorfit.data.model.db_model import MfftEvalTest

EVENT_COUNT: int = 8
COMBAT_TIER_VALIDATION_COUNT: int = 6

# (pull_ups, burpees, farmer_m, push_ups, drag_m, sandbag_m, run_s, swim_s)
COMBAT_THRESHOLDS: dict[MfftLevel, tuple[int, ...]] = {
    MfftLevel.GOLD: (8, 12, 70, 22, 35, 70, 30 * 60, 3 * 60),
    MfftLevel.SILVER: (6, 10, 60, 20, 30, 60, 34 * 60, 4 * 60),
    MfftLevel.BRONZE: (4, 8, 50, 18, 25, 50, 39 * 60, 5 * 60),
    MfftLevel.FIT: (2, 6, 40, 16, 20, 40, 44 * 60, 6 * 60),
}

ENABLER_THRESHOLDS: dict[str, tuple[int, ...]] = {
    "<30": (6, 10, 60, 20, 30, 60, 34 * 60, 4 * 60),
    "30-39": (4, 8, 50, 18, 25, 50, 39 * 60, 5 * 60),
    "40-49": (2, 6, 40, 16, 20, 40, 44 * 60, 6 * 60),
    "50+": (1, 4, 30, 14, 15, 30, 49 * 60, 7 * 60),
}

OPS_SP_THRESHOLDS_M: dict[str, tuple[int, ...]] = {
    "<30": (4, 8, 50, 18, 25, 50, 39 * 60, 5 * 60),
    "30-39": (2, 6, 40, 16, 20, 40, 44 * 60, 6 * 60),
    "40-49": (1, 4, 30, 14, 15, 30, 49 * 60, 7 * 60),
    "50+": (1, 2, 20, 12, 10, 20, 54 * 60, 8 * 60),
}

OPS_SP_THRESHOLDS_F: dict[str, tuple[int, ...]] = {
    "<30": (2, 6, 40, 16, 20, 40, 44 * 60, 6 * 60),
    "30-39": (2, 6, 30, 14, 15, 30, 49 * 60, 7 * 60),
    "40-49": (1, 4, 20, 12, 10, 20, 54 * 60, 8 * 60),
    "50+": (1, 2, 10, 10, 5, 10, 59 * 60, 8 * 60),
}

# TER_SP rows on the official table match OPS_SP one-for-one.
TER_SP_THRESHOLDS_M: dict[str, tuple[int, ...]] = OPS_SP_THRESHOLDS_M
TER_SP_THRESHOLDS_F: dict[str, tuple[int, ...]] = OPS_SP_THRESHOLDS_F


HIGHER_IS_BETTER_EVENTS: tuple[int, ...] = (0, 1, 2, 3, 4, 5)
LOWER_IS_BETTER_EVENTS: tuple[int, ...] = (6, 7)

# Tier order, best to worst — used when downgrading the overall result.
COMBAT_TIER_ORDER: tuple[MfftLevel, ...] = (
    MfftLevel.GOLD,
    MfftLevel.SILVER,
    MfftLevel.BRONZE,
    MfftLevel.FIT,
)


@dataclass(frozen=True, slots=True)
class MfftResult:
    """Outcome of evaluating an `MfftEvalTest` for a given soldier.

    `overall` is the cluster-aware verdict and is **UNFIT** whenever the
    soldier did not pass — `passed` and `overall != UNFIT` are equivalent.

    - COMBAT: highest tier validated (>= 6 events at tier, no UNFIT).
    - ENABLER / OPS_SP / TER_SP: FIT when every event meets the single
      age/sex threshold, UNFIT otherwise.
    - NON_DEP: no official scale, so we use the COMBAT-equivalent tier
      (`tier_info`) as the verdict. Any UNFIT event makes the row fail.

    `tier_info` is the COMBAT-equivalent tier regardless of cluster.
    """

    per_event: list[MfftLevel]
    overall: MfftLevel
    passed: bool
    tier_info: MfftLevel


def _meets(event_idx: int, value: int, threshold: int) -> bool:
    """A measurement meets the threshold (higher-is-better or timed)."""
    if event_idx in HIGHER_IS_BETTER_EVENTS:
        return value >= threshold
    return value <= threshold


def _age_bracket(age: int) -> str:
    if age < 30:
        return "<30"
    if age < 40:
        return "30-39"
    if age < 50:
        return "40-49"
    return "50+"


def _event_values(test: MfftEvalTest) -> tuple[int, ...]:
    return (
        int(test.pull_ups),
        int(test.burpees_step_over),
        int(test.farmer_walk_m),
        int(test.push_ups_release),
        int(test.casualty_drag_m),
        int(test.sandbag_carry_m),
        int(test.combat_run_seconds),
        int(test.combat_swim_seconds),
    )


def _normalize_gender(gender: Gender | str) -> Gender:
    if isinstance(gender, Gender):
        return gender
    if isinstance(gender, str) and gender.lower().startswith("m"):
        return Gender.M
    return Gender.F


class MfftEvalCalculator:
    """Stateless scoring for the MFFT Eval."""

    @staticmethod
    def event_tier_combat(event_idx: int, value: int) -> MfftLevel:
        """Return the highest COMBAT tier `value` reaches for `event_idx`."""
        if event_idx < 0 or event_idx >= EVENT_COUNT:
            raise ValueError(f"event_idx must be 0..{EVENT_COUNT - 1}, got {event_idx}")
        for tier in COMBAT_TIER_ORDER:
            threshold = COMBAT_THRESHOLDS[tier][event_idx]
            if _meets(event_idx, value, threshold):
                return tier
        return MfftLevel.UNFIT

    @staticmethod
    def per_event_combat_tiers(test: MfftEvalTest) -> list[MfftLevel]:
        values = _event_values(test)
        return [MfftEvalCalculator.event_tier_combat(i, v) for i, v in enumerate(values)]

    @staticmethod
    def _combat_overall(per_event: list[MfftLevel]) -> MfftLevel:
        if any(t is MfftLevel.UNFIT for t in per_event):
            return MfftLevel.UNFIT
        for tier in COMBAT_TIER_ORDER:
            count_at_or_above = sum(1 for t in per_event if t >= tier)
            if count_at_or_above >= COMBAT_TIER_VALIDATION_COUNT:
                return tier
        return MfftLevel.UNFIT

    @staticmethod
    def _single_threshold_row(
        cluster: Cluster, age: int, gender: Gender
    ) -> tuple[int, ...] | None:
        bracket = _age_bracket(age)
        if cluster is Cluster.ENABLER:
            return ENABLER_THRESHOLDS[bracket]
        if cluster is Cluster.OPS_SP:
            return (
                OPS_SP_THRESHOLDS_M[bracket]
                if gender is Gender.M
                else OPS_SP_THRESHOLDS_F[bracket]
            )
        if cluster is Cluster.TER_SP:
            return (
                TER_SP_THRESHOLDS_M[bracket]
                if gender is Gender.M
                else TER_SP_THRESHOLDS_F[bracket]
            )
        return None

    @staticmethod
    def evaluate(
        test: MfftEvalTest,
        cluster: Cluster,
        age: int,
        gender: Gender | str,
    ) -> MfftResult:
        """Score an MFFT Eval test against a cluster's scale.

        Always populates `tier_info` (the COMBAT-equivalent tier) so the UI
        can show the achieved tier even for ENABLER / OPS_SP / TER_SP /
        NON_DEP soldiers.
        """
        g = _normalize_gender(gender)
        per_event = MfftEvalCalculator.per_event_combat_tiers(test)
        tier_info = MfftEvalCalculator._combat_overall(per_event)

        if cluster is Cluster.COMBAT or cluster is Cluster.NON_DEP:
            # COMBAT has a formal scale; NON_DEP has none, so we apply the
            # COMBAT verdict to keep "any UNFIT event => not passed" honest.
            overall = tier_info
            passed = overall is not MfftLevel.UNFIT
            return MfftResult(
                per_event=per_event, overall=overall, passed=passed, tier_info=tier_info
            )

        row = MfftEvalCalculator._single_threshold_row(cluster, age, g)
        if row is None:
            return MfftResult(
                per_event=per_event, overall=MfftLevel.UNFIT, passed=False, tier_info=tier_info
            )

        values = _event_values(test)
        all_meet = all(_meets(i, values[i], row[i]) for i in range(EVENT_COUNT))
        overall = MfftLevel.FIT if all_meet else MfftLevel.UNFIT
        return MfftResult(
            per_event=per_event, overall=overall, passed=all_meet, tier_info=tier_info
        )
