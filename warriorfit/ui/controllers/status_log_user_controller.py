import pandas as pd
from sqlalchemy.orm import Mapped

from warriorfit.services.service_test import ServiceTest


class StatusLogUserController:
    """
    Handles user-related actions concerning status logs.

    This class is designed to work with user data and manage interactions related
    to retrieving and manipulating information on upcoming sessions. It uses
    the service layer to fetch necessary session details and formats them for
    consumption.

    """

    def __init__(self) -> None:
        self._service = ServiceTest()

    async def get_upcoming_session(
        self, serial_number_pti: Mapped[str]
    ) -> pd.DataFrame:
        """
        Retrieve upcoming session details for a given PTI serial number.

        Fetches the upcoming sessions related to the specified PTI serial number and
        returns a pandas DataFrame containing details of the sessions, including their
        date, type, and description. If no sessions are found, an empty DataFrame with
        the necessary columns is returned.

        :param serial_number_pti: The serial number of the PTI for which upcoming
            session details are being retrieved.
        :type serial_number_pti: str
        :return: A pandas DataFrame containing columns "Date", "Type", and "Description"
            with details of the upcoming sessions. An empty DataFrame if no sessions
            are found.
        :rtype: pandas.DataFrame
        """
        sessions = await self._service.get_upcoming_session_for_pti(serial_number_pti)
        if not sessions:
            return pd.DataFrame(columns=["Date", "Type", "Description"])
        data = []
        for s in sessions:
            type_str = (
                s.type_test.name if hasattr(s.type_test, "name") else str(s.type_test)
            )
            data.append(
                {
                    "Date": (
                        s.datetime_start.strftime("%Y-%m-%d %H:%M")
                        if s.datetime_start
                        else ""
                    ),
                    "Type": type_str,
                    "Description": s.description or "",
                }
            )

        return pd.DataFrame(data)
