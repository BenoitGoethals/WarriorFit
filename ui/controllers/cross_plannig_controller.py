from datetime import datetime
from typing import Dict, Optional, List, Any, Coroutine

from data.db.db_model import Cross, Runner
from services.service_cross import ServiceCross


class CrossPlanningController:
    """
    Controller for managing Cross registrations:
    - add/remove runners to a cross
    - return ordered runners list (by running_time asc)
    - group by serial_number for display
    - CRUD for Cross and Runner
    """

    def __init__(self):
        self._service = ServiceCross()

    # --- CRUD Cross ---
    async def create_cross(self, *, datetime_start: datetime, executed: bool = False, description: str | None = None) -> \
    Coroutine[Any, Any, dict]:
        cross = Cross(datetime_start=datetime_start, executed=executed, description=description)
        await self._service.add(cross)
        return  self.get_cross_view(cross.id)

    async def list_crosses(self) -> list[Dict]:
        crosses: list[Cross] = await self._service.get_all_crosses()
        if not crosses:
            return []
        # sort by datetime_start desc, then id desc
        crosses.sort(key=lambda c: (c.datetime_start, c.id), reverse=True)
        return [
            {
                "id": c.id,
                "datetime_start": c.datetime_start,
                "executed": c.executed,
                "description": c.description,
                "runners_count": len(c.runners or []),
            }
            for c in crosses
        ]

    async def update_cross(self, cross_id: int, *, datetime_start: datetime | None = None, executed: bool | None = None, description: str | None = None) -> Dict:
        return await self.set_cross_details(cross_id, datetime_start=datetime_start, executed=executed, description=description)

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
        """
        Returns the cross details with:
        - runners: ordered list by running_time asc
        - runners_by_serial: dict serial_number -> ordered list of runners
        """
        cross =  await self.get_cross(cross_id)
        runners = list(cross.runners or [])
        runners.sort(key=lambda r: (r.running_time, r.id))

        runners_list = [
            {
                "id": r.id,
                "serial_number": r.serial_number,
                "running_time": r.running_time,
            }
            for r in runners
        ]

        runners_by_serial: Dict[str, List[Dict]] = {}
        for r in runners_list:
            key = r["serial_number"] or ""
            runners_by_serial.setdefault(key, []).append(r)

        return {
            "id": cross.id,
            "datetime_start": cross.datetime_start,
            "executed": cross.executed,
            "description": cross.description,
            "runners": runners_list,
            "runners_by_serial": runners_by_serial,
        }


    async def set_cross_details(
        self,
        cross_id: int,
        *,
        datetime_start: Optional[datetime] = None,
        executed: Optional[bool] = None,
        description: Optional[str] = None,
    ) -> Dict:
        """
        Update basic cross fields. Returns fresh view.
        """
        cross = self.get_cross(cross_id)
        if datetime_start is not None:
            cross.datetime_start = datetime_start
        if executed is not None:
            cross.executed = executed
        if description is not None:
            cross.description = description

        await self._service.add(cross)

        return await self.get_cross_view(cross_id)

