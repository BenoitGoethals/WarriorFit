from datetime import datetime
from typing import Dict, Optional, List

from data.db.db_model import Cross, Runner
from services.service_cross import ServiceCross


class CrossPlannigController:
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
    def create_cross(self, *, datetime_start: datetime, executed: bool = False, description: str | None = None) -> Dict:
        cross = Cross(datetime_start=datetime_start, executed=executed, description=description)
        self._service.add(cross)
        return self.get_cross_view(cross.id)

    def list_crosses(self) -> list[Dict]:
        crosses: list[Cross] = self._service.list_all(Cross)
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

    def update_cross(self, cross_id: int, *, datetime_start: datetime | None = None, executed: bool | None = None, description: str | None = None) -> Dict:
        return self.set_cross_details(cross_id, datetime_start=datetime_start, executed=executed, description=description)

    def delete_cross(self, cross_id: int) -> None:
        cross = self.get_cross(cross_id)
        self._service.delete(cross)

    # --- Getters already present ---
    def get_cross(self, cross_id: int) -> Cross:
        cross = self._service.get(Cross, cross_id)
        if not cross:
            raise ValueError(f"Cross {cross_id} not found")
        return cross

    def get_cross_view(self, cross_id: int) -> Dict:
        """
        Returns the cross details with:
        - runners: ordered list by running_time asc
        - runners_by_serial: dict serial_number -> ordered list of runners
        """
        cross = self.get_cross(cross_id)
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

    # --- Runner attach/detach ---
    def add_runner(self, cross_id: int, runner_id: int) -> Dict:
        """
        Adds a runner to the cross if not already present.
        Returns fresh cross view.
        """
        cross = self.get_cross(cross_id)
        runner = self._service.get(Runner, runner_id)
        if not runner:
            raise ValueError(f"Runner {runner_id} not found")

        if runner not in cross.runners:
            cross.runners.append(runner)
            self._service.add(cross)

        return self.get_cross_view(cross_id)

    def remove_runner(self, cross_id: int, runner_id: int) -> Dict:
        """
        Removes a runner from the cross if present.
        Returns fresh cross view.
        """
        cross = self.get_cross(cross_id)
        runner = self._service.get(Runner, runner_id)
        if not runner:
            raise ValueError(f"Runner {runner_id} not found")

        if runner in cross.runners:
            cross.runners.remove(runner)
            self._service.add(cross)

        return self.get_cross_view(cross_id)

    def set_cross_details(
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

        self._service.add(cross)

        return self.get_cross_view(cross_id)

    # --- Runner CRUD (optional convenience) ---
    def create_runner(self, *, serial_number: str | None, running_time: float) -> Dict:
        runner = Runner(serial_number=serial_number, running_time=running_time)
        self._service.add(runner)
        return {"id": runner.id, "serial_number": runner.serial_number, "running_time": runner.running_time}

    def list_runners(self) -> list[Dict]:
        runners: list[Runner] = self._service.list_all(Runner)
        runners.sort(key=lambda r: (r.running_time, r.id))
        return [{"id": r.id, "serial_number": r.serial_number, "running_time": r.running_time} for r in runners]

    def delete_runner(self, runner_id: int) -> None:
        runner = self._service.get(Runner, runner_id)
        if not runner:
            raise ValueError(f"Runner {runner_id} not found")
        self._service.delete(runner)
# ... existing code ...eCross()