# tests/test_Functional_calculator.py

import pytest

from warriorfit.core.Gender import Gender
from warriorfit.logic.Functional_calculator import FunctionalCalculator


# Test for the `get_age_cat` method of FunctionalCalculator
@pytest.mark.parametrize(
    "age,expected_category",
    [
        (18, "18-27"),  # Age 18 falls in the "18-27" category
        (25, "18-27"),  # Age 25 falls in the "18-27" category
        (28, "28-37"),  # Age 28 falls in the "28-37" category
        (37, "28-37"),  # Age 37 falls in the "28-37" category
        (38, "38-47"),  # Age 38 falls in the "38-47" category
        (47, "38-47"),  # Age 47 falls in the "38-47" category
        (48, "48-56"),  # Age 48 falls in the "48-56" category
        (55, "48-56"),  # Age 55 falls in the "48-56" category
        (60, "48-56"),  # Age 60 falls in the "48-56" category
        (17, "18-27"),  # Edge case: Age 17 defaults to "18-27"
    ],
)
def test_get_age_cat(age, expected_category):
    """
    Test the `get_age_cat` method to ensure it correctly categorizes ages.
    """
    assert FunctionalCalculator.get_age_cat(age) == expected_category


# Test for the `get_score_pullup` method of FunctionalCalculator
@pytest.mark.parametrize(
    "gender,age,count,expected_score",
    [
        (Gender.M, 25, 20, 20.0),  # Max score for men (pull-ups)
        (Gender.F, 25, 12, 20.0),  # Max score for women (pull-ups)
        (Gender.M, 30, 15, 16.0),  # Max reps across age/gender for men
        (Gender.F, 30, 10, 20.0),  # Max reps across age/gender for women
        (Gender.M, 25, 9, 8.0),  # Men pull-ups: score for 9 reps
        (Gender.F, 48, 5, 18.0),  # Women pull-ups: score for 5 reps
        (Gender.M, 25, 0, 0.0),  # Edge: No reps
        (Gender.F, 25, -5, 0.0),  # Invalid: Negative reps
    ],
)
def test_get_score_pullup(gender, age, count, expected_score):
    """
    Test the `get_score_pullup` method to ensure it calculates pull-up scores
    based on gender, age, and count.
    """
    assert FunctionalCalculator.get_score_pullup(gender, age, count) == expected_score


# Test for the `get_score_pushup` method of FunctionalCalculator
@pytest.mark.parametrize(
    "gender,age,count,expected_score",
    [
        (Gender.M, 25, 75, 20.0),  # Max score for men (push-ups)
        (Gender.F, 25, 50, 20.0),  # Max score for women (push-ups)
        (Gender.M, 30, 38, 14.0),  # Exact middle score for men
        (Gender.F, 30, 6, 4.0),  # Women push-ups: low score reps
        (Gender.M, 38, 55, 20.0),  # Max reps across age for men
        (Gender.F, 48, 17, 16.0),  # Women push-ups: score for 17 reps
        (Gender.M, 25, 0, 0.0),  # Edge: No reps
        (Gender.F, 25, -1, 0.0),  # Invalid: Negative reps
    ],
)
def test_get_score_pushup(gender, age, count, expected_score):
    """
    Test the `get_score_pushup` method to ensure it calculates push-up scores
    based on gender, age, and count.
    """
    assert FunctionalCalculator.get_score_pushup(gender, age, count) == expected_score


# Test for the `get_score_situp` method of FunctionalCalculator
@pytest.mark.parametrize(
    "gender,age,count,expected_score",
    [
        (Gender.M, 25, 80, 20.0),  # Max score for men (sit-ups)
        (Gender.F, 25, 70, 20.0),  # Max score for women (sit-ups)
        (Gender.M, 30, 42, 14.0),  # Men sit-ups: exact middle reps
        (Gender.F, 30, 10, 4.0),  # Women sit-ups: low reps
        (Gender.M, 48, 50, 20.0),  # Max reps across age for men
        (Gender.F, 48, 40, 20.0),  # Women sit-ups: score for 40 reps
        (Gender.M, 48, 0, 0.0),  # Edge: No reps
        (Gender.F, 48, -5, 0.0),  # Invalid: Negative reps
    ],
)
def test_get_score_situp(gender, age, count, expected_score):
    """
    Test the `get_score_situp` method to ensure it calculates sit-up scores
    based on gender, age, and count.
    """
    assert FunctionalCalculator.get_score_situp(gender, age, count) == expected_score


# Test for the `get_scores` method of FunctionalCalculator
@pytest.mark.parametrize(
    "gender,age,count,expected_pullup_score,expected_situp_score,expected_pushup_score",
    [
        (Gender.M, 25, 20, 20.0, 4.0, 6.0),  # Max scores for all exercises
        (Gender.F, 25, 12, 20.0, 4.0, 6.0),  # Max scores for women
        (
            Gender.M,
            30,
            50,
            20.0,
            16.0,
            16.0,
        ),  # Exceeding max reps still yields max score
        (Gender.F, 48, 5, 18.0, 4.0, 6.0),  # Exact scores for low reps
        (Gender.M, 25, 0, 0.0, 0.0, 0.0),  # No reps for any exercise
        (Gender.F, 25, -1, 0.0, 0.0, 0.0),  # Invalid negative reps
    ],
)
def test_get_scores(
    gender,
    age,
    count,
    expected_pullup_score,
    expected_situp_score,
    expected_pushup_score,
):
    """
    Test the `get_scores` method to ensure it calculates scores for pull-ups,
    sit-ups, and push-ups based on gender, age, and count.
    """
    scores = FunctionalCalculator.get_scores(gender, age, count)
    assert scores == (
        expected_pullup_score,
        expected_situp_score,
        expected_pushup_score,
    )
