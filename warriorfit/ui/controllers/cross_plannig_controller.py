from datetime import datetime
from typing import Dict, Optional

from warriorfit.data.model.db_model import Cross
from warriorfit.services.service_cross import ServiceCross


class CrossPlanningController:
    """
    Manages the creation, retrieval, update, and deletion of cross entities within the planning system.

    This class acts as a controller to handle cross-related operations. It operates by utilizing
    a service layer to manage data storage and retrieval, providing an interface for working with
    crosses. Crosses represent scheduled or executed events with additional metadata such as
    descriptions and distances.

    :ivar _service: Service layer object responsible for accessing and manipulating cross data.
    :type _service: ServiceCross
    """

    def __init__(
        self,
        service: ServiceCross = None,
    ):
        self._service = service if service is not None else ServiceCross()

    # --- CRUD Cross ---
    async def create_cross(
        self,
        *,
        datetime_start: datetime,
        executed: bool = False,
        description: str | None = None,
        distance: float | None = None,
    ):
        """
        Creates a new cross instance and schedules it for storage. Returns a view of the created cross.

        This asynchronous method initializes and stores a `Cross` object with the provided attributes.
        After the cross is added, it retrieves and returns its detailed view.

        :param datetime_start: The starting date and time for the cross.
        :type datetime_start: datetime
        :param executed: Whether the cross has been executed. Defaults to ``False``.
        :type executed: bool
        :param description: An optional textual description of the cross. Defaults to ``None``.
        :type description: str | None
        :param distance: An optional distance value associated with the cross. Defaults to ``None``.
        :type distance: float | None
        :return: A dictionary representing the view of the created cross object.
        :rtype: dict
        """
        cross = Cross(
            datetime_start=datetime_start,
            executed=executed,
            description=description,
            distance=distance,
        )
        await self._service.add(cross)
        # Ensure we return the actual dict, not a coroutine or None
        return await self.get_cross_view(cross.id)

    async def list_crosses(self) -> list[Dict]:
        """
        Asynchronously retrieves a list of crosses and returns it in a formatted manner. The crosses
        are first sorted by `datetime_start` in descending order, and then by `id` in descending
        order. If no crosses are found, an empty list is returned. Each cross is represented by a
        dictionary containing specific details such as `id`, `datetime_start`, `executed`,
        `description`, and `distance`.

        :return: A list of dictionaries containing details of crosses after sorting.
        :rtype: list[Dict]
        """
        crosses: list[Cross] = await self._service.get_all_crosses()
        if not crosses:
            return []
        # sort by datetime_start desc, then id desc
        crosses.sort(key=lambda c: (c.datetime_start, c.id), reverse=False)
        return [
            {
                "id": c.id,
                "datetime_start": c.datetime_start,
                "executed": c.executed,
                "description": c.description,
                "distance": c.distance,
            }
            for c in crosses
        ]

    async def update_cross(
        self,
        cross_id: int,
        *,
        datetime_start: datetime | None = None,
        executed: bool | None = None,
        description: str | None = None,
        distance: int | None = None,
    ) -> Dict:
        """
        Updates the details of a specified cross. This method allows modifying attributes
        such as the start time, execution status, description, or distance of the cross,
        and then returns the updated details.

        :param cross_id: The unique identifier of the cross to be updated.
        :type cross_id: int
        :param datetime_start: The new start date and time for the cross. Optional.
        :param executed: The execution status of the cross. Optional.
        :param description: A brief description of the cross. Optional.
        :param distance: The distance associated with the cross. Optional.
        :return: A dictionary containing the updated cross details.
        :rtype: Dict
        """
        return await self.set_cross_details(
            cross_id,
            datetime_start=datetime_start,
            executed=executed,
            description=description,
            distance=distance,
        )

    def delete_cross(self, cross_id: int) -> None:
        """
        Deletes a cross entry identified by its ID.

        This method is used to remove a specific cross record from the system
        by its unique identifier. The operation assumes that the cross record
        exists and will call the appropriate service layer method to delete the
        record.

        :param cross_id: The unique identifier of the cross entry to delete.
        :type cross_id: int
        :return: None
        """
        cross = self.get_cross(cross_id)
        self._service.delete_cross(cross_id)

    # --- Getters already present ---
    async def get_cross(self, cross_id: int) -> Cross:
        """
        Fetches a cross object by its unique identifier.

        This method retrieves a cross object from the service based on the given cross
        ID. If the cross object does not exist, a ValueError is raised.

        :param cross_id: The unique identifier of the cross object to be retrieved.
        :type cross_id: int
        :return: The cross object corresponding to the provided ID.
        :rtype: Cross
        :raises ValueError: If the cross object with the given ID is not found.
        """
        cross = await self._service.get_cross(cross_id)
        if not cross:
            raise ValueError(f"Cross {cross_id} not found")
        return cross

    async def get_cross_view(self, cross_id: int) -> Dict:
        """
        Asynchronously retrieves a detailed view of a cross entity, including its ID,
        start datetime, execution status, description, and distance.

        :param cross_id: The unique identifier for the cross entity.
        :type cross_id: int
        :return: A dictionary containing details of the specified cross entity,
            including its ID, start datetime, execution status, description,
            and distance.
        :rtype: Dict
        """
        cross = await self.get_cross(cross_id)

        return {
            "id": cross.id,
            "datetime_start": cross.datetime_start,
            "executed": cross.executed,
            "description": cross.description,
            "distance": cross.distance,
        }

    async def set_cross_details(
        self,
        cross_id: int,
        *,
        datetime_start: Optional[datetime] = None,
        executed: Optional[bool] = None,
        description: Optional[str] = None,
        distance: Optional[float] = None,
    ) -> Dict:
        """
        Set the details of a cross by updating its attributes with the provided values
        and returning its updated view representation.

        :param cross_id: Unique identifier of the cross to be updated.
        :type cross_id: int
        :param datetime_start: Start datetime for the cross. Defaults to None.
        :type datetime_start: Optional[datetime]
        :param executed: Indicates whether the cross has been executed. Defaults to None.
        :type executed: Optional[bool]
        :param description: Description of the cross. Defaults to None.
        :type description: Optional[str]
        :param distance: Distance of the cross in relevant measurement units. Defaults to None.
        :type distance: Optional[float]
        :return: A dictionary representing the updated cross view.
        :rtype: Dict
        """
        cross = await self.get_cross(cross_id)
        if datetime_start is not None:
            cross.datetime_start = datetime_start
        if executed is not None:
            cross.executed = executed
        if description is not None:
            cross.description = description
        if distance is not None:
            cross.distance = distance

        await self._service.update_cross(cross)

        return await self.get_cross_view(cross_id)
