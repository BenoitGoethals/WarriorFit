# tests/test_Functional_calculator.py
import unittest

import pytest
from core.Gender import Gender
from logic.Functional_calculator import FunctionalCalculator


class TestFunctionalCalculator(unittest.TestCase):


    def test_get_score_pullup(self):
        result = FunctionalCalculator.get_score_pullup(Gender.MALE, 25, 10)
        assert result == 20.0, f"Expected 20.0, got {result}"


    def test_get_score_pullup_min_age(self):
        with pytest.raises(ValueError, match="Age must be >= 18"):
            FunctionalCalculator.get_score_pullup(Gender.FEMALE, 17, 5)


    def test_get_score_pullup_max_age(self):
        with pytest.raises(ValueError, match="Age must be <= 56"):
            FunctionalCalculator.get_score_pullup(Gender.FEMALE, 57, 5)


    def test_get_score_pullup_min_reps(self):
        result = FunctionalCalculator.get_score_pullup(Gender.MALE, 25, -1)
        assert result == 1.0, f"Expected 1.0, got {result}"


    def test_get_score_situp(self):
        result = FunctionalCalculator.get_score_situp(Gender.FEMALE, 30, 80)
        assert result == 20.0, f"Expected 20.0, got {result}"


    def test_get_score_pushup(self):
        result = FunctionalCalculator.get_score_pushup(Gender.MALE, 40, 90)
        assert result == 20.0, f"Expected 20.0, got {result}"


    def test_get_scores(self):
        calc = FunctionalCalculator()
        result = calc.get_scores(35, Gender.MALE, 10, 100, 100)
        expected = {
            "pullups": 20.0,
            "situps": 20.0,
            "pushups": 20.0,
            "total": 60.0,
            "average": 20.0,
            "_meta": {"age_group": "26-35", "exponent": calc.exponent, "gender": Gender.MALE},
        }
        assert result == expected, f"Expected {expected}, got {result}"


    def test_reps_for_score_nonlinear(self):
        calc = FunctionalCalculator(2.0)
        result = calc.reps_for_score_nonlinear(10, "18-25", Gender.FEMALE, "situps")
        assert result > 0, f"Expected a positive number, got {result}"


def test_make_tables():
    calc = FunctionalCalculator()
    tables = calc.make_tables()
    assert "pullups" in tables
    assert "situps" in tables
    assert "pushups" in tables
    assert not tables["pullups"].empty


def test_invalid_age_group_from_age():
    with pytest.raises(ValueError, match="Age must be >= 18"):
        FunctionalCalculator._age_group_from_age(17)


def test_invalid_age_group_above_max_age():
    with pytest.raises(ValueError, match="Age must be <= 56"):
        FunctionalCalculator._age_group_from_age(60)
