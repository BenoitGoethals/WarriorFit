from shiny import ui, reactive, render
import pandas as pd
from datetime import datetime

from warriorfit.data.model.db_model import March
from warriorfit.ui.controllers.march_controller import MarchController
from warriorfit.ui.pages.page import Page





class MarchPage(Page):

    def __init__(self):
        super().__init__()
        self.controller: MarchController = MarchController()

    def refresh(self):
        pass

    def get_ui(self):
        return ui.nav_panel(
            "March",
            ui.h2("🧪 March Tests"),
            ui.layout_columns(
                ui.div(
                    ui.card(
                        ui.div(
                            ui.input_text("service_number_march", "Service Number", placeholder="Service Number"),
                            ui.input_action_button("march_serial_search_btn", "🔍 Search own Unit", class_="btn-info btn-sm",
                                                  style="margin-top: 5px;"),
                        ),
                        ui.input_action_button("march_search", "Conform Serial", width="200px"),
                        ui.output_text("march_military"),
                        ui.br(),
                        ui.input_numeric("distance", "Distance (km)", value=30, min=0),
                        ui.input_date("datetime_executed", "Date Executed", value=str(datetime.now().date())),
                        ui.input_checkbox("succeeded", "Succeeded", value=False),
                        ui.br(),
                        ui.layout_columns(
                            ui.input_action_button("add_march_bn", "Add", class_="btn-primary w-100"),
                            ui.input_action_button("update_march_bn", "Update", class_="btn-warning w-100"),
                            ui.input_action_button("delete_march_bn", "Delete", class_="btn-danger w-100"),
                            ui.input_action_button("clear_march_bn", "Clear", class_="btn-secondary w-100"),
                            col_widths=(4,),
                        ),
                        ui.output_text("march_status"),
                        ui.br(),
                        full_screen=False,
                    ),
                ),
                ui.card(
                    ui.card_header("March Tests  (To pass the march)"),
                    ui.output_data_frame("march_grid"),
                    full_screen=False,
                ),
                col_widths=(4, 8),  # Records occupies ~2/3 width
            ),
        )

    def server(self, input, output, session):

        # State to track the ID of the currently selected row for Update/Delete
        selected_id = reactive.Value(None)
        status = reactive.Value("Ready.")
        # Reactive trigger to force grid refresh
        refresh_trigger = reactive.Value(0)
        military = reactive.Value("No selection")

        @output
        @render.text
        def march_status():
            return status.get()

        @output
        @render.text
        def march_military():
            return military.get()

        @reactive.Calc
        async def get_march_df():
            refresh_trigger.get()
            march_data = await self.controller.get_all_march()

            if not march_data:
                return pd.DataFrame(columns=["service_number", "distance", "succeeded", "datetime_executed"])

            # Convert list of march objects to DataFrame
            df = pd.DataFrame(
                [
                    {
                        "id": m.id,
                        "service_number": m.service_number,
                        "distance": m.distance,
                        "succeeded": m.succeeded,
                        "succeeded_display": "✓ Passed" if m.succeeded else "✗ Failed",
                        "datetime_executed": m.datetime_executed.date() if m.datetime_executed else None,
                    }
                    for m in march_data
                ]
            )

            return df

        @render.data_frame
        async def march_grid():
            try:
                df = await get_march_df()
                # Drop id and succeeded (keep succeeded_display instead)
                columns_to_drop = ["id", "succeeded"] if "id" in df.columns else ["succeeded"]
                display_df = df.drop(columns=columns_to_drop)
                display_df = display_df.sort_values(by=["service_number"])
                return render.DataGrid(display_df, selection_mode="row", filters=False, width="100%")
            except Exception as e:
                # Return empty grid on error
                empty_df = pd.DataFrame(columns=["service_number", "distance", "succeeded_display", "datetime_executed"])
                return render.DataGrid(empty_df, selection_mode="row", filters=False, width="100%")

        @reactive.Effect
        @reactive.event(input.march_grid_selected_rows)
        async def _fill_form_on_select():
            indices = input.march_grid_selected_rows()

            if indices:
                # Get the data from the reactive calc (this still contains "id")
                df = await get_march_df()
                df = df.sort_values(by=["service_number"])
                if df is not None and not df.empty:
                    row_idx = indices[0]
                    row = df.iloc[row_idx]
                    ui.update_action_button("add_march_bn", disabled=False)
                    ui.update_action_button("update_march_bn", disabled=False)
                    selected_id.set(row["id"] or "")
                    ui.update_text("service_number_march", value=str(row["service_number"]))
                    ui.update_numeric("distance", value=float(row["distance"]))
                    ui.update_checkbox("succeeded", value=bool(row["succeeded"]))
                    if row["datetime_executed"]:
                        ui.update_date("datetime_executed", value=row["datetime_executed"])
            else:
                ui.update_action_button("add_march_bn", disabled=True)
                ui.update_action_button("update_march_bn", disabled=True)



        @reactive.Effect
        @reactive.event(input.add_march_bn)
        async def _add():
            if not await valid_data():
                status.set("Invalid data.")
                return
            new_march = March(
                service_number=input.service_number_march(),
                distance=float(input.distance()),
                succeeded=input.succeeded(),
                datetime_executed=datetime.combine(input.datetime_executed(), datetime.min.time()),
            )

            await self.controller.add_march(new_march)
            _clear_form()
            refresh_trigger.set(refresh_trigger.get() + 1)

        async def valid_data()-> bool:
            # Check if combination of serial number, distance, and date is unique
            existing_march = await self.controller.get_march_is_unique(
                service_number=input.service_number_march(),
                distance=float(input.distance()),
                datetime_executed=datetime.combine(input.datetime_executed(), datetime.min.time()),
            )
            return existing_march

        @reactive.Effect
        @reactive.event(input.update_march_bn)
        async def _update():
            if not valid_data():
                status.set("Invalid data.")
                return
            current_id = selected_id.get()
            if current_id:
                # Construct object with ID for update
                updated_march = March(
                    id=current_id,
                    service_number=input.service_number_march(),
                    distance=float(input.distance()),
                    succeeded=input.succeeded(),
                    datetime_executed=datetime.combine(input.datetime_executed(), datetime.min.time()),
                )
                await self.controller.update_march(updated_march)
                _clear_form()
                refresh_trigger.set(refresh_trigger.get() + 1)

        @reactive.Effect
        @reactive.event(input.delete_march_bn)
        async def _delete():
            current_id = selected_id.get()
            if current_id:
                await self.controller.delete_march(current_id)
                _clear_form()
                refresh_trigger.set(refresh_trigger.get() + 1)

        def _clear_form():
            selected_id.set(None)
            ui.update_text("service_number_march", value="")
            ui.update_numeric("distance", value=30)
            ui.update_checkbox("succeeded", value=False)
            ui.update_date("datetime_executed", value=datetime.now().date())

        @reactive.Effect
        @reactive.event(input.clear_march_bn)
        def _on_clear():
            _clear_form()

        @reactive.effect
        @reactive.event(input.march_search, ignore_none=False)
        async def march_search():
            if input.service_number_march() is None:
                ui.update_action_button("add_march_bn", disabled=True)
                ui.update_action_button("update_march_bn", disabled=True)
                return
            try:
                val = await self.controller.search_military(input.service_number_march() or "")
                self.selected_military = val
                if val is None:
                    ui.update_text("march_combat_military", value="Not found")
                    ui.update_action_button("add_march_bn", disabled=True)
                    ui.update_action_button("update_march_bn", disabled=True)
                    return
                ui.update_action_button("add_march_bn", disabled=False)
                ui.update_action_button("update_march_bn", disabled=False)
                military.set(
                    f"{val.rank} {val.service_number} {val.first_name} {val.last_name} "
                    f"{val.gender} {val.age_from_birthdate()} years old"
                )
                ui.update_action_button("add_march_bn", disabled=False)
                ui.update_action_button("update_march_bn", disabled=False)
            except Exception:
                ui.update_text("march_combat_military", value="Not found")
                return

        # Serial number search modal
        @reactive.Effect
        @reactive.event(input.march_serial_search_btn)
        async def _open_serial_search_modal():
            modal_content = ui.modal(
                ui.card(
                    ui.card_header("Select Serial Number"),
                    ui.output_data_frame("march_serial_search_grid"),
                    full_screen=False,
                ),
                size="l",
                easy_close=True,
            )
            ui.modal_show(modal_content)

        @reactive.calc
        async def get_all_servicemen_df():
            servicemen = await self.controller.be_mil_service.get_all_service_men()
            if not servicemen:
                return pd.DataFrame(columns=["service_number", "first_name", "last_name", "gender"])

            df = pd.DataFrame(
                [
                    {
                        "service_number": s.service_number,
                        "first_name": s.first_name,
                        "last_name": s.last_name,
                        "gender": s.gender,
                    }
                    for s in servicemen
                ]
            )
            return df.sort_values(by=["service_number"])

        @render.data_frame
        async def march_serial_search_grid():
            df = await get_all_servicemen_df()
            return render.DataGrid(df, selection_mode="row", filters=True, width="100%")

        @reactive.Effect
        @reactive.event(input.march_serial_search_grid_selected_rows)
        async def _on_serial_selected():
            indices = input.march_serial_search_grid_selected_rows()
            if indices:
                df = await get_all_servicemen_df()
                if df is not None and not df.empty:
                    row_idx = indices[0]
                    row = df.iloc[row_idx]
                    ui.update_text("service_number_march", value=str(row["service_number"]))
                    ui.modal_remove()
                    #


_page = MarchPage()


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)