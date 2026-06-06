# Python
from __future__ import annotations

import pandas as pd

from warriorfit.services.data_collector import DataCollector
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.report_generator_pdf import ReportGeneratorPdf


class IndTestShowController:
    """
    Controller class for managing military service and handling data collection.

    This class is designed to interact with a military service interface and
    asynchronously collect test data while ensuring data integrity. It provides
    methods for retrieving military service information based on a serial number
    and collecting test data into a Pandas DataFrame.

    :ivar be_mil: Instance of the MilitaryService class used to interact with
        military information.
    :type be_mil: MilitaryService
    """

    def __init__(
        self,
        mil_service: MilitaryService = None,
        data_collector: DataCollector = None,
        report_generator_pdf: ReportGeneratorPdf = None,
    ):
        self.be_mil = mil_service if mil_service is not None else MilitaryService()
        self._data_collector = data_collector if data_collector is not None else DataCollector()
        self._report_generator_pdf = (
            report_generator_pdf if report_generator_pdf is not None else ReportGeneratorPdf()
        )

    async def find_military(self, serial: str):
        """
        Retrieve military servicemen information by their serial number.

        This is an asynchronous method that queries a service to retrieve the
        information of a servicemen based on the provided serial number.
        The query is executed with a non-lazy fetching strategy.

        :param serial: The serial number of the servicemen to retrieve.
        :type serial: str
        :return: The servicemen information obtained from the service.
        :rtype: Any
        """
        return await self.be_mil.get_servicemen_by_serial(serial, lazy=False)

    async def collect_tests_df(self, serial: str) -> pd.DataFrame:
        """
        Asynchronously collects test data for a given serial number and returns it
        as a pandas DataFrame. If the collected data is not a DataFrame
        or an exception occurs, an empty DataFrame is returned.

        :param serial: A string representing the serial number for which the
            test data is to be collected.
        :return: A pandas DataFrame containing the test data for the given serial
            number, or an empty DataFrame if the data could not be collected.
        """
        try:
            df = await self._data_collector.collect_tests_for_serial(serial, current_year=False)
            return df if isinstance(df, pd.DataFrame) else pd.DataFrame()
        except Exception:
            return pd.DataFrame()
