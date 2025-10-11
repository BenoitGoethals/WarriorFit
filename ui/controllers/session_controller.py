from typing import List, Optional, Dict, Any

from shiny import ui, render, reactive

from config.appliccation_config import ApplicationConfig
from data.db.db_model import TestSession,Role

import datetime
import pandas as pd

from core.type_fitness_test import TypeFitnessTest
from services.be_mil_service import BEMILService
from services.db_service import DBService
from services.mail_service import MailService


class SessionsController:
    """
    Thin controller encapsulating data access and formatting for SessionsPage.
    Keeps UI/server code slimmer and easier to test.
    """
    def __init__(self, db_service: DBService, be_mil_service: BEMILService):
        self.db_service = db_service
        self.be_mil_service = be_mil_service

    # Data fetchers
    async def list_sessions(self) -> list[TestSession]:
        return await self.db_service.get_all_test_sessions()

    async def list_sessions_df(self) -> pd.DataFrame:
        items = await self.list_sessions()
        return pd.DataFrame(
            [
                {
                    "ID": r.id,
                    "Type": str(r.type_test.name),
                    "Start": str(r.datetime_start),
                    "Description": r.description,
                    "Serial PTI": r.serial_number_pti,
                    "Executed": "Yes" if r.executed else "No",
                }
                for r in items
            ]
        )

    async def get_all_pti_serials(self) -> List[str]:
        pts = await self.db_service.get_all_pti()
        return [p.serial_number for p in pts]

    async def add_session(self, payload: Dict[str, Any]) -> Optional[TestSession]:
        ts = TestSession()
        ts.serial_number_pti = payload["serial_number_pti"]
        ts.datetime_start = payload["datetime_start"]
        ts.executed = bool(payload["executed"])
        ts.description = payload["description"]
        # payload["type_test"] is a string name
        try:
            ts.type_test = getattr(TypeFitnessTest, str(payload["type_test"]).upper())
        except Exception:
            ts.type_test = TypeFitnessTest.PHEF
        return await self.db_service.add_test_session(ts)

    async def update_session(self, sel_id: int, payload: Dict[str, Any]) -> bool:
        # Accepts string name for type_test for convenience
        try:
            enum_type = getattr(TypeFitnessTest, str(payload["type_test"]).upper())
        except Exception:
            enum_type = TypeFitnessTest.PHEF
        data = TestSession(
            id=sel_id,
            type_test=enum_type,
            serial_number_pti=payload["serial_number_pti"],
            datetime_start=payload["datetime_start"],
            executed=bool(payload["executed"]),
            description=payload["description"],
        )
        return await self.db_service.update_test_session(data)

    async def delete_session(self, sel_id: int) -> bool:
        return await self.db_service.delete_test_session(sel_id)

    async def get_session_by_id(self, sel_id: int) -> Optional[TestSession]:
        return await self.db_service.get_test_session_by_id(sel_id)

    # Mail helpers
    async def recipients_for_unit(self) -> list[str]:
        return [r.mail for r in await self.be_mil_service.get_all_be_mil_from_unit(ApplicationConfig().own_unit)]

    def build_added_html(self, ts: TestSession) -> str:
        status_text = "Executed" if ts.executed else "Planned"
        dt_str = ts.datetime_start.strftime("%d/%m/%Y %H:%M")
        desc = ts.description or "No description provided"
        return f"""
            <h2>New Fitness Test Session Added</h2>
            <div style='background-color: #f5f5f5; padding: 20px; border-radius: 5px;'>
                <p><strong>Type:</strong> {ts.type_test.name}</p>
                <p><strong>Date & Time:</strong> {dt_str}</p>
                <p><strong>PTI Serial Number:</strong> {ts.serial_number_pti}</p>
                <p><strong>Status:</strong> {status_text}</p>
                <p><strong>Description:</strong> {desc}</p>
            </div>
            <p style='color: #666; font-size: 12px;'>This is an automated message from the Fitness Test Management System.</p>
        """

    def build_updated_html(self, ts: TestSession) -> str:
        status_text = "Executed" if ts.executed else "Planned"
        dt_str = ts.datetime_start.strftime("%d/%m/%Y %H:%M")
        desc = ts.description or "No description provided"
        typ = ts.type_test.name if hasattr(ts.type_test, "name") else str(ts.type_test)
        return f"""
            <h2>New Fitness Test Session Update</h2>
            <div style='background-color: #f5f5f5; padding: 20px; border-radius: 5px;'>
                <p><strong>Type:</strong> {typ}</p>
                <p><strong>Date & Time:</strong> {dt_str}</p>
                <p><strong>PTI Serial Number:</strong> {ts.serial_number_pti}</p>
                <p><strong>Status:</strong> {status_text}</p>
                <p><strong>Description:</strong> {desc}</p>
            </div>
            <p style='color: #666; font-size: 12px;'>This is an automated message from the Fitness Test Management System.</p>
        """

    def build_deleted_html(self, ts: TestSession) -> str:
        status_text = "Executed" if ts.executed else "Planned"
        dt_str = ts.datetime_start.strftime("%d/%m/%Y %H:%M")
        desc = ts.description or "No description provided"
        return f"""
            <h2>New Fitness Test Session Deleted</h2>
            <div style='background-color: #f5f5f5; padding: 20px; border-radius: 5px;'>
                <p><strong>Type:</strong> {ts.type_test.name}</p>
                <p><strong>Date & Time:</strong> {dt_str}</p>
                <p><strong>PTI Serial Number:</strong> {ts.serial_number_pti}</p>
                <p><strong>Status:</strong> {status_text}</p>
                <p><strong>Description:</strong> {desc}</p>
            </div>
            <p style='color: #666; font-size: 12px;'>This is an automated message from the Fitness Test Management System.</p>
        """

    def send_html(self, *, subject: str, html_body: str, to: list[str], invite: bool = False,
                  start_dt: datetime.datetime | None = None, end_dt: datetime.datetime | None = None,
                  organizer_name: str | None = None):
        MailService().send_html(
            subject=subject,
            html_body=html_body,
            from_email=ApplicationConfig().mail_server.sender_email,
            to=to,
        )
        if invite:
            MailService().send_with_calendar_invite(
                to=to,
                subject="Fitness Assessment Invite",
                html_body="Fitness Session scheduled for today. Please join the session at the following URL:",
                start=start_dt,
                end=end_dt,
                organizer_email=ApplicationConfig().mail_server.sender_email,
                organizer_name=organizer_name,
                location="Gym Hall",
            )
