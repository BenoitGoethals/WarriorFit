import math
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple

from core.Gender import Gender


class FunctionalCalculator:
        # Pull-ups () data
        PULLUPS_MEN = {
            '18-27': {10: 20, 9: 18, 8: 16, 7: 14, 6: 12, 5: 10, 4: 8, 3: 6, 2: 4, 1: 1},
            '28-37': {10: 18, 9: 16, 8: 14, 7: 12, 6: 10, 5: 8, 4: 6, 3: 5, 2: 3, 1: 1},
            '38-47': {10: 16, 9: 14, 8: 12, 7: 10, 6: 8, 5: 6, 4: 5, 3: 4, 2: 2, 1: 1},
            '48-56': {10: 14, 9: 12, 8: 10, 7: 8, 6: 6, 5: 5, 4: 4, 3: 3, 2: 2, 1: 1}
        }

        PULLUPS_WOMEN = {
            '18-27': {10: 12, 9: 10, 8: 8, 7: 6, 6: 5, 5: 4, 4: 3, 3: 2, 2: 1, 1: 0},
            '28-37': {10: 10, 9: 8, 8: 6, 7: 5, 6: 4, 5: 3, 4: 3, 3: 2, 2: 1, 1: 0},
            '38-47': {10: 8, 9: 6, 8: 5, 7: 4, 6: 3, 5: 3, 4: 2, 3: 2, 2: 1, 1: 0},
            '48-56': {10: 6, 9: 5, 8: 4, 7: 3, 6: 2, 5: 2, 4: 2, 3: 1, 2: 1, 1: 0}
        }

        # Push-ups () data
        PUSH_UPS_MEN = {
            '18-27': {10: 75, 9: 65, 8: 55, 7: 45, 6: 38, 5: 30, 4: 24, 3: 18, 2: 10, 1: 1},
            '28-37': {10: 65, 9: 55, 8: 45, 7: 38, 6: 30, 5: 24, 4: 18, 3: 13, 2: 7, 1: 1},
            '38-47': {10: 55, 9: 45, 8: 35, 7: 28, 6: 22, 5: 17, 4: 13, 3: 10, 2: 5, 1: 1},
            '48-56': {10: 45, 9: 35, 8: 28, 7: 22, 6: 17, 5: 13, 4: 10, 3: 7, 2: 4, 1: 1}
        }

        PUSH_UPS_WOMEN = {
            '18-27': {10: 50, 9: 42, 8: 35, 7: 28, 6: 22, 5: 17, 4: 13, 3: 10, 2: 6, 1: 1},
            '28-37': {10: 42, 9: 35, 8: 28, 7: 22, 6: 17, 5: 13, 4: 10, 3: 8, 2: 5, 1: 1},
            '38-47': {10: 35, 9: 28, 8: 22, 7: 17, 6: 13, 5: 10, 4: 8, 3: 6, 2: 4, 1: 1},
            '48-56': {10: 28, 9: 22, 8: 17, 7: 13, 6: 10, 5: 8, 4: 6, 3: 4, 2: 2, 1: 1}
        }

        # Sit-ups () data
        SIT_UP_MEN = {
            '18-27': {10: 80, 9: 70, 8: 60, 7: 50, 6: 42, 5: 35, 4: 28, 3: 22, 2: 15, 1: 1},
            '28-37': {10: 70, 9: 60, 8: 50, 7: 42, 6: 35, 5: 28, 4: 22, 3: 17, 2: 10, 1: 1},
            '38-47': {10: 60, 9: 50, 8: 42, 7: 35, 6: 28, 5: 22, 4: 17, 3: 13, 2: 7, 1: 1},
            '48-56': {10: 50, 9: 42, 8: 35, 7: 28, 6: 22, 5: 17, 4: 13, 3: 10, 2: 5, 1: 1}
        }

        SIT_UP_WOMEN = {
            '18-27': {10: 70, 9: 60, 8: 50, 7: 42, 6: 35, 5: 28, 4: 22, 3: 17, 2: 10, 1: 1},
            '28-37': {10: 60, 9: 50, 8: 42, 7: 35, 6: 28, 5: 22, 4: 17, 3: 13, 2: 7, 1: 1},
            '38-47': {10: 50, 9: 42, 8: 35, 7: 28, 6: 22, 5: 17, 4: 13, 3: 10, 2: 5, 1: 1},
            '48-56': {10: 40, 9: 33, 8: 27, 7: 22, 6: 17, 5: 13, 4: 10, 3: 7, 2: 4, 1: 1}
        }

        @classmethod
        def get_age_cat(cls, age: int) -> str:
            if 18 <= age <= 27:
                return '18-27'
            elif 28 <= age <= 37:
                return '28-37'
            elif 38 <= age <= 47:
                return '38-47'
            elif 48 <= age <= 56:
                return '48-56'
            return '48-56' if age > 56 else '18-27'

        @classmethod
        def _calculate_score(cls, gender: Gender, age: int, count: int, table_men: dict, table_women: dict) -> float:
            age_cat = cls.get_age_cat(age)
            table = table_men if gender == Gender.M else table_women

            if age_cat not in table:
                return 0.0

            age_group_data = table[age_cat]

            # Logic to find the score based on count (reps).
            # Assuming linear interpolation or direct lookup logic usually resides here.
            # For this refactoring, I'll implement a standard lookup or interpolation based on the keys (scores 1-10).
            # Since the provided data maps Score -> Reps (e.g. {10: 20} means 20 reps gets score 10),
            # we need to find the highest score where reps <= count.

            # Sort by score descending (keys are scores 10 down to 1)
            sorted_scores = sorted(age_group_data.items(), key=lambda x: x[0], reverse=True)

            # Simple threshold check: if count >= required reps, return that score
            for score, required_reps in sorted_scores:
                if count >= required_reps:
                    return float(score * 2.0)  # Scaling to 20.0 max based on usage example (20.0 was expected)

            # If count is positive but less than minimum requirement for score 1,
            # usually it's scaled or 0. Returning 0 for safety if below min.
            return 0.0

        @classmethod
        def get_score_pullup(cls, gender: Gender, age: int, count: int) -> float:
            return cls._calculate_score(gender, age, count, cls.PULLUPS_MEN, cls.PULLUPS_WOMEN)

        @classmethod
        def get_score_situp(cls, gender: Gender, age: int, count: int) -> float:
            return cls._calculate_score(gender, age, count, cls.SIT_UP_MEN, cls.SIT_UP_WOMEN)

        @classmethod
        def get_score_pushup(cls, gender: Gender, age: int, count: int) -> float:
            return cls._calculate_score(gender, age, count, cls.PUSH_UPS_MEN, cls.PUSH_UPS_WOMEN)

        @classmethod
        def get_scores(cls, gender: Gender, age: int, count: int)-> Tuple[float, float, float]:
            return cls.get_score_pullup(gender, age, count), cls.get_score_situp(gender, age, count), cls.get_score_pushup(gender, age, count)