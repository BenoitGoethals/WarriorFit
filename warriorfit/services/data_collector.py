import pandas as pd

from warriorfit.config.application_config import ApplicationConfig
from warriorfit.core.type_fitness_test import TypeFitnessTest
from warriorfit.data.model.db_model import MfftEvalTest, PhefTest
from warriorfit.logic.mfft_eval_calculator import MfftEvalCalculator
from warriorfit.logic.phef_calculator import PhefCalculator
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_march import ServiceMarch
from warriorfit.services.service_test import ServiceTest
from warriorfit.utils.BenchmarkDecorator import benchmark


class DataCollector:
    """
    Responsible for collecting and processing fitness test data for servicemen.
    """

    def __init__(
        self,
        service_test: ServiceTest = None,
        service_march: ServiceMarch = None,
        military_service: MilitaryService = None,
        config: ApplicationConfig = None,
    ) -> None:
        self._service = service_test if service_test is not None else ServiceTest()
        self._service_mars = service_march if service_march is not None else ServiceMarch()
        self.be_mil = military_service if military_service is not None else MilitaryService()
        self._config = config if config is not None else ApplicationConfig()

    # -------------------------
    # Small helpers
    # -------------------------
    @staticmethod
    def _fmt_dt(dt) -> str:
        return "-" if dt is None else dt.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _empty_df(columns: list[str]) -> pd.DataFrame:
        return pd.DataFrame(columns=columns)

    async def _mil_for(self, serial: str):
        # single lookup + centralized guard
        return await self.be_mil.get_servicemen_by_serial(serial)

    # -------------------------
    # Public API
    # -------------------------
    async def collect_tests_data_for_serial(
        self, serial: str, current_year: bool = True
    ) -> pd.DataFrame:
        """
        Asynchronously collects fitness test data for a given serial number and compiles it into a
        pandas DataFrame. The function retrieves detailed records of multiple types of fitness tests
        such as PHEF, Functional, Combat, Swimming, Mars, and MFFT Evaluations from different
        services and processes them to calculate performance metrics and test results.

        :param serial: Unique identifier of the service member for which fitness data is to be collected.
        :type serial: str
        :param current_year: A flag indicating whether to only collect test data from the current year.
            Defaults to True.
        :type current_year: bool
        :return: A DataFrame containing fitness test records compiled and formatted for the specified
            serial number. If no records are available, an empty DataFrame with predefined columns is returned.
        :rtype: pandas.DataFrame
        """
        frames: list[pd.DataFrame] = []

        mil = await self._mil_for(serial)
        # We keep collecting non-PHEF types even if mil is missing (they don't need age/gender).
        # PHEF rows will be empty without mil.

        # PHEF (detailed)
        phef_rows: list[dict] = []
        phef_sessions = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
            serial, TypeFitnessTest.PHEF, this_year=current_year
        )
        for sess in phef_sessions or []:
            for t in sess.fitness_tests or []:
                if t.serial_number != serial:
                    continue
                if mil is None:
                    continue

                age = mil.age_from_birthdate_and_session_date(sess.datetime_start)
                run_s = int(t.running_time or 0)
                sbr_s = int(t.sideBridge_r or 0)
                sbl_s = int(t.sideBridge_l or 0)

                run_pts = PhefCalculator.running_result(run_s, age, mil.gender)
                sbr_pts = PhefCalculator.side_bridge_result(sbr_s, age, mil.gender)
                sbl_pts = PhefCalculator.side_bridge_result(sbl_s, age, mil.gender)

                total = (run_pts * (50 / 20.0)) + ((sbr_pts + sbl_pts) * (25 / 20.0))
                phef_rows.append(
                    {
                        "Date": self._fmt_dt(sess.datetime_start),
                        "Type": "PHEF",
                        "Run": f"{run_s}",
                        "SBR": f"{sbr_s}",
                        "SBL": f"{sbl_s}",
                        "Run_points": f"{run_pts}/20",
                        "SBR_points": f"{sbr_pts}/20",
                        "SBL_points": f"{sbl_pts}/20",
                        "Total": f"{total:.1f}/100",
                        "Result": "Passed" if total >= 50 else "Failed",
                    }
                )
        if phef_rows:
            frames.append(pd.DataFrame.from_records(phef_rows))

        # Functional (detailed)
        func_rows: list[dict] = []
        func_sessions = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
            serial, TypeFitnessTest.FUNCTIONAL, this_year=current_year
        )
        for sess in func_sessions or []:
            for t in sess.fitness_tests or []:
                if t.serial_number != serial:
                    continue

                pu = int(t.push_ups or 0)
                su = int(t.sit_ups or 0)
                plu = int(t.pull_ups or 0)
                total = pu + su + plu
                func_rows.append(
                    {
                        "Date": self._fmt_dt(sess.datetime_start),
                        "Type": "Functional",
                        "PU": f"{pu}",
                        "SU": f"{su}",
                        "PLU": f"{plu}",
                        "PU_scores": f"{pu}",
                        "SU_scores": f"{su}",
                        "PLU_scores": f"{plu}",
                        "Total": f"{total}",
                        "Result": "Passed" if total >= 50 else "Failed",
                    }
                )
        if func_rows:
            frames.append(pd.DataFrame.from_records(func_rows))

        # Combat (detailed)
        combat_rows: list[dict] = []
        combat_sessions = (
            await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
                serial, TypeFitnessTest.COMBAT, this_year=current_year
            )
        )
        for sess in combat_sessions or []:
            for t in sess.fitness_tests or []:
                if t.serial_number != serial:
                    continue

                rope = bool(t.rope_passed)
                obstacle = bool(t.obstacle_passed)
                run_s = int(t.running_time or 0)
                passed = rope and obstacle and run_s <= 7200
                combat_rows.append(
                    {
                        "Date": self._fmt_dt(sess.datetime_start),
                        "Type": "Combat",
                        "Rop": f"{rope}",
                        "Obs": f"{obstacle}",
                        "Speed": f"{run_s}",
                        "Rop_scores": f"{'OK' if rope else 'NO'}",
                        "Obs_scores": f"{'OK' if obstacle else 'NO'}",
                        "Speed_scores": f"{run_s}",
                        "Result": "Passed" if passed else "Failed",
                    }
                )
        if combat_rows:
            frames.append(pd.DataFrame.from_records(combat_rows))

        # Swimming (detailed)
        swim_rows: list[dict] = []
        swim_sessions = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
            serial, TypeFitnessTest.SWIMMING, this_year=current_year
        )
        for sess in swim_sessions or []:
            for t in sess.fitness_tests or []:
                if t.serial_number != serial:
                    continue
                ok = bool(t.swim_paased)
                swim_rows.append(
                    {
                        "Date": self._fmt_dt(sess.datetime_start),
                        "Type": "Swimming",
                        "Details": "Combat swim",
                        "Result": "Passed" if ok else "Failed",
                    }
                )
        if swim_rows:
            frames.append(pd.DataFrame.from_records(swim_rows))

        # Mars (detailed)
        mars_rows: list[dict] = []
        marses = await self._service_mars.get_march_from_service_men(
            serial_number=serial, this_year=False
        )
        for mars in marses or []:
            ok = bool(mars.succeeded)
            mars_rows.append(
                {
                    "Date": mars.datetime_executed.strftime("%Y-%m-%d %H:%M"),  # type: ignore[attr-defined]
                    "Type": "Mars",
                    "Details": f"{mars.distance} Km",
                    "Result": "Passed" if ok else "Failed",
                }
            )
        if mars_rows:
            frames.append(pd.DataFrame.from_records(mars_rows))

        # MFFT Eval (detailed)
        mfft_rows: list[dict] = []
        mfft_sessions = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
            serial, TypeFitnessTest.MFFT_EVAL, this_year=current_year
        )
        for sess in mfft_sessions or []:
            for t in sess.fitness_tests or []:
                if t.serial_number != serial:
                    continue
                if mil is None:
                    continue
                try:
                    age = mil.age_from_birthdate_and_session_date(sess.datetime_start)
                    res = MfftEvalCalculator.evaluate(t, mil.cluster, age, mil.gender)
                except (AttributeError, TypeError, KeyError, ValueError):
                    continue
                mfft_rows.append(
                    {
                        "Date": self._fmt_dt(sess.datetime_start),
                        "Type": "MFFT Eval",
                        "Cluster": str(mil.cluster),
                        "Overall": str(res.overall),
                        "Tier": str(res.tier_info),
                        "Result": "Passed" if res.passed else "Failed",
                    }
                )
        if mfft_rows:
            frames.append(pd.DataFrame.from_records(mfft_rows))

        # Finalize
        if not frames:
            return self._empty_df(
                columns=[
                    "Date",
                    "Type",
                    "Details",
                    "Scores",
                    "Total",
                    "Result",
                ]
            )

        df = pd.concat(frames, ignore_index=True, sort=False)
        # stable sort on the display string (keeps existing behavior)
        df = df.sort_values(by=["Date"], kind="stable").reset_index(drop=True)
        return df

    @benchmark
    async def collect_tests_for_serial(
        self, serial: str, current_year: bool = True
    ) -> pd.DataFrame:
        """
        Collects fitness test data for a specified serial number from various test types
        including Physical Fitness Efficiency Test (PHEF), Functional tests, Combat
        tests, Swimming, Mars marches, and Military Functional Fitness Test Evaluation
        (MFFT Eval). Aggregates and summarizes the data in tabular format.

        :param serial: The unique identifier representing the individual for whom
                       fitness test data is collected.
        :type serial: str
        :param current_year: A boolean flag indicating whether the data should be
                             limited to the tests conducted in the current year.
                             Defaults to True.
        :type current_year: bool
        :return: A pandas DataFrame summarizing all relevant fitness test sessions for
                 the specified serial number, including details, scores, total scores,
                 and pass/fail results for each test category. Returns an empty
                 DataFrame if no data is available.
        :rtype: pd.DataFrame
        """
        frames: list[pd.DataFrame] = []

        mil = await self._mil_for(serial)

        # PHEF (summary)
        phef_rows: list[dict] = []
        phef_sessions = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
            serial, TypeFitnessTest.PHEF, this_year=current_year
        )
        for sess in phef_sessions or []:
            for t in sess.fitness_tests or []:
                if t.serial_number != serial:
                    continue
                if mil is None:
                    continue

                age = mil.age_from_birthdate_and_session_date(sess.datetime_start)
                run_s = int(t.running_time or 0)
                sbr_s = int(t.sideBridge_r or 0)
                sbl_s = int(t.sideBridge_l or 0)

                run_pts = PhefCalculator.running_result(run_s, age, mil.gender)
                sbr_pts = PhefCalculator.side_bridge_result(sbr_s, age, mil.gender)
                sbl_pts = PhefCalculator.side_bridge_result(sbl_s, age, mil.gender)

                total = (run_pts * (50 / 20.0)) + ((sbr_pts + sbl_pts) * (25 / 20.0))
                test_passed = sbl_pts + sbr_pts >= 20 and run_pts >= 10
                phef_rows.append(
                    {
                        "Date": self._fmt_dt(sess.datetime_start),
                        "Type": "PHEF",
                        "Details": f"Run {run_s}s, SBR {sbr_s}s, SBL {sbl_s}s",
                        "Scores": f"Run {run_pts}/20, SBR {sbr_pts}/20, SBL {sbl_pts}/20",
                        "Total": f"{total:.1f}/100",
                        "Result": "🟢 Passed" if test_passed else " 🔴 Failed",
                    }
                )
        if phef_rows:
            frames.append(pd.DataFrame.from_records(phef_rows))

        # Functional (summary)
        func_rows: list[dict] = []
        func_sessions = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
            serial, TypeFitnessTest.FUNCTIONAL, this_year=current_year
        )
        for sess in func_sessions or []:
            for t in sess.fitness_tests or []:
                if t.serial_number != serial:
                    continue
                pu = int(t.push_ups or 0)
                su = int(t.sit_ups or 0)
                plu = int(t.pull_ups or 0)
                total = pu + su + plu
                func_rows.append(
                    {
                        "Date": self._fmt_dt(sess.datetime_start),
                        "Type": "Functional",
                        "Details": f"PU {pu}, SU {su}, PLU {plu}",
                        "Scores": f"PU {pu}, SU {su}, PLU {plu}",
                        "Total": f"{total}",
                        "Result": "🟢 Passed" if total >= 50 else " 🔴 Failed",
                    }
                )
        if func_rows:
            frames.append(pd.DataFrame.from_records(func_rows))

        # Combat (summary)
        combat_rows: list[dict] = []
        combat_sessions = (
            await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
                serial, TypeFitnessTest.COMBAT, this_year=current_year
            )
        )
        for sess in combat_sessions or []:
            for t in sess.fitness_tests or []:
                if t.serial_number != serial:
                    continue
                rope = bool(t.rope_passed)
                obstacle = bool(t.obstacle_passed)
                run_s = int(t.running_time or 0)
                passed = rope and obstacle and run_s <= 7200
                combat_rows.append(
                    {
                        "Date": self._fmt_dt(sess.datetime_start),
                        "Type": "Combat",
                        "Details": f"Rope {'OK' if rope else 'NO'}, Obstacle {'OK' if obstacle else 'NO'}, Speedmars {run_s}s",
                        "Scores": f"Rope {'OK' if rope else 'NO'}, Obstacle {'OK' if obstacle else 'NO'}",
                        "Total": "-",
                        "Result": "🟢 Passed" if passed else "🔴 Failed",
                    }
                )
        if combat_rows:
            frames.append(pd.DataFrame.from_records(combat_rows))

        # Swimming (summary)
        swim_rows: list[dict] = []
        swim_sessions = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
            serial, TypeFitnessTest.SWIMMING, this_year=current_year
        )
        for sess in swim_sessions or []:
            for t in sess.fitness_tests or []:
                if t.serial_number != serial:
                    continue
                ok = bool(t.swim_paased)
                swim_rows.append(
                    {
                        "Date": self._fmt_dt(sess.datetime_start),
                        "Type": "Swimming",
                        "Details": "Combat swim",
                        "Scores": "-",
                        "Total": "-",
                        "Result": "🟢 Passed" if ok else "🔴 Failed",
                    }
                )
        if swim_rows:
            frames.append(pd.DataFrame.from_records(swim_rows))

        # Mars (summary) — keep existing service call name used here
        mars_rows: list[dict] = []
        marses = await self._service_mars.get_march_from_service_men(
            serial_number=serial, this_year=False
        )
        for mars in marses or []:
            ok = bool(mars.succeeded)
            mars_rows.append(
                {
                    "Date": mars.datetime_executed.strftime("%Y-%m-%d %H:%M"),  # type: ignore[attr-defined]
                    "Type": "Mars",
                    "Details": f"{mars.distance} Km",
                    "Scores": "-",
                    "Total": "-",
                    "Result": "🟢 Passed" if ok else "🔴 Failed",
                }
            )
        if mars_rows:
            frames.append(pd.DataFrame.from_records(mars_rows))

        # MFFT Eval (summary)
        mfft_rows: list[dict] = []
        mfft_sessions = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
            serial, TypeFitnessTest.MFFT_EVAL, this_year=current_year
        )
        for sess in mfft_sessions or []:
            for t in sess.fitness_tests or []:
                if t.serial_number != serial:
                    continue
                if mil is None:
                    continue
                try:
                    age = mil.age_from_birthdate_and_session_date(sess.datetime_start)
                    res = MfftEvalCalculator.evaluate(t, mil.cluster, age, mil.gender)
                except (AttributeError, TypeError, KeyError, ValueError):
                    continue
                details = (
                    f"PU {t.pull_ups}, Burpees {t.burpees_step_over}, "
                    f"Farmer {t.farmer_walk_m}m, Push {t.push_ups_release}, "
                    f"Drag {t.casualty_drag_m}m, Sand {t.sandbag_carry_m}m, "
                    f"Run {t.combat_run_seconds}s, Swim {t.combat_swim_seconds}s"
                )
                mfft_rows.append(
                    {
                        "Date": self._fmt_dt(sess.datetime_start),
                        "Type": "MFFT Eval",
                        "Details": details,
                        "Scores": f"Tier {res.tier_info}",
                        "Total": str(res.overall),
                        "Result": "🟢 Passed" if res.passed else "🔴 Failed",
                    }
                )
        if mfft_rows:
            frames.append(pd.DataFrame.from_records(mfft_rows))

        if not frames:
            return self._empty_df(columns=["Date", "Type", "Details", "Scores", "Total", "Result"])

        df = pd.concat(frames, ignore_index=True, sort=False)
        df = df.sort_values(by=["Date"], kind="stable").reset_index(drop=True)
        return df

    async def collect_all_mil_from_own_unit_not_executed_phefs(self) -> pd.DataFrame:
        """
        Collects all military personnel from the user's own unit for whom no PHEF tests
        have been executed and returns the data in a pandas DataFrame.

        This asynchronous method retrieves all personnel data for the specified unit,
        and filters out those with no associated PHEF tests. The resulting data is
        formatted into a DataFrame.

        :return: A pandas DataFrame containing the following columns:
                 "Serial", "Name", "Gender", "Age", "Para". If no personnel meet
                 the criteria, an empty DataFrame with the specified columns is returned.
        :rtype: pd.DataFrame
        """
        mil_series = await self.be_mil.get_all_be_mil_from_unit(self._config.own_unit)
        rows: list[dict] = []
        for m in mil_series:
            mils: list[PhefTest] = await self._service.get_all_phef_mil(m.service_number)
            if len(mils) == 0:
                rows.append(
                    {
                        "Serial": m.service_number,
                        "Name": m.first_name + " " + m.last_name,
                        "Gender": m.gender,
                        "Age": m.age_from_birthdate(),
                        "Para": m.para,
                    }
                )
        if not rows:
            return pd.DataFrame(columns=["Serial", "Name", "Gender", "Age", "Para"])
        return (
            pd.DataFrame.from_records(rows)
            .sort_values(by=["Name"], kind="stable")
            .reset_index(drop=True)
        )

    async def collect_all_mil_from_own_unit_failed_phefs(self) -> pd.DataFrame:
        """
        Asynchronously collects and processes data to retrieve details of individuals
        from the specified unit whose PHEF (Physical Health Evaluation Framework) metrics
        indicate failed tests based on calculated scores. The results are returned as a
        pandas DataFrame, sorted and indexed.

        :param self:
            Instance of the class implementing this coroutine.
        :return:
            A pandas DataFrame with columns "Serial", "Name", "Gender", "Age", and "Para",
            containing details of individuals with failed PHEF scores. If no data is
            present, an empty DataFrame with the specified columns is returned.
        :rtype:
            pd.DataFrame
        """
        mil_series = await self.be_mil.get_all_be_mil_from_unit(self._config.own_unit)
        rows: list[dict] = []
        for m in mil_series:
            mils: list[PhefTest] = await self._service.get_all_phef_mil(m.service_number)

            passed = any(
                [
                    (
                        PhefCalculator.calculate_phef_score(
                            mil.running_time,
                            mil.sideBridge_l,
                            mil.sideBridge_r,
                            m.age_from_birthdate(),
                            m.gender,
                        )[4]
                    )
                    for mil in mils
                ]
            )
            if not passed:
                continue
            rows.append(
                {
                    "Serial": m.service_number,
                    "Name": m.first_name + " " + m.last_name,
                    "Gender": m.gender,
                    "Age": m.age_from_birthdate(),
                    "Para": m.para,
                }
            )
        if not rows:
            return pd.DataFrame(columns=["Serial", "Name", "Gender", "Age", "Para"])
        return (
            pd.DataFrame.from_records(rows)
            .sort_values(by=["Name"], kind="stable")
            .reset_index(drop=True)
        )

    async def collect_tests_data_for_own_unit(self) -> pd.DataFrame:
        """
        Asynchronously collects and aggregates fitness test data for service members in the current unit and
        returns the data as a pandas DataFrame. The fitness test data includes various test types such as
        PHEF, functional, combat, swimming, march, and MFFT evaluations. Each service member's results
        are summarized in a structured format.

        :rtype: pd.DataFrame
        :return: A pandas DataFrame containing aggregated fitness test results for service members
            in the current unit. The results include the following columns:
            - "Rank": The rank of the service member.
            - "Serial": The service number of the service member.
            - "Name": The full name of the service member (formatted as "FirstName LastName").
            - "Phef": The status of the PHEF test ("Passed", "Failed", or "Not Done").
            - "Combat": The status of the combat test ("Passed", "Failed", or "Not Done").
            - "Swimming": The status of the swimming test ("Passed", "Failed", or "Not Done").
            - "Functional": The status of the functional fitness test ("Passed", "Failed", or "Not Done").
            - "March": The status of the march test ("Passed", "Failed", or "Not Done").
            - "MFFT": The status of the MFFT evaluation ("Passed", "Failed", or "Not Done").
        """
        own_unit = await self.be_mil.get_all_be_mil_from_unit(self._config.own_unit)
        rows: list[dict] = []

        for m in own_unit:
            data_phef = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
                m.service_number, TypeFitnessTest.PHEF
            )
            data_functional = (
                await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
                    m.service_number, TypeFitnessTest.FUNCTIONAL
                )
            )
            data_combat = (
                await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
                    m.service_number, TypeFitnessTest.COMBAT
                )
            )
            data_swimming = (
                await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
                    m.service_number, TypeFitnessTest.SWIMMING
                )
            )
            data_mars = await self._service_mars.get_march_from_service_men(
                serial_number=m.service_number, this_year=False
            )
            data_mfft = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
                m.service_number, TypeFitnessTest.MFFT_EVAL
            )

            if data_phef and data_phef[0].fitness_tests:
                dt: PhefTest = data_phef[0].fitness_tests[0]
                tp = PhefCalculator.calculate_phef_score(
                    dt.running_time,
                    dt.sideBridge_l,
                    dt.sideBridge_r,
                    m.age_from_birthdate(),
                    m.gender,
                )
                phef_status = "Passed" if tp[4] else "Failed"
            else:
                phef_status = "Not Done"

            if data_combat and data_combat[0].fitness_tests:
                cmt = data_combat[0].fitness_tests[0]
                combat_status = "Passed" if cmt.rope_passed and cmt.obstacle_passed else "Failed"
            else:
                combat_status = "Not Done"

            if data_swimming and data_swimming[0].fitness_tests:
                dw = data_swimming[0].fitness_tests[0]
                swim_status = "Passed" if dw.swim_paased else "Failed"
            else:
                swim_status = "Not Done"

            if data_functional and data_functional[0].fitness_tests:
                dfd = data_functional[0].fitness_tests[0]
                functional_score = (dfd.push_ups + dfd.sit_ups + dfd.pull_ups) / 3
                func_status = "Passed" if functional_score >= 50 else "Failed"
            else:
                func_status = "Not Done"

            if data_mars and data_mars[0].succeeded:
                mars_status = "Passed"
            elif data_mars and not data_mars[0].succeeded:
                mars_status = "Failed"
            else:
                mars_status = "Not Done"

            mfft_status = "Not Done"
            if data_mfft and data_mfft[0].fitness_tests:
                mfft_test = data_mfft[0].fitness_tests[0]
                if isinstance(mfft_test, MfftEvalTest):
                    try:
                        age = m.age_from_birthdate_and_session_date(data_mfft[0].datetime_start)
                        res = MfftEvalCalculator.evaluate(mfft_test, m.cluster, age, m.gender)
                        mfft_status = "Passed" if res.passed else "Failed"
                    except (AttributeError, TypeError, KeyError, ValueError):
                        mfft_status = "Not Done"

            rows.append(
                {
                    "Rank": m.rank,
                    "Serial": m.service_number,
                    "Name": f"{m.first_name} {m.last_name}",
                    "Phef": phef_status,
                    "Combat": combat_status,
                    "Swimming": swim_status,
                    "Functional": func_status,
                    "March": mars_status,
                    "MFFT": mfft_status,
                }
            )

        if not rows:
            return pd.DataFrame(
                columns=[
                    "Rank",
                    "Serial",
                    "Name",
                    "Phef",
                    "Combat",
                    "Swimming",
                    "Functional",
                    "March",
                    "MFFT",
                ]
            )

        return pd.DataFrame.from_records(rows)

    async def collect_all_mil_from_own_unit_not_executed_mfft_eval(self) -> pd.DataFrame:
        """
        Collects all military personnel from the unit who have not executed their MFFT
        evaluations and returns their details in the form of a DataFrame. The dataset
        includes information such as serial number, name, gender, age, and cluster of
        each non-evaluated individual.

        :return: A pandas DataFrame containing columns: "Serial", "Name", "Gender",
            "Age", and "Cluster". If no eligible records are found, returns an empty
            DataFrame with these columns.
        :rtype: pd.DataFrame
        """
        mil_series = await self.be_mil.get_all_be_mil_from_unit(self._config.own_unit)
        rows: list[dict] = []
        for m in mil_series:
            tests = await self._service.get_all_mfft_eval_mil(m.service_number)
            if not tests:
                rows.append(
                    {
                        "Serial": m.service_number,
                        "Name": f"{m.first_name} {m.last_name}",
                        "Gender": m.gender,
                        "Age": m.age_from_birthdate(),
                        "Cluster": str(m.cluster),
                    }
                )
        if not rows:
            return pd.DataFrame(columns=["Serial", "Name", "Gender", "Age", "Cluster"])
        return (
            pd.DataFrame.from_records(rows)
            .sort_values(by=["Name"], kind="stable")
            .reset_index(drop=True)
        )
