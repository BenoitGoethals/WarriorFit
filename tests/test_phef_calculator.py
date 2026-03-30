# tests/test_phef_calculator.py

import unittest

from warriorfit.core.Gender import Gender
from warriorfit.logic.phef_calculator import PhefCalculator


class TestPhefCalculator(unittest.TestCase):
    """
    Unit tests for the PhefCalculator class, which calculates scores for various
    physical fitness exercises based on time, age, and gender.
    """

    def test_side_bridge_result_male_under_30_high_score(self):
        """
        Test the side_bridge_result method for a male under 30 years old
        achieving a high score.
        """
        result = PhefCalculator.side_bridge_result(
            125, 25, Gender.M
        )  # 125 seconds equivalent to 2:05
        self.assertEqual(20, result)

    def test_side_bridge_result_female_under_30_low_score(self):
        """
        Test the side_bridge_result method for a female under 30 years old
        achieving a low score.
        """
        result = PhefCalculator.side_bridge_result(40, 25, Gender.F)  # 40 seconds equivalent
        self.assertEqual(1, result)

    def test_side_bridge_result_male_30_to_39_medium_score(self):
        """
        Test the side_bridge_result method for a male aged 30-39 achieving
        a medium score.
        """
        result = PhefCalculator.side_bridge_result(
            85, 35, Gender.M.to_literal()
        )  # 85 seconds equivalent
        self.assertEqual(14, result)

    def test_side_bridge_result_female_40_to_49_high_score(self):
        """
        Test the side_bridge_result method for a female aged 40-49 achieving
        a high score.
        """
        result = PhefCalculator.side_bridge_result(
            100, 45, Gender.F.to_literal()
        )  # 100 seconds equivalent to 1:40
        self.assertEqual(20, result)

    def test_side_bridge_result_male_50_plus_zero_score(self):
        """
        Test the side_bridge_result method for a male aged 50+ achieving
        a zero score due to insufficient time.
        """
        result = PhefCalculator.side_bridge_result(
            25, 55, Gender.M.to_literal()
        )  # Time lower than minimum threshold
        self.assertEqual(0, result)

    def test_side_bridge_result_none_time(self):
        """
        Test the side_bridge_result method when the time is None.
        """
        result = PhefCalculator.side_bridge_result(None, 30, Gender.F.to_literal())
        self.assertEqual(0, result)

    def test_side_bridge_result_boundary_case_age_30(self):
        """
        Test the side_bridge_result method for a boundary case where age is 30,
        which falls into the 30-39 age category.
        """
        result = PhefCalculator.side_bridge_result(
            80, 30, Gender.M.to_literal()
        )  # Boundary age 30 falls into 30-39
        self.assertEqual(13, result)

    def test_side_bridge_result_boundary_case_age_40(self):
        """
        Test the side_bridge_result method for a boundary case where age is 40,
        which falls into the 40-49 age category.
        """
        result = PhefCalculator.side_bridge_result(
            70, 40, Gender.F.to_literal()
        )  # Boundary age 40 falls into 40-49
        self.assertEqual(14, result)

    # New tests for running_result
    def test_running_result_male_under_30_high_score(self):
        """
        Test the running_result method for a male under 30 years old
        achieving a high score.
        """
        result = PhefCalculator.running_result(
            570, 25, Gender.M.to_literal()
        )  # 570 seconds equivalent to 9:30
        self.assertEqual(20, result)

    def test_running_result_female_under_30_low_score(self):
        """
        Test the running_result method for a female under 30 years old
        achieving a low score.
        """
        result = PhefCalculator.running_result(
            951, 28, Gender.F.to_literal()
        )  # 951 seconds equivalent to ~15:51
        self.assertEqual(1, result)

    def test_running_result_male_40_to_44_medium_score(self):
        """
        Test the running_result method for a male aged 40-44 achieving
        a medium score.
        """
        result = PhefCalculator.running_result(
            645, 42, Gender.M.to_literal()
        )  # 645 seconds equivalent to ~10:45
        self.assertEqual(17, result)

    def test_running_result_female_55_to_59_high_score(self):
        """
        Test the running_result method for a female aged 55-59 achieving
        a high score.
        """
        result = PhefCalculator.running_result(
            960, 57, Gender.F.to_literal()
        )  # 960 seconds equivalent to ~16:00
        self.assertEqual(14, result)

    def test_running_result_boundary_age_30(self):
        """
        Test the running_result method for a boundary case where age is 30,
        which falls into the 30-34 age category.
        """
        result = PhefCalculator.running_result(
            605, 30, Gender.M.to_literal()
        )  # Boundary age 30 falls into 30-34
        self.assertEqual(18, result)

    def test_running_result_invalid_column(self):
        """
        Test the running_result method with an invalid gender value.
        """
        result = PhefCalculator.running_result(600, 20, "INVALID_GENDER")
        self.assertEqual(0, result)
