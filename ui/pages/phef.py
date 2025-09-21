from shiny import ui, render, reactive
import pandas as pd

from core.type_fitness_test import TypeFitnessTest
from ui.services.db_service import DBService
from ..user_store import UserStore

class PhefPage:
    def __init__(self, db: DBService):
        self.db = db


    def get_ui(self):
        if UserStore.get_user():
            return ui.nav_panel(
                "PHEF Tests",
                ui.h2("🧪 PHEF Tests"),
                ui.layout_columns(
                    ui.div(
                        ui.card(
                            ui.card_header("Session"),
                            ui.input_select("ph_session_id", "Session", choices=[]),

                            full_screen=False,
                        ),
                        ui.card(
                            ui.card_header("Add / Edit PHEF Test"),
                            ui.input_text("ph_serialnr", "Serial Number"),
                            ui.input_text(
                                "ph_side_bridge_r",
                                "Side-bridge Right time (mm:ss)",
                                placeholder="e.g., 2:30",
                            ),
                            ui.input_text(
                                "ph_side_bridge_l",
                                "Side-bridge time Left (mm:ss)",
                                placeholder="e.g., 2:30",
                            ),
                            ui.input_text(
                                "ph_run_2400",
                                "2400m run time (mm:ss)",
                                placeholder="e.g., 10:45 ",
                            ),
                            ui.br(),
                            ui.layout_columns(
                                ui.input_action_button("ph_add_btn", "Add"),
                                ui.input_action_button("ph_update_btn", "Update"),
                                ui.input_action_button("ph_clear_btn", "Clear Form"),
                                col_widths=(4,),
                            ),
                            ui.br(),
                        #    ui.output_text("ph_status"),
                            full_screen=False,
                        ),
                    ),
                    ui.card(
                        ui.card_header("Records"),
                        ui.output_data_frame("ph_grid"),
                        ui.br(),
                        ui.layout_columns(
                            ui.input_action_button("ph_delete_btn", "Delete Selected"),
                            col_widths=(6, 3, 3),
                        ),
                        full_screen=False,
                    ),
                    col_widths=(4, 8),  # Records occupies ~2/3 width
                ),
            )
        return None

    def server(self, input, output, session):
        # Reactive state
        records = reactive.Value([])

        status = reactive.Value("Ready.")
        selected_session_id = reactive.Value("")  # track current selection

        def _parse_time_to_seconds(val: str):
            txt = (val or "").strip()
            if not txt:
                return False, "Time value is required."
            try:
                if ":" in txt:
                    parts = txt.split(":")
                    if len(parts) != 2:
                        return False, "Time must be in mm:ss or seconds."
                    m = int(parts[0]); s = int(parts[1])
                    total = m * 60 + s
                else:
                    total = int(float(txt))
                if total <= 0:
                    return False, "Time must be positive."
                return True, int(total)
            except Exception:
                return False, "Time must be numeric (mm:ss or seconds)."

        def _format_seconds(sec: int):
            m = sec // 60
            s = sec % 60
            return f"{m}:{s:02d}"



        def _validate(data):
            if not (data["serialnr"] or "").strip():
                return False, "Serial number is required."
            if not (data["session_id"] or "").strip():
                return False, "Session selection is required."

            ok_sbr, sbr = _parse_time_to_seconds(data["side_bridge_r"])
            if not ok_sbr:
                return False, f"Side-bridge Right: {sbr}"
            ok_sbl, sbl = _parse_time_to_seconds(data["side_bridge_l"])
            if not ok_sbl:
                return False, f"Side-bridge Left: {sbl}"
            ok_run, run = _parse_time_to_seconds(data["run_2400"])
            if not ok_run:
                return False, f"2400m run: {run}"
            return True, {
                "session_id_int": int(data["session_id"]),
                "side_bridge_r_s": sbr,
                "side_bridge_l_s": sbl,
                "run2400_s": run,
            }

        def _read_form():
            return {
                "serialnr": (input.ph_serialnr() or "").strip(),
                "session_id": (input.ph_session_id() or "").strip(),
                "side_bridge_r": (input.ph_side_bridge_r() or "").strip(),
                "side_bridge_l": (input.ph_side_bridge_l() or "").strip(),
                "run_2400": (input.ph_run_2400() or "").strip(),
            }

        def _write_form(rec):
            session.send_input_message("ph_serialnr", {"value": rec.get("serialnr", "")})
            session.send_input_message(
                "ph_session_id",
                {"value": "" if rec.get("session_id") is None else str(rec.get("session_id"))},
            )
            sbr_val = rec.get("side_bridge_r_s")
            sbl_val = rec.get("side_bridge_l_s")
            run_val = rec.get("run2400_s")
            session.send_input_message("ph_side_bridge_r", {"value": "" if sbr_val is None else _format_seconds(sbr_val)})
            session.send_input_message("ph_side_bridge_l", {"value": "" if sbl_val is None else _format_seconds(sbl_val)})
            session.send_input_message("ph_run_2400", {"value": "" if run_val is None else _format_seconds(run_val)})

        def _clear_form():
            _write_form({
                "serialnr": "",
                "session_id": None,
                "side_bridge_r_s": None,
                "side_bridge_l_s": None,
                "run2400_s": None
            })

        # Populate sessions into the select input, preserving current selection when possible
        async def _refresh_session_choices():
            test_sessions = await self.db.get_all_test_sessions_type_fitnessTest(TypeFitnessTest.PHEF)
            items = [
                s.datetime_start.strftime("%Y-%m-%d %H:%M")+" "+s.type_test.name
                for s in test_sessions
            ]
            ui.update_select("ph_session_id", choices=items, )

        def _refresh_record_select():
            # No UI select exists for records; keep for future use if needed.
            pass

        @output
        @render.text
        def ph_status():
            return status.get()

        @reactive.calc
        async def sessions_phef__data():
            return pd.DataFrame([
                {
                    "ID": r.id,
                    "Serial": r.serial_number,
                    "runningTime": r.running_time,
                    "SidebridgeR": r.sideBridge_r,
                    "SidebridgeL": r.sideBridge_l,
                }
                for r in await self.db.get_all_phef()
            ])

        @output
        @render.data_frame
        async def ph_grid():
            df = await sessions_phef__data()
            return render.DataGrid(
                df,
                filters=True,
                selection_mode="rows",
            )

        # Single async initializer to avoid resetting choices
        @reactive.Effect
        async def _init():
            await _refresh_session_choices()
            _refresh_record_select()

        @reactive.Effect
        def _on_session_change():
            # Track selection changes
            val = (input.ph_session_id() or "").strip()
            selected_session_id.set(val)

        @reactive.Effect
        @reactive.event(input.ph_add_btn)
        def _on_add():
            data = _read_form()
            ok, res = _validate(data)
            if not ok:
                status.set(res)
                return

            # Placeholder: local-only add (no DB persistence implemented here)
            new_id = max([r["id"] for r in records.get()] + [0]) + 1
            record = {
                "id": new_id,
                "serialnr": data["serialnr"],
                "session_id": res["session_id_int"],
                "side_bridge_r_s": res["side_bridge_r_s"],
                "side_bridge_l_s": res["side_bridge_l_s"],
                "run2400_s": res["run2400_s"],
            }
            records.set(records.get() + [record])
            status.set(f"Added PHEF test #{new_id} for {record['serialnr']} in session {record['session_id']}.")
            _clear_form()

        @reactive.Effect
        @reactive.event(input.ph_update_btn)
        def _on_update():
            # Without a record selection UI, this is a placeholder
            status.set("Update not implemented without a record selection. Use grid selection + edit flow if added.")

        @reactive.Effect
        @reactive.event(input.ph_delete_btn)
        async def _on_delete():
            sel = input.ph_grid_selected_rows()
            if not sel:
                status.set("Select a row to delete.")
                return
            df = await sessions_phef__data()
            # Placeholder: dataset is coming from DB; deletion not implemented here
            try:
                row_idx = sel[0]
                row = df.iloc[row_idx]
                status.set(f"Delete not implemented in UI yet for record ID {row['ID']}.")
            except Exception:
                status.set("Invalid selection.")

        @reactive.Effect
        @reactive.event(input.ph_clear_btn)
        def _on_clear():
            _clear_form()
            status.set("Form cleared.")

# Public API: keep same signatures
_page = PhefPage(DBService("ui/config/config.yml"))

def get_ui():
    return _page.get_ui()

def server(input, output, session):
    _page.server(input, output, session)