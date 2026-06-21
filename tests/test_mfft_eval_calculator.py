"""Unit tests for the MFFT Eval calculator.

This test file verifies that the MFFT Eval calculator applies the correct
business rules for every supported soldier cluster.

Manager summary:
- The MFFT Eval consists of 8 physical events.
- Some events are scored by "higher is better" values, such as pull-ups.
- Timed events are scored by "lower is better" values, such as run and swim.
- COMBAT soldiers can receive GOLD, SILVER, BRONZE, FIT, or UNFIT.
- ENABLER, OPS_SP, and TER_SP soldiers are evaluated against pass/fail
  threshold rows based on age and, where applicable, gender.
- NON_DEP soldiers do not have a separate official scale, so the calculator
  uses the COMBAT-equivalent result to keep the verdict consistent.
- The tests also ensure that the system never displays an impossible state,
  such as Overall=UNFIT while Result=Passed.
"""

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
    """Build an MfftEvalTest from an 8-tuple of raw event values.

    This helper avoids repeating the same object setup in every test.

    The tuple must contain exactly 8 values, in the same order as the official
    MFFT Eval events:
    1. Pull-ups
    2. Burpees step-over
    3. Farmer walk distance in meters
    4. Push-ups with release
    5. Casualty drag distance in meters
    6. Sandbag carry distance in meters
    7. Combat run time in seconds
    8. Combat swim time in seconds

    Manager explanation:
    The production calculator works with an MfftEvalTest object. These unit
    tests do not need to save anything to the database, so this helper creates
    an in-memory test object with the required event values filled in.
    """
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


# Official COMBAT threshold rows reused throughout the tests.
#
# Manager explanation:
# Instead of hard-coding all thresholds in every test, these constants reuse the
# same official threshold table used by the calculator. This keeps the tests
# readable and clearly communicates which level each row represents.
GOLD_ROW = COMBAT_THRESHOLDS[MfftLevel.GOLD]
SILVER_ROW = COMBAT_THRESHOLDS[MfftLevel.SILVER]
BRONZE_ROW = COMBAT_THRESHOLDS[MfftLevel.BRONZE]
FIT_ROW = COMBAT_THRESHOLDS[MfftLevel.FIT]


class TestEventTierCombat(unittest.TestCase):
    """Per-event COMBAT tier classification.

    This test class verifies that a single event value is translated into the
    correct COMBAT tier.

    Manager explanation:
    Before checking the full final score, we first prove that each individual
    event can be classified correctly. For example, 8 pull-ups should be GOLD,
    while 1 pull-up should be UNFIT.
    """

    def test_pull_up_gold(self):
        """Verify that 8 pull-ups are classified as GOLD.

        Manager explanation:
        This confirms that a top-level pull-up performance receives the highest
        possible event tier.
        """
        self.assertEqual(MfftLevel.GOLD, MfftEvalCalculator.event_tier_combat(0, 8))

    def test_pull_up_silver(self):
        """Verify that 6 pull-ups are classified as SILVER.

        Manager explanation:
        This checks that the calculator correctly recognizes the second-highest
        pull-up performance level.
        """
        self.assertEqual(MfftLevel.SILVER, MfftEvalCalculator.event_tier_combat(0, 6))

    def test_pull_up_bronze(self):
        """Verify that 4 pull-ups are classified as BRONZE.

        Manager explanation:
        This confirms that a middle-tier pull-up result is graded correctly.
        """
        self.assertEqual(MfftLevel.BRONZE, MfftEvalCalculator.event_tier_combat(0, 4))

    def test_pull_up_fit(self):
        """Verify that 2 pull-ups are classified as FIT.

        Manager explanation:
        FIT is the minimum acceptable tier before a soldier becomes UNFIT for
        that event. This test proves the calculator accepts the minimum passing
        value.
        """
        self.assertEqual(MfftLevel.FIT, MfftEvalCalculator.event_tier_combat(0, 2))

    def test_pull_up_unfit(self):
        """Verify that 1 pull-up is classified as UNFIT.

        Manager explanation:
        This confirms that a result below the minimum acceptable pull-up
        standard fails the event.
        """
        self.assertEqual(MfftLevel.UNFIT, MfftEvalCalculator.event_tier_combat(0, 1))

    def test_combat_run_gold(self):
        """Verify that a 30-minute combat run is classified as GOLD.

        Manager explanation:
        Timed events work differently from repetition or distance events.
        For running and swimming, a lower time is better. This test confirms
        that a fast enough run receives the highest tier.
        """
        # Lower time is better; <= 30 minutes = GOLD.
        self.assertEqual(MfftLevel.GOLD, MfftEvalCalculator.event_tier_combat(6, 30 * 60))

    def test_combat_run_silver(self):
        """Verify that a 34-minute combat run is classified as SILVER.

        Manager explanation:
        This checks that the calculator correctly handles a timed event at the
        SILVER threshold.
        """
        self.assertEqual(MfftLevel.SILVER, MfftEvalCalculator.event_tier_combat(6, 34 * 60))

    def test_combat_run_unfit(self):
        """Verify that a 50-minute combat run is classified as UNFIT.

        Manager explanation:
        This proves that the calculator fails a run time that is slower than
        the minimum allowed FIT threshold.
        """
        # Slower than the FIT threshold (44 min) -> UNFIT.
        self.assertEqual(MfftLevel.UNFIT, MfftEvalCalculator.event_tier_combat(6, 50 * 60))

    def test_combat_swim_fit(self):
        """Verify that a 6-minute combat swim is classified as FIT.

        Manager explanation:
        This confirms that the swim event is handled as a timed event and that
        the minimum accepted swim threshold is recognized.
        """
        self.assertEqual(MfftLevel.FIT, MfftEvalCalculator.event_tier_combat(7, 6 * 60))

    def test_invalid_event_idx_raises(self):
        """Verify that an invalid event index raises a ValueError.

        Manager explanation:
        The MFFT Eval has exactly 8 events, indexed from 0 to 7. Index 8 does
        not exist. This test ensures the calculator rejects invalid input
        instead of producing an unreliable result.
        """
        with self.assertRaises(ValueError):
            MfftEvalCalculator.event_tier_combat(8, 0)


class TestCombatClusterEvaluation(unittest.TestCase):
    """COMBAT cluster validates a tier when >= 6 of 8 events hit that tier.

    Manager explanation:
    COMBAT has the most detailed scoring model. A soldier can receive GOLD,
    SILVER, BRONZE, FIT, or UNFIT. To validate a tier, at least 6 of the
    8 events must meet that tier. However, if any event is UNFIT, the whole
    result becomes UNFIT.
    """

    def test_all_gold_overall_gold(self):
        """Verify that all GOLD event values produce an overall GOLD result.

        Manager explanation:
        This is the ideal case. Every event meets the GOLD threshold, so the
        final result must be GOLD and the soldier must pass.
        """
        test = _make_test(GOLD_ROW)
        res = MfftEvalCalculator.evaluate(test, Cluster.COMBAT, age=25, gender=Gender.M)
        self.assertEqual(MfftLevel.GOLD, res.overall)
        self.assertTrue(res.passed)

    def test_six_gold_two_silver_is_gold(self):
        """Verify that 6 GOLD events and 2 SILVER events still produce GOLD.

        Manager explanation:
        COMBAT scoring allows a tier when at least 6 of 8 events reach that
        tier. This test confirms that two slightly lower events do not prevent
        a GOLD result when six events are still GOLD.
        """
        values = list(GOLD_ROW)
        # Demote 2 higher-is-better events down to SILVER thresholds.
        values[0] = SILVER_ROW[0]
        values[1] = SILVER_ROW[1]
        res = MfftEvalCalculator.evaluate(
            _make_test(tuple(values)), Cluster.COMBAT, age=25, gender=Gender.M
        )
        self.assertEqual(MfftLevel.GOLD, res.overall)

    def test_five_gold_three_silver_is_silver(self):
        """Verify that only 5 GOLD events are not enough for overall GOLD.

        Manager explanation:
        This protects against over-promoting a soldier. Since only 5 events are
        GOLD, the 6-event rule is not satisfied. The correct result becomes
        SILVER.
        """
        values = list(GOLD_ROW)
        values[0] = SILVER_ROW[0]
        values[1] = SILVER_ROW[1]
        values[2] = SILVER_ROW[2]
        res = MfftEvalCalculator.evaluate(
            _make_test(tuple(values)), Cluster.COMBAT, age=25, gender=Gender.M
        )
        self.assertEqual(MfftLevel.SILVER, res.overall)

    def test_any_unfit_event_fails_combat(self):
        """Verify that any UNFIT event makes a COMBAT result fail.

        Manager explanation:
        Even if the other events are excellent, one event below the minimum
        acceptable FIT standard means the soldier is not considered passed for
        COMBAT.
        """
        values = list(GOLD_ROW)
        values[0] = 0  # pull-ups below FIT threshold
        res = MfftEvalCalculator.evaluate(
            _make_test(tuple(values)), Cluster.COMBAT, age=25, gender=Gender.M
        )
        self.assertEqual(MfftLevel.UNFIT, res.overall)
        self.assertFalse(res.passed)

    def test_all_fit_no_unfit_is_fit(self):
        """Verify that all minimum FIT values produce an overall FIT result.

        Manager explanation:
        This confirms that a soldier who meets the minimum standard in every
        event is accepted as passed and receives the FIT level.
        """
        res = MfftEvalCalculator.evaluate(
            _make_test(FIT_ROW), Cluster.COMBAT, age=25, gender=Gender.M
        )
        self.assertEqual(MfftLevel.FIT, res.overall)
        self.assertTrue(res.passed)


class TestEnablerClusterEvaluation(unittest.TestCase):
    """ENABLER uses a single age-bracketed pass threshold, gender neutral.

    Manager explanation:
    ENABLER scoring is simpler than COMBAT scoring. It uses one pass/fail row
    based on age. Gender does not change the threshold. The soldier must meet
    every event threshold to pass.
    """

    def test_under_30_meets_threshold(self):
        """Verify that an ENABLER soldier under 30 passes at the correct row.

        Manager explanation:
        This checks that younger ENABLER soldiers are evaluated against the
        correct under-30 threshold and receive FIT when all events pass.
        """
        # ENABLER <30 row == COMBAT SILVER row.
        res = MfftEvalCalculator.evaluate(
            _make_test(SILVER_ROW), Cluster.ENABLER, age=29, gender=Gender.M
        )
        self.assertTrue(res.passed)
        self.assertEqual(MfftLevel.FIT, res.overall)

    def test_age_30_bumps_to_next_bracket(self):
        """Verify that age 30 uses the next ENABLER age bracket.

        Manager explanation:
        Age boundaries are common sources of mistakes. This test confirms that
        age 30 is no longer treated as under 30 and uses the next threshold row.
        """
        # At age 30 the threshold drops to the BRONZE row - passing values
        # at SILVER row trivially pass.
        res = MfftEvalCalculator.evaluate(
            _make_test(BRONZE_ROW), Cluster.ENABLER, age=30, gender=Gender.F
        )
        self.assertTrue(res.passed)

    def test_age_50_uses_50_plus_bracket(self):
        """Verify that soldiers aged 50 or older use the 50+ ENABLER bracket.

        Manager explanation:
        This confirms the oldest age bracket is selected correctly. It also
        confirms that a value below that bracket's minimum threshold still
        causes a failure.
        """
        # 50+ ENABLER row: pull-up threshold is 1; 0 should fail.
        values = list(BRONZE_ROW)
        values[0] = 0
        res = MfftEvalCalculator.evaluate(
            _make_test(tuple(values)), Cluster.ENABLER, age=55, gender=Gender.M
        )
        self.assertFalse(res.passed)
        self.assertEqual(MfftLevel.UNFIT, res.overall)

    def test_one_event_below_threshold_fails(self):
        """Verify that one failed ENABLER event fails the whole test.

        Manager explanation:
        ENABLER scoring requires every event to meet the threshold. This test
        makes the run too slow to confirm that one failed event is enough to
        fail the final result.
        """
        values = list(SILVER_ROW)
        values[6] = 60 * 60  # combat run too slow
        res = MfftEvalCalculator.evaluate(
            _make_test(tuple(values)), Cluster.ENABLER, age=25, gender=Gender.M
        )
        self.assertFalse(res.passed)


class TestOpsSpClusterEvaluation(unittest.TestCase):
    """OPS_SP uses an age and sex bracketed single pass threshold.

    Manager explanation:
    OPS_SP scoring depends on both the soldier's age and gender. The soldier
    passes only if every event meets the selected threshold row.
    """

    def test_men_under_30_passes_bronze_row(self):
        """Verify that an OPS_SP man under 30 passes at the expected threshold.

        Manager explanation:
        This confirms that the calculator selects the correct young male OPS_SP
        threshold row and marks the result as passed.
        """
        # OPS_SP men <30 row == COMBAT BRONZE row.
        res = MfftEvalCalculator.evaluate(
            _make_test(BRONZE_ROW), Cluster.OPS_SP, age=25, gender=Gender.M
        )
        self.assertTrue(res.passed)

    def test_women_30_to_39_passes(self):
        """Verify that an OPS_SP woman aged 30-39 passes on the exact threshold.

        Manager explanation:
        This confirms the correct age/gender row is selected. It also proves
        that values exactly equal to the required threshold count as passing.
        """
        # OPS_SP women 30-39 row: 2/6/30/14/15/30/49:00/7:00 — exact row passes.
        row = (2, 6, 30, 14, 15, 30, 49 * 60, 7 * 60)
        res = MfftEvalCalculator.evaluate(_make_test(row), Cluster.OPS_SP, age=35, gender=Gender.F)
        self.assertTrue(res.passed)

    def test_women_50_plus_fails_on_slow_swim(self):
        """Verify that an OPS_SP woman aged 50+ fails when the swim is too slow.

        Manager explanation:
        The swim threshold for this bracket is 8 minutes. This test uses
        9 minutes, proving that timed events are enforced correctly.
        """
        # OPS_SP women 50+ row swim threshold is 8:00; 9:00 fails.
        row = (1, 2, 10, 10, 5, 10, 59 * 60, 9 * 60)
        res = MfftEvalCalculator.evaluate(_make_test(row), Cluster.OPS_SP, age=55, gender=Gender.F)
        self.assertFalse(res.passed)


class TestTerSpClusterEvaluation(unittest.TestCase):
    """TER_SP shares the same scoring shape as OPS_SP.

    Manager explanation:
    TER_SP also uses age and gender specific threshold rows. The final result
    is pass/fail, and every event must meet the selected threshold.
    """

    def test_men_40_to_49_passes(self):
        """Verify that a TER_SP man aged 40-49 passes at the correct threshold.

        Manager explanation:
        This confirms that the calculator chooses the correct TER_SP male
        40-49 bracket and marks exact threshold values as passing.
        """
        row = (1, 4, 30, 14, 15, 30, 49 * 60, 7 * 60)
        res = MfftEvalCalculator.evaluate(_make_test(row), Cluster.TER_SP, age=45, gender=Gender.M)
        self.assertTrue(res.passed)

    def test_women_under_30_fails_when_short(self):
        """Verify that a TER_SP woman under 30 fails when one event is too low.

        Manager explanation:
        This test sets pull-ups below the required threshold. Even though the
        other values are acceptable, one failed event means the entire test
        fails.
        """
        row = (1, 6, 40, 16, 20, 40, 44 * 60, 6 * 60)  # pull-ups 1 < threshold 2
        res = MfftEvalCalculator.evaluate(_make_test(row), Cluster.TER_SP, age=25, gender=Gender.F)
        self.assertFalse(res.passed)


class TestNonDeployable(unittest.TestCase):
    """NON_DEP has no official scale, so COMBAT-equivalent verdict is used.

    Manager explanation:
    Since NON_DEP does not have its own official scoring table, the calculator
    uses the COMBAT-equivalent result. This keeps reporting consistent and
    prevents a soldier with an UNFIT event from being shown as passed.
    """

    def test_non_dep_passes_when_all_events_at_least_fit(self):
        """Verify that NON_DEP passes when all events meet a strong standard.

        Manager explanation:
        This test uses GOLD-level values. The soldier should pass, and both the
        overall result and displayed tier information should show GOLD.
        """
        res = MfftEvalCalculator.evaluate(
            _make_test(GOLD_ROW), Cluster.NON_DEP, age=40, gender=Gender.M
        )
        self.assertTrue(res.passed)
        self.assertEqual(MfftLevel.GOLD, res.overall)
        self.assertEqual(MfftLevel.GOLD, res.tier_info)

    def test_non_dep_fails_when_any_event_is_unfit(self):
        """Verify that NON_DEP fails when any event is below FIT.

        Manager explanation:
        This prevents unsafe or misleading reporting. A soldier with an UNFIT
        event must not be displayed as passed, even in the NON_DEP cluster.
        """
        values = list(GOLD_ROW)
        values[0] = 0  # pull-ups below FIT threshold -> UNFIT
        res = MfftEvalCalculator.evaluate(
            _make_test(tuple(values)), Cluster.NON_DEP, age=40, gender=Gender.M
        )
        self.assertFalse(res.passed)
        self.assertEqual(MfftLevel.UNFIT, res.overall)
        self.assertEqual(MfftLevel.UNFIT, res.tier_info)


class TestTierInfoForNonCombat(unittest.TestCase):
    """tier_info is the COMBAT-equivalent tier regardless of cluster.

    Manager explanation:
    Some clusters officially use only pass/fail scoring. However, the system
    still calculates a COMBAT-equivalent tier as additional information. This
    helps management understand the strength of the raw performance.
    """

    def test_enabler_gets_combat_tier_info(self):
        """Verify that ENABLER results still include COMBAT-equivalent tier info.

        Manager explanation:
        Even though ENABLER officially reports FIT or UNFIT, the system still
        stores the achieved tier information for transparency and reporting.
        """
        res = MfftEvalCalculator.evaluate(
            _make_test(GOLD_ROW), Cluster.ENABLER, age=25, gender=Gender.M
        )
        self.assertEqual(MfftLevel.GOLD, res.tier_info)


class TestPassedOverallInvariant(unittest.TestCase):
    """Verify the global consistency rule between passed and overall.

    Invariant:
    passed is True if and only if overall is not UNFIT.

    Manager explanation:
    The application must never show a confusing result such as:
    - Overall = UNFIT
    - Result = Passed

    This test class checks that the rule holds for every supported cluster.
    """

    # A deliberately failing set of values for all 8 events.
    #
    # Manager explanation:
    # Zero values fail repetition and distance events. The 99-minute run and
    # swim values are intentionally much too slow.
    UNFIT_VALUES = (0, 0, 0, 0, 0, 0, 99 * 60, 99 * 60)

    # Every cluster supported by the calculator.
    #
    # Manager explanation:
    # The consistency rule must work for every cluster, not just COMBAT.
    CLUSTERS = (Cluster.COMBAT, Cluster.ENABLER, Cluster.OPS_SP, Cluster.TER_SP, Cluster.NON_DEP)

    def test_gold_row_invariant_holds(self):
        """Verify that strong GOLD values obey the passed/overall invariant.

        Manager explanation:
        This loops through every cluster using strong performance values and
        confirms that the pass flag agrees with the overall result.
        """
        for cluster in self.CLUSTERS:
            with self.subTest(cluster=cluster):
                res = MfftEvalCalculator.evaluate(
                    _make_test(GOLD_ROW), cluster, age=25, gender=Gender.M
                )
                self.assertEqual(res.passed, res.overall is not MfftLevel.UNFIT)

    def test_unfit_row_invariant_holds(self):
        """Verify that clearly failing values fail in every cluster.

        Manager explanation:
        This proves no cluster accidentally passes a clearly unfit test result.
        It protects dashboard and reporting accuracy.
        """
        for cluster in self.CLUSTERS:
            with self.subTest(cluster=cluster):
                res = MfftEvalCalculator.evaluate(
                    _make_test(self.UNFIT_VALUES), cluster, age=25, gender=Gender.M
                )
                self.assertFalse(res.passed)
                self.assertEqual(MfftLevel.UNFIT, res.overall)


class TestGenderStringAccepted(unittest.TestCase):
    """The calculator accepts a Gender enum or its string literal.

    Manager explanation:
    Different parts of the application may provide gender as an enum value
    or as plain text from a form/API. This test confirms both styles are
    accepted by the calculator.
    """

    def test_gender_literal_string(self):
        """Verify that gender can be passed as the string 'M'.

        Manager explanation:
        This protects integration points where gender may arrive from the UI,
        database, or external payload as text instead of a Python enum.
        """
        res = MfftEvalCalculator.evaluate(_make_test(GOLD_ROW), Cluster.OPS_SP, 25, "M")
        self.assertTrue(res.passed)


if __name__ == "__main__":
    unittest.main()