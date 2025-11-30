# tests/test_phef_calculator.py

import unittest
import pytest
from warriorfit.core.Gender import Gender
from warriorfit.logic.phef_calculator import PhefCalculator


class TestPhefCalculator(unittest.TestCase):

    def test_side_bridge_result_male_under_30_high_score(self):
        result = PhefCalculator.side_bridge_result(125, 25, Gender.M)  # 125 seconds equivalent to 2:05
        self.assertEqual(20, result)

    def test_side_bridge_result_female_under_30_low_score(self):
        result = PhefCalculator.side_bridge_result(40, 25, Gender.F)  # 40 seconds equivalent
        self.assertEqual(1, result)

    def test_side_bridge_result_male_30_to_39_medium_score(self):
        result = PhefCalculator.side_bridge_result(85, 35, Gender.M)  # 85 seconds equivalent
        self.assertEqual(14, result)

    def test_side_bridge_result_female_40_to_49_high_score(self):
        result = PhefCalculator.side_bridge_result(100, 45, Gender.F)  # 100 seconds equivalent to 1:40
        self.assertEqual(20, result)

    def test_side_bridge_result_male_50_plus_zero_score(self):
        result = PhefCalculator.side_bridge_result(25, 55, Gender.M)  # Time lower than minimum threshold
        self.assertEqual(0, result)

    def test_side_bridge_result_none_time(self):
        result = PhefCalculator.side_bridge_result(None, 30, Gender.F)
        self.assertEqual(0, result)

    def test_side_bridge_result_boundary_case_age_30(self):
        result = PhefCalculator.side_bridge_result(80, 30, Gender.M)  # Boundary age 30 falls into 30-39
        self.assertEqual(13, result)

    def test_side_bridge_result_boundary_case_age_40(self):
        result = PhefCalculator.side_bridge_result(70, 40, Gender.F)  # Boundary age 40 falls into 40-49
        self.assertEqual(14, result)

    # New tests for running_result
    def test_running_result_male_under_30_high_score(self):
        result = PhefCalculator.running_result(570, 25, Gender.M)  # 570 seconds equivalent to 9:30
        self.assertEqual(20, result)

    def test_running_result_female_under_30_low_score(self):
        result = PhefCalculator.running_result(951, 28, Gender.F)  # 951 seconds equivalent to ~15:51
        self.assertEqual(1, result)

    def test_running_result_male_40_to_44_medium_score(self):
        result = PhefCalculator.running_result(645, 42, Gender.M)  # 645 seconds equivalent to ~10:45
        self.assertEqual(17, result)

    def test_running_result_female_55_to_59_high_score(self):
        result = PhefCalculator.running_result(960, 57, Gender.F)  # 960 seconds equivalent to ~16:00
        self.assertEqual(14, result)

    def test_running_result_boundary_age_30(self):
        result = PhefCalculator.running_result(605, 30, Gender.M)  # Boundary age 30 falls into 30-34
        self.assertEqual(18, result)

    def test_running_result_invalid_column(self):
        result = PhefCalculator.running_result(600, 20, "INVALID_GENDER")
        self.assertEqual(0, result)

    def test_side_bridge_result_male_under_30_high_score_time_str(self):
        result = PhefCalculator.side_bridge_result("02:05", 25, Gender.M)  # 125 seconds equivalent to 2:05
        self.assertEqual(20, result)

    def test_side_bridge_result_female_under_30_low_score_time_str(self):
        result = PhefCalculator.side_bridge_result("00:40", 25, Gender.F)  # 40 seconds equivalent
        self.assertEqual(1, result)

    def test_side_bridge_result_male_30_to_39_medium_score_time_str(self):
        result = PhefCalculator.side_bridge_result("01:25", 35, Gender.M)  # 85 seconds equivalent
        self.assertEqual(14, result)

    def test_side_bridge_result_female_40_to_49_high_score_time_str(self):
        result = PhefCalculator.side_bridge_result("01:40", 45, Gender.F)  # 100 seconds equivalent to 1:40
        self.assertEqual(20, result)

    def test_side_bridge_result_male_50_plus_zero_score_time_str(self):
        result = PhefCalculator.side_bridge_result("00:25", 55, Gender.M)  # Time lower than minimum threshold
        self.assertEqual(0, result)

    def test_side_bridge_result_none_time_time_str(self):
        result = PhefCalculator.side_bridge_result(None, 30, Gender.F)
        self.assertEqual(0, result)

    def test_side_bridge_result_boundary_case_age_30_time_str(self):
        result = PhefCalculator.side_bridge_result("01:20", 30, Gender.M)  # 80 seconds
        self.assertEqual(13, result)

    def test_side_bridge_result_boundary_case_age_40_time_str(self):
        result = PhefCalculator.side_bridge_result("01:10", 40, Gender.F)  # 70 seconds
        self.assertEqual(14, result)

        # New tests for running_result

    def test_running_result_male_under_30_high_score_time_str(self):
        result = PhefCalculator.running_result("09:30", 25, Gender.M)  # 570 seconds
        self.assertEqual(20, result)

    def test_running_result_female_under_30_low_score_time_str(self):
        result = PhefCalculator.running_result("15:51", 28, Gender.F)  # 951 seconds
        self.assertEqual(1, result)

    def test_running_result_male_40_to_44_medium_score_time_str(self):
        result = PhefCalculator.running_result("10:45", 42, Gender.M)  # 645 seconds
        self.assertEqual(17, result)

    def test_running_result_female_55_to_59_high_score_time_str(self):
        result = PhefCalculator.running_result("16:00", 57, Gender.F)  # 960 seconds
        self.assertEqual(14, result)

    def test_running_result_boundary_age_30_time_str(self):
        result = PhefCalculator.running_result("10:05", 30, Gender.M)  # 605 seconds
        self.assertEqual(18, result)

    def test_running_result_invalid_column_time_str(self):

         result = PhefCalculator.running_result("10:00", 20, "INVALID_GENDER")
         self.assertEqual(0, result)


@pytest.mark.parametrize(
    "age, seconds, gender, expected_score",
    [
        # Example from your message: below minimum threshold for <30 male -> 0
        (25, 55, Gender.M, 0),

        # Score 20 thresholds (from table) — exact times converted to seconds
        # <30 man 2'05" = 125s -> score 20
        (25, 125, Gender.M, 20),
        # <30 woman 1'50" = 110s -> score 20
        (25, 110, Gender.F, 20),
        # 30-39 man 1'55" = 115s -> score 20
        (35, 115, Gender.M, 20),
        # 30-39 woman 1'45" = 105s -> score 20
        (35, 105, Gender.F, 20),
        # 40-49 man 1'50" = 110s -> score 20
        (45, 110, Gender.M, 20),
        # 50+ woman 1'35" = 95s -> score 20
        (55, 95, Gender.F, 20),

        # Score 10 examples (mid-table) — exact times to seconds
        # <30 man 1'15" = 75s -> score 10
        (28, 75, Gender.M, 10),
        # <30 woman 60" = 60s -> score 10
        (28, 60, Gender.F, 10),
        # 30-39 man 1'05" = 65s -> score 10
        (31, 65, Gender.M, 10),
        # 50+ woman 45" = 45s -> score 10
        (52, 45, Gender.F, 10),

        # Boundary checks: exactly at score-1 threshold should return 1 (if table says so)
        # From table: <30 man score 1 threshold = 60s -> score 1
        (29, 60, Gender.M, 1),
        # <30 woman score 1 threshold = 40s -> score 1
        (29, 40, Gender.F, 1),

        # Slightly below those thresholds -> 0
        (29, 59, Gender.M, 0),
        (29, 39, Gender.F, 0),
        # Example from your message: below minimum threshold for <30 male -> 0
        (25, "00:55", Gender.M, 0),

        # Score 20 thresholds (from table) — exact times as "MM:SS"
        # <30 man 2'05" -> score 20
        (25, "02:05", Gender.M, 20),
        # <30 woman 1'50" -> score 20
        (25, "01:50", Gender.F, 20),
        # 30-39 man 1'55" -> score 20
        (35, "01:55", Gender.M, 20),
        # 30-39 woman 1'45" -> score 20
        (35, "01:45", Gender.F, 20),
        # 40-49 man 1'50" -> score 20
        (45, "01:50", Gender.M, 20),
        # 50+ woman 1'35" -> score 20
        (55, "01:35", Gender.F, 20),

        # Score 10 examples (mid-table)
        # <30 man 1'15" -> score 10
        (28, "01:15", Gender.M, 10),
        # <30 woman 60" -> score 10
        (28, "01:00", Gender.F, 10),
        # 30-39 man 1'05" -> score 10
        (31, "01:05", Gender.M, 10),
        # 50+ woman 45" -> score 10
        (52, "00:45", Gender.F, 10),

        # Boundary checks: exactly at score-1 threshold should return 1 (if table says so)
        # From table: <30 man score 1 threshold = 60s -> score 1
        (29, "01:00", Gender.M, 1),
        # <30 woman score 1 threshold = 40s -> score 1
        (29, "00:40", Gender.F, 1),

        # Slightly below those thresholds -> 0
        (29, "00:59", Gender.M, 0),
        (29, "00:39", Gender.F, 0),
    ],
)
def test_side_bridge_result_various(age, seconds, gender, expected_score):
    """Parametrized test cases from the side-bridge scoring table."""
    result = PhefCalculator.side_bridge_result( seconds, age, gender)
    assert result == expected_score


if __name__ == "__main__":
    unittest.main()
