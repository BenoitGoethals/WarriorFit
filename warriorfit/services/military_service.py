from warriorfit.data.model.db_model import ServiceMen
from warriorfit.data.repositories.servicemen_repository import ServicemenRepository
from warriorfit.services.be_mil_service import BEMILService


class MilitaryService:
    """
    Handles operations related to military service management.

    Provides methods for adding, updating, retrieving, and performing various
    operations on servicemen and military units. This class serves as an interface
    that interacts with an underlying repository to manage military personnel and
    unit data.
    """
    def __init__(self):
        """
        Initializes the MilitaryService with a ServicemenRepository.
        """
        self._repo = ServicemenRepository()
        self._be_mil_service=BEMILService()


    async def add_service_men(self, service_men):
        """
        Adds a new serviceman to the repository.

        Args:
            service_men: The serviceman object to add.

        Returns:
            The created serviceman object.
        """
        return await self._repo.create_serviceman(service_men)

    async def update_service_men(self, service_men):
        """
        Updates an existing serviceman in the repository.

        Args:
            service_men: The serviceman object with updated information.

        Returns:
            The updated serviceman object.
        """
        return await self._repo.update_serviceman(service_men=service_men)

    async def get_all_service_men(self):
        """
        Retrieves all servicemen from the repository.

        Returns:
            A list of all servicemen.
        """
        return await self._repo.list_all()

    async def get_servicemen_by_id(self, ind_id):
        """
        Retrieves a serviceman by their ID.

        Args:
            ind_id: The ID of the serviceman.

        Returns:
            The serviceman object if found.
        """
        return await self._repo.get_servicemen_by_id(ind_id)

    async def get_servicemen_by_serial(self, serial: str, lazy=True)->ServiceMen|None:

        sm= await self._repo.get_by_service_number(serial, lazy=lazy)
        if not sm:
           sm = await self._be_mil_service.get_be_mil_by_id(serial)
        return sm


    async def get_all_units(self):
        """
        Retrieves all military units from the repository.

        Returns:
            A list of all military units.
        """
        return await self._repo.list_all_units()

    async def add_unit(self, unit):
        """
        Adds a new military unit to the repository.

        Args:
            unit: The unit object to add.

        Returns:
            The created unit object.
        """
        return await self._repo.add_unit(unit)

    def get_unit_by_id(self, ind_id):
        """
        Retrieves a military unit by its ID.

        Args:
            ind_id: The ID of the unit.

        Returns:
            The unit object if found.
        """
        return self._repo.get_by_unit_id(ind_id)

    async def get_all_be_mil_from_unit(self, own_unit):
        """
        Retrieves all servicemen belonging to a specific unit.

        Args:
            own_unit: The unit to filter servicemen by.

        Returns:
            A list of servicemen in the specified unit.
        """
        return await self._repo.get_all_be_mil_from_unit(own_unit)
