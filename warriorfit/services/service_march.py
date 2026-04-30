from warriorfit.config.application_config import ApplicationConfig
from warriorfit.data.model.db_model import March, ServiceMen
from warriorfit.data.repositories.march_repository import MarchRepository
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service import Service
from warriorfit.services.notify_mail import NotifyMail


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

    def __init__(
        self,
        march_repository: MarchRepository = None,
        user_repository=None,
        military_service: MilitaryService = None,
        config=None,
        notify_mail=None,
    ):
        super().__init__(
            user_repository=user_repository,
            military_service=military_service,
            config=config,
        )
        self.__repo = (
            march_repository if march_repository is not None else MarchRepository()
        )
        self.be_mil_service = (
            military_service if military_service is not None else MilitaryService()
        )
        self._notify_mail = notify_mail

    async def get_all_march(self):
        """
        Retrieves all "March" records asynchronously from the repository.

        This method fetches all records related to "March" stored in the repository
        using an asynchronous approach. It acts as a wrapper to the underlying
        repository's functionality.

        :return: A collection of "March" records fetched from the repository.
        :rtype: Any
        """
        return await self.__repo.get_all_march()

    async def get_all_march_from_unit(self):
        """
        Retrieves all march records associated with the unit name configured
        in the application.

        This asynchronous method queries the repository to fetch march records
        that are linked to the unit name specified in the application
        configuration. It serves as an abstraction layer to separate data
        retrieval and business logic.

        :return: A list of march records corresponding to the unit name
                 in the configuration.
        :rtype: list
        """
        return await self.__repo.get_all_march_by_unit_name(
            ApplicationConfig().own_unit
        )

    async def get_march_by_id(self, ind_id):
        """
        Fetches the march by its unique ID.

        This asynchronous method retrieves a specific march based on the provided
        individual ID using the repository layer.

        :param ind_id: Unique identifier of the individual to fetch the march for.
        :type ind_id: int
        :return: An object representing the march corresponding to the provided ID.
        :rtype: Any
        """
        return await self.__repo.get_march_by_id(ind_id)

    async def get_march_from_service_men(
        self, serial_number, this_year=True
    ) -> list[March]:
        """
        Retrieves a list of March objects associated with service personnel based
        on the given serial number. Optionally, filters the results to include only
        those relevant to the current year.

        :param serial_number: The unique identifier of the service personnel for
            whom the March objects are to be retrieved.
        :param this_year: If set to True (default), filters the March objects to
            include only those relevant to the current year. If False, retrieves
            all March objects without year-specific filtering.
        :return: A list of March objects retrieved from the service personnel's
            data.
        :rtype: list[March]
        """
        return await self.__repo.get_all_march_form_service_men(
            serial_number, this_year
        )

    async def add_march(self, march: March):
        """
        Adds a new march to the repository, sends notifications, and logs the action.

        This method handles the process of adding a new march record to the repository,
        notifying the concerned serviceman via email, and adding an audit log for the action.

        :param march: The instance of the march record to be added.
        :type march: March
        :return: The newly added march instance.
        :rtype: March
        """
        from warriorfit.app import FitnessWarriorApp

        march = await self.__repo.add_march(march)  # type: ignore[assignment]
        sm = await self.be_mil_service.get_servicemen_by_serial(
            str(march.service_number)
        )

        body = self.build_email_body_march(march, sm)  # type: ignore[arg-type]

        await FitnessWarriorApp.get_broker().send_message(march)
        if body:
            notify = (
                self._notify_mail if self._notify_mail is not None else NotifyMail()
            )
            await notify.send_mail(body=body, subject="Result Test", to=str(sm.mail))  # type: ignore[union-attr]
        await self.add_audit_log(
            details=f"Fitness test {sm.service_number} added to March session {march.datetime_executed} {march.distance} ",  # type: ignore[union-attr]
            action="add",
        )

    async def delete_march(self, ind_march):
        """
        Deletes a march identified by its index.

        This asynchronous method interfaces with the repository to remove a specific
        march record from the data store.

        :param ind_march: Index or unique identifier of the march to be deleted.
        :type ind_march: int
        :return: A coroutine that completes when the deletion operation is performed.
        :rtype: Any
        """
        return await self.__repo.delete_march(ind_march)

    async def update_march(self, march):
        """
        Updates the given march object in the repository.

        This coroutine handles updating the provided `march` object by using the
        repository's update functionality. It ensures the persistence layer reflects
        the changes made to the `march` object.

        :param march: The march object to be updated.
        :return: A coroutine that resolves to the result of the update operation.
        """
        return await self.__repo.update_march(march)

    async def get_march_is_unique(self, service_number, distance, datetime_executed):
        """
        Checks if a march with the given parameters is unique in the repository.

        :param service_number: Unique identifier for the service.
        :type service_number: str
        :param distance: Distance associated with the march.
        :type distance: float
        :param datetime_executed: Date and time when the march was executed.
        :type datetime_executed: datetime
        :return: Boolean value indicating whether the march is unique.
        :rtype: bool
        """
        return await self.__repo.get_march_is_unique(
            service_number, distance, datetime_executed
        )

    def build_email_body_march(self, march: March, service_men: ServiceMen) -> str:
        """
        Builds the HTML body for an email summarizing the results of a march operation. The email
        includes details such as the distance covered and the overall success status of the operation.

        :param march: The instance representing the details of the march. It includes attributes
                      such as distance and success status (succeeded or failed).
        :type march: March
        :param service_men: The instance representing the team or personnel involved in the march.
                            Contains relevant data about the participants.
        :type service_men: ServiceMen
        :return: A string containing the HTML structure for the email body with formatted details
                 about the march operation.
        :rtype: str
        """
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
