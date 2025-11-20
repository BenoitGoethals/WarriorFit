# tests/test_Functional_calculator.py

import pytest
from core.Gender import Gender
from logic.Functional_calculator import FunctionalCalculator


@pytest.mark.parametrize(
    "age,expected_category",
    [
        (18, "18-27"),
        (25, "18-27"),
        (28, "28-37"),
        (37, "28-37"),
        (38, "38-47"),
        (47, "38-47"),
        (48, "48-56"),
        (55, "48-56"),
        (60, "48-56"),
        (17, "18-27"),
    ],
)
def test_get_age_cat(age, expected_category):
    assert FunctionalCalculator.get_age_cat(age) == expected_category


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
    assert FunctionalCalculator.get_score_pullup(gender, age, count) == expected_score


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
    assert FunctionalCalculator.get_score_pushup(gender, age, count) == expected_score


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
    assert FunctionalCalculator.get_score_situp(gender, age, count) == expected_score


@pytest.mark.parametrize(
    "gender,age,count,expected_pullup_score,expected_situp_score,expected_pushup_score",
    [
        (Gender.M, 25, 20, 20.0, 4.0, 6.0),  # Max scores for all exercises
        (Gender.F, 25, 12, 20.0, 4.0, 6.0),  # Max scores for women
        (Gender.M, 30, 50, 20.0, 16.0, 16.0),  # Exceeding max reps still yields max score
        (Gender.F, 48, 5, 18.0, 4.0, 6.0),  # Exact scores for low reps
        (Gender.M, 25, 0, 0.0, 0.0, 0.0),  # No reps for any exercise
        (Gender.F, 25, -1, 0.0, 0.0, 0.0),  # Invalid negative reps
    ],
)
def test_get_scores(gender, age, count, expected_pullup_score, expected_situp_score, expected_pushup_score):
    scores = FunctionalCalculator.get_scores(gender, age, count)
    assert scores == (expected_pullup_score, expected_situp_score, expected_pushup_score)
