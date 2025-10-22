import math
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple

from core.Gender import Gender


class FunctionalCalculator:
    BASE_MAX = {
        "male": {"pullups": 10, "situps": 100, "pushups": 100},
        "female": {"pullups": 7, "situps": 80, "pushups": 80},
    }
    AGE_GROUPS = {
        "18-25": 0.00,
        "26-35": 0.05,
        "36-45": 0.10,
        "46-56": 0.15,
    }
    SCORES = list(range(1, 21))

    def __init__(self, exponent: float = 2.0):
        """
        exponent > 1 maakt hogere scores relatief moeilijker.
        """
        self.exponent = float(exponent)
        self.tables = {}  # will hold pandas DataFrames per test if generated

    @staticmethod
    def _age_group_from_age(age: int) -> str:
        if age < 18:
            raise ValueError("Age must be >= 18")
        if age <= 25:
            return "18-25"
        if age <= 35:
            return "26-35"
        if age <= 45:
            return "36-45"
        if age <= 56:
            return "46-56"
        raise ValueError("Age must be <= 56")

    @staticmethod
    def _sex_key(gender: Gender) -> str:
        return "male" if gender == Gender.MALE else "female"

    def _adjusted_max(self, age_group: str, gender: Gender, test: str) -> int:
        base = self.BASE_MAX[self._sex_key(gender)][test]
        correction = self.AGE_GROUPS[age_group]
        return round(base * (1 - correction))

    def _score_for_reps_nonlinear(self, reps: int, age_group: str, gender: Gender, test: str) -> int:
        """Return integer score 1..20 for given reps using non-linear formula."""
        reps = int(reps)
        if reps <= 0:
            return 1
        max_adj = self._adjusted_max(age_group, gender, test)
        if max_adj <= 0:
            return 1
        if reps >= max_adj:
            return 20
        frac = reps / max_adj
        score_cont = 1 + 19 * (frac ** self.exponent)
        score = int(round(score_cont))
        return max(1, min(20, score))

    # Publieke API-methodes (static)
    @staticmethod
    def get_score_pullup(gender: Gender, age: int, count: int) -> float:
        calc = FunctionalCalculator()
        ag = calc._age_group_from_age(int(age))
        return float(calc._score_for_reps_nonlinear(int(count), ag, gender, "pullups"))

    @staticmethod
    def get_score_situp(gender: Gender, age: int, count: int) -> float:
        calc = FunctionalCalculator()
        ag = calc._age_group_from_age(int(age))
        return float(calc._score_for_reps_nonlinear(int(count), ag, gender, "situps"))

    @staticmethod
    def get_score_pushup(gender: Gender, age: int, count: int) -> float:
        calc = FunctionalCalculator()
        ag = calc._age_group_from_age(int(age))
        return float(calc._score_for_reps_nonlinear(int(count), ag, gender, "pushups"))

    def get_scores(self, age: int, gender: Gender, pullups: int, situps: int, pushups: int) -> Dict[str, float]:
        ag = self._age_group_from_age(int(age))
        pl = self._score_for_reps_nonlinear(pullups, ag, gender, "pullups")
        su = self._score_for_reps_nonlinear(situps, ag, gender, "situps")
        pu = self._score_for_reps_nonlinear(pushups, ag, gender, "pushups")
        total = pl + su + pu
        return {
            "pullups": float(pl),
            "situps": float(su),
            "pushups": float(pu),
            "total": float(total),
            "average": round(total / 3, 2),
            "_meta": {"age_group": ag, "exponent": self.exponent, "gender": gender},
        }

    def make_tables(self):
        """Construct pandas DataFrames for each test and store in self.tables"""
        import pandas as pd  # local import to keep public API lean
        tests = ["pullups", "situps", "pushups"]
        for test in tests:
            rows = []
            idx = []
            for sex in (Gender.MALE, Gender.FEMALE):
                for age_group in self.AGE_GROUPS.keys():
                    row = [self.reps_for_score_nonlinear(s, age_group, sex, test) for s in self.SCORES]
                    rows.append(row)
                    idx.append((sex, age_group))
            mi = pd.MultiIndex.from_tuples(idx, names=("sex", "age_group"))
            df = pd.DataFrame(rows, index=mi, columns=[f"score_{s}" for s in self.SCORES])
            self.tables[test] = df
        return self.tables

    def reps_for_score_nonlinear(self, score: int, age_group: str, gender: Gender, test: str) -> int:
        """Inverse: minimal reps required to reach given score"""
        score = int(score)
        if score <= 1:
            return 0
        if score >= 20:
            return self._adjusted_max(age_group, gender, test)
        max_adj = self._adjusted_max(age_group, gender, test)
        frac = (score - 1) / 19
        reps_cont = (frac ** (1.0 / self.exponent)) * max_adj
        return int(round(reps_cont))

