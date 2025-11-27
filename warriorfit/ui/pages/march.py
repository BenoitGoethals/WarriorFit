from shiny import ui, reactive, render
import pandas as pd
from datetime import datetime

from warriorfit.data.db.db_model import March
from warriorfit.ui.controllers.march_controller import MarchController


class marchPage:

    def __init__(self):
        self.controller:MarchController = MarchController()

    def get_ui(self):

        return ui.nav_panel(
            "March",
            ui.h2("🧪 March Tests"),
            ui.layout_columns(
                ui.div(
                     ui.card(

                         ui.input_text("service_number_march", "Service Number", placeholder="Service Number"),
                         ui.input_action_button("march_search", "Conform Serial", width="150px"),
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
                       ui.output_text("march_status", ),
                        ui.br(),
                        #  ui.output_text("march_status"),
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
        military = reactive.Value("")

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
            # Establish dependency on the trigger
            refresh_trigger.get()

            # Fetch data using the controller
            march_data = await self.controller.get_all_march()

            if not march_data:
                return pd.DataFrame(columns=["service_number", "distance", "succeeded", "datetime_executed"])

            # Convert list of march objects to DataFrame
            df = pd.DataFrame([
                {
                    "id": m.id,
                    "service_number": m.service_number,
                    "distance": m.distance,
                    "succeeded": m.succeeded,
                    "datetime_executed": m.datetime_executed.date() if m.datetime_executed else None
                }
                for m in march_data
            ])

            # Set the 'id' column as the index to keep it in the DataFrame but hide it from view


            return df
        @render.data_frame
        async def march_grid():
            df = await get_march_df()
            return render.DataGrid(df, selection_mode="row",filters=False, width="100%")

        @reactive.Effect
        @reactive.event(input.march_grid_selected_rows)
        async def _fill_form_on_select():
            indices = input.march_grid_selected_rows()

            if indices:
                # Get the data from the reactive calc
                df = await get_march_df()
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
            new_march = March(
                service_number=input.service_number_march(),
                distance=float(input.distance()),
                succeeded=input.succeeded(),
                datetime_executed=datetime.combine(input.datetime_executed(), datetime.min.time())
            )
            await self.controller.add_march(new_march)
            _clear_form()
            refresh_trigger.set(refresh_trigger.get() + 1)

        @reactive.Effect
        @reactive.event(input.update_march_bn)
        async def _update():
            current_id = selected_id.get()
            if current_id:
                # Construct object with ID for update
                updated_march = March(
                    id=current_id,
                    service_number=input.service_number_march(),
                    distance=float(input.distance()),
                    succeeded=input.succeeded(),
                    datetime_executed=datetime.combine(input.datetime_executed(), datetime.min.time())
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
            if input.service_number_march() is None :
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
                military.set(val.rank + " " + val.service_number + " " + val.first_name + " " + val.last_name)
                ui.update_action_button("add_march_bn", disabled=False)
                ui.update_action_button("update_march_bn", disabled=False)
            except Exception:
                ui.update_text("march_combat_military", value="Not found")
                return


_page = marchPage()


def get_ui():
    return _page.get_ui()


def server(input, output, session):
    _page.server(input, output, session)