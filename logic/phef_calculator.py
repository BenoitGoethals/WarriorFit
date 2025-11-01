from core.Gender import Gender
import pandas as pd
from datetime import date, datetime


class PhefCalculator:
    """
    A utility class for calculating physical exercise scores based on various datasets.

    This class provides mechanisms for determining scores for physical fitness tests,
    including the 'side bridge' test. The scores are derived from preloaded datasets
    that vary by age group and gender.

    :ivar _running_data: Preloaded dataset containing running test scores based on
                         age group, gender, and other factors.
    :type _running_data: pandas.DataFrame
    :ivar _side_bridge_data: Preloaded dataset containing side bridge test scores
                             based on age group, gender, and other factors.
    :type _side_bridge_data: pandas.DataFrame
    """
    _running_data = pd.DataFrame(
        {
            "Score": list(range(20, -1, -1)),
            "<30_m": [
                "9:31", "9:42", "9:54", "10:05", "10:17", "10:28", "10:39", "10:50", "11:01", "11:12",
                "11:23", "11:34", "11:45", "11:56", "12:08", "12:19", "12:30", "12:41", "12:52", "13:04", "99:59"
            ],
            "<30_v": [
                "10:55", "11:10", "11:24", "11:39", "11:53", "12:08", "12:22", "12:37", "12:51", "13:06",
                "13:21", "13:37", "13:52", "14:08", "14:23", "14:49", "15:04", "15:20", "15:35", "15:51", "99:59"
            ],
            "30-34_m": [
                "9:49", "10:00", "10:12", "10:23", "10:35", "10:46", "10:58", "11:09", "11:21", "11:33",
                "11:45", "11:58", "12:11", "12:24", "12:38", "12:51", "13:04", "13:17", "13:30", "13:44", "99:59"
            ],
            "30-34_v": [
                "11:39", "11:56", "12:13", "12:30", "12:47", "13:04", "13:21", "13:38", "13:55", "14:12",
                "14:29", "14:43", "15:00", "15:12", "15:27", "15:42", "15:56", "16:11", "16:26", "16:41", "99:59"
            ],
            "35-39_m": [
                "9:57", "10:09", "10:22", "10:34", "10:47", "10:59", "11:12", "11:24", "11:37", "11:50",
                "12:03", "12:16", "12:30", "12:42", "12:57", "13:11", "13:24", "13:38", "13:51", "14:06", "99:59"
            ],
            "35-39_v": [
                "12:00", "12:17", "12:34", "12:51", "13:08", "13:25", "13:42", "13:59", "14:16", "14:32",
                "14:49", "15:08", "15:26", "15:42", "15:57", "16:14", "16:37", "16:55", "17:13", "17:30", "99:59"
            ],
            "40-44_m": [
                "10:05", "10:18", "10:32", "10:45", "10:59", "11:13", "11:27", "11:40", "11:54", "12:07",
                "12:21", "12:35", "12:50", "13:03", "13:17", "13:31", "13:45", "13:59", "14:13", "14:28", "99:59"
            ],
            "40-44_v": [
                "12:21", "12:38", "12:55", "13:12", "13:29", "13:46", "14:03", "14:20", "14:37", "14:54",
                "15:12", "15:32", "15:50", "16:03", "16:30", "16:57", "17:19", "17:40", "18:00", "17:21", "99:59"
            ],
            "45-49_m": [
                "10:35", "10:49", "11:04", "11:19", "11:34", "11:49", "12:05", "12:20", "12:34", "12:49",
                "13:04", "13:19", "13:34", "13:49", "14:04", "14:19", "14:34", "14:48", "15:03", "15:19", "99:59"
            ],
            "45-49_v": [
                "13:07", "13:25", "13:44", "14:02", "14:21", "14:39", "14:58", "15:16", "15:35", "15:53",
                "16:12", "16:33", "16:53", "17:13", "17:34", "17:54", "18:15", "18:35", "18:55", "19:15", "99:59"
            ],
            "50-54_m": [
                "11:05", "11:21", "11:37", "11:54", "12:10", "12:26", "12:43", "12:59", "13:15", "13:32",
                "13:48", "14:04", "14:20", "14:35", "14:51", "15:07", "15:24", "15:38", "15:54", "16:10", "99:59"
            ],
            "50-54_v": [
                "13:53", "14:13", "14:33", "14:53", "15:13", "15:33", "15:53", "16:13", "16:33", "16:53",
                "17:13", "17:33", "17:53", "18:12", "18:32", "18:52", "19:11", "19:31", "19:51", "20:10", "99:59"
            ],
            "55-59_m": [
                "11:35", "11:53", "12:10", "12:28", "12:46", "13:03", "13:21", "13:39", "13:56", "14:14",
                "14:32", "14:50", "15:09", "15:28", "15:47", "16:06", "16:24", "16:43", "17:02", "17:21", "99:59"
            ],
            "55-59_v": [
                "14:10", "14:30", "14:50", "15:10", "15:30", "15:50", "16:10", "16:30", "16:50", "17:10",
                "17:30", "17:50", "18:10", "18:29", "18:49", "19:09", "19:28", "19:48", "20:08", "20:27", "99:59"
            ],
            "60+_m": [
                "12:06", "12:25", "12:44", "13:03", "13:22", "13:41", "14:00", "14:19", "14:38", "14:57",
                "15:17", "15:37", "15:59", "16:21", "16:43", "17:05", "17:27", "17:49", "18:11", "18:33", "99:59"
            ],
            "60+_v": [
                "15:27", "15:47", "16:07", "16:27", "16:47", "17:06", "17:26", "17:46", "18:06", "18:26",
                "18:45", "19:09", "19:34", "19:58", "20:23", "20:47", "21:13", "21:36", "22:01", "22:26", "99:59"
            ]
        })

    _side_bridge_data = pd.DataFrame({
        "Quotering": list(range(20, -1, -1)),
        "<30_m": ["2:05", "2:00", "1:55", "1:50", "1:45", "1:40", "1:35", "1:30", "1:25", "1:20", "1:15", "1:13",
                  "1:11", "1:10", "1:08", "1:06", "1:05", "1:03", "1:01", "00:60", "00:50"],
        "<30_v": ["1:50", "1:45", "1:40", "1:35", "1:30", "1:25", "1:20", "1:15", "1:10", "1:05", "00:60", "00:58",
                  "00:56", "00:54", "00:52", "00:50", "00:47", "00:45", "00:42", "00:40", "00:50"],
        "30-39_m": ["1:55", "1:50", "1:45", "1:40", "1:35", "1:30", "1:25", "1:20", "1:15", "1:10", "1:05", "1:03",
                    "1:01", "00:59", "00:57", "00:55", "00:52", "00:50", "00:47", "00:45", "00:50"],
        "30-39_v": ["1:45", "1:40", "1:35", "1:30", "1:25", "1:20", "1:15", "1:10", "1:05", "00:60", "00:55", "00:53",
                    "00:51", "00:49", "00:47", "00:45", "00:42", "00:40", "00:37", "00:35", "00:50"],
        "40-49_m": ["1:50", "1:45", "1:40", "1:35", "1:30", "1:25", "1:20", "1:15", "1:10", "1:05", "00:60", "00:58",
                    "00:56", "00:54", "00:52", "00:50", "00:47", "00:45", "00:42", "00:40", "00:50"],
        "40-49_v": ["1:40", "1:35", "1:30", "1:25", "1:20", "1:15", "1:10", "1:05", "1:00", "00:55", "00:50", "00:48",
                    "00:46", "00:44", "00:42", "00:40", "00:37", "00:35", "00:32", "00:30", "00:50"],
        "50+_m": ["1:45", "1:40", "1:35", "1:30", "1:25", "1:20", "1:15", "1:10", "1:05", "1:00", "00:55", "00:53",
                  "00:51", "00:49", "00:47", "00:45", "00:42", "00:40", "00:37", "00:35", "00:50"],
        "50+_v": ["1:35", "1:30", "1:25", "1:20", "1:15", "1:10", "1:05", "1:00", "00:55", "00:50", "00:45", "00:43",
                  "00:41", "00:39", "00:37", "00:35", "00:32", "00:30", "00:27", "00:25", "00:50"],
    }
    )


    @classmethod
    def side_bridge_result(cls, side_time: float|str, age: int, gender: Gender)->int:
        """
        Calculates the result of the side bridge test based on the provided time, age, and gender.
        The method determines the age group and gender category to match the corresponding score in
        the dataset. If no match is found where the provided time is greater than or equal to the
        threshold, the score defaults to 0.

        :param side_time: The time in seconds or string format for the side bridge test.
                          If a string, it will be converted into seconds.
        :type side_time: float | str

        :param age: The age of the individual performing the test.
        :type age: int

        :param gender: The gender of the individual performing the test, which must be
                       a value of the Gender enum or a valid gender identifier such as "M" or "F".
        :type gender: Gender

        :return: Returns an integer score for the test result based on the corresponding dataset.
        :rtype: int
        """
        if side_time is None:
            return 0
        elif isinstance(side_time, str):
            side_time = cls.convert_to_seconds(side_time)
        elif not isinstance(side_time, (int, float)):
            raise TypeError(f"Tijd moet een int of float zijn, niet {type(side_time)}")

        if gender == Gender.MALE or gender == "M":
            kolom = "m"
        elif gender == Gender.FEMALE or gender == "F":
            kolom = "v"
        else:
            return 0

        # leeftijdscategorie bepalen
        if age < 30:
            age_group = "<30"
        elif age < 40:
            age_group = "30-39"
        elif age < 50:
            age_group = "40-49"
        else:
            age_group = "50+"

        col = f"{age_group}_{kolom}"

        # door dataframe lopen en hoogste score vinden waarbij tijd >= grens
        for i, row in cls._side_bridge_data.iterrows():
            town_time = cls.convert_to_seconds(row[col])
            if side_time >= town_time:
                return cls._side_bridge_data["Quotering"][i]

        return 0  # standaard: geen score


    @classmethod
    def running_result(cls, running_time: float|str, age: int, gender: Gender|str)->int:
        """
        Determines the running score based on the provided running time, age, and gender. The method calculates the age
        category, resolves the column name based on gender and age category, and compares the running time against timing norms
        from a preloaded dataset to return a corresponding score. If the running time does not match any criteria, a default
        score of zero will be returned.

        :param running_time: The running time as a string (formatted time) or as a numerical value (seconds).
        :param age: The age of the individual, used to determine the age category. Must be a positive integer.
        :param gender: Gender of the individual, provided as a Gender enum instance or as a string ("M" for male or "F" for female).
        :return: An integer representing the score of the individual based on running norms.
        :raises TypeError: If the running_time is neither a float, int, nor a properly formatted string.
        :raises ValueError: If no norms are available for the resolved column corresponding to the age and gender.
        """
        if gender == Gender.MALE or gender == "M":
            kolom = "m"
        elif gender == Gender.FEMALE or gender == "F":
            kolom = "v"
        else:
            return 0

        if running_time is None:
            return 0
        elif isinstance(running_time, str):
            running_time = cls.convert_to_seconds(running_time)
        elif not isinstance(running_time, (int, float)):
            raise TypeError(f"Tijd moet een int of float zijn, niet {type(running_time)}")

        # Leeftijdscategorie bepalen
        if age < 30:
            kolom = "<30_" + kolom
        elif age < 35:
            kolom = "30-34_" + kolom
        elif age < 40:
            kolom = "35-39_" + kolom
        elif age < 45:
            kolom = "40-44_" + kolom
        elif age < 50:
            kolom = "45-49_" + kolom
        elif age < 55:
            kolom = "50-54_" +kolom
        elif age < 60:
            kolom = "55-59_" + kolom
        else:
            kolom = "60+_" + kolom

        if kolom not in cls._running_data.columns:
            raise ValueError(f"Geen normen beschikbaar voor kolom: {kolom}")

        for i, normtijd in enumerate(cls._running_data[kolom]):
            if running_time <= cls.convert_to_seconds(normtijd):
                return cls._running_data["Score"][i]

        return 0  # trager dan laagste norm


    @staticmethod
    def convert_to_seconds(tijd_str:str):
        """Zet tijd in 'M:SS' formaat om naar seconden."""
        minuten, seconden = map(int, tijd_str.split(':'))
        return minuten * 60 + seconden


    @staticmethod
    def calculate_phef_score(running_time: float|str, side_time_l: float|str, side_time_r: float|str , age: int, gender: Gender|str)->tuple[float, float,float,float ,bool]:
        """
        Calculate the Physical Health Evaluation and Fitness (PHEF) score based on running time,
        side bridge times, age, and gender. The function evaluates an individual's fitness level
        by calculating scores for running and side bridge performance, then determines
        if a passing threshold is met.

        :param running_time: Running performance time in seconds or as a string
        :param side_time_l: Side bridge time for the left side in seconds or as a string
        :param side_time_r: Side bridge time for the right side in seconds or as a string
        :param age: Age of the individual
        :param gender: Gender of the individual

        :return: A tuple containing the following:
            - running_score (float): Score calculated for the running performance.
            - side_l_score (float): Score for the left-side bridge performance.
            - side_r_score (float): Score for the right-side bridge performance.
            - total_score (float): Cumulative score for the three tests.
            - passed (bool): A boolean indicating whether the individual has passed
              based on the minimum required scores for each evaluation.

        """
        running_score = PhefCalculator.running_result(running_time, age, gender)
        side_l_score = PhefCalculator.side_bridge_result(side_time_l, age, gender)
        side_r_score = PhefCalculator.side_bridge_result(side_time_r, age, gender)
        total_score = running_score + side_l_score + side_r_score
        passed = running_score >= 10 and side_l_score >= 10 and side_r_score >= 10
        return running_score, side_l_score, side_r_score, total_score,passed



assert PhefCalculator.running_result(571, 20, Gender.MALE) == 20
assert PhefCalculator.running_result(PhefCalculator.convert_to_seconds("11:15"), 20, Gender.FEMALE) == 18
assert PhefCalculator.running_result(PhefCalculator.convert_to_seconds("11:15"), 43, Gender.MALE) == 14

assert PhefCalculator.side_bridge_result(PhefCalculator.convert_to_seconds("1:20"), 44, Gender.MALE) == 14
assert PhefCalculator.side_bridge_result(PhefCalculator.convert_to_seconds("1:20"), 44, Gender.FEMALE) == 16

assert PhefCalculator.side_bridge_result(PhefCalculator.convert_to_seconds("1:05"), 35, Gender.MALE) == 10
assert PhefCalculator.side_bridge_result(PhefCalculator.convert_to_seconds("1:05"), 35, Gender.FEMALE) == 12

assert PhefCalculator.running_result("11:15", 20, Gender.FEMALE) == 18
assert PhefCalculator.running_result("11:15", 43, Gender.MALE) == 14

assert PhefCalculator.side_bridge_result("1:20", 44, Gender.MALE) == 14
assert PhefCalculator.side_bridge_result("1:20", 44, Gender.FEMALE) == 16

assert PhefCalculator.side_bridge_result("1:05", 35, Gender.MALE) == 10
assert PhefCalculator.side_bridge_result("1:05", 35, Gender.FEMALE) == 12