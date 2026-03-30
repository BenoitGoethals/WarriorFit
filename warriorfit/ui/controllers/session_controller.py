from typing import List, Optional, Dict, Any
from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.data.model.db_model import TestSession
import datetime
import pandas as pd
from warriorfit.core.type_fitness_test import TypeFitnessTest

from warriorfit.services.mail_service import MailService
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_test import ServiceTest


class SessionsController:
    """
    Handles operations related to managing fitness test sessions for the system.

    This class supports fetching, adding, updating, and deleting fitness test sessions. It also provides
    mechanisms to send notifications and manage session details. The class interacts with external services
    to complete its operations and is designed to handle asynchronous workflows.

    :ivar be_mil_service: Service responsible for interacting with military personnel data.
    :type be_mil_service: MilitaryService
    """

    def __init__(
        self,
        service: ServiceTest = None,
        mil_service: MilitaryService = None,
    ):
        self._service = service if service is not None else ServiceTest()
        self.be_mil_service = (
            mil_service if mil_service is not None else MilitaryService()
        )

    # Data fetchers
    async def list_sessions(self) -> list[TestSession]:
        return await self._service.get_all_test_sessions()

    async def list_sessions_df(self) -> pd.DataFrame:
        """
        Asynchronously retrieves a DataFrame representation of session data.

        This method fetches a list of sessions and transforms the results into a
        pandas DataFrame. The DataFrame includes detailed information about each
        session, such as unique identifiers, session type, start datetime,
        a description, serial number, and whether the session was canceled.
        The resulting DataFrame is sorted by the session start datetime in
        ascending order.

        :return: DataFrame containing session data with the following columns:
            - ID: Unique identifier for the session
            - Type: Type of the session
            - Start: Start datetime of the session
            - Description: Description of the session
            - Serial PTI: Serial number for PTI
            - Canceled: Whether the session was canceled ("Yes" or "No")
        :rtype: pd.DataFrame
        """
        items = await self.list_sessions()
        if not items:
            return pd.DataFrame(
                columns=["ID", "Type", "Start", "Description", "Serial PTI", "Canceled"]
            )
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

    async def get_all_pti_choices(self) -> Dict[str, str]:
        """Returns a dict mapping serial_number to 'serial - username' for display"""
        pts = await self._service.get_all_pti()
        return {
            p.serial_number: f"{p.serial_number} - {p.username}"
            for p in pts
            if p.serial_number
        }

    async def add_session(self, payload: Dict[str, Any]) -> Optional[TestSession]:
        """
        Asynchronously adds a new test session based on the provided payload. The method
        parses the input payload to configure a new test session, determines the type of the
        test, and interacts with the service layer to store the session in the system. It also
        sends an email concerning the new session to the appropriate recipients including
        session details.

        :param payload: Dictionary containing session details such as serial number, start datetime,
            cancellation status, description, and type of the fitness test. Keys and expected
            values are:
                - serial_number_pti (str): Serial number of the test session initiator.
                - datetime_start (datetime): Start date and time of the test session.
                - canceled (bool): True if the session was canceled, False otherwise.
                - description (str): Description or notes regarding the fitness session.
                - type_test (str): String representing the type of fitness test.

        :return: An instance of TestSession containing information about the added session
            if successfully created, otherwise None.
        :rtype: Optional[TestSession]
        """
        ts = TestSession()
        ts.serial_number_pti = payload["serial_number_pti"]
        ts.datetime_start = payload["datetime_start"]
        ts.canceled = bool(payload["canceled"])
        ts.description = payload["description"]
        try:
            ts.type_test = getattr(TypeFitnessTest, str(payload["type_test"]).upper())
        except Exception:
            ts.type_test = TypeFitnessTest.PHEF
        sess = await self._service.add_test_session(ts)
        await self._send_html(
            subject=f"Fitness {ts.type_test.name} session added",
            html_body=self._build_added_html(sess),
            start_dt=sess.datetime_start,
            end_dt=sess.datetime_start + datetime.timedelta(hours=2),
            organizer_name=sess.serial_number_pti,
            invite=True,
        )
        return sess

    async def update_session(self, sel_id: int, payload: Dict[str, Any]) -> bool:
        """
        Updates a fitness test session with new information and sends an HTML-based
        notification email after the session update is completed.

        The method receives an identifier for the session to update and a payload
        containing the new session information. It updates the session using the data
        provided, determines the session type, and sends an email with the session
        details if the update is successful.

        In case the session type is not found in the payload, it defaults to a specific
        type (`TypeFitnessTest.PHEF`). Additional details, such as event start time
        and organizer name, are utilized for the email notification.

        :param sel_id: Unique identifier of the session to update
        :type sel_id: int
        :param payload: Dictionary containing updated attributes of the session
        :type payload: Dict[str, Any]
        :return: Whether the session update operation was successful
        :rtype: bool
        """
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
        sess = await self._service.update_test_session(data)

        await self._send_html(
            subject=f"Update Fitness {sess.type_test.name} session added",
            html_body=self._build_updated_html(sess),
            start_dt=sess.datetime_start,
            end_dt=sess.datetime_start + datetime.timedelta(hours=2),
            organizer_name=sess.serial_number_pti,
            invite=True,
        )
        return sess

    async def delete_session(self, sel_id: int) -> bool:
        """
        Deletes a test session by session ID asynchronously. This function retrieves the relevant session
        information, deletes it from the service, and sends a notification email summarizing the deletion.

        :param sel_id: The ID of the test session to be deleted.
        :type sel_id: int
        :return: A boolean indicating whether the deletion was successful.
        :rtype: bool
        """
        sess = await self._service.get_test_session_by_id(sel_id)
        success = await self._service.delete_test_session(sel_id)

        await self._send_html(
            subject=f"Delete Fitness {sess.type_test.name} session added",
            html_body=self._build_deleted_html(sess),
            start_dt=sess.datetime_start,
            end_dt=sess.datetime_start + datetime.timedelta(hours=2),
            organizer_name=sess.serial_number_pti,
            invite=False,
        )
        return success

    async def get_session_by_id(self, sel_id: int | None) -> Optional[TestSession]:
        """
        Retrieve a test session by its unique identifier.

        This method asynchronously fetches a test session based on the specified
        selection identifier. If a valid session is found, it will return the session
        object; otherwise, it may return None.

        :param sel_id: A unique identifier for the targeted test session. If None,
            no identifier is specified, and the method may return None.
        :return: An optional `TestSession` object if a session with the given
            identifier exists, otherwise returns None.
        """
        return await self._service.get_test_session_by_id(sel_id)

    async def _recipients_for_unit(self) -> list[str]:
        results = await self.be_mil_service.get_all_be_mil_from_unit(
            ApplicationConfig().own_unit
        )
        if not results:
            return []
        return [r.mail for r in results if r.mail]

    def _build_added_html(self, ts: TestSession) -> str:
        """
        Generates an HTML string summarizing a newly added fitness test session.

        :param ts: An instance of `TestSession` containing details of the fitness
            test session.
        :type ts: TestSession
        :return: A formatted HTML string providing details about the fitness test
            session, including type, date and time, PTI serial number, status,
            and description.
        :rtype: str
        """
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
        """
        Builds an updated HTML content string for a fitness test session based on the provided session
        details, including type, date and time, status, and description.

        :param ts: TestSession object containing details about the fitness test session.
        :type ts: TestSession
        :return: A formatted HTML string representing an updated fitness test session.
        :rtype: str
        """
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
        """
        Generates an HTML string representation of a deleted fitness test session, providing key
        details such as session type, date and time, PTI serial number, status, and description.

        :param ts: The TestSession instance containing session information
        :type ts: TestSession
        :return: A string containing the formatted HTML representation of the deleted session
        :rtype: str
        """
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

    async def _send_html(
        self,
        *,
        subject: str,
        html_body: str,
        invite: bool = False,
        start_dt: datetime.datetime | None = None,
        end_dt: datetime.datetime | None = None,
        organizer_name: str | None = None,
    ):
        """
        Sends an HTML email and optionally includes a calendar invite.

        This asynchronous method sends an HTML email to a list of recipients. If the
        `invite` parameter is set to `True`, it also sends a calendar invite for an
        event. All required parameters for scheduling the event should be provided
        when using the `invite` feature.

        :param subject: The subject of the email.
        :type subject: str
        :param html_body: The HTML content to include in the body of the email.
        :type html_body: str
        :param invite: Whether to include a calendar invitation in the email.
                       Defaults to False.
        :type invite: bool
        :param start_dt: The start datetime of the event for the calendar invite.
        :type start_dt: Optional[datetime.datetime]
        :param end_dt: The end datetime of the event for the calendar invite.
        :type end_dt: Optional[datetime.datetime]
        :param organizer_name: The name of the organizer for the event invite.
        :type organizer_name: Optional[str]
        :return: None
        :rtype: None
        """
        recipients = await self._recipients_for_unit()
        if not recipients:
            return
        MailService().send_html(
            subject=subject,
            html_body=html_body,
            from_email=ApplicationConfig().mail_server.sender_email,
            to=recipients,
        )
        if invite:
            MailService().send_with_calendar_invite(
                to=recipients,
                subject="Fitness Assessment Invite",
                html_body="Fitness Session scheduled",
                start=start_dt,
                end=end_dt,
                organizer_email=ApplicationConfig().mail_server.sender_email,
                organizer_name=organizer_name,
                location="Gym Hall",
            )
