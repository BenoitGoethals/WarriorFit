import pandas as pd
from config.appliccation_config import ApplicationConfig
from core.type_fitness_test import TypeFitnessTest
from data.db.db_model import PhefTest
from logic.phef_calculator import PhefCalculator
from logic.singleton import Singleton
from services.military_service import MilitaryService
from services.service_mars import ServiceMars
from services.service_test import ServiceTest


class DataCollector(metaclass=Singleton):

    def __init__(self):
        self._service = ServiceTest()
        self._service_mars = ServiceMars()
        self.be_mil = MilitaryService()

    async def collect_tests_data_for_serial(self, serial: str, current_year=True) ->pd.DataFrame:
        rows: list[dict] = []

        # PHEF
        phef_sessions = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
            serial, TypeFitnessTest.PHEF, this_year=current_year
        )
        for sess in phef_sessions or []:
            phef_tests = sess.fitness_tests
            for t in phef_tests or []:
                if getattr(t, "serial_number", "") != serial:
                    continue

                mil = await self.be_mil.get_servicemen_by_serial(serial)
                if not mil:
                    continue
                age = mil.age_from_birthdate_and_session_date(sess.datetime_start)
                run_pts = PhefCalculator.running_result(
                    getattr(t, "running_time", 0) or 0, age, mil.gender
                )
                sbr_pts = PhefCalculator.side_bridge_result(
                    getattr(t, "sideBridge_r", 0) or 0, age, mil.gender
                )
                sbl_pts = PhefCalculator.side_bridge_result(
                    getattr(t, "sideBridge_l", 0) or 0, age, mil.gender
                )
                total = (run_pts * (50 / 20.0)) + ((sbr_pts + sbl_pts) * (25 / 20.0))
                rows.append(
                    {
                        "Date": (
                            "-"
                            if sess.datetime_start is None
                            else sess.datetime_start.strftime("%Y-%m-%d %H:%M")
                        ),
                        "Type": "PHEF",
                        "Run" : f"{t.running_time}",
                        "SBR": f"{t.sideBridge_r}",
                        "SBL": f"{t.sideBridge_l}",
                        "Run_points" : f"{run_pts}/20",
                        "SBR_points" : f"{sbr_pts}/20",
                        "SBL_points" : f"{sbl_pts}/20",
                        "Total": f"{total:.1f}/100",
                        "Result": "Passed" if total >= 50 else "Failed",

                    }
                )

        # Functional
        func_sessions = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(serial,
                                                                                                    TypeFitnessTest.FUNCTIONAL,
                                                                                                    this_year=current_year
                                                                                                    )
        for sess in func_sessions or []:
            func_tests = await sess.fitness_tests
            for t in func_tests or []:
                if getattr(t, "serial_number", "") != serial:
                    continue
                pu = int(getattr(t, "push_ups", 0) or 0)
                su = int(getattr(t, "sit_ups", 0) or 0)
                plu = int(getattr(t, "pull_ups", 0) or 0)
                total = pu + su + plu
                rows.append(
                    {
                        "Date": (
                            "-"
                            if sess.datetime_start is None
                            else sess.datetime_start.strftime("%Y-%m-%d %H:%M")
                        ),
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

        # Combat
        combat_sessions = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(serial,
                                                                                                      TypeFitnessTest.COMBAT,
                                                                                                      this_year=current_year
                                                                                                      )
        for sess in combat_sessions or []:
            tests = sess.fitness_tests
            for t in tests or []:
                if getattr(t, "serial_number", "") != serial:
                    continue
                rope = bool(getattr(t, "rope_passed", False))
                obstacle = bool(getattr(t, "obstacle_passed", False))
                run_s = int(getattr(t, "running_time", 0) or 0)
                passed = rope and obstacle and run_s <= 7200
                rows.append(
                    {
                        "Date": (
                            "-"
                            if sess.datetime_start is None
                            else sess.datetime_start.strftime("%Y-%m-%d %H:%M")
                        ),
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

        # Swimming
        swim_sessions = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(serial,
                                                                                                    TypeFitnessTest.SWIMMING,
                                                                                                    this_year=current_year
                                                                                                    )
        for sess in swim_sessions or []:
            tests = sess.fitness_tests
            for t in tests or []:
                if getattr(t, "serial_number", "") != serial:
                    continue
                ok = bool(getattr(t, "swim_paased", False))
                rows.append(
                    {
                        "Date": (
                            "-"
                            if sess.datetime_start is None
                            else sess.datetime_start.strftime("%Y-%m-%d %H:%M")
                        ),
                        "Type": "Swimming",
                        "Details": "Combat swim",

                        "Result": "Passed" if ok else "Failed",

                    }
                )

        # mars
        marses = await self._service_mars.get_mars_from_service_men(serial_number=serial, this_year=False)
        for mars in marses or []:
            ok = bool(getattr(mars, "succeeded", False))
            rows.append(
                {
                    "Date": mars.datetime_executed.strftime("%Y-%m-%d %H:%M"),
                    "Type": "Mars",
                    "Details": f"{mars.distance} Km",
                    "Result": "Passed" if ok else "Failed",
                }
            )

        if not rows:
            return pd.DataFrame(
                columns=[
                    "Date",
                    "Type",
                    "Details",
                    "Scores",
                    "Total",
                    "Result",

                ]
            )
        rows.sort(key=lambda r: r["Date"])
        return pd.DataFrame(rows)

    async def collect_tests_for_serial(self, serial: str,current_year=True) -> pd.DataFrame:

        rows: list[dict] = []

        # PHEF
        phef_sessions = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
           serial, TypeFitnessTest.PHEF,this_year=current_year
        )
        for sess in phef_sessions or []:
            phef_tests = sess.fitness_tests
            for t in phef_tests or []:
                if getattr(t, "serial_number", "") != serial:
                    continue

                mil = await self.be_mil.get_servicemen_by_serial(serial)
                if not mil:
                    continue
                age = mil.age_from_birthdate_and_session_date(sess.datetime_start)
                run_pts = PhefCalculator.running_result(
                    getattr(t, "running_time", 0) or 0, age, mil.gender
                )
                sbr_pts = PhefCalculator.side_bridge_result(
                    getattr(t, "sideBridge_r", 0) or 0, age, mil.gender
                )
                sbl_pts = PhefCalculator.side_bridge_result(
                    getattr(t, "sideBridge_l", 0) or 0, age, mil.gender
                )
                total = (run_pts * (50 / 20.0)) + ((sbr_pts + sbl_pts) * (25 / 20.0))
                rows.append(
                    {
                        "Date": (
                            "-"
                            if sess.datetime_start is None
                            else sess.datetime_start.strftime("%Y-%m-%d %H:%M")
                        ),
                        "Type": "PHEF",
                        "Details": f"Run {t.running_time}s, SBR {t.sideBridge_r}s, SBL {t.sideBridge_l}s",
                        "Scores": f"Run {run_pts}/20, SBR {sbr_pts}/20, SBL {sbl_pts}/20",
                        "Total": f"{total:.1f}/100",
                        "Result": "🟢 Passed" if total >= 50 else " 🔴 Failed",

                    }
                )

        # Functional
        func_sessions = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(serial,
            TypeFitnessTest.FUNCTIONAL,this_year=current_year
        )
        for sess in func_sessions or []:
            func_tests = await sess.fitness_tests
            for t in func_tests or []:
                if getattr(t, "serial_number", "") != serial:
                    continue
                pu = int(getattr(t, "push_ups", 0) or 0)
                su = int(getattr(t, "sit_ups", 0) or 0)
                plu = int(getattr(t, "pull_ups", 0) or 0)
                total = pu + su + plu
                rows.append(
                    {
                        "Date": (
                            "-"
                            if sess.datetime_start is None
                            else sess.datetime_start.strftime("%Y-%m-%d %H:%M")
                        ),
                        "Type": "Functional",
                        "Details": f"PU {pu}, SU {su}, PLU {plu}",
                        "Scores": f"PU {pu}, SU {su}, PLU {plu}",
                        "Total": f"{total}",
                         "Result": "🟢 Passed" if total >= 50 else " 🔴 Failed",

                    }
                )

        # Combat
        combat_sessions = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(serial,
            TypeFitnessTest.COMBAT,this_year=current_year
        )
        for sess in combat_sessions or []:
            tests =  sess.fitness_tests
            for t in tests or []:
                if getattr(t, "serial_number", "") != serial:
                    continue
                rope = bool(getattr(t, "rope_passed", False))
                obstacle = bool(getattr(t, "obstacle_passed", False))
                run_s = int(getattr(t, "running_time", 0) or 0)
                passed = rope and obstacle and run_s <= 7200
                rows.append(
                    {
                        "Date": (
                            "-"
                            if sess.datetime_start is None
                            else sess.datetime_start.strftime("%Y-%m-%d %H:%M")
                        ),
                        "Type": "Combat",
                        "Details": f"Rope {'OK' if rope else 'NO'}, Obstacle {'OK' if obstacle else 'NO'}, Speedmars {run_s}s",
                        "Scores": f"Rope {'OK' if rope else 'NO'}, Obstacle {'OK' if obstacle else 'NO'}",
                        "Total": "-",
                        "Result": "🟢 Passed" if passed else "🔴 Failed",

                    }
                )

        # Swimming
        swim_sessions = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(serial,
            TypeFitnessTest.SWIMMING,this_year=current_year
        )
        for sess in swim_sessions or []:
            tests =  sess.fitness_tests
            for t in tests or []:
                if getattr(t, "serial_number", "") != serial:
                    continue
                ok = bool(getattr(t, "swim_paased", False))
                rows.append(
                    {
                        "Date": (
                            "-"
                            if sess.datetime_start is None
                            else sess.datetime_start.strftime("%Y-%m-%d %H:%M")
                        ),
                        "Type": "Swimming",
                        "Details": "Combat swim",
                        "Scores": "-",
                        "Total": "-",
                        "Result": "🟢 Passed" if ok else "🔴 Failed",

                    }
                )


        #mars
        marses= await self._service_mars.get_mars_from_service_men(serial_number=serial,this_year=False)
        for mars in marses or []:
            ok = bool(getattr(mars, "succeeded", False))
            rows.append(
                {
                    "Date": mars.datetime_executed.strftime("%Y-%m-%d %H:%M"),
                    "Type": "Mars",
                    "Details": f"{mars.distance} Km",
                    "Scores": "-",
                    "Total": "-",
                    "Result": "🟢 Passed" if ok else "🔴 Failed",
                }
            )

        if not rows:
            return pd.DataFrame(
                columns=[
                    "Date",
                    "Type",
                    "Details",
                    "Scores",
                    "Total",
                    "Result",

                ]
            )
        rows.sort(key=lambda r: r["Date"])
        return pd.DataFrame(rows)

    async def collect_all_mil_from_own_unit_not_executed_phefs(self) -> pd.DataFrame:
        mil_series = await self.be_mil.get_all_be_mil_from_unit(
            ApplicationConfig().own_unit
        )
        rows = []
        for m in mil_series:
            mils: list[PhefTest] = await self._service.get_all_phef_mil(
                m.service_number
            )

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
        rows.sort(key=lambda r: r["Name"])
        return pd.DataFrame(rows)

    async def collect_all_mil_from_own_unit_failed_phefs(self) -> pd.DataFrame:
        mil_series = await self.be_mil.get_all_be_mil_from_unit(
            ApplicationConfig().own_unit
        )
        rows = []
        for m in mil_series:
            mils: list[PhefTest] = await self._service.get_all_phef_mil(
                m.service_number
            )

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
        rows.sort(key=lambda r: r["Name"])
        return pd.DataFrame(rows)

    async def collect_tests_data_for_own_unit(self) -> pd.DataFrame:
        own_unit = await self.be_mil.get_all_be_mil_from_unit(ApplicationConfig().own_unit)
        rows = []
        for m in own_unit:
            data_phef = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(m.service_number,
                                                                                                    TypeFitnessTest.PHEF)
            data_functional = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
                m.service_number, TypeFitnessTest.FUNCTIONAL)
            data_combat = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(m.service_number,
                                                                                                      TypeFitnessTest.COMBAT)
            data_swimming = await self._service.get_all_test_sessions_type_fitness_test_for_service_men(
                m.service_number, TypeFitnessTest.SWIMMING)
            data_mars = await self._service_mars.get_mars_from_service_men(serial_number=m.service_number,
                                                                           this_year=False)

            if data_phef and data_phef[0].fitness_tests:
                dt:PhefTest = data_phef[0].fitness_tests[0]
                tp =PhefCalculator.calculate_phef_score(dt.running_time, dt.sideBridge_l, dt.sideBridge_r, m.age_from_birthdate(), m.gender)
                phef_status = "Passed" if tp[4] else "Failed"
            else:
                phef_status = "Not Done"

            if data_combat and data_combat[0].fitness_tests:
                cmt = data_combat[0].fitness_tests[0]
                combat_status = "Passed" if cmt.rope_passed and cmt.obstacle_passed else "Failed"
            else:
                combat_status = "Not Done"
            if data_swimming and data_swimming[0].fitness_tests:
                dw=data_swimming[0].fitness_tests[0]
                swim_status = "Passed" if dw.swim_paased else "Failed"
            else:
                swim_status = "Not Done"
            if data_functional and data_functional[0].fitness_tests:
               dfd=data_functional[0].fitness_tests[0]
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


            rows.append({
                "Rank": m.rank,
                "Serial": m.service_number,
                "Name": f"{m.first_name} {m.last_name}",
                "Phef": phef_status,
                "Combat": combat_status,
                "Swimming": swim_status,
                "Functional": func_status,
                "Mars": mars_status
            })

        if not rows:
            return pd.DataFrame(columns=["Rank", "Serial","Name", "Phef", "Combat", "Swimming", "Functional", "Mars"])

        return pd.DataFrame(rows)
