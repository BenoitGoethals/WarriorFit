from shiny import ui, render, reactive
import pandas as pd

from ui.services.db_service import DBService
from ui.services.be_mil_service import BEMILService
from core.type_fitness_test import TypeFitnessTest
from data.db.db_model import PhefTest, FunctionalTest, CombatTestParatrooper, CombatSwimmingTest
from logic.phef_calculator import PhefCalculator


class IndTestShowPage:
    def __init__(self, db: DBService):
        self.db = db
        self.be_mil = BEMILService()
        self.refresh_tick = reactive.Value(0)
        self.serial = reactive.Value("")
        self.mil_info = reactive.Value("No serviceman selected.")
        self.tests_df = reactive.Value(pd.DataFrame())

    def get_ui(self):
        return ui.nav_panel(
            "Individual",
            ui.h2("Individual Test History"),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Lookup"),
                    ui.input_text("ind_serial", "Serial number"),
                    ui.input_action_button("ind_search", "Search", width="150px"),
                    ui.br(),
                    ui.output_text("ind_status"),
                    ui.hr(),
                    ui.h4("Serviceman"),
                    ui.output_text("ind_mil_info"),
                    full_screen=False,
                ),
                ui.card(
                    ui.card_header("Test history"),
                    ui.output_data_frame("ind_grid"),
                    full_screen=True,
                ),
                col_widths=(4, 8),
            ),
        )

    def server(self, input, output, session):
        status = reactive.Value("Ready.")

        async def _collect_tests_for_serial(serial: str) -> pd.DataFrame:
            # Load tests per type (current-year sessions in DBService)
            rows: list[dict] = []

            # PHEF
            phef_sessions = await self.db.get_all_test_sessions_type_fitnessTest(TypeFitnessTest.PHEF)
            for sess in phef_sessions or []:
                phef_tests = await self.db.get_all_phef(sess.id)
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
            func_sessions = await self.db.get_all_test_sessions_type_fitnessTest(TypeFitnessTest.FUNCTIONAL)
            for sess in func_sessions or []:
                func_tests = await self.db.get_all_functional_test(sess.id)
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
            combat_sessions = await self.db.get_all_test_sessions_type_fitnessTest(TypeFitnessTest.COMBAT)
            for sess in combat_sessions or []:
                tests = await self.db.get_all_combat_test(sess.id)
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
            swim_sessions = await self.db.get_all_test_sessions_type_fitnessTest(TypeFitnessTest.SWIMMING)
            for sess in swim_sessions or []:
                tests = await self.db.get_all_combat_swimming_test(sess.id)
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
                return pd.DataFrame(columns=["Date", "Type", "Details", "Scores", "Total", "Result", "Session ID", "Record ID"])
            rows.sort(key=lambda r: r["Date"])
            return pd.DataFrame(rows)

        @reactive.effect
        @reactive.event(input.ind_search, ignore_none=False)
        async def _on_search():
            s = (input.ind_serial() or "").strip()
            if not s:
                status.set("Enter a serial number.")
                self.mil_info.set("No serviceman selected.")
                self.tests_df.set(pd.DataFrame())
                return
            try:
                mil = await self.be_mil.get_be_mil_by_id(s)
                self.serial.set(s)
                self.mil_info.set(f"{mil.rank} {mil.first_name} {mil.last_name} — {mil.service_number} — {mil.unit}")
                df = await _collect_tests_for_serial(s)
                self.tests_df.set(df)
                status.set(f"Loaded {len(df)} records." if not df.empty else "No tests found.")
            except Exception:
                self.serial.set("")
                self.mil_info.set("Not found.")
                self.tests_df.set(pd.DataFrame())
                status.set("Serviceman not found.")

        @output
        @render.text
        def ind_status():
            return status.get()

        @output
        @render.text
        def ind_mil_info():
            return self.mil_info.get()

        @output
        @render.data_frame
        def ind_grid():
            return render.DataGrid(
                self.tests_df.get(),
                filters=False,
                selection_mode="none",
            )


_page = IndTestShowPage(DBService("ui/config/config.yml"))

def get_ui():
    return _page.get_ui()

def server(input, output, session):
    _page.server(input, output, session)