import logging
from typing import Optional

from warriorfit.data.model.db_model import ServiceMen
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_march import ServiceMarch


class MarchController:
    """
    Controller for managing march-related operations.

    The `MarchController` class provides methods for performing asynchronous operations
    related to marches, such as retrieving, adding, updating, and deleting marches. It also
    includes functionality for searching military personnel by their serial number, interacting
    with the appropriate services.

    :ivar be_mil_service: Instance of `MilitaryService` used to perform operations
        related to servicemen.
    :type be_mil_service: MilitaryService
    """
    def __init__(self,) -> None:
        self._service = ServiceMarch()
        self.be_mil_service = MilitaryService()
        self._logger = logging.getLogger(__name__)

    async def get_all_march(self):
        """
        Retrieves all items or data related to "march" by leveraging a service function.

        This method asynchronously calls the `_service.get_all_march` method to fetch
        all relevant data.

        :return: A list or collection of data items provided by the service.
        :rtype: Any
        """
        return await self._service.get_all_march()

    async def add_march(self, new_march):
        """
        Initiates the addition of a new march by delegating it to the service layer.

        :param new_march: The march details to be added.
        :return: The result of the addition operation from the service.
        """
        return await self._service.add_march(new_march)

    async def update_march(self, updated_march):
        """
        Updates the March data asynchronously. This method relies on an external
        service to process the update and returns the awaited result.

        :param updated_march: New data for updating the March entry. The format
            and structure of the input data depends on the underlying service logic.
        :type updated_march: Any

        :return: The result of the update operation.
        :rtype: Any
        """
        return await self._service.update_march(updated_march)

    async def delete_march(self, current_id):
        """
        Deletes a march asynchronously based on the given identifier.

        This method utilizes the service layer to perform the deletion
        operation for the specified march. The operation is executed
        asynchronously, ensuring non-blocking behavior for the caller.

        :param current_id: Identifier for the march to be deleted.
        :type current_id: int
        :return: The result of the deletion operation.
        :rtype: Any
        """
        return await self._service.delete_march(current_id)

    async def search_military(self, serial_nr: str) -> Optional[ServiceMen]:
        """
        Searches for a serviceman in the military database using a given serial number.

        This asynchronous method retrieves a serviceman's record by invoking the
        get_servicemen_by_serial method on the be_mil_service instance. If the provided
        serial number is invalid or empty, the function returns None.

        :param serial_nr: A string representing the unique serial number of the serviceman.
        :return: An instance of ServiceMen if a match is found, otherwise None.
        """
        serial = (serial_nr or "").strip()
        if not serial:
            return None
        return await self.be_mil_service.get_servicemen_by_serial(serial)
