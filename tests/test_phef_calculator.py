# tests/test_phef_calculator.py

import unittest

from core.Gender import Gender
from logic.phef_calculator import PhefCalculator


class TestPhefCalculator(unittest.TestCase):

    def test_side_bridge_result_male_under_30_high_score(self):
        result = PhefCalculator.side_bridge_result(125, 25, Gender.MALE)  # 125 seconds equivalent to 2:05
        self.assertEqual(20, result)

    def test_side_bridge_result_female_under_30_low_score(self):
        result = PhefCalculator.side_bridge_result(40, 25, Gender.FEMALE)  # 40 seconds equivalent
        self.assertEqual(0, result)

    def test_side_bridge_result_male_30_to_39_medium_score(self):
        result = PhefCalculator.side_bridge_result(85, 35, Gender.MALE)  # 85 seconds equivalent
        self.assertEqual(5, result)

    def test_side_bridge_result_female_40_to_49_high_score(self):
        result = PhefCalculator.side_bridge_result(100, 45, Gender.FEMALE)  # 100 seconds equivalent to 1:40
        self.assertEqual(19, result)

    def test_side_bridge_result_male_50_plus_zero_score(self):
        result = PhefCalculator.side_bridge_result(25, 55, Gender.MALE)  # Time lower than minimum threshold
        self.assertEqual(0, result)

    def test_side_bridge_result_none_time(self):
        result = PhefCalculator.side_bridge_result(None, 30, Gender.FEMALE)
        self.assertEqual(0, result)

    def test_side_bridge_result_boundary_case_age_30(self):
        result = PhefCalculator.side_bridge_result(80, 30, Gender.MALE)  # Boundary age 30 falls into 30-39
        self.assertEqual(7, result)

    def test_side_bridge_result_boundary_case_age_40(self):
        result = PhefCalculator.side_bridge_result(70, 40, Gender.FEMALE)  # Boundary age 40 falls into 40-49
        self.assertEqual(5, result)

    # New tests for running_result
    def test_running_result_male_under_30_high_score(self):
        result = PhefCalculator.running_result(570, 25, Gender.MALE)  # 570 seconds equivalent to 9:30
        self.assertEqual(20, result)

    def test_running_result_female_under_30_low_score(self):
        result = PhefCalculator.running_result(951, 28, Gender.FEMALE)  # 951 seconds equivalent to ~15:51
        self.assertEqual(0, result)

    def test_running_result_male_40_to_44_medium_score(self):
        result = PhefCalculator.running_result(645, 42, Gender.MALE)  # 645 seconds equivalent to ~10:45
        self.assertEqual(16, result)

    def test_running_result_female_55_to_59_high_score(self):
        result = PhefCalculator.running_result(960, 57, Gender.FEMALE)  # 960 seconds equivalent to ~16:00
        self.assertEqual(18, result)

    def test_running_result_boundary_age_30(self):
        result = PhefCalculator.running_result(605, 30, Gender.MALE)  # Boundary age 30 falls into 30-34
        self.assertEqual(20, result)

    def test_running_result_invalid_column(self):
        with self.assertRaises(ValueError):
            PhefCalculator.running_result(600, 20, "INVALID_GENDER")


if __name__ == "__main__":
    unittest.main()
