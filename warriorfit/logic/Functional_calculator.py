from typing import Tuple

from warriorfit.core.Gender import Gender


class FunctionalCalculator:
    """
    Represents a functional calculator for assessing physical performance scores.

    This class is used to calculate performance scores for exercises such as pull-ups, push-ups,
    and sit-ups based on gender, age, and repetition count. It provides predefined scoring tables
    for men and women across various age categories, enabling standardized calculations. The scores
    are scaled consistently, with a maximum value of 20 points.

    :ivar PULLUPS_MEN: Scoring table for pull-ups for men, categorized by age groups.
    :type PULLUPS_MEN: dict
    :ivar PULLUPS_WOMEN: Scoring table for pull-ups for women, categorized by age groups.
    :type PULLUPS_WOMEN: dict
    :ivar PUSH_UPS_MEN: Scoring table for push-ups for men, categorized by age groups.
    :type PUSH_UPS_MEN: dict
    :ivar PUSH_UPS_WOMEN: Scoring table for push-ups for women, categorized by age groups.
    :type PUSH_UPS_WOMEN: dict
    :ivar SIT_UP_MEN: Scoring table for sit-ups for men, categorized by age groups.
    :type SIT_UP_MEN: dict
    :ivar SIT_UP_WOMEN: Scoring table for sit-ups for women, categorized by age groups.
    :type SIT_UP_WOMEN: dict
    """

    # Pull-ups () data
    PULLUPS_MEN = {
        "18-27": {
            10: 20,
            9: 18,
            8: 16,
            7: 14,
            6: 12,
            5: 10,
            4: 8,
            3: 6,
            2: 4,
            1: 1,
        },
        "28-37": {10: 18, 9: 16, 8: 14, 7: 12, 6: 10, 5: 8, 4: 6, 3: 5, 2: 3, 1: 1},
        "38-47": {10: 16, 9: 14, 8: 12, 7: 10, 6: 8, 5: 6, 4: 5, 3: 4, 2: 2, 1: 1},
        "48-56": {10: 14, 9: 12, 8: 10, 7: 8, 6: 6, 5: 5, 4: 4, 3: 3, 2: 2, 1: 1},
    }

    PULLUPS_WOMEN = {
        "18-27": {10: 12, 9: 10, 8: 8, 7: 6, 6: 5, 5: 4, 4: 3, 3: 2, 2: 1, 1: 0},
        "28-37": {10: 10, 9: 8, 8: 6, 7: 5, 6: 4, 5: 3, 4: 3, 3: 2, 2: 1, 1: 0},
        "38-47": {10: 8, 9: 6, 8: 5, 7: 4, 6: 3, 5: 3, 4: 2, 3: 2, 2: 1, 1: 0},
        "48-56": {10: 6, 9: 5, 8: 4, 7: 3, 6: 2, 5: 2, 4: 2, 3: 1, 2: 1, 1: 0},
    }

    # Push-ups () data
    PUSH_UPS_MEN = {
        "18-27": {
            10: 75,
            9: 65,
            8: 55,
            7: 45,
            6: 38,
            5: 30,
            4: 24,
            3: 18,
            2: 10,
            1: 1,
        },
        "28-37": {
            10: 65,
            9: 55,
            8: 45,
            7: 38,
            6: 30,
            5: 24,
            4: 18,
            3: 13,
            2: 7,
            1: 1,
        },
        "38-47": {
            10: 55,
            9: 45,
            8: 35,
            7: 28,
            6: 22,
            5: 17,
            4: 13,
            3: 10,
            2: 5,
            1: 1,
        },
        "48-56": {
            10: 45,
            9: 35,
            8: 28,
            7: 22,
            6: 17,
            5: 13,
            4: 10,
            3: 7,
            2: 4,
            1: 1,
        },
    }

    PUSH_UPS_WOMEN = {
        "18-27": {
            10: 50,
            9: 42,
            8: 35,
            7: 28,
            6: 22,
            5: 17,
            4: 13,
            3: 10,
            2: 6,
            1: 1,
        },
        "28-37": {
            10: 42,
            9: 35,
            8: 28,
            7: 22,
            6: 17,
            5: 13,
            4: 10,
            3: 8,
            2: 5,
            1: 1,
        },
        "38-47": {
            10: 35,
            9: 28,
            8: 22,
            7: 17,
            6: 13,
            5: 10,
            4: 8,
            3: 6,
            2: 4,
            1: 1,
        },
        "48-56": {10: 28, 9: 22, 8: 17, 7: 13, 6: 10, 5: 8, 4: 6, 3: 4, 2: 2, 1: 1},
    }

    # Sit-ups () data
    SIT_UP_MEN = {
        "18-27": {
            10: 80,
            9: 70,
            8: 60,
            7: 50,
            6: 42,
            5: 35,
            4: 28,
            3: 22,
            2: 15,
            1: 1,
        },
        "28-37": {
            10: 70,
            9: 60,
            8: 50,
            7: 42,
            6: 35,
            5: 28,
            4: 22,
            3: 17,
            2: 10,
            1: 1,
        },
        "38-47": {
            10: 60,
            9: 50,
            8: 42,
            7: 35,
            6: 28,
            5: 22,
            4: 17,
            3: 13,
            2: 7,
            1: 1,
        },
        "48-56": {
            10: 50,
            9: 42,
            8: 35,
            7: 28,
            6: 22,
            5: 17,
            4: 13,
            3: 10,
            2: 5,
            1: 1,
        },
    }

    SIT_UP_WOMEN = {
        "18-27": {
            10: 70,
            9: 60,
            8: 50,
            7: 42,
            6: 35,
            5: 28,
            4: 22,
            3: 17,
            2: 10,
            1: 1,
        },
        "28-37": {
            10: 60,
            9: 50,
            8: 42,
            7: 35,
            6: 28,
            5: 22,
            4: 17,
            3: 13,
            2: 7,
            1: 1,
        },
        "38-47": {
            10: 50,
            9: 42,
            8: 35,
            7: 28,
            6: 22,
            5: 17,
            4: 13,
            3: 10,
            2: 5,
            1: 1,
        },
        "48-56": {
            10: 40,
            9: 33,
            8: 27,
            7: 22,
            6: 17,
            5: 13,
            4: 10,
            3: 7,
            2: 4,
            1: 1,
        },
    }

    @classmethod
    def get_age_cat(cls, age: int) -> str:
        """
        Determines the age category of an individual based on their age.

        This method categorizes an input age into a predefined range. The result
        is returned as a string representing one of the intervals: '18-27',
        '28-37', '38-47', '48-56', or a fallback '48-56' for those older than 56.

        :param age: Age of the individual to categorize.
        :type age: int
        :return: A string representing the age category of the individual.
        :rtype: str
        """
        if 18 <= age <= 27:
            return "18-27"
        elif 28 <= age <= 37:
            return "28-37"
        elif 38 <= age <= 47:
            return "38-47"
        elif 48 <= age <= 56:
            return "48-56"
        return "48-56" if age > 56 else "18-27"

    @classmethod
    def _calculate_score(
        cls,
        gender: Gender,
        age: int,
        count: int,
        table_men: dict,
        table_women: dict,
    ) -> float:
        """
        Calculates the performance score for a given individual based on their gender, age, repetition count,
        and the performance tables for men and women. The score is scaled to a maximum of 20.0.

        :param gender: The gender of the individual, represented as a `Gender` enum.
        :param age: The age of the individual.
        :param count: The number of repetitions completed by the individual.
        :param table_men: A dictionary representing the performance table for men. The keys are age categories,
            and the values are dictionaries mapping scores to the required number of repetitions.
        :param table_women: A dictionary representing the performance table for women. The keys are age categories,
            and the values are dictionaries mapping scores to the required number of repetitions.
        :return: The calculated performance score scaled as a `float`. Returns 0.0 if no score could be determined.
        """
        age_cat = cls.get_age_cat(age)
        table = table_men if gender == Gender.M else table_women
        if age_cat not in table:
            return 0.0
        age_group_data = table[age_cat]
        sorted_scores = sorted(age_group_data.items(), key=lambda x: x[0], reverse=True)
        for score, required_reps in sorted_scores:
            if count >= required_reps:
                return float(
                    score * 2.0
                )  # Scaling to 20.0 max based on usage example (20.0 was expected)

        return 0.0

    @classmethod
    def get_score_pullup(cls, gender: Gender, age: int, count: int) -> float:
        """
        Determines the score for pull-up exercises based on gender, age, and the number
        of pull-ups performed. The scoring is calculated using predefined scoring tables.

        :param gender: The gender of the individual performing the pull-ups. Acceptable
                       values are instances of :class:`Gender`.
        :param age: The age of the individual. Must be a positive integer.
        :param count: The number of pull-ups performed. Must be a non-negative integer.
        :return: A floating-point value representing the computed score based on the
                 provided inputs.
        :rtype: float
        """
        return cls._calculate_score(
            gender, age, count, cls.PULLUPS_MEN, cls.PULLUPS_WOMEN
        )

    @classmethod
    def get_score_situp(cls, gender: Gender, age: int, count: int) -> float:
        """
        Calculates the score for sit-ups based on the provided gender, age, and count, using
        specific scoring metrics for men and women. The method is a class method, allowing
        access to class-level scoring data for sit-up calculation, and ensures appropriate
        classification by gender and age.

        :param gender: The gender of the individual performing the sit-ups.
        :type gender: Gender
        :param age: The age of the individual, used for determining age-specific benchmarks.
        :type age: int
        :param count: The count of sit-ups performed, which will be evaluated against
            the scoring metrics.
        :type count: int
        :return: The sit-up performance score calculated based on the inputs.
        :rtype: float
        """
        return cls._calculate_score(
            gender, age, count, cls.SIT_UP_MEN, cls.SIT_UP_WOMEN
        )

    @classmethod
    def get_score_pushup(cls, gender: Gender, age: int, count: int) -> float:
        """
        Calculate and return the score for push-ups based on the individual's gender, age,
        and the number of push-ups performed. This method utilizes predefined scoring
        metrics for men and women to determine the result.

        :param gender: The gender of the individual for whom the score is being calculated.
        :type gender: Gender
        :param age: The age of the individual.
        :type age: int
        :param count: The number of push-ups completed by the individual.
        :type count: int
        :return: A float value representing the calculated score for push-ups.
        :rtype: float
        """
        return cls._calculate_score(
            gender, age, count, cls.PUSH_UPS_MEN, cls.PUSH_UPS_WOMEN
        )

    @classmethod
    def get_scores(
        cls, gender: Gender, age: int, count: int
    ) -> Tuple[float, float, float]:
        """
        Computes the performance scores for pullups, situps, and pushups based on the input
        parameters such as gender, age, and count. This method uses the corresponding class
        methods to calculate and return the scores for these physical exercises.

        :param gender: The gender of the individual, used to determine the scoring criteria.
        :type gender: Gender
        :param age: The age of the individual, used to adjust scoring metrics.
        :type age: int
        :param count: The number of repetitions completed for the exercise.
        :type count: int
        :return: A tuple containing the scores for pullups, situps, and pushups in the
            respective order.
        :rtype: Tuple[float, float, float]
        """
        return (
            cls.get_score_pullup(gender, age, count),
            cls.get_score_situp(gender, age, count),
            cls.get_score_pushup(gender, age, count),
        )
