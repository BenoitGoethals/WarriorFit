from datetime import datetime
from typing import Dict, Optional

from warriorfit.data.db.db_model import Cross
from warriorfit.services.service_cross import ServiceCross


class CrossPlanningController:
    """
    Controller for managing Cross registrations:


    - group by serial_number for display
    - CRUD for Cross and Runner
    """

    def __init__(self):
        self._service = ServiceCross()

    # --- CRUD Cross ---
    async def create_cross(self, *, datetime_start: datetime, executed: bool = False, description: str | None = None, distance: float | None = None) :

        cross = Cross(datetime_start=datetime_start, executed=executed, description=description, distance=distance)
        await self._service.add(cross)
        # Ensure we return the actual dict, not a coroutine or None
        return await self.get_cross_view(cross.id)

    async def list_crosses(self) -> list[Dict]:
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

    async def update_cross(self, cross_id: int, *, datetime_start: datetime | None = None, executed: bool | None = None, description: str | None = None, distance: int | None = None) -> Dict:
        return await self.set_cross_details(cross_id, datetime_start=datetime_start, executed=executed, description=description, distance=distance)

    def delete_cross(self, cross_id: int) -> None:
        cross = self.get_cross(cross_id)
        self._service.delete_cross(cross_id)

    # --- Getters already present ---
    async def get_cross(self, cross_id: int) -> Cross:
        cross = await self._service.get_cross(cross_id)
        if not cross:
            raise ValueError(f"Cross {cross_id} not found")
        return cross

    async def get_cross_view(self, cross_id: int) -> Dict:


        cross =  await self.get_cross(cross_id)

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
        Update basic cross fields. Returns fresh view.
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

