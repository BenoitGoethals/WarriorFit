"""Unit tests for the MFFT Eval calculator."""

import unittest

from warriorfit.core.cluster import Cluster
from warriorfit.core.Gender import Gender
from warriorfit.core.mfft_level import MfftLevel
from warriorfit.data.model.db_model import MfftEvalTest
from warriorfit.logic.mfft_eval_calculator import (
    COMBAT_THRESHOLDS,
    MfftEvalCalculator,
)


def _make_test(values: tuple[int, ...]) -> MfftEvalTest:
    """Build an MfftEvalTest from an 8-tuple of raw event values."""
    (pull_ups, burpees, farmer_m, push_ups, drag_m, sandbag_m, run_s, swim_s) = values
    t = MfftEvalTest()
    t.pull_ups = pull_ups
    t.burpees_step_over = burpees
    t.farmer_walk_m = farmer_m
    t.push_ups_release = push_ups
    t.casualty_drag_m = drag_m
    t.sandbag_carry_m = sandbag_m
    t.combat_run_seconds = run_s
    t.combat_swim_seconds = swim_s
    return t


GOLD_ROW = COMBAT_THRESHOLDS[MfftLevel.GOLD]
SILVER_ROW = COMBAT_THRESHOLDS[MfftLevel.SILVER]
BRONZE_ROW = COMBAT_THRESHOLDS[MfftLevel.BRONZE]
FIT_ROW = COMBAT_THRESHOLDS[MfftLevel.FIT]


class TestEventTierCombat(unittest.TestCase):
    """Per-event COMBAT tier classification."""

    def test_pull_up_gold(self):
        self.assertEqual(MfftLevel.GOLD, MfftEvalCalculator.event_tier_combat(0, 8))

    def test_pull_up_silver(self):
        self.assertEqual(MfftLevel.SILVER, MfftEvalCalculator.event_tier_combat(0, 6))

    def test_pull_up_bronze(self):
        self.assertEqual(MfftLevel.BRONZE, MfftEvalCalculator.event_tier_combat(0, 4))

    def test_pull_up_fit(self):
        self.assertEqual(MfftLevel.FIT, MfftEvalCalculator.event_tier_combat(0, 2))

    def test_pull_up_unfit(self):
        self.assertEqual(MfftLevel.UNFIT, MfftEvalCalculator.event_tier_combat(0, 1))

    def test_combat_run_gold(self):
        # Lower time is better; <= 30 minutes = GOLD.
        self.assertEqual(MfftLevel.GOLD, MfftEvalCalculator.event_tier_combat(6, 30 * 60))

    def test_combat_run_silver(self):
        self.assertEqual(MfftLevel.SILVER, MfftEvalCalculator.event_tier_combat(6, 34 * 60))

    def test_combat_run_unfit(self):
        # Slower than the FIT threshold (44 min) -> UNFIT.
        self.assertEqual(MfftLevel.UNFIT, MfftEvalCalculator.event_tier_combat(6, 50 * 60))

    def test_combat_swim_fit(self):
        self.assertEqual(MfftLevel.FIT, MfftEvalCalculator.event_tier_combat(7, 6 * 60))

    def test_invalid_event_idx_raises(self):
        with self.assertRaises(ValueError):
            MfftEvalCalculator.event_tier_combat(8, 0)


class TestCombatClusterEvaluation(unittest.TestCase):
    """COMBAT cluster validates a tier when >= 6 of 8 events hit that tier."""

    def test_all_gold_overall_gold(self):
        test = _make_test(GOLD_ROW)
        res = MfftEvalCalculator.evaluate(test, Cluster.COMBAT, age=25, gender=Gender.M)
        self.assertEqual(MfftLevel.GOLD, res.overall)
        self.assertTrue(res.passed)

    def test_six_gold_two_silver_is_gold(self):
        values = list(GOLD_ROW)
        # Demote 2 higher-is-better events down to SILVER thresholds.
        values[0] = SILVER_ROW[0]
        values[1] = SILVER_ROW[1]
        res = MfftEvalCalculator.evaluate(
            _make_test(tuple(values)), Cluster.COMBAT, age=25, gender=Gender.M
        )
        self.assertEqual(MfftLevel.GOLD, res.overall)

    def test_five_gold_three_silver_is_silver(self):
        values = list(GOLD_ROW)
        values[0] = SILVER_ROW[0]
        values[1] = SILVER_ROW[1]
        values[2] = SILVER_ROW[2]
        res = MfftEvalCalculator.evaluate(
            _make_test(tuple(values)), Cluster.COMBAT, age=25, gender=Gender.M
        )
        self.assertEqual(MfftLevel.SILVER, res.overall)

    def test_any_unfit_event_fails_combat(self):
        values = list(GOLD_ROW)
        values[0] = 0  # pull-ups below FIT threshold
        res = MfftEvalCalculator.evaluate(
            _make_test(tuple(values)), Cluster.COMBAT, age=25, gender=Gender.M
        )
        self.assertEqual(MfftLevel.UNFIT, res.overall)
        self.assertFalse(res.passed)

    def test_all_fit_no_unfit_is_fit(self):
        res = MfftEvalCalculator.evaluate(
            _make_test(FIT_ROW), Cluster.COMBAT, age=25, gender=Gender.M
        )
        self.assertEqual(MfftLevel.FIT, res.overall)
        self.assertTrue(res.passed)


class TestEnablerClusterEvaluation(unittest.TestCase):
    """ENABLER uses a single age-bracketed pass threshold (gender neutral)."""

    def test_under_30_meets_threshold(self):
        # ENABLER <30 row == COMBAT SILVER row.
        res = MfftEvalCalculator.evaluate(
            _make_test(SILVER_ROW), Cluster.ENABLER, age=29, gender=Gender.M
        )
        self.assertTrue(res.passed)
        self.assertEqual(MfftLevel.FIT, res.overall)

    def test_age_30_bumps_to_next_bracket(self):
        # At age 30 the threshold drops to the BRONZE row - passing values
        # at SILVER row trivially pass.
        res = MfftEvalCalculator.evaluate(
            _make_test(BRONZE_ROW), Cluster.ENABLER, age=30, gender=Gender.F
        )
        self.assertTrue(res.passed)

    def test_age_50_uses_50_plus_bracket(self):
        # 50+ ENABLER row: pull-up threshold is 1; 0 should fail.
        values = list(BRONZE_ROW)
        values[0] = 0
        res = MfftEvalCalculator.evaluate(
            _make_test(tuple(values)), Cluster.ENABLER, age=55, gender=Gender.M
        )
        self.assertFalse(res.passed)
        self.assertEqual(MfftLevel.UNFIT, res.overall)

    def test_one_event_below_threshold_fails(self):
        values = list(SILVER_ROW)
        values[6] = 60 * 60  # combat run too slow
        res = MfftEvalCalculator.evaluate(
            _make_test(tuple(values)), Cluster.ENABLER, age=25, gender=Gender.M
        )
        self.assertFalse(res.passed)


class TestOpsSpClusterEvaluation(unittest.TestCase):
    """OPS_SP uses an age + sex bracketed single pass threshold."""

    def test_men_under_30_passes_bronze_row(self):
        # OPS_SP men <30 row == COMBAT BRONZE row.
        res = MfftEvalCalculator.evaluate(
            _make_test(BRONZE_ROW), Cluster.OPS_SP, age=25, gender=Gender.M
        )
        self.assertTrue(res.passed)

    def test_women_30_to_39_passes(self):
        # OPS_SP women 30-39 row: 2/6/30/14/15/30/49:00/7:00 — exact row passes.
        row = (2, 6, 30, 14, 15, 30, 49 * 60, 7 * 60)
        res = MfftEvalCalculator.evaluate(
            _make_test(row), Cluster.OPS_SP, age=35, gender=Gender.F
        )
        self.assertTrue(res.passed)

    def test_women_50_plus_fails_on_slow_swim(self):
        # OPS_SP women 50+ row swim threshold is 8:00; 9:00 fails.
        row = (1, 2, 10, 10, 5, 10, 59 * 60, 9 * 60)
        res = MfftEvalCalculator.evaluate(
            _make_test(row), Cluster.OPS_SP, age=55, gender=Gender.F
        )
        self.assertFalse(res.passed)


class TestTerSpClusterEvaluation(unittest.TestCase):
    """TER_SP shares scoring shape with OPS_SP."""

    def test_men_40_to_49_passes(self):
        row = (1, 4, 30, 14, 15, 30, 49 * 60, 7 * 60)
        res = MfftEvalCalculator.evaluate(
            _make_test(row), Cluster.TER_SP, age=45, gender=Gender.M
        )
        self.assertTrue(res.passed)

    def test_women_under_30_fails_when_short(self):
        row = (1, 6, 40, 16, 20, 40, 44 * 60, 6 * 60)  # pull-ups 1 < threshold 2
        res = MfftEvalCalculator.evaluate(
            _make_test(row), Cluster.TER_SP, age=25, gender=Gender.F
        )
        self.assertFalse(res.passed)


class TestNonDeployable(unittest.TestCase):
    """NON_DEP has no official scale; we apply the COMBAT-equivalent verdict
    so a soldier with any UNFIT event is not marked as passed."""

    def test_non_dep_passes_when_all_events_at_least_fit(self):
        res = MfftEvalCalculator.evaluate(
            _make_test(GOLD_ROW), Cluster.NON_DEP, age=40, gender=Gender.M
        )
        self.assertTrue(res.passed)
        self.assertEqual(MfftLevel.GOLD, res.overall)
        self.assertEqual(MfftLevel.GOLD, res.tier_info)

    def test_non_dep_fails_when_any_event_is_unfit(self):
        values = list(GOLD_ROW)
        values[0] = 0  # pull-ups below FIT threshold -> UNFIT
        res = MfftEvalCalculator.evaluate(
            _make_test(tuple(values)), Cluster.NON_DEP, age=40, gender=Gender.M
        )
        self.assertFalse(res.passed)
        self.assertEqual(MfftLevel.UNFIT, res.overall)
        self.assertEqual(MfftLevel.UNFIT, res.tier_info)


class TestTierInfoForNonCombat(unittest.TestCase):
    """`tier_info` is the COMBAT-equivalent tier regardless of cluster."""

    def test_enabler_gets_combat_tier_info(self):
        res = MfftEvalCalculator.evaluate(
            _make_test(GOLD_ROW), Cluster.ENABLER, age=25, gender=Gender.M
        )
        self.assertEqual(MfftLevel.GOLD, res.tier_info)


class TestPassedOverallInvariant(unittest.TestCase):
    """Invariant: ``passed`` is True if and only if ``overall != UNFIT``,
    for every cluster. The grid must never show ``Overall=UNFIT`` with
    ``Result=Passed``.
    """

    UNFIT_VALUES = (0, 0, 0, 0, 0, 0, 99 * 60, 99 * 60)
    CLUSTERS = (Cluster.COMBAT, Cluster.ENABLER, Cluster.OPS_SP, Cluster.TER_SP, Cluster.NON_DEP)

    def test_gold_row_invariant_holds(self):
        for cluster in self.CLUSTERS:
            with self.subTest(cluster=cluster):
                res = MfftEvalCalculator.evaluate(
                    _make_test(GOLD_ROW), cluster, age=25, gender=Gender.M
                )
                self.assertEqual(res.passed, res.overall is not MfftLevel.UNFIT)

    def test_unfit_row_invariant_holds(self):
        for cluster in self.CLUSTERS:
            with self.subTest(cluster=cluster):
                res = MfftEvalCalculator.evaluate(
                    _make_test(self.UNFIT_VALUES), cluster, age=25, gender=Gender.M
                )
                self.assertFalse(res.passed)
                self.assertEqual(MfftLevel.UNFIT, res.overall)


class TestGenderStringAccepted(unittest.TestCase):
    """The calculator accepts a Gender enum or its string literal."""

    def test_gender_literal_string(self):
        res = MfftEvalCalculator.evaluate(_make_test(GOLD_ROW), Cluster.OPS_SP, 25, "M")
        self.assertTrue(res.passed)


if __name__ == "__main__":
    unittest.main()
