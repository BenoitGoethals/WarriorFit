from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.data.model.db_model import March, ServiceMen
from warriorfit.data.repositories.march_repository import MarchRepository

from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service import Service
from warriorfit.ui.pages.notify_mail import NotifyMail


class ServiceMarch(Service):
    """
    Provides functionalities to manage and interact with military march records.

    The ServiceMarch class provides various methods for retrieving, adding,
    updating, and deleting march records. It serves as an intermediary layer
    that interacts with a repository to perform database operations.

    :ivar be_mil_service: Represents the military service instance this class
        interacts with.
    :type be_mil_service: MilitaryService
    """

    def __init__(self):
        super().__init__()
        self.__repo = MarchRepository()
        self.be_mil_service = MilitaryService()

    async def get_all_march(self):
        return await self.__repo.get_all_march()

    async def get_all_march_from_unit(self):
        return await self.__repo.get_all_march_by_unit_name(
            ApplicationConfig().own_unit
        )

    async def get_march_by_id(self, ind_id):
        return await self.__repo.get_march_by_id(ind_id)

    async def get_march_from_service_men(
        self, serial_number, this_year=True
    ) -> list[March]:
        return await self.__repo.get_all_march_form_service_men(
            serial_number, this_year
        )

    async def add_march(self, march: March):
        from warriorfit.app import FitnessWarriorApp

        march = await self.__repo.add_march(march)
        sm = await self.be_mil_service.get_servicemen_by_serial(
            str(march.service_number)
        )

        body = self.build_email_body_march(march, sm)

        await FitnessWarriorApp.get_broker().send_message(march)
        if body:
            await NotifyMail().send_mail(
                body=body, subject="Result Test", to=str(sm.mail)
            )
        await self.add_audit_log(
            details=f"Fitness test {sm.service_number} added to March session {march.datetime_executed} {march.distance} ",
            action="add",
        )

    async def delete_march(self, ind_march):
        return await self.__repo.delete_march(ind_march)

    async def update_march(self, march):
        return await self.__repo.update_march(march)

    async def get_march_is_unique(self, service_number, distance, datetime_executed):
        return await self.__repo.get_march_is_unique(
            service_number, distance, datetime_executed
        )

    def build_email_body_march(self, march: March, service_men: ServiceMen) -> str:
        """Build HTML email body for march test results."""
        HEADER_STYLE = "background-color: #f2f2f2;"
        CELL_STYLE = "padding: 8px;"
        TEXT_LEFT = "text-align: left;"

        status_color = "green" if march.succeeded else "red"
        status_text = "PASSED" if march.succeeded else "FAILED"

        return f"""
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <thead>
                <tr style="{HEADER_STYLE}">
                    <th style="{CELL_STYLE} {TEXT_LEFT}">Test Component</th>
                    <th style="{CELL_STYLE} {TEXT_LEFT}">Result</th>
                    <th style="{CELL_STYLE} {TEXT_LEFT}">Status</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="{CELL_STYLE}">March</td>
                    <td style="{CELL_STYLE}">{march.distance} km</td>
                    <td style="{CELL_STYLE} color: {status_color}">
                        {status_text}
                    </td>
                </tr>
            </tbody>
        </table>
        """
