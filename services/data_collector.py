import pandas as pd

from config.appliccation_config import ApplicationConfig
from core.type_fitness_test import TypeFitnessTest
from data.db.db_model import PhefTest
from logic.phef_calculator import PhefCalculator
from logic.singleton import Singleton
from services.be_mil_service import BEMILService
from services.service_test import ServiceTest


class DataCollector(metaclass=Singleton):

    def __init__(self):
        self._service = ServiceTest()
        self.be_mil = BEMILService()


    async def collect_tests_for_serial(self,serial: str) -> pd.DataFrame:
        # Load tests per type (current-year sessions in DBService)
        rows: list[dict] = []

        # PHEF
        phef_sessions = await self._service.get_all_test_sessions_type_fitness_test(TypeFitnessTest.PHEF, True)
        for sess in phef_sessions or []:
            phef_tests = await self._service.get_all_phef(sess.id)
            for t in phef_tests or []:
                if getattr(t, "serial_number", "") != serial:
                    continue
                # compute detailed scores
                mil = await self.be_mil.get_be_mil_by_id(serial)
                if not mil:
                    continue
                age = mil.age_from_birthdate_and_session_date(sess.datetime_start)
                run_pts = PhefCalculator.running_result(getattr(t, "running_time", 0) or 0, age, mil.gender)
                sbr_pts = PhefCalculator.side_bridge_result(getattr(t, "sideBridge_r", 0) or 0, age, mil.gender)
                sbl_pts = PhefCalculator.side_bridge_result(getattr(t, "sideBridge_l", 0) or 0, age, mil.gender)
                total = (run_pts * (50 / 20.0)) + ((sbr_pts + sbl_pts) * (25 / 20.0))
                rows.append({
                    "Date": "-" if sess.datetime_start is None else sess.datetime_start.strftime("%Y-%m-%d %H:%M"),
                    "Type": "PHEF",
                    "Details": f"Run {t.running_time}s, SBR {t.sideBridge_r}s, SBL {t.sideBridge_l}s",
                    "Scores": f"Run {run_pts}/20, SBR {sbr_pts}/20, SBL {sbl_pts}/20",
                    "Total": f"{total:.1f}/100",
                    "Result": "Passed" if total >= 50 else "Failed",
                    "Session ID": sess.id,
                    "Record ID": t.id,
                })

        # Functional
        func_sessions = await self._service.get_all_test_sessions_type_fitness_test(TypeFitnessTest.FUNCTIONAL, True)
        for sess in func_sessions or []:
            func_tests = await self._service.get_all_functional_test(sess.id)
            for t in func_tests or []:
                if getattr(t, "serial_number", "") != serial:
                    continue
                pu = int(getattr(t, "push_ups", 0) or 0)
                su = int(getattr(t, "sit_ups", 0) or 0)
                plu = int(getattr(t, "pull_ups", 0) or 0)
                total = pu + su + plu
                rows.append({
                    "Date": "-" if sess.datetime_start is None else sess.datetime_start.strftime("%Y-%m-%d %H:%M"),
                    "Type": "Functional",
                    "Details": f"PU {pu}, SU {su}, PLU {plu}",
                    "Scores": f"PU {pu}, SU {su}, PLU {plu}",
                    "Total": f"{total}",
                    "Result": "Passed" if total >= 50 else "Failed",
                    "Session ID": sess.id,
                    "Record ID": t.id,
                })

        # Combat
        combat_sessions = await self._service.get_all_test_sessions_type_fitness_test(TypeFitnessTest.COMBAT, True)
        for sess in combat_sessions or []:
            tests = await self._service.get_all_combat_test(sess.id)
            for t in tests or []:
                if getattr(t, "serial_number", "") != serial:
                    continue
                rope = bool(getattr(t, "rope_passed", False))
                obstacle = bool(getattr(t, "obstacle_passed", False))
                run_s = int(getattr(t, "running_time", 0) or 0)
                passed = rope and obstacle and run_s <= 7200
                rows.append({
                    "Date": "-" if sess.datetime_start is None else sess.datetime_start.strftime("%Y-%m-%d %H:%M"),
                    "Type": "Combat",
                    "Details": f"Rope {'OK' if rope else 'NO'}, Obstacle {'OK' if obstacle else 'NO'}, Speedmars {run_s}s",
                    "Scores": f"Rope {'OK' if rope else 'NO'}, Obstacle {'OK' if obstacle else 'NO'}",
                    "Total": "-",
                    "Result": "Passed" if passed else "Failed",
                    "Session ID": sess.id,
                    "Record ID": t.id,
                })

        # Swimming
        swim_sessions = await self._service.get_all_test_sessions_type_fitness_test(TypeFitnessTest.SWIMMING, True)
        for sess in swim_sessions or []:
            tests = await self._service.get_all_combat_swimming_test(sess.id)
            for t in tests or []:
                if getattr(t, "serial_number", "") != serial:
                    continue
                ok = bool(getattr(t, "swim_paased", False))
                rows.append({
                    "Date": "-" if sess.datetime_start is None else sess.datetime_start.strftime("%Y-%m-%d %H:%M"),
                    "Type": "Swimming",
                    "Details": "Combat swim",
                    "Scores": "-",
                    "Total": "-",
                    "Result": "Passed" if ok else "Failed",
                    "Session ID": sess.id,
                    "Record ID": t.id,
                })

        if not rows:
            return pd.DataFrame(
                columns=["Date", "Type", "Details", "Scores", "Total", "Result", "Session ID", "Record ID"])
        rows.sort(key=lambda r: r["Date"])
        return pd.DataFrame(rows)


    async def collect_all_mil_from_own_unit_not_executed_phefs(self) -> pd.DataFrame:
        mil_series = await self.be_mil.get_all_be_mil_from_unit(ApplicationConfig().own_unit)
        rows = []
        for m in mil_series:
            mils: list[PhefTest] = await self._service.get_all_phef_mil(m.service_number)


            if len(mils)==0:
                rows.append({
                    "Serial": m.service_number,
                    "Name": m.first_name + " " + m.last_name,
                    "Gender": m.gender,
                    "Age": m.age_from_birthdate(),
                    "Para" : m.para,

                })
        if not rows:
            return pd.DataFrame(
                columns=["Serial", "Name", "Gender", "Age","Para"])
        rows.sort(key=lambda r: r["Name"])
        return pd.DataFrame(rows)



    async def collect_all_mil_from_own_unit_failed_phefs(self) -> pd.DataFrame:
        mil_series = await self.be_mil.get_all_be_mil_from_unit(ApplicationConfig().own_unit)
        rows = []
        for m in mil_series:
            mils: list[PhefTest] = await self._service.get_all_phef_mil(m.service_number)

            passed=any([(PhefCalculator.calculate_phef_score(mil.running_time, mil.sideBridge_l, mil.sideBridge_r, m.age_from_birthdate(), m.gender)[4]) for mil in mils])
            if not passed:
                continue
            rows.append({
                "Serial": m.service_number,
                "Name": m.first_name + " " + m.last_name,
                "Gender": m.gender,
                "Age": m.age_from_birthdate(),
                "Para" : m.para,

            })
        if not rows:
            return pd.DataFrame(
                columns=["Serial", "Name", "Gender", "Age","Para"])
        rows.sort(key=lambda r: r["Name"])
        return pd.DataFrame(rows)



