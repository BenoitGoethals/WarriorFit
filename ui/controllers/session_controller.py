from typing import List, Optional, Dict, Any
from config.appliccation_config import ApplicationConfig
from data.db.db_model import TestSession
import datetime
import pandas as pd
from core.type_fitness_test import TypeFitnessTest

from services.mail_service import MailService
from services.military_service import MilitaryService
from services.service_test import ServiceTest


class SessionsController:
    """
    Thin controller encapsulating data access and formatting for SessionsPage.
    Keeps UI/server code slimmer and easier to test.
    """
    def __init__(self, ):
        self._service = ServiceTest()
        self.be_mil_service = MilitaryService()

    # Data fetchers
    async def list_sessions(self) -> list[TestSession]:
        return await self._service.get_all_test_sessions()

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
                    "Canceled": "Yes" if r.canceled else "No",
                }
                for r in items
            ]
        ).sort_values(by="Start", ascending=True)

    async def get_all_pti_serials(self) -> List[str]:
        pts = await self._service.get_all_pti()
        return [p.serial_number for p in pts]

    async def add_session(self, payload: Dict[str, Any]) -> Optional[TestSession]:
        ts = TestSession()
        ts.serial_number_pti = payload["serial_number_pti"]
        ts.datetime_start = payload["datetime_start"]
        ts.canceled = bool(payload["canceled"])
        ts.description = payload["description"]
        try:
            ts.type_test = getattr(TypeFitnessTest, str(payload["type_test"]).upper())
        except Exception:
            ts.type_test = TypeFitnessTest.PHEF
        sess= await self._service.add_test_session(ts)
        await self._send_html(subject=f"Fitness {ts.type_test.name} session added",html_body=self._build_added_html(sess),start_dt=sess.datetime_start,end_dt=sess.datetime_start+datetime.timedelta(hours=2),organizer_name=sess.serial_number_pti,invite=True,)
        return sess

    async def update_session(self, sel_id: int, payload: Dict[str, Any]) -> bool:
        try:
            enum_type = getattr(TypeFitnessTest, str(payload["type_test"]).upper())
        except Exception:
            enum_type = TypeFitnessTest.PHEF
        data = TestSession(
            id=sel_id,
            type_test=enum_type,
            serial_number_pti=payload["serial_number_pti"],
            datetime_start=payload["datetime_start"],
            canceled=bool(payload["canceled"]),
            description=payload["description"],
        )
        sess= await self._service.update_test_session(data)

        await self._send_html(subject=f"Update Fitness {sess.type_test.name} session added", html_body=self._build_updated_html(sess),
                              start_dt=sess.datetime_start, end_dt=sess.datetime_start + datetime.timedelta(hours=2),
                              organizer_name=sess.serial_number_pti, invite=True, )
        return sess

    async def delete_session(self, sel_id: int) -> bool:
        sess = await self._service.get_test_session_by_id(sel_id)
        success= await self._service.delete_test_session(sel_id)

        await self._send_html(subject=f"Delete Fitness {sess.type_test.name} session added",
                              html_body=self._build_deleted_html(sess),
                              start_dt=sess.datetime_start, end_dt=sess.datetime_start + datetime.timedelta(hours=2),
                              organizer_name=sess.serial_number_pti, invite=False, )
        return success

    async def get_session_by_id(self, sel_id: int|None) -> Optional[TestSession]:
        return await self._service.get_test_session_by_id(sel_id)


    async def _recipients_for_unit(self) -> list[str]:
        return [r.mail for r in await self.be_mil_service.get_all_be_mil_from_unit(ApplicationConfig().own_unit)]

    def _build_added_html(self, ts: TestSession) -> str:
        status_text = "Canceled" if ts.canceled else "Planned"
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

    def _build_updated_html(self, ts: TestSession) -> str:
        status_text = "Canceled" if ts.canceled else "Planned"
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

    def _build_deleted_html(self, ts: TestSession) -> str:
        status_text = "Canceled" if ts.canceled else "Planned"
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




    async def _send_html(self, *, subject: str, html_body: str,  invite: bool = False,
                  start_dt: datetime.datetime | None = None, end_dt: datetime.datetime | None = None,
                  organizer_name: str | None = None):
        MailService().send_html(
            subject=subject,
            html_body=html_body,
            from_email=ApplicationConfig().mail_server.sender_email,
            to=await self._recipients_for_unit(),
        )
        if invite:
            MailService().send_with_calendar_invite(
                to=await self._recipients_for_unit(),
                subject="Fitness Assessment Invite",
                html_body="Fitness Session scheduled",
                start=start_dt,
                end=end_dt,
                organizer_email=ApplicationConfig().mail_server.sender_email,
                organizer_name=organizer_name,
                location="Gym Hall",
            )
